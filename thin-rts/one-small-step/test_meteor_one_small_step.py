import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("one_small_step.py")
spec = importlib.util.spec_from_file_location("one_small_step", MODULE)
oss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oss)


def base(**extra):
    case = {
        "case_id": "meteor",
        "profile": {
            "capabilities": ["write"],
            "constraints": ["limited time"],
            "current_state": "uncertain",
        },
        "resources": ["phone", "AI"],
        "brain_dump": ["need income"],
        "goal": {
            "status": "HYPOTHESIS",
            "statement": "Get one client conversation",
            "success_measure": "one qualified conversation",
            "metric_validity": "SUPPORTED",
        },
    }
    case.update(extra)
    return case


class MeteorTests(unittest.TestCase):
    def test_unknown_attempt_result_fails_closed(self):
        r = oss.evaluate(base(attempt={"result": "MAGIC_WIN"}))
        self.assertIn("INVALID_ATTEMPT_RESULT", r["blocking_states"])
        self.assertEqual(r["next_step_kind"], "CLASSIFY_RESULT_BEFORE_NEXT_STEP")

    def test_unknown_cause_confidence_fails_closed(self):
        r = oss.evaluate(base(attempt={
            "result": "FAILURE",
            "observed": "no reply",
            "failure_measure": "0/10",
            "cause": "maybe timing",
            "cause_confidence": "CERTAINISH",
            "prevention_method": "send later",
        }))
        self.assertIn("INVALID_CAUSE_CONFIDENCE", r["blocking_states"])
        self.assertEqual(r["next_step_kind"], "RECONSTRUCT_EVENT_AND_COLLECT_EVIDENCE")

    def test_unknown_metric_cannot_support_strong_outcome_progress(self):
        c = base(progress={"outcome": True})
        c["goal"]["metric_validity"] = "UNKNOWN"
        r = oss.evaluate(c)
        self.assertIn("METRIC_UNVALIDATED", r["blocking_states"])
        self.assertEqual(r["classification"], "REVIEW_REQUIRED")

    def test_minimal_capacity_reduces_action(self):
        r = oss.evaluate(base(capacity="MINIMAL"))
        self.assertEqual(r["next_step_kind"], "ONE_DECISION_OR_CHECKPOINT")

    def test_preservation_counts_as_progress_and_avoids_effort_gap(self):
        r = oss.evaluate(base(effort={"hours": 2}, progress={"preservation": True}))
        self.assertNotIn("EFFORT_EFFECT_GAP", r["blocking_states"])

    def test_lucky_success_is_not_gold(self):
        r = oss.evaluate(base(attempt={"result": "SUCCESS", "measure": "1 client"}))
        self.assertEqual(r["experience_status"], "SUCCESS_1")

    def test_transfer_without_method_is_not_gold(self):
        r = oss.evaluate(base(attempt={
            "result": "SUCCESS",
            "measure": "3/10",
            "success_explanation": "CTA",
            "personal_reproduction": "VERIFIED",
            "transfer_reproduction": "VERIFIED",
            "evidence_refs": ["run:1"],
        }))
        self.assertEqual(r["experience_status"], "SUCCESS_4")

    def test_prevention_pass_without_verified_cause_is_not_gold(self):
        r = oss.evaluate(base(attempt={
            "result": "FAILURE",
            "observed": "duplicate",
            "failure_measure": "1",
            "cause": "maybe missing guard",
            "cause_confidence": "HYPOTHESIS",
            "prevention_method": "idempotency key",
            "prevention_test": "PASS",
            "evidence_refs": ["test:1"],
        }))
        self.assertEqual(r["experience_status"], "FAILURE_5")
        self.assertNotEqual(r["experience_status"], "GOLD_EXPERIENCE_FAILURE")

    def test_gold_regression_reopens_even_when_capacity_none(self):
        r = oss.evaluate(base(capacity="NONE", attempt={
            "result": "SUCCESS",
            "measure": "3/10",
            "success_explanation": "method",
            "personal_reproduction": "VERIFIED",
            "transfer_reproduction": "VERIFIED",
            "reusable_method": "method",
            "boundary_conditions": "condition",
            "evidence_refs": ["run:1"],
            "regression": "FAIL",
        }))
        self.assertEqual(r["experience_status"], "EXPERIENCE_REVIEW_REQUIRED")
        self.assertEqual(r["phase"], "PRESERVE_AND_RESTART")

    def test_external_blocker_is_not_solved_by_more_effort(self):
        r = oss.evaluate(base(
            effort={"hours": 100},
            external_blocker={"active": True, "description": "required record withheld", "options_considered": ["alternate record"]},
        ))
        self.assertEqual(r["classification"], "BLOCKED")
        self.assertNotIn("EFFORT_EFFECT_GAP", r["blocking_states"])

    def test_step_without_review_boundary_is_blocked(self):
        r = oss.evaluate(base(step_plan={
            "action": "send ten messages",
            "expected_signal": "reply rate changes",
        }))
        self.assertIn("STEP_PLAN_INCOMPLETE", r["blocking_states"])
        self.assertEqual(r["classification"], "REVIEW_REQUIRED")

    def test_complete_step_has_cutoff_and_can_run(self):
        r = oss.evaluate(base(step_plan={
            "action": "send ten messages",
            "expected_signal": "at least one qualified reply",
            "review_boundary": "after 10 messages",
            "stop_or_change_rule": "if zero qualified replies, change target or CTA before adding volume",
        }))
        self.assertEqual(r["next_step_kind"], "ACT_AND_OBSERVE")
        self.assertEqual(r["phase"], "ONE_SMALL_STEP")


if __name__ == "__main__":
    unittest.main()
