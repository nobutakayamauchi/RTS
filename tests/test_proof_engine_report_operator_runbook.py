from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stdout

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_operator_runbook import (
    verify_checkpoint,
    verify_hardening_result,
    verify_instruction_provenance_policy,
    verify_instruction_record,
    verify_intake_contract,
    verify_operator_runbook,
    verify_operator_runbook_stage,
    verify_support_escalation,
)
from proof_engine_pilot.report_operator_runbook_cli import build_parser, main


def resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = fingerprint(result)
    return result


class OperatorRunbookTests(unittest.TestCase):
    def test_stage_is_complete_and_bounded(self) -> None:
        bundle = verify_operator_runbook_stage()
        self.assertEqual(
            bundle["summary"],
            {
                "state": "INTERNAL_OPERATOR_RUNBOOK_AND_INTAKE_CONTRACT_COMPLETE",
                "next_gate": "HUMAN_INDEPENDENT_READER_REVIEW_PLAN_REQUIRED",
                "rts_overall_planning_estimate_percent": 73,
                "short_term_internal_product_candidate_percent": 95,
                "product_readiness_score": 82,
                "runbook_phases": 7,
                "intake_required_fields": 7,
                "intake_rejection_conditions": 6,
                "escalation_levels": 4,
                "rough_input_robustness_preserved": True,
                "verbatim_raw_instruction_required": False,
                "remaining_work_items": ["HARD-003", "HARD-004", "HARD-005"],
            },
        )

    def test_instruction_policy_preserves_insight_without_raw_display(self) -> None:
        policy = verify_instruction_provenance_policy()
        self.assertTrue(policy["demonstration_policy"]["rough_input_robustness_may_be_reported"])
        self.assertFalse(policy["demonstration_policy"]["verbatim_user_example_required"])
        self.assertEqual(policy["demonstration_policy"]["preferred_example_source"], "SYNTHETIC_OR_NORMALIZED_EXAMPLE")
        self.assertFalse(policy["record_layers"]["restricted_raw_log"]["enabled"])

    def test_runbook_intake_and_escalation_are_complete(self) -> None:
        runbook = verify_operator_runbook()
        intake = verify_intake_contract()
        escalation = verify_support_escalation()
        self.assertEqual(len(runbook["phases"]), 7)
        self.assertEqual(len(runbook["required_artifacts"]), 10)
        self.assertEqual(len(intake["required_inputs"]), 7)
        self.assertEqual(len(intake["rejection_conditions"]), 6)
        self.assertEqual([item["level"] for item in escalation["levels"]], ["L0_OPERATOR", "L1_PROJECT_OWNER", "L2_SECURITY_PRIVACY_REVIEW", "L3_SEPARATE_GOVERNANCE_DECISION"])

    def test_instruction_record_has_only_audit_binding(self) -> None:
        record = verify_instruction_record()
        self.assertFalse(record["raw_text_retained"])
        self.assertFalse(record["scope_widened"])
        self.assertEqual(len(record["raw_input_fingerprint"]), 64)
        self.assertIn("preserve rough-input robustness insight", record["normalization_actions"])

    def test_cli_is_read_only(self) -> None:
        parser = build_parser()
        choices = set(parser._subparsers._group_actions[0].choices)
        self.assertEqual(choices, {"verify", "summary", "runbook", "intake", "instruction-policy"})
        self.assertTrue(choices.isdisjoint({"build", "accept", "publish", "price", "deliver", "outreach", "contract", "execute", "contact"}))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["summary"]), 0)
        self.assertIn('"short_term_internal_product_candidate_percent": 95', output.getvalue())

    def test_verbatim_requirement_tampering_fails_closed(self) -> None:
        value = verify_instruction_provenance_policy()
        mutated = copy.deepcopy(value)
        mutated["demonstration_policy"]["verbatim_user_example_required"] = True
        mutated = resign(mutated, "policy_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_instruction_provenance_policy(mutated)

    def test_raw_log_enablement_fails_closed(self) -> None:
        value = verify_instruction_provenance_policy()
        mutated = copy.deepcopy(value)
        mutated["record_layers"]["restricted_raw_log"]["enabled"] = True
        mutated = resign(mutated, "policy_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_instruction_provenance_policy(mutated)

    def test_instruction_raw_retention_fails_closed(self) -> None:
        value = verify_instruction_record()
        mutated = copy.deepcopy(value)
        mutated["raw_text_retained"] = True
        mutated = resign(mutated, "record_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_instruction_record(mutated)

    def test_scope_widening_fails_closed(self) -> None:
        value = verify_instruction_record()
        mutated = copy.deepcopy(value)
        mutated["scope_widened"] = True
        mutated = resign(mutated, "record_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_instruction_record(mutated)

    def test_intake_rejection_loss_fails_closed(self) -> None:
        value = verify_intake_contract()
        mutated = copy.deepcopy(value)
        mutated["rejection_conditions"].pop()
        mutated = resign(mutated, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_intake_contract(mutated)

    def test_runbook_wip_widening_fails_closed(self) -> None:
        value = verify_operator_runbook()
        mutated = copy.deepcopy(value)
        mutated["wip_limit"] = 2
        mutated = resign(mutated, "runbook_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_operator_runbook(mutated)

    def test_runbook_publication_authority_fails_closed(self) -> None:
        value = verify_operator_runbook()
        mutated = copy.deepcopy(value)
        mutated["authority"]["publication_authorized"] = True
        mutated = resign(mutated, "runbook_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_operator_runbook(mutated)

    def test_progress_inflation_fails_closed(self) -> None:
        value = verify_hardening_result()
        mutated = copy.deepcopy(value)
        mutated["completion_update"]["short_term_internal_product_candidate_percent"] = 100
        mutated = resign(mutated, "result_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_hardening_result(mutated)

    def test_checkpoint_external_action_fails_closed(self) -> None:
        value = verify_checkpoint()
        mutated = copy.deepcopy(value)
        mutated["publication_performed"] = True
        mutated = resign(mutated, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_checkpoint(mutated)


if __name__ == "__main__":
    unittest.main()
