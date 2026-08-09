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
    def observation(self) -> dict:
        return {
            "service_unit": "rts-video-flow-web.service",
            "working_directory": "/srv/rts-video-flow",
            "executable_or_module": "python -m app.web",
            "active_route_surface": "POST /render",
            "deployed_revision": "abc123",
            "source_revision": "abc123",
            "observer_id": "observer-prod-01",
            "observation_session_id": "session-001",
            "observed_at": "2026-08-09T17:00:00+09:00",
        }

    def establish(self, observation: dict | None = None, **kwargs):
        return establish_deployment_identity(
            observation or self.observation(),
            trusted_observer_ids=kwargs.get("trusted_observer_ids", {"observer-prod-01"}),
            reference_time=kwargs.get("reference_time", "2026-08-09T17:00:10+09:00"),
            max_age_seconds=kwargs.get("max_age_seconds", 300),
        )

    def runtime_observation(self, proof: dict, observed_at: str = "2026-08-09T17:00:15+09:00") -> dict:
        return {
            "deployment_identity_fingerprint": proof["observation_fingerprint"],
            "observation_session_id": "session-001",
            "observed_at": observed_at,
            "result": {"status": "ok"},
        }

    def test_matching_explicit_identity_establishes_runtime_classification(self) -> None:
        result = self.establish()
        self.assertEqual(result["status"], ESTABLISHED)
        self.assertTrue(result["runtime_classification_authorized"])
        self.assertEqual(result["identity"]["revision"], "abc123")

    def test_untrusted_observer_cannot_self_authorize(self) -> None:
        observation = self.observation()
        observation["observer_id"] = "attacker-self-declared"
        result = self.establish(observation)
        self.assertEqual(result["status"], NOT_ESTABLISHED)
        self.assertEqual(result["reason"], "UNTRUSTED_OBSERVER")
        self.assertFalse(result["runtime_classification_authorized"])

    def test_stale_observation_replay_fails_closed(self) -> None:
        result = self.establish(reference_time="2026-08-09T17:10:01+09:00", max_age_seconds=300)
        self.assertEqual(result["status"], NOT_ESTABLISHED)
        self.assertEqual(result["reason"], "STALE_OR_FUTURE_OBSERVATION")

    def test_future_observation_fails_closed(self) -> None:
        result = self.establish(reference_time="2026-08-09T16:59:59+09:00")
        self.assertEqual(result["reason"], "STALE_OR_FUTURE_OBSERVATION")

    def test_revision_mismatch_fails_closed(self) -> None:
        observation = self.observation()
        observation["deployed_revision"] = "stale456"
        result = self.establish(observation)
        self.assertEqual(result["status"], NOT_ESTABLISHED)
        self.assertEqual(result["reason"], "DEPLOYED_REVISION_MISMATCH")

    def test_revision_whitespace_is_rejected_not_normalized(self) -> None:
        for field in ("deployed_revision", "source_revision"):
            with self.subTest(field=field):
                observation = self.observation()
                observation[field] = "abc123 "
                with self.assertRaisesRegex(DeploymentIdentityError, "whitespace"):
                    self.establish(observation)

    def test_missing_runtime_surface_is_rejected(self) -> None:
        observation = self.observation()
        del observation["active_route_surface"]
        with self.assertRaisesRegex(DeploymentIdentityError, "active_route_surface"):
            self.establish(observation)

    def test_missing_observer_or_session_is_rejected(self) -> None:
        for field in ("observer_id", "observation_session_id"):
            with self.subTest(field=field):
                observation = self.observation()
                del observation[field]
                with self.assertRaisesRegex(DeploymentIdentityError, field):
                    self.establish(observation)

    def test_naive_timestamp_is_rejected(self) -> None:
        observation = self.observation()
        observation["observed_at"] = "2026-08-09T17:00:00"
        with self.assertRaisesRegex(DeploymentIdentityError, "timezone"):
            self.establish(observation)

    def test_fingerprint_is_deterministic_and_order_independent(self) -> None:
        first = self.observation()
        second = dict(reversed(list(first.items())))
        self.assertEqual(fingerprint_observation(first), fingerprint_observation(second))

    def test_runtime_observation_requires_exact_deployment_fingerprint(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof)
        runtime["deployment_identity_fingerprint"] = "forged"
        result = bind_runtime_observation(proof, runtime)
        self.assertEqual(result["status"], NOT_BOUND)
        self.assertEqual(result["reason"], "DEPLOYMENT_FINGERPRINT_MISMATCH")

    def test_runtime_observation_requires_same_session(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof)
        runtime["observation_session_id"] = "other-session"
        result = bind_runtime_observation(proof, runtime)
        self.assertEqual(result["reason"], "OBSERVATION_SESSION_MISMATCH")

    def test_toctou_window_fails_closed(self) -> None:
        proof = self.establish()
        runtime = self.runtime_observation(proof, "2026-08-09T17:01:00+09:00")
        result = bind_runtime_observation(proof, runtime, max_skew_seconds=30)
        self.assertEqual(result["status"], NOT_BOUND)
        self.assertEqual(result["reason"], "RUNTIME_OBSERVATION_OUTSIDE_BINDING_WINDOW")

    def test_runtime_observation_binds_inside_window(self) -> None:
        proof = self.establish()
        result = bind_runtime_observation(proof, self.runtime_observation(proof), max_skew_seconds=30)
        self.assertEqual(result["status"], BOUND)
        self.assertTrue(result["runtime_classification_authorized"])

    def test_cli_requires_trust_anchor_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "observation.json"
            path.write_text(json.dumps(self.observation()), encoding="utf-8")
            self.assertEqual(main([
                "verify", "--observation", str(path),
                "--trusted-observer-id", "observer-prod-01",
                "--reference-time", "2026-08-09T17:00:10+09:00",
            ]), 0)

    def test_code_existence_alone_cannot_establish_identity(self) -> None:
        source_only = {
            "source_revision": "abc123",
            "observed_at": "2026-08-09T17:00:00+09:00",
        }
        with self.assertRaises(DeploymentIdentityError):
            self.establish(source_only)


if __name__ == "__main__":
    unittest.main()
