from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.cross_repo_review_round3 import (
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    build_learning_observation,
    build_round_three_review,
    verify_round_three_review_bundle,
)
from proof_engine_pilot.cross_repo_review_round3_cli import build_parser


class CrossRepoRoundThreeReviewTests(unittest.TestCase):
    def test_committed_round_three_review_advances_to_round_four(self):
        bundle = verify_round_three_review_bundle()
        self.assertEqual(bundle["review"]["counts"], {
            "original_candidates": 8,
            "originals_approved": 7,
            "originals_revised": 1,
            "revisions_approved": 1,
            "effective_approved": 8,
            "rejected": 0,
            "redacted": 0,
            "expired": 0,
            "withheld_claims_retained": 2,
        })
        self.assertEqual(bundle["checkpoint"]["state"], "ROUND_3_COMPLETE_ROUND_4_REVIEW_REQUIRED")
        self.assertEqual(bundle["checkpoint"]["completed_rounds"], ["ROUND-2", "ROUND-3"])
        self.assertFalse(bundle["checkpoint"]["private_repository_payload_copied"])
        self.assertFalse(bundle["checkpoint"]["publication_performed"])

    def test_revision_is_append_only_and_bounded_to_single_run(self):
        review = build_round_three_review()
        revision = review["revision"]
        self.assertEqual(revision["revision_id"], "MC-008-R1")
        self.assertEqual(revision["record_kind"], "PROCESS_BYPRODUCT")
        self.assertTrue(revision["claim"].startswith("In this validation run,"))
        self.assertIn("does not establish", revision["factuality_note"])
        effective = {item["candidate_id"]: item for item in review["effective_candidates"]}
        self.assertEqual(effective["MC-008"]["candidate_version"], 2)
        self.assertEqual(effective["MC-008"]["source"], "REVISION_LEDGER")
        self.assertTrue(review["originals_preserved"])

    def test_learning_observation_retains_commercial_and_automation_withholds(self):
        observation = build_learning_observation(build_round_three_review())
        self.assertEqual(len(observation["positive_examples"]), 7)
        self.assertEqual(len(observation["correction_pairs"]), 1)
        self.assertEqual(len(observation["withheld_claims"]), 2)
        self.assertEqual(observation["rule_change"]["new_rule_activated"], False)
        self.assertEqual(observation["metrics"]["comparison_state"], "POSITIVE_SIGNAL_NOT_PROOF")

    def test_resigned_contract_authority_widening_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["authority"]["publication_authorized"] = True
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "authority widened"):
            verify_round_three_review_bundle(contract=contract)

    def test_resigned_instruction_substitution_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["human_authorization"]["instruction"] = "AI approved this review."
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "explicit human confirmation"):
            verify_round_three_review_bundle(contract=contract)

    def test_resigned_generalized_revision_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["revision"]["claim"] = "Private repositories can be analyzed safely without exposing customer records."
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "not bounded"):
            verify_round_three_review_bundle(contract=contract)

    def test_resigned_private_payload_checkpoint_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["private_repository_payload_copied"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "exceeded boundary"):
            verify_round_three_review_bundle(checkpoint=checkpoint)

    def test_cli_has_no_publish_or_target_write_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "effective", "round-4-template"})


if __name__ == "__main__":
    unittest.main()
