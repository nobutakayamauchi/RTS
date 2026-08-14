from __future__ import annotations

import unittest

from choice_gate import apply_choice_gate


def ready_core(case):
    return {
        "classification": "READY_FOR_NEXT_STEP",
        "phase": "ONE_SMALL_STEP",
        "next_step_kind": "ACT_AND_OBSERVE",
        "blocking_states": [],
        "questions": [],
        "reasons": [],
    }


def orientation_core(case):
    return {
        "classification": "NEEDS_ORIENTATION",
        "phase": "SELF_PROFILE",
        "next_step_kind": "ORIENT",
        "blocking_states": [],
        "questions": [],
        "reasons": [],
    }


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


class ChoiceGateTests(unittest.TestCase):
    def test_material_choice_requires_tradeoff_map(self):
        r = apply_choice_gate({"choice": {"active": True, "materiality": "MATERIAL"}}, ready_core)
        self.assertEqual(r["classification"], "NEEDS_CHOICE_REVIEW")
        self.assertEqual(r["decision_owner"], "USER")

    def test_informed_reversible_choice_remains_user_owned(self):
        r = apply_choice_gate({"choice": informed_choice()}, ready_core)
        self.assertEqual(r["classification"], "READY_FOR_NEXT_STEP")
        self.assertEqual(r["choice_status"], "INFORMED_CHOICE_READY")
        self.assertEqual(r["decision_owner"], "USER")

    def test_material_severe_risk_blocks_normal_action(self):
        r = apply_choice_gate(
            {"choice": informed_choice(severe_or_irreversible_harm_risk="MATERIAL")},
            ready_core,
        )
        self.assertEqual(r["classification"], "SAFETY_REVIEW_REQUIRED")
        self.assertEqual(r["phase"], "SAFETY_BOUNDARY")

    def test_unknown_risk_plus_irreversibility_fails_closed(self):
        r = apply_choice_gate(
            {"choice": informed_choice(reversibility="IRREVERSIBLE", severe_or_irreversible_harm_risk="UNKNOWN")},
            ready_core,
        )
        self.assertEqual(r["classification"], "SAFETY_REVIEW_REQUIRED")

    def test_low_consequence_choice_does_not_force_life_review(self):
        r = apply_choice_gate({"choice": {"active": True, "materiality": "LOW"}}, ready_core)
        self.assertEqual(r["classification"], "READY_FOR_NEXT_STEP")
        self.assertEqual(r["decision_owner"], "USER")

    def test_choice_gate_does_not_override_orientation(self):
        r = apply_choice_gate({"choice": informed_choice()}, orientation_core)
        self.assertEqual(r["phase"], "SELF_PROFILE")


if __name__ == "__main__":
    unittest.main()
