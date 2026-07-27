from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_product_readiness import (
    ASSESSMENT_PATH,
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    INSTRUCTION_PATH,
    PLAN_PATH,
    verify_assessment,
    verify_assessment_contract,
    verify_hardening_plan,
    verify_instruction_record,
    verify_product_readiness,
)
from proof_engine_pilot.report_product_readiness_cli import build_parser, main


def resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = fingerprint(result)
    return result


class ProductReadinessTests(unittest.TestCase):
    def test_product_readiness_summary_and_completion(self) -> None:
        bundle = verify_product_readiness()
        self.assertEqual(bundle["summary"]["completion"], {
            "overall_rts_percent": 72,
            "short_term_internal_product_candidate_percent": 92,
            "product_readiness_score": 82,
        })
        self.assertEqual(bundle["summary"]["decision"], "READY_FOR_BOUNDED_INTERNAL_HARDENING")
        self.assertFalse(bundle["summary"]["customer_pilot_ready"])
        self.assertFalse(bundle["summary"]["production_service_ready"])

    def test_readiness_dimension_distribution(self) -> None:
        assessment = verify_assessment()
        results = [item["result"] for item in assessment["dimension_results"]]
        self.assertEqual(results.count("PASS"), 4)
        self.assertEqual(results.count("PARTIAL"), 5)
        self.assertEqual(results.count("NOT_STARTED"), 1)
        self.assertEqual(sum(item["score"] for item in assessment["dimension_results"]), 82)

    def test_completion_basis_reconciles(self) -> None:
        assessment = verify_assessment()
        completion = assessment["completion_estimates"]
        self.assertEqual(sum(item["score"] for item in completion["overall_rts"]["basis"]), 72)
        self.assertEqual(sum(item["score"] for item in completion["short_term_target"]["basis"]), 92)

    def test_instruction_record_uses_normalized_operator_copy(self) -> None:
        record = verify_instruction_record()
        self.assertFalse(record["raw_input_retained_in_operator_surfaces"])
        self.assertNotIn("raw_input", record)
        self.assertTrue(record["normalized_instruction"].endswith("記録する。"))

    def test_raw_instruction_retention_fails_closed(self) -> None:
        record = verify_instruction_record()
        mutated = copy.deepcopy(record)
        mutated["raw_input_retained_in_operator_surfaces"] = True
        mutated = resign(mutated, "record_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_instruction_record(mutated)

    def test_readiness_score_drift_fails_closed(self) -> None:
        assessment = verify_assessment()
        mutated = copy.deepcopy(assessment)
        mutated["dimension_results"][3]["score"] = 10
        mutated["weighted_score"] = 84
        mutated = resign(mutated, "assessment_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_assessment(mutated)

    def test_customer_pilot_claim_fails_closed(self) -> None:
        assessment = verify_assessment()
        mutated = copy.deepcopy(assessment)
        mutated["customer_pilot_ready"] = True
        mutated = resign(mutated, "assessment_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_assessment(mutated)

    def test_contract_authority_widening_fails_closed(self) -> None:
        contract = verify_assessment_contract()
        mutated = copy.deepcopy(contract)
        mutated["authority"]["outreach_authorized"] = True
        mutated = resign(mutated, "contract_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_assessment_contract(mutated)

    def test_hardening_plan_authority_widening_fails_closed(self) -> None:
        plan = verify_hardening_plan()
        mutated = copy.deepcopy(plan)
        mutated["authority"]["bounded_internal_hardening_authorized"] = True
        mutated = resign(mutated, "plan_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_hardening_plan(mutated)

    def test_checkpoint_external_action_fails_closed(self) -> None:
        bundle = verify_product_readiness()
        mutated = copy.deepcopy(bundle["checkpoint"])
        mutated["publication_performed"] = True
        mutated = resign(mutated, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_product_readiness(checkpoint=mutated)

    def test_cli_is_read_only(self) -> None:
        parser = build_parser()
        choices = set(parser._subparsers._group_actions[0].choices)
        self.assertTrue(choices.isdisjoint({"authorize", "execute", "build", "publish", "price", "outreach", "contract", "deliver"}))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["verify"]), 0)
        self.assertIn('"score": 82', output.getvalue())

    def test_operator_readmes_do_not_quote_raw_chat(self) -> None:
        root = Path(__file__).resolve().parents[1]
        current = (root / "proof_engine_pilot" / "product_readiness" / "round_0001" / "README.md").read_text(encoding="utf-8")
        previous = (root / "proof_engine_pilot" / "operational_validation_builds" / "round_0001" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("The project owner instructed:", current)
        self.assertNotIn("The project owner instructed:", previous)
        self.assertNotIn("\n> ", current)
        self.assertNotIn("\n> ", previous)

    def test_all_signed_artifacts_exist(self) -> None:
        for path in (INSTRUCTION_PATH, CONTRACT_PATH, ASSESSMENT_PATH, PLAN_PATH, CHECKPOINT_PATH):
            self.assertTrue(path.is_file(), path)


if __name__ == "__main__":
    unittest.main()
