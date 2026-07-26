from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.publication_review import (
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    effective_wording_records,
    verify_publication_review,
)
from proof_engine_pilot.publication_review_cli import build_parser


class PublicationReviewTests(unittest.TestCase):
    def test_committed_review_reaches_release_gate_without_publication(self):
        bundle = verify_publication_review()
        self.assertEqual(bundle["summary"]["counts"], {
            "wordings_reviewed": 6,
            "originals_approved": 3,
            "originals_revised": 3,
            "revisions_approved": 3,
            "effective_wordings": 6,
            "rejected": 0,
            "redacted": 0,
            "expired": 0,
        })
        self.assertEqual(bundle["summary"]["review_state"], "ALL_WORDINGS_APPROVED_FOR_RELEASE_GATE")
        self.assertEqual(bundle["summary"]["publication_status"], "NOT_PUBLISHED")
        self.assertEqual(bundle["summary"]["release_authorization_status"], "REQUIRED")
        self.assertFalse(bundle["checkpoint"]["publication_performed"])
        self.assertFalse(bundle["checkpoint"]["external_actions_performed"])

    def test_review_origin_separates_human_delegation_from_ai_judgment(self):
        bundle = verify_publication_review()
        origin = bundle["summary"]["review_origin"]
        self.assertEqual(origin["human_authorization"]["type"], "HUMAN")
        self.assertEqual(origin["reviewer"]["type"], "AI_ASSISTANT")
        self.assertEqual(origin["reviewer"]["decision_origin"], "AI_REVIEW_UNDER_EXPLICIT_HUMAN_DELEGATION")

    def test_three_revisions_are_append_only_and_fact_bounded(self):
        bundle = verify_publication_review()
        source = {item["wording_id"]: item for item in bundle["source"]["wordings"]}
        revisions = {item["wording_id"]: item for item in bundle["summary"]["revisions"]}
        self.assertEqual(set(revisions), {"WORDING-002", "WORDING-003", "WORDING-005"})
        self.assertIn("in the governed pilot", revisions["WORDING-002"]["headline"])
        self.assertIn("expired or stale decisions", revisions["WORDING-003"]["summary"])
        self.assertIn("declared change and authority context", revisions["WORDING-005"]["headline"])
        for wording_id, revision in revisions.items():
            self.assertEqual(revision["revision_of_fingerprint"], source[wording_id]["wording_fingerprint"])
            self.assertNotEqual(revision["wording_fingerprint"], source[wording_id]["wording_fingerprint"])
            self.assertEqual(revision["publication_status"], "NOT_PUBLISHED")
        self.assertTrue(bundle["summary"]["original_wording_drafts_preserved"])

    def test_effective_set_contains_six_once(self):
        records = effective_wording_records(verify_publication_review())
        self.assertEqual(len(records), 6)
        self.assertEqual({item["wording_id"] for item in records}, {f"WORDING-{index:03d}" for index in range(1, 7)})

    def test_resigned_contract_authority_widening_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["authority"]["publication_authorized"] = True
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "authority widened"):
            verify_publication_review(contract=contract)

    def test_resigned_publication_checkpoint_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["publication_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "unauthorized action"):
            verify_publication_review(checkpoint=checkpoint)

    def test_cli_has_no_publish_or_approve_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "effective", "release-template"})


if __name__ == "__main__":
    unittest.main()
