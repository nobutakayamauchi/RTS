from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deployment_identity.core import build_snapshot
from runtime_evidence_correlation.core import correlate_candidates
from runtime_code_mapping.core import CodeMappingError, establish_code_mapping, validate_code_mapping_result


class RuntimeCodeMappingTests(unittest.TestCase):
    def _correlation(self):
        with tempfile.TemporaryDirectory() as temp:
            identity = build_snapshot(
                root=Path(temp),
                service_unit="rts.service",
                deployed_revision="a" * 40,
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        return correlate_candidates(
            deployment_identity=identity,
            candidates=[
                {
                    "candidate_id": "c1",
                    "source_ref": "app.py",
                    "revision": "a" * 40,
                    "runtime_evidence_refs": ["trace:1"],
                }
            ],
        )

    def test_mapping_requires_evidence_and_preserves_root_cause_boundary(self):
        result = establish_code_mapping(
            correlation_result=self._correlation(),
            mapping={
                "candidate_id": "c1",
                "source_ref": "app.py",
                "symbols": ["handle_request"],
                "mapping_evidence_refs": ["stack:frame-3"],
            },
        )
        self.assertEqual(result["state"], "READY_FOR_ROOT_CAUSE_ANALYSIS")
        self.assertTrue(result["mapping_established"])
        self.assertFalse(result["root_cause_claim_allowed"])

    def test_source_mismatch_fails_closed(self):
        with self.assertRaisesRegex(CodeMappingError, "source_ref"):
            establish_code_mapping(
                correlation_result=self._correlation(),
                mapping={
                    "candidate_id": "c1",
                    "source_ref": "other.py",
                    "symbols": ["handle_request"],
                    "mapping_evidence_refs": ["stack:frame-3"],
                },
            )

    def test_missing_mapping_evidence_fails_closed(self):
        with self.assertRaisesRegex(CodeMappingError, "mapping_evidence_refs"):
            establish_code_mapping(
                correlation_result=self._correlation(),
                mapping={
                    "candidate_id": "c1",
                    "source_ref": "app.py",
                    "symbols": ["handle_request"],
                    "mapping_evidence_refs": [],
                },
            )

    def test_validator_rejects_root_cause_authority(self):
        result = establish_code_mapping(
            correlation_result=self._correlation(),
            mapping={
                "candidate_id": "c1",
                "source_ref": "app.py",
                "symbols": ["handle_request"],
                "mapping_evidence_refs": ["stack:frame-3"],
            },
        )
        result["root_cause_claim_allowed"] = True
        with self.assertRaisesRegex(CodeMappingError, "must not grant"):
            validate_code_mapping_result(result)


if __name__ == "__main__":
    unittest.main()
