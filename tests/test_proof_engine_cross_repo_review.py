from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.cross_repo_review import (
    CHECKPOINT_PATH,
    LEARNING_PATH,
    REVIEW_PATH,
    verify_round_two_review,
    verify_round_two_review_bundle,
)
from proof_engine_pilot.cross_repo_review_cli import build_parser
from proof_engine_pilot.cross_repo_validation import verify_bundle as verify_cross_repo_bundle


def resign(value: dict, field: str) -> dict:
    material = copy.deepcopy(value)
    material.pop(field, None)
    value[field] = fingerprint(material)
    return value


class CrossRepoRoundTwoReviewTests(unittest.TestCase):
    def test_committed_round_two_review_is_complete(self):
        bundle = verify_round_two_review_bundle()
        self.assertEqual(bundle["review"]["counts"], {
            "original_candidates": 6,
            "originals_approved": 5,
            "originals_revised": 1,
            "revisions_approved": 1,
            "effective_approved": 6,
            "rejected": 0,
            "redacted": 0,
            "expired": 0,
        })
        self.assertEqual(bundle["review"]["review_state"], "ROUND_2_COMPLETE")
        self.assertEqual(bundle["checkpoint"]["state"], "ROUND_2_COMPLETE_ROUND_3_REVIEW_REQUIRED")
        self.assertFalse(bundle["checkpoint"]["publication_performed"])
        self.assertFalse(bundle["checkpoint"]["target_repository_writes_performed"])

    def test_effective_round_two_set_contains_five_originals_and_one_revision(self):
        effective = verify_round_two_review_bundle()["review"]["effective_candidates"]
        self.assertEqual(len(effective), 6)
        self.assertEqual({item["candidate_id"] for item in effective}, {f"SC-{index:03d}" for index in range(1, 7)})
        revision = next(item for item in effective if item["candidate_id"] == "SC-006")
        self.assertEqual(revision["candidate_version"], 2)
        self.assertEqual(revision["source"], "REVISION_LEDGER")

    def test_sc006_revision_corrects_classification_and_preserves_evidence(self):
        bundle = verify_round_two_review_bundle()
        revision = bundle["review"]["revision"]
        self.assertEqual(revision["record_kind"], "PROCESS_BYPRODUCT")
        self.assertEqual(revision["evidence_prs"], [12, 13, 14, 15, 16])
        self.assertNotIn(17, revision["evidence_prs"])
        self.assertNotIn(18, revision["evidence_prs"])
        self.assertIn("not evidence of an independent audit", revision["factuality_note"])

    def test_round_two_source_keeps_unmerged_prs_ineligible(self):
        run = verify_cross_repo_bundle()["run"]
        round_two = next(item for item in run["rounds"] if item["round_id"] == "ROUND-2")
        self.assertEqual(round_two["excluded_unmerged_prs"], [17, 18])
        for candidate in round_two["candidates"]:
            self.assertFalse(set(candidate["evidence_prs"]) & {17, 18})

    def test_resigned_review_authority_widening_fails_closed(self):
        review = copy.deepcopy(load(REVIEW_PATH))
        review["authority"]["publication_authorized"] = True
        review["authority_fingerprint"] = fingerprint(review["authority"])
        resign(review, "review_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "authority widened"):
            verify_round_two_review(review)

    def test_resigned_human_instruction_substitution_fails_closed(self):
        review = copy.deepcopy(load(REVIEW_PATH))
        review["author"]["instruction"] = "AI inferred approval"
        review["author_fingerprint"] = fingerprint(review["author"])
        resign(review, "review_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "explicit human confirmation"):
            verify_round_two_review(review)

    def test_learning_observation_cannot_activate_a_new_rule(self):
        observation = copy.deepcopy(load(LEARNING_PATH))
        observation["rule_change"]["new_rule_activated"] = True
        resign(observation, "observation_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "learning rule authority mismatch"):
            verify_round_two_review_bundle(observation=observation)

    def test_resigned_checkpoint_action_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["target_repository_writes_performed"] = True
        resign(checkpoint, "checkpoint_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "exceeded boundary"):
            verify_round_two_review_bundle(checkpoint=checkpoint)

    def test_resigned_checkpoint_unknown_field_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["social_posting_performed"] = False
        resign(checkpoint, "checkpoint_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "schema fields mismatch"):
            verify_round_two_review_bundle(checkpoint=checkpoint)

    def test_cli_has_no_approve_publish_or_apply_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {
            "verify-round-2",
            "summary-round-2",
            "effective-round-2",
            "round-3-template",
        })


if __name__ == "__main__":
    unittest.main()
