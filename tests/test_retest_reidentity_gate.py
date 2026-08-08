from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deployment_identity.core import build_snapshot
from runtime_evidence_correlation.core import correlate_candidates
from runtime_code_mapping.core import establish_code_mapping
from root_cause_claim_gate.core import evaluate_root_cause_claims
from retest_reidentity_gate.core import RetestGateError, evaluate_retest, validate_retest_result


class RetestReidentityGateTests(unittest.TestCase):
    def _identity(self, revision: str, observed_at: str):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return build_snapshot(
            root=Path(temp.name),
            service_unit="rts.service",
            deployed_revision=revision,
            entrypoint="app.py",
            observed_at=observed_at,
        )

    def _root_cause(self, identity):
        correlation = correlate_candidates(
            deployment_identity=identity,
            candidates=[
                {
                    "candidate_id": "c1",
                    "source_ref": "app.py",
                    "revision": identity["fields"]["deployed_revision"]["value"],
                    "runtime_evidence_refs": ["trace:1"],
                }
            ],
        )
        mapping = establish_code_mapping(
            correlation_result=correlation,
            mapping={
                "candidate_id": "c1",
                "source_ref": "app.py",
                "symbols": ["handle_request"],
                "mapping_evidence_refs": ["stack:frame-3"],
            },
        )
        return evaluate_root_cause_claims(
            code_mapping_result=mapping,
            claims=[
                {
                    "claim_id": "rc1",
                    "candidate_id": "c1",
                    "hypothesis": "null branch triggers the observed HTTP 500",
                    "supporting_evidence_refs": ["trace:1"],
                    "reproduction_refs": ["repro:test-17"],
                    "falsification_refs": ["negative:test-18"],
                    "unresolved_counterevidence_refs": [],
                }
            ],
        )

    def test_pass_with_reestablished_identity_validates_fix(self):
        before = self._identity("a" * 40, "2026-08-08T00:00:00Z")
        after = self._identity("b" * 40, "2026-08-08T00:10:00Z")
        result = evaluate_retest(
            pre_patch_identity=before,
            post_patch_identity=after,
            root_cause_result=self._root_cause(before),
            retest={
                "claim_id": "rc1",
                "deployed_revision": "b" * 40,
                "verification_refs": ["retest:17"],
                "regression_refs": ["suite:42"],
                "outcome": "PASS",
            },
        )
        self.assertEqual(result["state"], "FIX_VALIDATED")
        self.assertTrue(result["fix_validated"])
        self.assertTrue(result["deployment_identity_reestablished"])
        self.assertTrue(result["identity_changed"])

    def test_revision_mismatch_fails_closed(self):
        before = self._identity("a" * 40, "2026-08-08T00:00:00Z")
        after = self._identity("b" * 40, "2026-08-08T00:10:00Z")
        with self.assertRaisesRegex(RetestGateError, "does not match"):
            evaluate_retest(
                pre_patch_identity=before,
                post_patch_identity=after,
                root_cause_result=self._root_cause(before),
                retest={
                    "claim_id": "rc1",
                    "deployed_revision": "c" * 40,
                    "verification_refs": ["retest:17"],
                    "regression_refs": ["suite:42"],
                    "outcome": "PASS",
                },
            )

    def test_pass_without_regression_evidence_does_not_validate(self):
        before = self._identity("a" * 40, "2026-08-08T00:00:00Z")
        after = self._identity("b" * 40, "2026-08-08T00:10:00Z")
        result = evaluate_retest(
            pre_patch_identity=before,
            post_patch_identity=after,
            root_cause_result=self._root_cause(before),
            retest={
                "claim_id": "rc1",
                "deployed_revision": "b" * 40,
                "verification_refs": ["retest:17"],
                "regression_refs": [],
                "outcome": "PASS",
            },
        )
        self.assertEqual(result["state"], "BLOCKED_INSUFFICIENT_RETEST_EVIDENCE")
        self.assertFalse(result["fix_validated"])

    def test_failed_retest_returns_to_analysis(self):
        before = self._identity("a" * 40, "2026-08-08T00:00:00Z")
        after = self._identity("b" * 40, "2026-08-08T00:10:00Z")
        result = evaluate_retest(
            pre_patch_identity=before,
            post_patch_identity=after,
            root_cause_result=self._root_cause(before),
            retest={
                "claim_id": "rc1",
                "deployed_revision": "b" * 40,
                "verification_refs": ["retest:failed"],
                "regression_refs": ["suite:42"],
                "outcome": "FAIL",
            },
        )
        self.assertEqual(result["state"], "RETEST_FAILED")
        self.assertFalse(result["fix_validated"])

    def test_validator_rejects_manufactured_fix_validation(self):
        before = self._identity("a" * 40, "2026-08-08T00:00:00Z")
        after = self._identity("b" * 40, "2026-08-08T00:10:00Z")
        result = evaluate_retest(
            pre_patch_identity=before,
            post_patch_identity=after,
            root_cause_result=self._root_cause(before),
            retest={
                "claim_id": "rc1",
                "deployed_revision": "b" * 40,
                "verification_refs": [],
                "regression_refs": [],
                "outcome": "PASS",
            },
        )
        result["state"] = "FIX_VALIDATED"
        result["fix_validated"] = True
        with self.assertRaisesRegex(RetestGateError, "requires verification"):
            validate_retest_result(result)


if __name__ == "__main__":
    unittest.main()
