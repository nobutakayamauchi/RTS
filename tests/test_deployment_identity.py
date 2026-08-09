from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from deployment_identity.cli import main
from deployment_identity.core import (
    BOUND,
    DeploymentIdentityError,
    ESTABLISHED,
    NOT_BOUND,
    NOT_ESTABLISHED,
    bind_runtime_observation,
    establish_deployment_identity,
    fingerprint_observation,
)


class DeploymentIdentityTests(unittest.TestCase):
    def expectation(self) -> dict:
        return {
            "source_revision": "abc123",
            "artifact_digest": "sha256:artifact-good",
            "config_fingerprint": "sha256:config-good",
            "environment_fingerprint": "sha256:env-good",
        }

    def instance(self, instance_id: str = "worker-1") -> dict:
        return {
            "instance_id": instance_id,
            "revision": "abc123",
            "artifact_digest": "sha256:artifact-good",
            "config_fingerprint": "sha256:config-good",
            "environment_fingerprint": "sha256:env-good",
        }

    def observation(self) -> dict:
        return {
            "service_unit": "rts-video-flow-web.service",
            "working_directory": "/srv/rts-video-flow",
            "executable_or_module": "python -m app.web",
            "active_route_surface": "POST /render",
            "deployed_revision": "abc123",
            "deployed_artifact_digest": "sha256:artifact-good",
            "runtime_config_fingerprint": "sha256:config-good",
            "runtime_environment_fingerprint": "sha256:env-good",
            "source_tree_state": "CLEAN",
            "runtime_instances": [self.instance()],
            "active_route_instance_ids": ["worker-1"],
            "observer_id": "observer-prod-01",
            "observation_session_id": "session-001",
            "observed_at": "2026-08-09T17:00:00+09:00",
        }

    def establish(self, observation: dict | None = None, **kwargs):
        return establish_deployment_identity(
            observation or self.observation(),
            expected_deployment=kwargs.get("expected_deployment", self.expectation()),
            trusted_observer_ids=kwargs.get("trusted_observer_ids", {"observer-prod-01"}),
            reference_time=kwargs.get("reference_time", "2026-08-09T17:00:10+09:00"),
            max_age_seconds=kwargs.get("max_age_seconds", 300),
        )

    def runtime_observation(self, proof: dict, observed_at: str = "2026-08-09T17:00:15+09:00") -> dict:
        return {
            "deployment_identity_fingerprint": proof["observation_fingerprint"],
            "deployment_expectation_fingerprint": proof["expectation_fingerprint"],
            "observation_session_id": "session-001",
            "observed_at": observed_at,
            "result": {"status": "ok"},
        }

    def test_matching_material_and_route_set_establishes_identity(self) -> None:
        result = self.establish()
        self.assertEqual(result["status"], ESTABLISHED)
        self.assertTrue(result["runtime_classification_authorized"])
        self.assertEqual(result["identity"]["revision"], "abc123")
        self.assertEqual(result["identity"]["active_route_instance_ids"], ["worker-1"])

    def test_untrusted_observer_cannot_self_authorize(self) -> None:
        observation = self.observation()
        observation["observer_id"] = "attacker-self-declared"
        result = self.establish(observation)
        self.assertEqual(result["reason"], "UNTRUSTED_OBSERVER")

    def test_stale_or_future_observation_fails_closed(self) -> None:
        self.assertEqual(
            self.establish(reference_time="2026-08-09T17:10:01+09:00", max_age_seconds=300)["reason"],
            "STALE_OR_FUTURE_OBSERVATION",
        )
        self.assertEqual(
            self.establish(reference_time="2026-08-09T16:59:59+09:00")["reason"],
            "STALE_OR_FUTURE_OBSERVATION",
        )

    def test_dirty_source_tree_fails_even_when_revision_matches(self) -> None:
        observation = self.observation()
        observation["source_tree_state"] = "DIRTY"
        result = self.establish(observation)
        self.assertEqual(result["status"], NOT_ESTABLISHED)
        self.assertEqual(result["reason"], "SOURCE_TREE_NOT_CLEAN")

    def test_same_revision_with_different_artifact_fails(self) -> None:
        observation = self.observation()
        observation["deployed_artifact_digest"] = "sha256:artifact-other"
        result = self.establish(observation)
        self.assertEqual(result["reason"], "ARTIFACT_DIGEST_MISMATCH")

    def test_same_revision_with_different_config_fails(self) -> None:
        observation = self.observation()
        observation["runtime_config_fingerprint"] = "sha256:config-other"
        result = self.establish(observation)
        self.assertEqual(result["reason"], "CONFIG_FINGERPRINT_MISMATCH")

    def test_same_revision_with_different_environment_fails(self) -> None:
        observation = self.observation()
        observation["runtime_environment_fingerprint"] = "sha256:env-other"
        result = self.establish(observation)
        self.assertEqual(result["reason"], "ENVIRONMENT_FINGERPRINT_MISMATCH")

    def test_expectation_is_external_not_self_declared_source_revision(self) -> None:
        expectation = self.expectation()
        expectation["source_revision"] = "wanted999"
        result = self.establish(expected_deployment=expectation)
        self.assertEqual(result["reason"], "DEPLOYED_REVISION_MISMATCH")

    def test_reverse_proxy_route_cannot_reference_unknown_worker(self) -> None:
        observation = self.observation()
        observation["active_route_instance_ids"] = ["worker-not-observed"]
        with self.assertRaisesRegex(DeploymentIdentityError, "unknown runtime instance"):
            self.establish(observation)

    def test_heterogeneous_routed_worker_revision_fails(self) -> None:
        observation = self.observation()
        stale = self.instance("worker-2")
        stale["revision"] = "old456"
        observation["runtime_instances"].append(stale)
        observation["active_route_instance_ids"] = ["worker-1", "worker-2"]
        result = self.establish(observation)
        self.assertEqual(result["reason"], "ROUTE_INSTANCE_REVISION_MISMATCH")
        self.assertEqual(result["instance_id"], "worker-2")

    def test_heterogeneous_routed_worker_artifact_fails(self) -> None:
        observation = self.observation()
        other = self.instance("worker-2")
        other["artifact_digest"] = "sha256:other"
        observation["runtime_instances"].append(other)
        observation["active_route_instance_ids"] = ["worker-1", "worker-2"]
        result = self.establish(observation)
        self.assertEqual(result["reason"], "ROUTE_INSTANCE_ARTIFACT_MISMATCH")

    def test_non_routed_old_worker_does_not_define_active_route_reality(self) -> None:
        observation = self.observation()
        stale = self.instance("worker-idle")
        stale["revision"] = "old456"
        observation["runtime_instances"].append(stale)
        result = self.establish(observation)
        self.assertEqual(result["status"], ESTABLISHED)

    def test_duplicate_instance_ids_fail_closed(self) -> None:
        observation = self.observation()
        observation["runtime_instances"].append(self.instance("worker-1"))
        with self.assertRaisesRegex(DeploymentIdentityError, "duplicate runtime instance"):
            self.establish(observation)

    def test_runtime_observation_requires_both_observed_and_expected_material_fingerprints(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof)
        runtime["deployment_expectation_fingerprint"] = "forged"
        result = bind_runtime_observation(proof, runtime)
        self.assertEqual(result["status"], NOT_BOUND)
        self.assertEqual(result["reason"], "DEPLOYMENT_EXPECTATION_FINGERPRINT_MISMATCH")

    def test_runtime_observation_requires_exact_deployment_fingerprint(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof)
        runtime["deployment_identity_fingerprint"] = "forged"
        result = bind_runtime_observation(proof, runtime)
        self.assertEqual(result["reason"], "DEPLOYMENT_FINGERPRINT_MISMATCH")

    def test_runtime_observation_requires_same_session_and_time_window(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof)
        runtime["observation_session_id"] = "other-session"
        self.assertEqual(bind_runtime_observation(proof, runtime)["reason"], "OBSERVATION_SESSION_MISMATCH")

        runtime = self.runtime_observation(proof, "2026-08-09T17:01:00+09:00")
        self.assertEqual(
            bind_runtime_observation(proof, runtime, max_skew_seconds=30)["reason"],
            "RUNTIME_OBSERVATION_OUTSIDE_BINDING_WINDOW",
        )

    def test_runtime_observation_binds_inside_window(self) -> None:
        proof = self.establish()
        result = bind_runtime_observation(proof, self.runtime_observation(proof), max_skew_seconds=30)
        self.assertEqual(result["status"], BOUND)
        self.assertTrue(result["runtime_classification_authorized"])

    def test_cli_requires_external_expectation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            expectation_path = Path(temporary) / "expectation.json"
            observation_path.write_text(json.dumps(self.observation()), encoding="utf-8")
            expectation_path.write_text(json.dumps(self.expectation()), encoding="utf-8")
            self.assertEqual(main([
                "verify", "--observation", str(observation_path),
                "--expectation", str(expectation_path),
                "--trusted-observer-id", "observer-prod-01",
                "--reference-time", "2026-08-09T17:00:10+09:00",
            ]), 0)

    def test_code_existence_alone_cannot_establish_identity(self) -> None:
        source_only = {
            "deployed_revision": "abc123",
            "observed_at": "2026-08-09T17:00:00+09:00",
        }
        with self.assertRaises(DeploymentIdentityError):
            self.establish(source_only)

    def test_fingerprint_is_deterministic_and_order_independent(self) -> None:
        first = self.observation()
        second = dict(reversed(list(first.items())))
        self.assertEqual(fingerprint_observation(first), fingerprint_observation(second))


if __name__ == "__main__":
    unittest.main()
