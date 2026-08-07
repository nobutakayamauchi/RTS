from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from deployment_identity.core import (
    DeploymentIdentityError,
    build_snapshot,
    validate_snapshot,
)

DEPLOYMENT_ENV = {
    "DEPLOYED_REVISION": "",
    "GIT_COMMIT": "",
    "SOURCE_VERSION": "",
    "RENDER_GIT_COMMIT": "",
    "VERCEL_GIT_COMMIT_SHA": "",
    "GITHUB_SHA": "",
    "SYSTEMD_UNIT": "",
    "SERVICE_UNIT": "",
    "K_SERVICE": "",
    "ACTIVE_ROUTE": "",
    "SERVICE_URL": "",
    "RENDER_EXTERNAL_URL": "",
}


class DeploymentIdentityProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = mock.patch.dict(os.environ, DEPLOYMENT_ENV, clear=False)
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()

    def test_established_requires_runtime_anchor_and_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = build_snapshot(
                root=Path(temp),
                service_unit="rts.service",
                deployed_revision="a" * 40,
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(snapshot["status"], "ESTABLISHED")
        self.assertTrue(snapshot["runtime_classification_allowed"])
        self.assertFalse(snapshot["code_existence_is_runtime_evidence"])
        validate_snapshot(snapshot)

    def test_repository_code_without_revision_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("print('exists')\n", encoding="utf-8")
            snapshot = build_snapshot(
                root=root,
                service_unit="rts.service",
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(snapshot["status"], "PARTIAL")
        self.assertFalse(snapshot["runtime_classification_allowed"])
        self.assertIn("deployed_revision", snapshot["missing_required_fields"])

    def test_revision_without_runtime_anchor_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = build_snapshot(
                root=Path(temp),
                deployed_revision="b" * 40,
                entrypoint="worker.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(snapshot["status"], "PARTIAL")
        self.assertFalse(snapshot["runtime_classification_allowed"])
        self.assertIn("service_unit_or_active_route", snapshot["missing_required_fields"])

    def test_active_route_can_be_runtime_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = build_snapshot(
                root=Path(temp),
                active_route="https://example.invalid/health",
                deployed_revision="c" * 40,
                entrypoint="api.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(snapshot["status"], "ESTABLISHED")
        self.assertTrue(snapshot["runtime_classification_allowed"])

    def test_conflicting_revision_environment_is_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(
            os.environ,
            {"GIT_COMMIT": "d" * 40, "SOURCE_VERSION": "e" * 40},
            clear=False,
        ):
            snapshot = build_snapshot(
                root=Path(temp),
                service_unit="rts.service",
                entrypoint="api.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(snapshot["status"], "CONFLICT")
        self.assertFalse(snapshot["runtime_classification_allowed"])
        self.assertEqual(snapshot["conflicts"], ["deployed_revision"])

    def test_artifact_hash_is_evidence_not_substitute_for_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifact = root / "app.bin"
            artifact.write_bytes(b"runtime artifact")
            snapshot = build_snapshot(
                root=root,
                service_unit="rts.service",
                entrypoint="app.bin",
                artifact=artifact,
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(snapshot["status"], "PARTIAL")
        self.assertIsNotNone(snapshot["fields"]["artifact_sha256"]["value"])
        self.assertFalse(snapshot["runtime_classification_allowed"])

    def test_validator_rejects_manufactured_runtime_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = build_snapshot(
                root=Path(temp),
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        snapshot["runtime_classification_allowed"] = True
        with self.assertRaisesRegex(DeploymentIdentityError, "gate mismatch"):
            validate_snapshot(snapshot)

    def test_validator_rejects_code_as_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = build_snapshot(
                root=Path(temp),
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        snapshot["code_existence_is_runtime_evidence"] = True
        with self.assertRaisesRegex(DeploymentIdentityError, "must never"):
            validate_snapshot(snapshot)

    def test_missing_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(DeploymentIdentityError, "artifact"):
                build_snapshot(
                    root=Path(temp),
                    service_unit="rts.service",
                    deployed_revision="f" * 40,
                    entrypoint="app.py",
                    artifact=Path(temp) / "missing.bin",
                )


if __name__ == "__main__":
    unittest.main()
