from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deployment_identity.core import build_snapshot
from runtime_evidence_correlation.core import correlate_candidates
from runtime_code_mapping.core import establish_code_mapping
from root_cause_claim_gate.core import RootCauseGateError, evaluate_root_cause_claims, validate_root_cause_result


class RootCauseClaimGateTests(unittest.TestCase):
    def _mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            identity = build_snapshot(
                root=Path(temp),
                service_unit="rts.service",
                deployed_revision="a" * 40,
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        correlation = correlate_candidates(
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
        return establish_code_mapping(
            correlation_result=correlation,
            mapping={
                "candidate_id": "c1",
                "source_ref": "app.py",
                "symbols": ["handle_request"],
                "mapping_evidence_refs": ["stack:frame-3"],
            },
        )

    def _claim(self, **overrides):
        claim = {
            "claim_id": "rc1",
            "candidate_id": "c1",
            "hypothesis": "null branch triggers the observed HTTP 500",
            "supporting_evidence_refs": ["trace:1", "stack:frame-3"],
            "reproduction_refs": ["repro:test-17"],
            "falsification_refs": ["negative:test-18"],
            "unresolved_counterevidence_refs": [],
        }
        claim.update(overrides)
        return claim

    def test_complete_evidence_supports_single_root_cause_claim(self):
        result = evaluate_root_cause_claims(code_mapping_result=self._mapping(), claims=[self._claim()])
        self.assertEqual(result["state"], "ROOT_CAUSE_CLAIM_SUPPORTED")
        self.assertTrue(result["root_cause_claim_allowed"])
        self.assertFalse(result["fix_validated"])
        self.assertEqual(result["selected_claim_id"], "rc1")

    def test_missing_reproduction_blocks_claim(self):
        result = evaluate_root_cause_claims(
            code_mapping_result=self._mapping(),
            claims=[self._claim(reproduction_refs=[])],
        )
        self.assertEqual(result["state"], "BLOCKED_INSUFFICIENT_ROOT_CAUSE_EVIDENCE")
        self.assertFalse(result["root_cause_claim_allowed"])

    def test_missing_falsification_blocks_claim(self):
        result = evaluate_root_cause_claims(
            code_mapping_result=self._mapping(),
            claims=[self._claim(falsification_refs=[])],
        )
        self.assertEqual(result["state"], "BLOCKED_INSUFFICIENT_ROOT_CAUSE_EVIDENCE")

    def test_unresolved_counterevidence_blocks_claim(self):
        result = evaluate_root_cause_claims(
            code_mapping_result=self._mapping(),
            claims=[self._claim(unresolved_counterevidence_refs=["counter:2"])],
        )
        self.assertFalse(result["root_cause_claim_allowed"])
        self.assertIn("unresolved_counterevidence", result["claims"][0]["blocking_reasons"])

    def test_multiple_supported_claims_are_ambiguous(self):
        second = self._claim(claim_id="rc2", hypothesis="alternate supported cause")
        result = evaluate_root_cause_claims(code_mapping_result=self._mapping(), claims=[self._claim(), second])
        self.assertEqual(result["state"], "BLOCKED_AMBIGUOUS_ROOT_CAUSE")
        self.assertFalse(result["root_cause_claim_allowed"])

    def test_validator_rejects_fix_validation_manufacture(self):
        result = evaluate_root_cause_claims(code_mapping_result=self._mapping(), claims=[self._claim()])
        result["fix_validated"] = True
        with self.assertRaisesRegex(RootCauseGateError, "must not validate"):
            validate_root_cause_result(result)


if __name__ == "__main__":
    unittest.main()
