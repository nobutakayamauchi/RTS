import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("one_small_step.py")
spec = importlib.util.spec_from_file_location("one_small_step", MODULE)
oss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oss)


def oriented(**extra):
    case = {
        "case_id": "case-1",
        "profile": {
            "capabilities": ["write"],
            "constraints": ["limited time"],
            "current_state": "uncertain",
        },
        "resources": ["phone", "AI"],
        "brain_dump": ["need income", "project idea"],
        "goal": {
            "status": "HYPOTHESIS",
            "statement": "Get one qualified client conversation",
            "success_measure": "one qualified client conversation",
            "metric_validity": "SUPPORTED",
        },
    }
    case.update(extra)
    return case


class BaselineTests(unittest.TestCase):
    def test_lost_user_starts_with_profile(self):
        r = oss.evaluate({"case_id": "lost"})
        self.assertEqual(r["phase"], "SELF_PROFILE")
        self.assertEqual(r["next_step_kind"], "ORIENT")

    def test_goal_can_be_invalidated(self):
        c = oriented()
        c["goal"]["status"] = "INVALIDATED"
        r = oss.evaluate(c)
        self.assertEqual(r["next_step_kind"], "REDEFINE_GOAL")

    def test_no_capacity_requires_checkpoint_not_productivity(self):
        c = oriented(capacity="NONE")
        r = oss.evaluate(c)
        self.assertEqual(r["classification"], "PRESERVE")
        self.assertEqual(r["next_step_kind"], "CHECKPOINT_ONLY")

    def test_effort_is_not_progress(self):
        c = oriented(effort={"hours": 20})
        r = oss.evaluate(c)
        self.assertIn("EFFORT_EFFECT_GAP", r["blocking_states"])

    def test_unknown_failure_does_not_invent_cause(self):
        c = oriented(attempt={"result": "FAILURE", "observed": "no reply", "failure_measure": "0/10", "cause_confidence": "UNKNOWN"})
        r = oss.evaluate(c)
        self.assertEqual(r["next_step_kind"], "RECONSTRUCT_EVENT_AND_COLLECT_EVIDENCE")
        self.assertEqual(r["experience_status"], "FAILURE_2")

    def test_success_gold_requires_transfer_and_retained_method(self):
        c = oriented(attempt={
            "result": "SUCCESS",
            "measure": "3/10",
            "success_explanation": "lower-friction CTA",
            "personal_reproduction": "VERIFIED",
            "transfer_reproduction": "VERIFIED",
            "reusable_method": "ask one low-friction question first",
            "boundary_conditions": "cold outreach to similar audience",
            "evidence_refs": ["run:42"],
        })
        r = oss.evaluate(c)
        self.assertEqual(r["experience_status"], "GOLD_EXPERIENCE_SUCCESS")

    def test_failure_gold_requires_verified_repeat_prevention(self):
        c = oriented(attempt={
            "result": "FAILURE",
            "observed": "duplicate submission",
            "failure_measure": "1 duplicate",
            "cause": "no idempotency guard",
            "cause_confidence": "VERIFIED",
            "prevention_method": "idempotency key",
            "prevention_test": "PASS",
            "evidence_refs": ["test:idempotency-regression"],
        })
        r = oss.evaluate(c)
        self.assertEqual(r["experience_status"], "GOLD_EXPERIENCE_FAILURE")

    def test_gold_is_revocable(self):
        c = oriented(attempt={
            "result": "SUCCESS",
            "measure": "3/10",
            "success_explanation": "method",
            "personal_reproduction": "VERIFIED",
            "transfer_reproduction": "VERIFIED",
            "reusable_method": "method",
            "boundary_conditions": "condition",
            "evidence_refs": ["run:42"],
            "contradicting_evidence": ["run:43"],
        })
        r = oss.evaluate(c)
        self.assertEqual(r["experience_status"], "EXPERIENCE_REVIEW_REQUIRED")

    def test_external_blocker_is_not_effort_failure(self):
        c = oriented(external_blocker={"active": True, "description": "document unavailable"})
        r = oss.evaluate(c)
        self.assertEqual(r["phase"], "BLOCKER_REVIEW")
        self.assertIn("EXTERNAL_BLOCKER", r["blocking_states"])


if __name__ == "__main__":
    unittest.main()
