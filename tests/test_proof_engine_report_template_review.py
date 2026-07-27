from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.report_template_review import (
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    REQUIRED_DECISION_FIELDS,
    REVIEW_CRITERIA,
    build_report_template_review,
    render_revised_markdown,
    verify_report_template_review,
)
from proof_engine_pilot.report_template_review_cli import build_parser


class EvidenceReportTemplateReviewTests(unittest.TestCase):
    def test_review_revises_template_and_three_reports_without_release(self):
        bundle = verify_report_template_review()
        self.assertEqual(bundle["template"]["template_version"], 2)
        self.assertEqual(bundle["pack"]["counts"], {
            "reports": 3,
            "effective_achievement_records": 16,
            "withheld_claims": 5,
        })
        self.assertEqual(bundle["summary"]["source_decisions"], {
            "template": "REVISE",
            "reports_revised": 3,
        })
        self.assertEqual(bundle["summary"]["state"], "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED")
        self.assertEqual(bundle["summary"]["pricing_status"], "NOT_PRICED")
        self.assertEqual(bundle["summary"]["publication_status"], "NOT_PUBLISHED")
        self.assertEqual(bundle["summary"]["delivery_status"], "NOT_DELIVERED")

    def test_source_template_and_reports_remain_append_only(self):
        bundle = verify_report_template_review()
        self.assertTrue(bundle["summary"]["source_artifacts_preserved"])
        self.assertEqual(
            bundle["template"]["revision_of_template_fingerprint"],
            bundle["source"]["template"]["template_fingerprint"],
        )
        source_reports = {item["report_id"]: item for item in bundle["source"]["pack"]["reports"]}
        for report in bundle["pack"]["reports"]:
            self.assertEqual(
                report["revision_of_report_fingerprint"],
                source_reports[report["report_id"]]["report_fingerprint"],
            )

    def test_markdown_renders_all_nine_sections_for_all_reports(self):
        markdown = render_revised_markdown(build_report_template_review())
        headings = [
            "### 1. Executive summary",
            "### 2. Repository scope",
            "### 3. Methodology",
            "### 4. Evidence inventory",
            "### 5. Effective achievement records",
            "### 6. Human and AI contribution map",
            "### 7. Withheld or unsupported claims",
            "### 8. Limitations",
            "### 9. Human review decision",
        ]
        for heading in headings:
            self.assertEqual(markdown.count(heading), 3)
        self.assertIn("Human:", markdown)
        self.assertIn("AI tool:", markdown)
        self.assertIn("NOT_PRICED", markdown)

    def test_review_origin_does_not_manufacture_human_judgment(self):
        bundle = verify_report_template_review()
        origin = bundle["summary"]["review_origin"]
        self.assertEqual(origin["human_authorization"]["type"], "HUMAN")
        self.assertEqual(origin["reviewer"]["type"], "AI_ASSISTANT")
        self.assertEqual(
            origin["reviewer"]["decision_origin"],
            "AI_REVIEW_UNDER_EXPLICIT_HUMAN_NEXT_WORK_AUTHORIZATION",
        )
        for report in bundle["pack"]["reports"]:
            gate = report["sections"]["human_review_decision"]
            self.assertEqual(gate["decisions"], [])
            self.assertEqual(gate["review_criteria"], REVIEW_CRITERIA)
            self.assertEqual(gate["required_decision_fields"], REQUIRED_DECISION_FIELDS)

    def test_private_and_negative_control_boundaries_remain_visible(self):
        bundle = verify_report_template_review()
        reports = {item["round_id"]: item for item in bundle["pack"]["reports"]}
        round3 = reports["ROUND-3"]
        self.assertEqual(
            round3["sections"]["repository_scope"]["source_mode"],
            "READ_ONLY_METADATA_SNAPSHOT",
        )
        self.assertIn(
            "customer-specific payload",
            " ".join(round3["sections"]["limitations"]),
        )
        round4 = reports["ROUND-4"]
        self.assertEqual(len(round4["sections"]["withheld_or_unsupported_claims"]), 3)
        self.assertIn("frozen scaffold", " ".join(round4["sections"]["limitations"]))

    def test_resigned_contract_authority_widening_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["authority"]["pricing_authorized"] = True
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "deterministic fingerprint mismatch|authority widened"):
            verify_report_template_review(contract=contract)

    def test_resigned_checkpoint_action_and_unknown_field_fail_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["delivery_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "exceeded boundary"):
            verify_report_template_review(checkpoint=checkpoint)

        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["automatic_delivery_performed"] = False
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "schema fields mismatch"):
            verify_report_template_review(checkpoint=checkpoint)

    def test_resigned_fingerprint_substitution_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["revised_markdown_fingerprint"] = "0" * 64
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "checkpoint link mismatch"):
            verify_report_template_review(checkpoint=checkpoint)

    def test_cli_has_no_price_publish_outreach_contract_or_delivery_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {
            "build-summary",
            "verify",
            "summary",
            "generate",
            "render-markdown",
            "productization-template",
        })


if __name__ == "__main__":
    unittest.main()
