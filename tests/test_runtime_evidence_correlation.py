from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from deployment_identity.core import build_snapshot
from runtime_evidence_correlation.core import CorrelationError, correlate_candidates, validate_correlation_result

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


class RuntimeEvidenceCorrelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = mock.patch.dict(os.environ, DEPLOYMENT_ENV, clear=False)
        self.environment.start()
        self.temp = tempfile.TemporaryDirectory()
        self.identity = build_snapshot(
            root=Path(self.temp.name),
            service_unit="rts.service",
            deployed_revision="a" * 40,
            entrypoint="app.py",
            observed_at="2026-08-08T00:00:00Z",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()
        self.environment.stop()

    def test_single_revision_matched_evidence_bound_candidate_is_ready(self) -> None:
        result = correlate_candidates(
            deployment_identity=self.identity,
            candidates=[{
                "candidate_id": "candidate-1",
                "source_ref": "services/api/app.py",
                "revision": "a" * 40,
                "runtime_evidence_refs": ["trace:abc", "route:/health"],
            }],
        )
        self.assertEqual(result["state"], "READY_FOR_CODE_MAPPING")
        self.assertTrue(result["code_mapping_allowed"])
        self.assertFalse(result["root_cause_claim_allowed"])

    def test_stale_revision_is_rejected_even_when_source_exists(self) -> None:
        result = correlate_candidates(
            deployment_identity=self.identity,
            candidates=[{
                "candidate_id": "stale",
                "source_ref": "services/api/app.py",
                "revision": "b" * 40,
                "runtime_evidence_refs": ["trace:abc"],
            }],
        )
        self.assertEqual(result["state"], "BLOCKED_NO_CORRELATED_CANDIDATE")
        self.assertEqual(result["candidates"][0]["disposition"], "REJECTED_REVISION_MISMATCH")
        self.assertFalse(result["code_mapping_allowed"])

    def test_revision_match_without_runtime_evidence_is_blocked(self) -> None:
        result = correlate_candidates(
            deployment_identity=self.identity,
            candidates=[{
                "candidate_id": "candidate-1",
                "source_ref": "services/api/app.py",
                "revision": "a" * 40,
                "runtime_evidence_refs": [],
            }],
        )
        self.assertEqual(result["state"], "BLOCKED_NO_CORRELATED_CANDIDATE")
        self.assertEqual(result["candidates"][0]["disposition"], "BLOCKED_MISSING_RUNTIME_EVIDENCE")

    def test_multiple_correlated_candidates_are_ambiguous(self) -> None:
        candidates = [
            {
                "candidate_id": "one",
                "source_ref": "services/api/app.py",
                "revision": "a" * 40,
                "runtime_evidence_refs": ["trace:abc"],
            },
            {
                "candidate_id": "two",
                "source_ref": "services/api/router.py",
                "revision": "a" * 40,
                "runtime_evidence_refs": ["trace:abc"],
            },
        ]
        result = correlate_candidates(deployment_identity=self.identity, candidates=candidates)
        self.assertEqual(result["state"], "BLOCKED_AMBIGUOUS_CANDIDATES")
        self.assertFalse(result["code_mapping_allowed"])

    def test_non_established_identity_is_rejected(self) -> None:
        partial = build_snapshot(
            root=Path(self.temp.name),
            service_unit="rts.service",
            entrypoint="app.py",
            observed_at="2026-08-08T00:00:00Z",
        )
        with self.assertRaisesRegex(CorrelationError, "requires ESTABLISHED"):
            correlate_candidates(
                deployment_identity=partial,
                candidates=[{
                    "candidate_id": "one",
                    "source_ref": "app.py",
                    "revision": "a" * 40,
                    "runtime_evidence_refs": ["trace:abc"],
                }],
            )

    def test_validator_rejects_root_cause_authority(self) -> None:
        result = correlate_candidates(
            deployment_identity=self.identity,
            candidates=[{
                "candidate_id": "candidate-1",
                "source_ref": "services/api/app.py",
                "revision": "a" * 40,
                "runtime_evidence_refs": ["trace:abc"],
            }],
        )
        result["root_cause_claim_allowed"] = True
        with self.assertRaisesRegex(CorrelationError, "never grant root-cause"):
            validate_correlation_result(result)


if __name__ == "__main__":
    unittest.main()
