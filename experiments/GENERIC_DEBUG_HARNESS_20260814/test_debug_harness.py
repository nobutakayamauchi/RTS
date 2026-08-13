import copy
import unittest

from deployment_identity.core import fingerprint_expectation, fingerprint_observation
from experiments.GENERIC_DEBUG_HARNESS_20260814.debug_harness import evaluate
from tests.test_deployment_identity import DeploymentIdentityTests


def identity_pair(session: str, observed_at: str):
    fixture = DeploymentIdentityTests()
    observation = fixture.observation()
    observation["observation_session_id"] = session
    observation["observed_at"] = observed_at
    expected = fixture.expectation()
    evidence = {
        "observation": observation,
        "attestations": fixture.attestations(observation, expected),
        "collector_provenance": fixture.provenance(observation, expected),
    }
    verifier = {
        "expected_deployment": expected,
        "trusted_observer_ids": ["observer-prod-01"],
        "reference_time": "2026-08-09T17:00:10+09:00",
        "trusted_attestation_keys": fixture.attestor_keys(),
        "trusted_collector_keys": fixture.collector_keys(),
        "trusted_collector_domains": fixture.collector_domains(),
    }
    return evidence, verifier


def probe_result(evidence, verifier, status: str, definition: str = "probe:v1"):
    observation = evidence["observation"]
    expected = verifier["expected_deployment"]
    return {
        "probe_id": "health",
        "definition_fingerprint": definition,
        "status": status,
        "evidence_refs": [f"health:{status}"],
        "deployment_observation_fingerprint": fingerprint_observation(observation),
        "deployment_expectation_fingerprint": fingerprint_expectation(expected),
        "observation_session_id": observation["observation_session_id"],
    }


class RealDeploymentIdentityIntegrationTests(unittest.TestCase):
    def case_and_verifiers(self):
        before, initial_verifier = identity_pair("session-001", "2026-08-09T17:00:00+09:00")
        after, post_verifier = identity_pair("session-002", "2026-08-09T17:00:01+09:00")
        case = {
            "deployment_identity_evidence": before,
            "probe_manifest": [
                {"probe_id": "health", "definition_fingerprint": "probe:v1", "required": True}
            ],
            "probe_results": [probe_result(before, initial_verifier, "FAIL")],
            "regression_manifest": {"suite_fingerprint": "regression:v1"},
            "patch": {
                "applied": True,
                "applied_at": "2026-08-09T17:00:00.500000+09:00",
                "post_deployment_identity_evidence": after,
                "replay_results": [probe_result(after, post_verifier, "PASS")],
                "regression_result": {
                    "suite_fingerprint": "regression:v1",
                    "status": "PASS",
                    "evidence_refs": ["regression:pass"],
                    "deployment_observation_fingerprint": fingerprint_observation(after["observation"]),
                    "deployment_expectation_fingerprint": fingerprint_expectation(post_verifier["expected_deployment"]),
                    "observation_session_id": after["observation"]["observation_session_id"],
                },
            },
        }
        verifiers = {"initial": initial_verifier, "post_patch": post_verifier}
        return case, verifiers

    def test_real_identity_fix_chain(self):
        case, verifiers = self.case_and_verifiers()
        self.assertEqual(evaluate(case, identity_verifiers=verifiers)["state"], "FIX_VALIDATED")

    def test_clean_initial_deployment(self):
        case, verifiers = self.case_and_verifiers()
        case["probe_results"][0]["status"] = "PASS"
        case.pop("patch")
        result = evaluate(case, identity_verifiers=verifiers)
        self.assertEqual(result["state"], "DEPLOYMENT_VALIDATED")
        self.assertTrue(result["stable_eligible"])

    def test_evidence_cannot_supply_trust_anchors(self):
        case, verifiers = self.case_and_verifiers()
        case["deployment_identity_evidence"]["trusted_attestation_keys"] = {"attacker": "secret"}
        with self.assertRaises(ValueError):
            evaluate(case, identity_verifiers=verifiers)

    def test_fake_identity_shape_rejected(self):
        case, verifiers = self.case_and_verifiers()
        case["deployment_identity_evidence"] = {"status": "ESTABLISHED", "fingerprint": "fake"}
        with self.assertRaises(ValueError):
            evaluate(case, identity_verifiers=verifiers)

    def test_probe_definition_drift_rejected(self):
        case, verifiers = self.case_and_verifiers()
        case["patch"]["replay_results"][0]["definition_fingerprint"] = "probe:weakened"
        with self.assertRaises(ValueError):
            evaluate(case, identity_verifiers=verifiers)

    def test_reused_initial_identity_cannot_validate_patch(self):
        case, verifiers = self.case_and_verifiers()
        initial_evidence = case["deployment_identity_evidence"]
        initial_verifier = verifiers["initial"]
        case["patch"]["post_deployment_identity_evidence"] = copy.deepcopy(initial_evidence)
        verifiers["post_patch"] = copy.deepcopy(initial_verifier)
        case["patch"]["replay_results"] = [probe_result(initial_evidence, initial_verifier, "PASS")]
        case["patch"]["regression_result"]["deployment_observation_fingerprint"] = fingerprint_observation(initial_evidence["observation"])
        case["patch"]["regression_result"]["deployment_expectation_fingerprint"] = fingerprint_expectation(initial_verifier["expected_deployment"])
        case["patch"]["regression_result"]["observation_session_id"] = initial_evidence["observation"]["observation_session_id"]
        result = evaluate(case, identity_verifiers=verifiers)
        self.assertEqual(result["state"], "PATCH_NOT_VALIDATED")
        self.assertIn("POST_PATCH_SESSION_NOT_NEW", result["blocking_states"])
        self.assertIn("POST_PATCH_TEMPORAL_ORDER_NOT_PROVEN", result["blocking_states"])

    def test_stale_post_patch_identity_rejected(self):
        case, verifiers = self.case_and_verifiers()
        verifiers["post_patch"]["reference_time"] = "2026-08-09T18:00:10+09:00"
        with self.assertRaises(ValueError):
            evaluate(case, identity_verifiers=verifiers)


if __name__ == "__main__":
    unittest.main()
