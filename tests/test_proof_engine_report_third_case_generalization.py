from __future__ import annotations

import copy
import inspect
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot import report_third_case_generalization as stage


def resign(value: dict, field: str) -> dict:
    value = copy.deepcopy(value)
    value.pop(field, None)
    value[field] = fingerprint(value)
    return value


class ThirdCaseGeneralizationTests(unittest.TestCase):
    def test_valid_stage(self) -> None:
        result = stage.verify_third_case_generalization_stage()
        self.assertEqual(result["summary"]["state"], "INTERNAL_THREE_CASE_GENERALIZATION_VALIDATED")
        self.assertEqual(result["summary"]["current_step"], "HARD-005")

    def test_double_build_is_deterministic(self) -> None:
        self.assertEqual(stage.build_third_case_package_bindings(), stage.build_third_case_package_bindings())
        self.assertEqual(len(stage.build_third_case_package_bindings()), 8)

    def test_progress_and_speed_summary(self) -> None:
        summary = stage.verify_third_case_generalization_stage()["summary"]
        self.assertEqual(summary["rts_overall_planning_estimate_percent"], 75)
        self.assertEqual(summary["short_term_internal_product_candidate_percent"], 99)
        self.assertEqual(summary["development_speed_level"], "HIGH_VELOCITY_GOVERNED_SOLO_AI_DEVELOPMENT")
        self.assertFalse(summary["speed_is_sla"])

    def test_source_substitution_fails_closed(self) -> None:
        value = stage.verify_selection()
        value = copy.deepcopy(value)
        value["selected_case"]["snapshot_ref"] = "main"
        value = resign(value, "selection_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_selection(value)

    def test_unmerged_pr_inclusion_fails_closed(self) -> None:
        value = stage.verify_manifest()
        value = copy.deepcopy(value)
        value["selected_merged_prs"].append({"number": 66})
        value["selected_pr_count"] = 9
        value = resign(value, "manifest_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_manifest(value)

    def test_withheld_topic_deletion_fails_closed(self) -> None:
        value = stage.verify_report()
        value = copy.deepcopy(value)
        value["sections"]["withheld_or_unsupported_claims"] = value["sections"]["withheld_or_unsupported_claims"][:-1]
        value = resign(value, "report_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_report(value)

    def test_evidence_escape_fails_closed(self) -> None:
        value = stage.verify_report()
        value = copy.deepcopy(value)
        record = value["sections"]["effective_achievement_records"][0]
        record["evidence_prs"] = [66]
        record = resign(record, "achievement_record_fingerprint")
        value["sections"]["effective_achievement_records"][0] = record
        value = resign(value, "report_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_report(value)

    def test_authority_widening_fails_closed(self) -> None:
        value = stage.verify_acceptance()
        value = copy.deepcopy(value)
        value["authority"]["pricing_authorized"] = True
        value = resign(value, "packet_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_acceptance(value)

    def test_arbitrary_generalization_claim_fails_closed(self) -> None:
        value = stage.verify_comparison()
        value = copy.deepcopy(value)
        value["not_proven"] = "NONE"
        value = resign(value, "comparison_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_comparison(value)

    def test_speed_sla_claim_fails_closed(self) -> None:
        value = stage.verify_speed_baseline()
        value = copy.deepcopy(value)
        value["measurement_policy"]["claim_boundary"] = "Guaranteed SLA"
        value = resign(value, "baseline_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_speed_baseline(value)

    def test_speed_metric_tamper_fails_closed(self) -> None:
        value = stage.verify_speed_baseline()
        value = copy.deepcopy(value)
        value["aggregate"]["median_sequential_stage_seconds"] = 60
        value = resign(value, "baseline_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_speed_baseline(value)

    def test_external_review_manufacture_fails_closed(self) -> None:
        value = stage.verify_acceptance()
        value = copy.deepcopy(value)
        value["external_human_review_performed"] = True
        value = resign(value, "packet_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_acceptance(value)

    def test_checkpoint_external_action_fails_closed(self) -> None:
        value = stage.verify_checkpoint()
        value = copy.deepcopy(value)
        value["publication_performed"] = True
        value = resign(value, "checkpoint_fingerprint")
        with self.assertRaises(ProofEngineError):
            stage.verify_checkpoint(value)

    def test_verifier_and_cli_are_read_only(self) -> None:
        source = inspect.getsource(stage)
        forbidden = ["subprocess", "requests.", "urllib.", ".write_text(", ".write_bytes(", "os.system", "git push", "gh pr"]
        self.assertFalse(any(item in source for item in forbidden))
        self.assertNotIn("if repository ==", source)
        self.assertNotIn("match repository", source)


if __name__ == "__main__":
    unittest.main()
