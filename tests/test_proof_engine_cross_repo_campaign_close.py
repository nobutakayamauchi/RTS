from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.cross_repo_campaign_close import (
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    build_campaign_evaluation,
    build_round_four_review,
    verify_campaign_close,
)
from proof_engine_pilot.cross_repo_campaign_close_cli import build_parser


class CrossRepoCampaignCloseTests(unittest.TestCase):
    def test_round_four_approves_two_and_retains_three_withheld_claims(self):
        bundle = verify_campaign_close()
        self.assertEqual(bundle["review"]["counts"], {
            "original_candidates": 2,
            "originals_approved": 2,
            "originals_revised": 0,
            "revisions_approved": 0,
            "effective_approved": 2,
            "rejected": 0,
            "withheld_claims": 3,
        })
        self.assertEqual(
            {item["topic"] for item in bundle["review"]["withheld_claims"]},
            {"END_TO_END_OPERATION", "TRANSCRIPTION_ACCURACY", "PRODUCTION_READINESS"},
        )
        self.assertTrue(all(item["status"] == "WITHHELD_UNSUPPORTED" for item in bundle["review"]["withheld_claims"]))

    def test_campaign_totals_are_fact_bounded(self):
        evaluation = verify_campaign_close()["evaluation"]
        self.assertEqual(evaluation["cross_repo_totals"]["candidates"], 16)
        self.assertEqual(evaluation["cross_repo_totals"]["first_pass_approved"], 14)
        self.assertEqual(evaluation["cross_repo_totals"]["revised"], 2)
        self.assertEqual(evaluation["cross_repo_totals"]["withheld_unsupported_claims"], 5)
        self.assertEqual(evaluation["baseline_reference"]["interpretation"], "POSITIVE_SIGNAL_NOT_CAUSAL_PROOF")
        self.assertIn("ARBITRARY_REPOSITORY_GENERALIZATION", evaluation["conclusion"]["not_proven"])
        self.assertIn("COMMERCIAL_EFFECTIVENESS", evaluation["conclusion"]["not_proven"])

    def test_review_and_evaluation_are_deterministic(self):
        first = build_round_four_review()["review"]
        second = build_round_four_review()["review"]
        self.assertEqual(first["review_fingerprint"], second["review_fingerprint"])
        self.assertEqual(
            build_campaign_evaluation()["evaluation_fingerprint"],
            build_campaign_evaluation()["evaluation_fingerprint"],
        )

    def test_resigned_authority_widening_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["authority"]["publication_authorized"] = True
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "authority widened"):
            verify_campaign_close(contract=contract)

    def test_instruction_substitution_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["human_authorization"]["instruction"] = "approve everything"
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "explicit human confirmation"):
            verify_campaign_close(contract=contract)

    def test_checkpoint_external_action_and_unknown_fields_fail_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["target_repository_writes_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "exceeded boundary"):
            verify_campaign_close(checkpoint=checkpoint)

        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["unknown_external_action"] = False
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "schema fields mismatch"):
            verify_campaign_close(checkpoint=checkpoint)

    def test_cli_has_no_publish_price_or_outreach_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "evaluation", "report-template-design"})


if __name__ == "__main__":
    unittest.main()
