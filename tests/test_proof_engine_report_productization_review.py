from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_productization_review import (
    REVIEWED_REPORT_FINGERPRINTS,
    build_productization_review,
    verify_productization_decision,
    verify_productization_review,
)
from proof_engine_pilot.report_productization_review_cli import build_parser


class ProductizationReviewTests(unittest.TestCase):
    def test_review_verifies_and_stops_before_external_action(self):
        bundle = verify_productization_review()
        self.assertEqual(
            bundle["summary"]["state"],
            "APPROVED_FOR_INTERNAL_PRODUCTIZATION_SPECIFICATION",
        )
        self.assertEqual(
            bundle["summary"]["productization_scope"],
            "INTERNAL_PRODUCTIZATION_SPECIFICATION_ONLY",
        )
        self.assertEqual(bundle["summary"]["counts"]["reports_reviewed"], 3)
        self.assertEqual(bundle["summary"]["counts"]["effective_achievement_records"], 16)
        self.assertEqual(bundle["summary"]["counts"]["withheld_claims"], 5)
        self.assertEqual(
            bundle["decision"]["reviewed_report_fingerprints"],
            REVIEWED_REPORT_FINGERPRINTS,
        )
        for field in (
            "pricing_authorized",
            "delivery_authorized",
            "publication_authorized",
            "outreach_authorized",
            "contract_authorized",
            "external_execution_authorized",
            "target_repository_write_authorized",
            "automatic_approval_authorized",
            "automatic_rewrite_authorized",
        ):
            self.assertIs(bundle["decision"][field], False)
        self.assertIn("Pricing authorized: false", bundle["markdown"])
        self.assertIn("Target-repository writes authorized: false", bundle["markdown"])

    def test_decision_fails_closed_on_authority_widening_even_when_resigned(self):
        decision = copy.deepcopy(build_productization_review()["decision"])
        decision["pricing_authorized"] = True
        decision["decision_fingerprint"] = fingerprint({
            key: value for key, value in decision.items()
            if key != "decision_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_productization_decision(decision)

    def test_decision_fails_closed_on_instruction_substitution(self):
        decision = copy.deepcopy(build_productization_review()["decision"])
        decision["human_authorization"]["instruction"] = "continue"
        decision["decision_fingerprint"] = fingerprint({
            key: value for key, value in decision.items()
            if key != "decision_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_productization_decision(decision)

    def test_decision_fails_closed_on_report_fingerprint_substitution(self):
        decision = copy.deepcopy(build_productization_review()["decision"])
        decision["reviewed_report_fingerprints"][
            "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-4"
        ] = "0" * 64
        decision["decision_fingerprint"] = fingerprint({
            key: value for key, value in decision.items()
            if key != "decision_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_productization_decision(decision)

    def test_checkpoint_fails_closed_on_unknown_field(self):
        bundle = verify_productization_review()
        checkpoint = copy.deepcopy(bundle["checkpoint"])
        checkpoint["unknown"] = False
        checkpoint["checkpoint_fingerprint"] = fingerprint({
            key: value for key, value in checkpoint.items()
            if key != "checkpoint_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_productization_review(checkpoint=checkpoint)

    def test_checkpoint_fails_closed_on_external_action(self):
        bundle = verify_productization_review()
        checkpoint = copy.deepcopy(bundle["checkpoint"])
        checkpoint["publication_performed"] = True
        checkpoint["checkpoint_fingerprint"] = fingerprint({
            key: value for key, value in checkpoint.items()
            if key != "checkpoint_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_productization_review(checkpoint=checkpoint)

    def test_cli_has_no_price_publish_deliver_or_outreach_command(self):
        parser = build_parser()
        choices = parser._subparsers._group_actions[0].choices
        self.assertEqual(
            set(choices),
            {"verify", "summary", "decision", "render-markdown", "next-stage"},
        )
        for forbidden in ("price", "publish", "deliver", "outreach", "approve"):
            self.assertNotIn(forbidden, choices)


if __name__ == "__main__":
    unittest.main()
