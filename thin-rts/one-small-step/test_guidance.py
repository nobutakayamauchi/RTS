from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import guidance


def base(**extra):
    case = {
        "case_id": "guidance",
        "profile": {"capabilities": ["write"], "constraints": ["limited time"], "current_state": "uncertain"},
        "resources": ["phone", "AI"],
        "brain_dump": ["need income"],
        "goal": {"status": "HYPOTHESIS", "statement": "Get one client conversation", "success_measure": "one qualified conversation", "metric_validity": "SUPPORTED"},
    }
    case.update(extra)
    return case


def informed_choice(**overrides):
    choice = {
        "active": True,
        "materiality": "MATERIAL",
        "values_or_priorities": ["stability", "independence"],
        "expected_gains": ["more control"],
        "accepted_costs_or_losses": ["lower short-term income"],
        "alternatives_considered": ["stay with current route", "try bounded alternative"],
        "reversibility": "REVERSIBLE",
        "severe_or_irreversible_harm_risk": "NONE",
        "counterevidence_or_reasons_to_stop": ["cash runway below threshold"],
    }
    choice.update(overrides)
    return choice


class GuidanceTests(unittest.TestCase):
    def test_canonical_entrypoint_does_not_bypass_fear_gate(self):
        r = guidance.evaluate(base(fear={"active": True, "feared_loss": "rejection"}))
        self.assertEqual(r["phase"], "RISK_BOUNDING")

    def test_canonical_entrypoint_preserves_core_orientation_precedence(self):
        r = guidance.evaluate({"case_id": "lost", "fear": {"active": True}})
        self.assertEqual(r["phase"], "SELF_PROFILE")

    def test_canonical_entrypoint_does_not_bypass_choice_gate(self):
        r = guidance.evaluate(base(choice={"active": True, "materiality": "MATERIAL"}))
        self.assertEqual(r["phase"], "CHOICE_REVIEW")
        self.assertEqual(r["decision_owner"], "USER")

    def test_safety_boundary_dominates_fear_gate(self):
        r = guidance.evaluate(
            base(
                choice=informed_choice(severe_or_irreversible_harm_risk="MATERIAL"),
                fear={"active": True, "feared_loss": "rejection"},
            )
        )
        self.assertEqual(r["phase"], "SAFETY_BOUNDARY")
        self.assertEqual(r["classification"], "SAFETY_REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
