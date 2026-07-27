from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_operational_validation_plan import (
    build_operational_validation_plan,
    build_plan_review_template,
    verify_case_selection,
    verify_operational_validation_plan,
    verify_plan_document,
    verify_plan_review_contract,
)
from proof_engine_pilot.report_operational_validation_plan_cli import build_parser


def resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result[field] = fingerprint({key: item for key, item in result.items() if key != field})
    return result


class OperationalValidationPlanTests(unittest.TestCase):
    def test_plan_verifies_and_stops_before_build(self):
        bundle = verify_operational_validation_plan()
        self.assertEqual(
            bundle["summary"]["state"],
            "INTERNAL_OPERATIONAL_VALIDATION_PLAN_COMPLETE",
        )
        self.assertEqual(
            bundle["summary"]["next_gate"],
            "HUMAN_SECOND_CASE_OPERATIONAL_VALIDATION_BUILD_REVIEW_REQUIRED",
        )
        self.assertEqual(
            bundle["summary"]["selected_repository"],
            "nobutakayamauchi/rts-video-flow",
        )
        self.assertEqual(bundle["summary"]["counts"], {
            "candidates_considered": 3,
            "public_candidates": 2,
            "selected_cases": 1,
            "workflow_steps": 10,
            "validation_hypotheses": 5,
            "plan_review_criteria": 12,
            "required_report_sections": 9,
            "required_outputs": 8,
            "expected_effective_records": 2,
            "required_withheld_topics": 3,
            "comparison_dimensions": 10,
        })
        self.assertFalse(bundle["summary"]["second_case_build_authorized"])
        self.assertIn("rts-video-flow", bundle["markdown"])
        self.assertIn("PRODUCTION_READINESS", bundle["markdown"])

    def test_selection_fails_closed_on_authority_widening(self):
        selection = copy.deepcopy(build_operational_validation_plan()["selection"])
        selection["authority"]["second_case_build_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_case_selection(resign(selection, "selection_fingerprint"))

    def test_selection_fails_closed_on_repository_substitution(self):
        selection = copy.deepcopy(build_operational_validation_plan()["selection"])
        selection["selected_case"]["repository"] = "nobutakayamauchi/seminar-compass"
        with self.assertRaises(ProofEngineError):
            verify_case_selection(resign(selection, "selection_fingerprint"))

    def test_plan_fails_closed_when_withheld_topic_is_removed(self):
        plan = copy.deepcopy(build_operational_validation_plan()["plan"])
        plan["negative_control_contract"]["required_withheld_topics"].pop()
        with self.assertRaises(ProofEngineError):
            verify_plan_document(resign(plan, "plan_fingerprint"))

    def test_plan_fails_closed_when_generic_execution_rule_is_weakened(self):
        plan = copy.deepcopy(build_operational_validation_plan()["plan"])
        plan["execution_contract"]["implementation_rule"] = "Use case-specific code."
        with self.assertRaises(ProofEngineError):
            verify_plan_document(resign(plan, "plan_fingerprint"))

    def test_review_contract_fails_closed_on_manufactured_decision(self):
        contract = copy.deepcopy(build_operational_validation_plan()["review_contract"])
        contract["decision_contract"]["decisions"] = [
            {"decision": "APPROVE_SECOND_CASE_OPERATIONAL_VALIDATION_BUILD"}
        ]
        with self.assertRaises(ProofEngineError):
            verify_plan_review_contract(resign(contract, "contract_fingerprint"))

    def test_review_contract_fails_closed_on_missing_criterion(self):
        contract = copy.deepcopy(build_operational_validation_plan()["review_contract"])
        contract["criteria"].pop()
        with self.assertRaises(ProofEngineError):
            verify_plan_review_contract(resign(contract, "contract_fingerprint"))

    def test_checkpoint_fails_closed_on_build_authority(self):
        checkpoint = copy.deepcopy(verify_operational_validation_plan()["checkpoint"])
        checkpoint["second_case_build_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_operational_validation_plan(
                checkpoint=resign(checkpoint, "checkpoint_fingerprint")
            )

    def test_checkpoint_fails_closed_on_source_write(self):
        checkpoint = copy.deepcopy(verify_operational_validation_plan()["checkpoint"])
        checkpoint["source_repository_writes_performed"] = True
        with self.assertRaises(ProofEngineError):
            verify_operational_validation_plan(
                checkpoint=resign(checkpoint, "checkpoint_fingerprint")
            )

    def test_review_template_is_blank_and_closed(self):
        template = build_plan_review_template()
        self.assertIsNone(template["decision"])
        self.assertIsNone(template["reviewer_identity"])
        self.assertFalse(template["second_case_build_authorized"])
        self.assertFalse(template["pricing_authorized"])
        self.assertFalse(template["delivery_authorized"])
        self.assertFalse(template["publication_authorized"])
        self.assertEqual(len(template["criteria_results"]), 12)

    def test_cli_has_no_build_or_external_action_command(self):
        choices = build_parser()._subparsers._group_actions[0].choices
        self.assertEqual(set(choices), {
            "verify",
            "summary",
            "selection",
            "plan",
            "review-contract",
            "review-template",
            "render-markdown",
        })
        for forbidden in (
            "build",
            "execute",
            "approve",
            "price",
            "outreach",
            "contract",
            "deliver",
            "publish",
        ):
            self.assertNotIn(forbidden, choices)


if __name__ == "__main__":
    unittest.main()
