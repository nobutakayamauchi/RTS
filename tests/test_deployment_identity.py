from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from deployment_identity.cli import main
from deployment_identity.core import (
    DeploymentIdentityError,
    ESTABLISHED,
    NOT_ESTABLISHED,
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
            "observed_at": "2026-08-09T17:00:00+09:00",
        }

    def test_matching_explicit_identity_establishes_runtime_classification(self) -> None:
        result = establish_deployment_identity(self.observation())
        self.assertEqual(result["status"], ESTABLISHED)
        self.assertTrue(result["runtime_classification_authorized"])
        self.assertEqual(result["identity"]["revision"], "abc123")

    def test_revision_mismatch_fails_closed(self) -> None:
        observation = self.observation()
        observation["deployed_revision"] = "stale456"
        result = establish_deployment_identity(observation)
        self.assertEqual(result["status"], NOT_ESTABLISHED)
        self.assertFalse(result["runtime_classification_authorized"])
        self.assertEqual(result["reason"], "DEPLOYED_REVISION_MISMATCH")

    def test_revision_whitespace_is_rejected_not_normalized(self) -> None:
        for field in ("deployed_revision", "source_revision"):
            with self.subTest(field=field):
                observation = self.observation()
                observation[field] = "abc123 "
                with self.assertRaisesRegex(DeploymentIdentityError, "whitespace"):
                    establish_deployment_identity(observation)

    def test_missing_runtime_surface_is_rejected(self) -> None:
        observation = self.observation()
        del observation["active_route_surface"]
        with self.assertRaisesRegex(DeploymentIdentityError, "active_route_surface"):
            establish_deployment_identity(observation)

    def test_blank_runtime_fields_are_rejected(self) -> None:
        for field in (
            "service_unit",
            "working_directory",
            "executable_or_module",
            "active_route_surface",
            "deployed_revision",
            "source_revision",
            "observed_at",
        ):
            with self.subTest(field=field):
                observation = self.observation()
                observation[field] = "  "
                with self.assertRaises(DeploymentIdentityError):
                    establish_deployment_identity(observation)

    def test_naive_timestamp_is_rejected(self) -> None:
        observation = self.observation()
        observation["observed_at"] = "2026-08-09T17:00:00"
        with self.assertRaisesRegex(DeploymentIdentityError, "timezone"):
            establish_deployment_identity(observation)

    def test_fingerprint_is_deterministic_and_order_independent(self) -> None:
        first = self.observation()
        second = dict(reversed(list(first.items())))
        self.assertEqual(fingerprint_observation(first), fingerprint_observation(second))

    def test_cli_returns_nonzero_when_identity_is_not_established(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "observation.json"
            observation = self.observation()
            observation["deployed_revision"] = "wrong"
            path.write_text(json.dumps(observation), encoding="utf-8")
            self.assertEqual(main(["verify", "--observation", str(path)]), 2)

    def test_code_existence_alone_cannot_establish_identity(self) -> None:
        source_only = {
            "source_revision": "abc123",
            "observed_at": "2026-08-09T17:00:00+09:00",
        }
        with self.assertRaises(DeploymentIdentityError):
            establish_deployment_identity(source_only)


if __name__ == "__main__":
    unittest.main()
