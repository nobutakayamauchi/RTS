import copy
import unittest

from deployment_identity.core import fingerprint_expectation, fingerprint_observation
from experiments.GENERIC_DEBUG_HARNESS_20260814.debug_harness import evaluate
from tests.test_deployment_identity import DeploymentIdentityTests


def bundle(session: str):
    fixture = DeploymentIdentityTests()
    observation = fixture.observation()
    observation["observation_session_id"] = session
    expected = fixture.expectation()
    return {
        "observation": observation,
        "expected_deployment": expected,
        "trusted_observer_ids": ["observer-prod-01"],
        "reference_time": "2026-08-09T17:00:10+09:00",
        "attestations": fixture.attestations(observation, expected),
        "trusted_attestation_keys": fixture.attestor_keys(),
        "collector_provenance": fixture.provenance(observation, expected),
        "trusted_collector_keys": fixture.collector_keys(),
        "trusted_collector_domains": fixture.collector_domains(),
    }


def probe_result(identity_bundle, status: str, definition: str = "probe:v1"):
    observation = identity_bundle["observation"]
    expected = identity_bundle["expected_deployment"]
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
    def case(self):
        before = bundle("session-001")
        after = bundle("session-002")
        return {
            "deployment_identity_bundle": before,
            "probe_manifest": [
                {"probe_id": "health", "definition_fingerprint": "probe:v1", "required": True}
            ],
            "probe_results": [probe_result(before, "FAIL")],
            "regression_manifest": {"suite_fingerprint": "regression:v1"},
            "patch": {
                "applied": True,
                "post_deployment_identity_bundle": after,
                "replay_results": [probe_result(after, "PASS")],
                "regression_result": {
                    "suite_fingerprint": "regression:v1",
                    "status": "PASS",
                    "evidence_refs": ["regression:pass"],
                    "deployment_observation_fingerprint": fingerprint_observation(after["observation"]),
                    "deployment_expectation_fingerprint": fingerprint_expectation(after["expected_deployment"]),
                    "observation_session_id": after["observation"]["observation_session_id"],
                },
            },
        }

    def test_real_identity_fix_chain(self):
        self.assertEqual(evaluate(self.case())["state"], "FIX_VALIDATED")

    def test_clean_initial_deployment(self):
        case = self.case()
        case["probe_results"][0]["status"] = "PASS"
        case.pop("patch")
        result = evaluate(case)
        self.assertEqual(result["state"], "DEPLOYMENT_VALIDATED")
        self.assertTrue(result["stable_eligible"])

    def test_fake_identity_rejected(self):
        case = self.case()
        case["deployment_identity_bundle"] = {"status": "ESTABLISHED", "fingerprint": "fake"}
        with self.assertRaises(ValueError):
            evaluate(case)

    def test_probe_definition_drift_rejected(self):
        case = self.case()
        case["patch"]["replay_results"][0]["definition_fingerprint"] = "probe:weakened"
        with self.assertRaises(ValueError):
            evaluate(case)

    def test_stale_post_patch_identity_rejected(self):
        case = self.case()
        case["patch"]["post_deployment_identity_bundle"]["reference_time"] = "2026-08-09T18:00:10+09:00"
        with self.assertRaises(ValueError):
            evaluate(case)


if __name__ == "__main__":
    unittest.main()
