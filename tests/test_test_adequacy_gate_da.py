from __future__ import annotations

import copy
import unittest

from test_adequacy_gate import TestAdequacyError, evaluate_test_adequacy, verify_test_adequacy_report


def lane(case_id: str, passed: bool = True):
    return [{"case_id": case_id, "passed": passed, "detail": "fixture"}]


def mutation_report(*, critical_status="KILLED", equivalent_status="SURVIVED", invalid_status="INVALID_MUTANT"):
    return {
        "schema_version": "false-green-mutation-report/v1",
        "source_sha256_before": "a" * 64,
        "source_sha256_after": "a" * 64,
        "target_tests": ["tests.test_human_escalation_gate"],
        "baseline": {"load_ok": True, "tests_ran": True, "test_returncode": 0, "output_tail": ""},
        "results": [
            {"id": "M", "kind": "CRITICAL", "status": critical_status, "match_count": 1, "load_ok": True, "tests_ran": True, "test_returncode": 1 if critical_status == "KILLED" else 0, "output_tail": ""},
            {"id": "E", "kind": "EQUIVALENT_CONTROL", "status": equivalent_status, "match_count": 1, "load_ok": True, "tests_ran": True, "test_returncode": 0, "output_tail": ""},
            {"id": "I", "kind": "INVALID_CONTROL", "status": invalid_status, "match_count": 1, "load_ok": False, "tests_ran": False, "test_returncode": None, "output_tail": "syntax"},
        ],
        "audit": {
            "critical_total": 1,
            "critical_killed": 1,
            "invalid_not_counted_as_kill": True,
            "mutation_lane_pass": True,
            "controls_pass": True,
            "production_source_unchanged": True,
        },
    }


class TestAdequacyGateDATests(unittest.TestCase):
    def test_surviving_critical_mutant_cannot_hide_behind_true_audit_flag(self):
        tampered = mutation_report(critical_status="SURVIVED")
        with self.assertRaises(TestAdequacyError):
            evaluate_test_adequacy(tampered, known_bad=lane("KB"), held_out=lane("HO"), metamorphic=lane("MM"))

    def test_killed_equivalent_control_cannot_hide_behind_true_controls_flag(self):
        tampered = mutation_report(equivalent_status="KILLED")
        with self.assertRaises(TestAdequacyError):
            evaluate_test_adequacy(tampered, known_bad=lane("KB"), held_out=lane("HO"), metamorphic=lane("MM"))

    def test_invalid_critical_mutant_is_not_a_kill(self):
        tampered = mutation_report(critical_status="INVALID_MUTANT")
        with self.assertRaises(TestAdequacyError):
            evaluate_test_adequacy(tampered, known_bad=lane("KB"), held_out=lane("HO"), metamorphic=lane("MM"))

    def test_verify_recomputes_lane_truth_instead_of_trusting_summary(self):
        report = evaluate_test_adequacy(mutation_report(), known_bad=lane("KB"), held_out=lane("HO"), metamorphic=lane("MM"))
        report = copy.deepcopy(report)
        report["held_out"][0]["passed"] = False
        report["lanes"]["held_out"] = True
        report["status"] = "ADEQUATE"
        with self.assertRaises(TestAdequacyError):
            verify_test_adequacy_report(report)

    def test_single_percentage_cannot_mask_failed_known_bad_lane(self):
        report = evaluate_test_adequacy(mutation_report(), known_bad=lane("KB", False), held_out=lane("HO"), metamorphic=lane("MM"))
        self.assertEqual(report["status"], "HOLD_FALSE_GREEN_RISK")


if __name__ == "__main__":
    unittest.main()
