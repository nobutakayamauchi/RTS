from __future__ import annotations

import copy
import inspect
import io
import unittest
from contextlib import redirect_stdout

from proof_engine_pilot import report_operational_validation_build as build_impl
from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_operational_validation_build import verify_plan_review_decision
from proof_engine_pilot.report_operational_validation_build_v2 import (
    BUILD_CHECKPOINT_FINGERPRINT,
    COMPARISON_MATRIX_FINGERPRINT,
    REPORT_JSON_FINGERPRINT,
    TOPICS,
    verify_second_case_package,
)
from proof_engine_pilot.report_operational_validation_result import (
    FINAL_GATE,
    FINAL_STATE,
    verify_operational_reproduction_result,
)
from proof_engine_pilot.report_operational_validation_result_cli import build_parser, main


def _resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = fingerprint(result)
    return result


class OperationalValidationResultTests(unittest.TestCase):
    def test_second_case_package_is_deterministic_and_complete(self) -> None:
        bundle = verify_second_case_package()
        self.assertEqual(bundle["dynamic_fingerprints"]["report_json_fingerprint"], REPORT_JSON_FINGERPRINT)
        self.assertEqual(bundle["dynamic_fingerprints"]["comparison_matrix_fingerprint"], COMPARISON_MATRIX_FINGERPRINT)
        self.assertEqual(bundle["dynamic_fingerprints"]["build_checkpoint_fingerprint"], BUILD_CHECKPOINT_FINGERPRINT)
        self.assertEqual(bundle["summary"]["counts"], {
            "artifacts": 8,
            "report_sections": 9,
            "effective_records": 2,
            "withheld_claims": 3,
            "comparison_dimensions": 10,
            "post_build_review_criteria": 12,
            "automated_pass": 9,
            "pending_human": 3,
        })
        self.assertEqual(bundle["rollback_index"]["artifact_count"], 8)
        self.assertEqual(bundle["rollback_index"]["indexed_artifact_count"], 7)
        self.assertIs(bundle["rollback_index"]["self_record_is_eighth_artifact"], True)

    def test_negative_control_records_and_withheld_topics_are_preserved(self) -> None:
        bundle = verify_second_case_package()
        self.assertEqual(
            [item["candidate_id"] for item in bundle["report_json"]["sections"]["effective_achievement_records"]],
            ["VF-001", "VF-002"],
        )
        self.assertEqual([item["topic"] for item in bundle["evidence_inventory"]["withheld_claims"]], TOPICS)
        self.assertTrue(all(item["status"] == "WITHHELD_UNSUPPORTED" for item in bundle["evidence_inventory"]["withheld_claims"]))
        self.assertEqual(bundle["comparison_matrix"]["overall"], "PASS_REPRODUCED_WITH_NEGATIVE_CONTROL")
        self.assertIs(bundle["comparison_matrix"]["repository_specific_code_paths"], False)

    def test_generic_builder_contains_no_repository_specific_literal(self) -> None:
        source = inspect.getsource(build_impl._build_generic_case_package)
        self.assertNotIn("nobutakayamauchi/rts-video-flow", source)
        self.assertNotIn("nobutakayamauchi/seminar-compass", source)

    def test_final_reproduction_result_is_internal_and_accepted(self) -> None:
        result = verify_operational_reproduction_result()
        self.assertEqual(result["evaluation"]["state"], FINAL_STATE)
        self.assertEqual(result["evaluation"]["next_gate"], FINAL_GATE)
        self.assertEqual(result["evaluation"]["reproduction_result"], "PASS")
        self.assertIs(result["decision"]["second_case_package_accepted"], True)
        self.assertIs(result["decision"]["reproduction_validated"], True)
        self.assertEqual([item["result"] for item in result["decision"]["criteria_results"]], ["PASS"] * 12)
        self.assertEqual([item["result"] for item in result["evaluation"]["hypothesis_results"]], ["PASS"] * 5)

    def test_plan_review_authority_widening_fails_closed(self) -> None:
        decision = verify_plan_review_decision()
        mutated = copy.deepcopy(decision)
        mutated["publication_authorized"] = True
        mutated = _resign(mutated, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_plan_review_decision(mutated)

    def test_missing_withheld_topic_fails_closed(self) -> None:
        package = verify_second_case_package()
        mutated = copy.deepcopy(package)
        mutated["evidence_inventory"]["withheld_claims"][0]["topic"] = "REMOVED_TOPIC"
        with self.assertRaises(ProofEngineError):
            verify_operational_reproduction_result(package=mutated)

    def test_repository_specific_comparison_claim_fails_closed(self) -> None:
        package = verify_second_case_package()
        mutated = copy.deepcopy(package)
        mutated["comparison_matrix"]["repository_specific_code_paths"] = True
        with self.assertRaises(ProofEngineError):
            verify_operational_reproduction_result(package=mutated)

    def test_positive_runtime_overclaim_fails_closed(self) -> None:
        package = verify_second_case_package()
        mutated = copy.deepcopy(package)
        mutated["report_json"]["sections"]["executive_summary"]["reader_summary"] = "The end-to-end workflow is operational."
        with self.assertRaises(ProofEngineError):
            verify_operational_reproduction_result(package=mutated)

    def test_acceptance_criterion_failure_fails_closed(self) -> None:
        result = verify_operational_reproduction_result()
        mutated = copy.deepcopy(result["decision"])
        mutated["criteria_results"][0]["result"] = "FAIL"
        mutated = _resign(mutated, "decision_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_operational_reproduction_result(acceptance=mutated)

    def test_final_checkpoint_external_action_fails_closed(self) -> None:
        result = verify_operational_reproduction_result()
        mutated = copy.deepcopy(result["checkpoint"])
        mutated["publication_performed"] = True
        mutated = _resign(mutated, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            verify_operational_reproduction_result(checkpoint=mutated)

    def test_cli_is_read_only_and_has_no_consequential_commands(self) -> None:
        parser = build_parser()
        choices = set(parser._subparsers._group_actions[0].choices)
        self.assertTrue(choices.isdisjoint({"build", "accept", "publish", "price", "deliver", "outreach", "contract", "execute"}))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["verify"]), 0)
        self.assertIn('"reproduction_result": "PASS"', output.getvalue())

    def test_active_binding_layer_has_no_pending_fingerprints(self) -> None:
        self.assertNotEqual(REPORT_JSON_FINGERPRINT, "PENDING_PROBE")
        self.assertNotEqual(COMPARISON_MATRIX_FINGERPRINT, "PENDING_PROBE")
        self.assertNotEqual(BUILD_CHECKPOINT_FINGERPRINT, "PENDING_PROBE")


if __name__ == "__main__":
    unittest.main()
