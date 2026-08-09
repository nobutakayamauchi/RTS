from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from deployment_identity.attestation import (
    AttestationError,
    compute_hmac_signature,
    establish_attested_deployment_identity,
)
from deployment_identity.cli import main
from deployment_identity.core import (
    BOUND,
    ESTABLISHED,
    NOT_BOUND,
    NOT_ESTABLISHED,
    DeploymentIdentityError,
    bind_runtime_observation,
    establish_deployment_identity,
    fingerprint_expectation,
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

    def keyring(self) -> dict[str, str]:
        return {"attestor-a": "secret-a", "attestor-b": "secret-b", "attestor-c": "secret-c"}

    def make_attestation(self, attestor_id: str, observation: dict | None = None, expectation: dict | None = None) -> dict:
        observation = observation or self.observation()
        expectation = expectation or self.expectation()
        material = {
            "attestor_id": attestor_id,
            "observation_fingerprint": fingerprint_observation(observation),
            "expectation_fingerprint": fingerprint_expectation(expectation),
            "observation_session_id": observation["observation_session_id"],
            "issued_at": "2026-08-09T17:00:05+09:00",
        }
        return {**material, "signature": compute_hmac_signature(material, self.keyring()[attestor_id])}

    def attestations(self, observation: dict | None = None, expectation: dict | None = None) -> list[dict]:
        return [
            self.make_attestation("attestor-a", observation, expectation),
            self.make_attestation("attestor-b", observation, expectation),
        ]

    def material_proof(self, observation: dict | None = None, expectation: dict | None = None, **kwargs):
        return establish_deployment_identity(
            observation or self.observation(),
            expected_deployment=expectation or self.expectation(),
            trusted_observer_ids=kwargs.get("trusted_observer_ids", {"observer-prod-01"}),
            reference_time=kwargs.get("reference_time", "2026-08-09T17:00:10+09:00"),
            max_age_seconds=kwargs.get("max_age_seconds", 300),
        )

    def establish(self, observation: dict | None = None, expectation: dict | None = None, **kwargs):
        observation = observation or self.observation()
        expectation = expectation or self.expectation()
        return establish_attested_deployment_identity(
            observation,
            expected_deployment=expectation,
            trusted_observer_ids=kwargs.get("trusted_observer_ids", ["observer-prod-01"]),
            reference_time=kwargs.get("reference_time", "2026-08-09T17:00:10+09:00"),
            attestations=kwargs.get("attestations", self.attestations(observation, expectation)),
            trusted_attestation_keys=kwargs.get("trusted_attestation_keys", self.keyring()),
            max_age_seconds=kwargs.get("max_age_seconds", 300),
            min_attestors=kwargs.get("min_attestors", 2),
        )

    def runtime_observation(self, proof: dict, observed_at: str = "2026-08-09T17:00:15+09:00") -> dict:
        return {
            "deployment_identity_fingerprint": proof["observation_fingerprint"],
            "deployment_expectation_fingerprint": proof["expectation_fingerprint"],
            "observation_session_id": "session-001",
            "observed_at": observed_at,
            "result": {"status": "ok"},
        }

    def test_raw_material_match_cannot_authorize_runtime_classification(self) -> None:
        proof = self.material_proof()
        self.assertEqual(proof["status"], ESTABLISHED)
        self.assertTrue(proof["material_match_verified"])
        self.assertFalse(proof["runtime_classification_authorized"])
        self.assertEqual(proof["reason"], "RUNTIME_MATERIAL_MATCH_ATTESTATION_REQUIRED")
        result = bind_runtime_observation(proof, self.runtime_observation(proof))
        self.assertEqual(result["status"], NOT_BOUND)
        self.assertEqual(result["reason"], "DEPLOYMENT_IDENTITY_NOT_FULLY_AUTHORIZED")

    def test_two_independent_signed_attestors_authorize(self) -> None:
        proof = self.establish()
        self.assertEqual(proof["status"], ESTABLISHED)
        self.assertTrue(proof["runtime_classification_authorized"])
        self.assertEqual(proof["attestation_quorum"]["verified_attestors"], ["attestor-a", "attestor-b"])

    def test_single_attestor_cannot_authorize(self) -> None:
        with self.assertRaisesRegex(AttestationError, "quorum not met"):
            self.establish(attestations=[self.make_attestation("attestor-a")])

    def test_duplicate_attestor_cannot_fake_quorum(self) -> None:
        attestation = self.make_attestation("attestor-a")
        with self.assertRaisesRegex(AttestationError, "duplicate attestor_id"):
            self.establish(attestations=[attestation, dict(attestation)])

    def test_forged_signature_fails_closed(self) -> None:
        attestations = self.attestations()
        attestations[1]["signature"] = "0" * 64
        with self.assertRaisesRegex(AttestationError, "invalid signature"):
            self.establish(attestations=attestations)

    def test_untrusted_attestor_fails_closed(self) -> None:
        attestations = self.attestations()
        material = {
            "attestor_id": "attacker",
            "observation_fingerprint": fingerprint_observation(self.observation()),
            "expectation_fingerprint": fingerprint_expectation(self.expectation()),
            "observation_session_id": "session-001",
            "issued_at": "2026-08-09T17:00:05+09:00",
        }
        attestations[1] = {**material, "signature": compute_hmac_signature(material, "attacker-secret")}
        with self.assertRaisesRegex(AttestationError, "untrusted attestor_id"):
            self.establish(attestations=attestations)

    def test_attestor_cannot_sign_different_observation_or_expectation(self) -> None:
        altered = self.observation()
        altered["deployed_revision"] = "other"
        bad = self.make_attestation("attestor-b", altered, self.expectation())
        with self.assertRaisesRegex(AttestationError, "different observation"):
            self.establish(attestations=[self.make_attestation("attestor-a"), bad])

        altered_expectation = self.expectation()
        altered_expectation["artifact_digest"] = "sha256:other"
        bad = self.make_attestation("attestor-b", self.observation(), altered_expectation)
        with self.assertRaisesRegex(AttestationError, "different expectation"):
            self.establish(attestations=[self.make_attestation("attestor-a"), bad])

    def test_stale_attestation_replay_fails_closed(self) -> None:
        with self.assertRaisesRegex(AttestationError, "stale or future-dated"):
            self.establish(reference_time="2026-08-09T17:10:01+09:00", max_age_seconds=300)

    def test_untrusted_primary_observer_cannot_self_authorize(self) -> None:
        observation = self.observation()
        observation["observer_id"] = "attacker-self-declared"
        result = self.establish(observation=observation, attestations=self.attestations(observation, self.expectation()))
        self.assertEqual(result["status"], NOT_ESTABLISHED)
        self.assertEqual(result["reason"], "UNTRUSTED_OBSERVER")

    def test_dirty_source_tree_and_material_drift_fail(self) -> None:
        observation = self.observation()
        observation["source_tree_state"] = "DIRTY"
        result = self.establish(observation=observation, attestations=self.attestations(observation, self.expectation()))
        self.assertEqual(result["reason"], "SOURCE_TREE_NOT_CLEAN")

        for field, reason in (
            ("deployed_artifact_digest", "ARTIFACT_DIGEST_MISMATCH"),
            ("runtime_config_fingerprint", "CONFIG_FINGERPRINT_MISMATCH"),
            ("runtime_environment_fingerprint", "ENVIRONMENT_FINGERPRINT_MISMATCH"),
        ):
            with self.subTest(field=field):
                observation = self.observation()
                observation[field] = "sha256:other"
                result = self.establish(observation=observation, attestations=self.attestations(observation, self.expectation()))
                self.assertEqual(result["reason"], reason)

    def test_reverse_proxy_route_cannot_reference_unknown_worker(self) -> None:
        observation = self.observation()
        observation["active_route_instance_ids"] = ["worker-not-observed"]
        with self.assertRaisesRegex(DeploymentIdentityError, "unknown runtime instance"):
            self.establish(observation=observation, attestations=self.attestations(observation, self.expectation()))

    def test_mixed_routed_worker_set_fails(self) -> None:
        observation = self.observation()
        stale = self.instance("worker-2")
        stale["revision"] = "old456"
        observation["runtime_instances"].append(stale)
        observation["active_route_instance_ids"] = ["worker-1", "worker-2"]
        result = self.establish(observation=observation, attestations=self.attestations(observation, self.expectation()))
        self.assertEqual(result["reason"], "ROUTE_INSTANCE_REVISION_MISMATCH")

    def test_non_routed_old_worker_does_not_define_active_route_reality(self) -> None:
        observation = self.observation()
        stale = self.instance("worker-idle")
        stale["revision"] = "old456"
        observation["runtime_instances"].append(stale)
        proof = self.establish(observation=observation, attestations=self.attestations(observation, self.expectation()))
        self.assertTrue(proof["runtime_classification_authorized"])

    def test_runtime_observation_requires_authorized_fingerprints_session_and_time(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof)
        runtime["deployment_identity_fingerprint"] = "forged"
        self.assertEqual(bind_runtime_observation(proof, runtime)["reason"], "DEPLOYMENT_FINGERPRINT_MISMATCH")

        runtime = self.runtime_observation(proof)
        runtime["deployment_expectation_fingerprint"] = "forged"
        self.assertEqual(bind_runtime_observation(proof, runtime)["reason"], "DEPLOYMENT_EXPECTATION_FINGERPRINT_MISMATCH")

        runtime = self.runtime_observation(proof)
        runtime["observation_session_id"] = "other-session"
        self.assertEqual(bind_runtime_observation(proof, runtime)["reason"], "OBSERVATION_SESSION_MISMATCH")

        runtime = self.runtime_observation(proof, "2026-08-09T17:01:00+09:00")
        self.assertEqual(bind_runtime_observation(proof, runtime, max_skew_seconds=30)["reason"], "RUNTIME_OBSERVATION_OUTSIDE_BINDING_WINDOW")

        bound = bind_runtime_observation(proof, self.runtime_observation(proof), max_skew_seconds=30)
        self.assertEqual(bound["status"], BOUND)
        self.assertTrue(bound["runtime_classification_authorized"])

    def test_cli_requires_attestations_and_external_keyring(self) -> None:
        observation = self.observation()
        expectation = self.expectation()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            observation_path = root / "observation.json"
            expectation_path = root / "expectation.json"
            attestations_path = root / "attestations.json"
            keyring_path = root / "keyring.json"
            observation_path.write_text(json.dumps(observation), encoding="utf-8")
            expectation_path.write_text(json.dumps(expectation), encoding="utf-8")
            attestations_path.write_text(json.dumps(self.attestations(observation, expectation)), encoding="utf-8")
            keyring_path.write_text(json.dumps(self.keyring()), encoding="utf-8")
            self.assertEqual(main([
                "verify", "--observation", str(observation_path),
                "--expectation", str(expectation_path),
                "--attestations", str(attestations_path),
                "--attestation-keyring", str(keyring_path),
                "--trusted-observer-id", "observer-prod-01",
                "--reference-time", "2026-08-09T17:00:10+09:00",
            ]), 0)

    def test_code_existence_alone_cannot_establish_identity(self) -> None:
        source_only = {"deployed_revision": "abc123", "observed_at": "2026-08-09T17:00:00+09:00"}
        with self.assertRaises(DeploymentIdentityError):
            self.material_proof(source_only)

    def test_fingerprints_are_deterministic(self) -> None:
        first = self.observation()
        second = dict(reversed(list(first.items())))
        self.assertEqual(fingerprint_observation(first), fingerprint_observation(second))


if __name__ == "__main__":
    unittest.main()
