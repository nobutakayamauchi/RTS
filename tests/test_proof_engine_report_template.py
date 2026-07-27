from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.report_template import (
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    REQUIRED_ACHIEVEMENT_FIELDS,
    REQUIRED_SECTIONS,
    build_demonstration_pack,
    render_demonstration_markdown,
    verify_report_template,
)
from proof_engine_pilot.report_template_cli import build_parser


class EvidenceReportTemplateTests(unittest.TestCase):
    def test_three_reports_cover_all_effective_candidates_and_withheld_claims(self):
        bundle = verify_report_template()
        self.assertEqual(bundle["pack"]["counts"], {
            "reports": 3,
            "effective_achievement_records": 16,
            "withheld_claims": 5,
        })
        self.assertEqual(
            [item["round_id"] for item in bundle["pack"]["reports"]],
            ["ROUND-2", "ROUND-3", "ROUND-4"],
        )

    def test_each_report_has_required_sections_and_fields(self):
        bundle = verify_report_template()
        for report in bundle["pack"]["reports"]:
            self.assertEqual(list(report["sections"]), REQUIRED_SECTIONS)
            self.assertEqual(report["draft_state"], "HUMAN_REPORT_REVIEW_REQUIRED")
            self.assertEqual(report["publication_status"], "NOT_PUBLISHED")
            self.assertEqual(report["delivery_status"], "NOT_DELIVERED")
            self.assertEqual(report["sections"]["human_review_decision"]["decisions"], [])
            for record in report["sections"]["effective_achievement_records"]:
                self.assertFalse(set(REQUIRED_ACHIEVEMENT_FIELDS) - set(record))

    def test_revisions_and_originals_keep_lineage(self):
        bundle = verify_report_template()
        records = {
            record["candidate_id"]: record
            for report in bundle["pack"]["reports"]
            for record in report["sections"]["effective_achievement_records"]
        }
        self.assertEqual(records["SC-006"]["lineage"]["source"], "REVISION_LEDGER")
        self.assertEqual(records["SC-006"]["lineage"]["candidate_version"], 2)
        self.assertEqual(records["MC-008"]["lineage"]["source"], "REVISION_LEDGER")
        self.assertEqual(records["MC-008"]["lineage"]["candidate_version"], 2)
        self.assertEqual(records["VF-001"]["lineage"]["source"], "CROSS_REPO_RUN")

    def test_private_and_negative_control_limits_remain_visible(self):
        bundle = verify_report_template()
        reports = {item["round_id"]: item for item in bundle["pack"]["reports"]}
        round3_limits = " ".join(reports["ROUND-3"]["sections"]["limitations"])
        self.assertIn("metadata-only", round3_limits)
        self.assertIn("copies no customer-specific payload", round3_limits)
        round4_limits = " ".join(reports["ROUND-4"]["sections"]["limitations"])
        self.assertIn("frozen scaffold", round4_limits)
        self.assertIn("production readiness remain unverified", round4_limits)

    def test_markdown_is_internal_and_does_not_claim_release(self):
        markdown = render_demonstration_markdown(verify_report_template())
        self.assertIn("HUMAN_REPORT_TEMPLATE_REVIEW_REQUIRED", markdown)
        self.assertIn("NOT_PUBLISHED", markdown)
        self.assertIn("No report in this demonstration has been approved for pricing", markdown)

    def test_generation_is_deterministic(self):
        first = build_demonstration_pack()
        second = build_demonstration_pack()
        self.assertEqual(first["template"]["template_fingerprint"], second["template"]["template_fingerprint"])
        self.assertEqual(first["pack"]["pack_fingerprint"], second["pack"]["pack_fingerprint"])

    def test_resigned_authority_widening_fails_closed(self):
        contract = copy.deepcopy(load(CONTRACT_PATH))
        contract["authority"]["pricing_authorized"] = True
        material = copy.deepcopy(contract)
        material.pop("contract_fingerprint")
        contract["contract_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "deterministic fingerprint mismatch|authority widened"):
            verify_report_template(contract=contract)

    def test_checkpoint_release_or_unknown_field_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["delivery_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "exceeded boundary"):
            verify_report_template(checkpoint=checkpoint)

        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["automatic_delivery_performed"] = False
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "schema fields mismatch"):
            verify_report_template(checkpoint=checkpoint)

    def test_cli_has_no_publish_price_outreach_or_delivery_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "generate", "render-markdown", "review-template"})


if __name__ == "__main__":
    unittest.main()
