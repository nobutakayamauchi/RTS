import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("one_small_step.py")
spec = importlib.util.spec_from_file_location("one_small_step", MODULE)
oss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oss)


def oriented(**extra):
    case = {
        "case_id": "review-regression",
        "profile": {
            "capabilities": ["write"],
            "constraints": ["limited time"],
            "current_state": "uncertain",
        },
        "resources": ["phone", "AI"],
        "brain_dump": ["need income"],
        "goal": {
            "status": "HYPOTHESIS",
            "statement": "Get one qualified client conversation",
            "success_measure": "one qualified client conversation",
            "metric_validity": "SUPPORTED",
        },
    }
    case.update(extra)
    return case


class ReviewRegressionTests(unittest.TestCase):
    def test_goal_success_definition_is_not_observed_measure(self):
        c = oriented(attempt={
            "result": "SUCCESS",
            "success_explanation": "lower-friction CTA",
            "personal_reproduction": "VERIFIED",
            "transfer_reproduction": "VERIFIED",
            "reusable_method": "ask one low-friction question first",
            "boundary_conditions": "similar audience",
            "evidence_refs": ["run:42"],
        })
        r = oss.evaluate(c)
        self.assertNotEqual(r["experience_status"], "GOLD_EXPERIENCE_SUCCESS")
        self.assertEqual(r["experience_status"], "SUCCESS_1")

    def test_null_evidence_reference_cannot_grant_success_gold(self):
        c = oriented(attempt={
            "result": "SUCCESS",
            "measure": "3/10",
            "success_explanation": "method",
            "personal_reproduction": "VERIFIED",
            "transfer_reproduction": "VERIFIED",
            "reusable_method": "method",
            "boundary_conditions": "condition",
            "evidence_refs": [None],
        })
        r = oss.evaluate(c)
        self.assertNotEqual(r["experience_status"], "GOLD_EXPERIENCE_SUCCESS")

    def test_null_evidence_reference_cannot_grant_failure_gold(self):
        c = oriented(attempt={
            "result": "FAILURE",
            "observed": "duplicate submission",
            "failure_measure": "1 duplicate",
            "cause": "no idempotency guard",
            "cause_confidence": "VERIFIED",
            "prevention_method": "idempotency key",
            "prevention_test": "PASS",
            "evidence_refs": [None],
        })
        r = oss.evaluate(c)
        self.assertEqual(r["experience_status"], "FAILURE_5")

    def test_string_false_cannot_become_progress(self):
        c = oriented(progress={"outcome": "false"}, effort={"hours": 2})
        r = oss.evaluate(c)
        self.assertFalse(r["progress"]["outcome"])
        self.assertIn("INVALID_PROGRESS_VALUE", r["blocking_states"])
        self.assertIn("EFFORT_EFFECT_GAP", r["blocking_states"])


if __name__ == "__main__":
    unittest.main()
