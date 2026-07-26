from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, verify_run
from proof_engine_pilot.review import (
    APPROVED_ORIGINAL_IDS,
    CHECKPOINT_PATH,
    DECISION_INDEX_PATH,
    REVISED_IDS,
    REVISIONS_PATH,
    SUMMARY_PATH,
    build_summary,
    effective_candidate_records,
    load,
    load_decision_chain,
    verify_review_round,
)
from proof_engine_pilot.review_cli import build_parser


class ProofEngineHumanReviewTests(unittest.TestCase):
    def test_review_round_approves_seven_originals_and_five_revisions(self):
        summary = verify_review_round()
        self.assertEqual(summary["counts"]["originals_approved"], 7)
        self.assertEqual(summary["counts"]["originals_revised"], 5)
        self.assertEqual(summary["counts"]["revisions_approved"], 5)
        self.assertEqual(summary["counts"]["effective_candidates_approved"], 12)
        self.assertEqual(
            {item["candidate_id"] for item in summary["effective_candidates"] if item["candidate_version"] == 1},
            APPROVED_ORIGINAL_IDS,
        )
        self.assertEqual(
            {item["candidate_id"] for item in summary["effective_candidates"] if item["candidate_version"] == 2},
            REVISED_IDS,
        )

    def test_original_candidate_run_is_preserved(self):
        run = verify_run()
        self.assertEqual(
            run["run_fingerprint"],
            "0935b4b594b3d80a0d38fe2cb95dc9a90eed82ba8591a7251cd4ef1dde9d7ee1",
        )
        self.assertEqual(run["review_queue"]["decisions"], [])
        self.assertEqual(run["review_queue"]["state"], "HUMAN_REVIEW_REQUIRED")

    def test_effective_records_use_factual_revisions(self):
        records = {item["candidate_id"]: item for item in effective_candidate_records()}
        self.assertEqual(records["ACH-001"]["record_kind"], "PROCESS_BYPRODUCT")
        self.assertEqual(records["ACH-002"]["record_kind"], "PROJECT_OUTPUT")
        self.assertEqual(records["ACH-007"]["record_kind"], "INTEGRATION_BYPRODUCT")
        self.assertEqual(records["ACH-010"]["record_kind"], "AUDIT_REMEDIATION_BYPRODUCT")
        self.assertEqual(records["ACH-012"]["record_kind"], "REUSABILITY_SIGNAL")
        self.assertEqual(records["ACH-012"]["evidence_label"], "INFERRED")
        self.assertIn("not yet proof", records["ACH-012"]["claim"])

    def test_revision_tamper_fails_closed(self):
        revisions = copy.deepcopy(load(REVISIONS_PATH))
        revisions["revisions"][0]["claim"] += " altered"
        material = copy.deepcopy(revisions)
        material.pop("revisions_fingerprint")
        revisions["revisions_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "revision ACH-001 fingerprint mismatch"):
            verify_review_round(
                revisions=revisions,
                index=load(DECISION_INDEX_PATH),
                summary=load(SUMMARY_PATH),
                checkpoint=load(CHECKPOINT_PATH),
            )

    def test_decision_chain_contains_seventeen_linked_records(self):
        decisions = load_decision_chain(load(DECISION_INDEX_PATH))
        self.assertEqual(len(decisions), 17)
        self.assertEqual(decisions[0]["sequence"], 1)
        self.assertEqual(decisions[-1]["sequence"], 17)
        for previous, current in zip(decisions, decisions[1:]):
            self.assertEqual(current["previous_decision_fingerprint"], previous["decision_fingerprint"])

    def test_review_does_not_authorize_publication(self):
        summary = verify_review_round()
        self.assertEqual(summary["output_asset"]["state"], "READY_FOR_INTERNAL_DRAFT")
        self.assertEqual(summary["output_asset"]["publication_status"], "NOT_PUBLISHED")
        self.assertTrue(all(value is False for value in summary["authority"].values()))

    def test_committed_summary_is_deterministic(self):
        base = verify_run()
        revisions = load(REVISIONS_PATH)
        index = load(DECISION_INDEX_PATH)
        decisions = load_decision_chain(index)
        self.assertEqual(load(SUMMARY_PATH), build_summary(base, revisions, index, decisions))

    def test_review_cli_has_no_consequential_commands(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "effective"})


if __name__ == "__main__":
    unittest.main()
