from __future__ import annotations

import unittest

from adaptive_governance.cli import build_parser
from adaptive_governance.compiler import compile_plan, verify_plan
from adaptive_governance.models import AdaptiveGovernanceError, CONTEXT_SCHEMA


def context(**impact_overrides):
    impact = {
        "read_only": False,
        "repository_scope": "LOCAL",
        "reversible": True,
        "touches_approval_flow": False,
        "handles_personal_data": False,
        "handles_sensitive_material": False,
        "financial_or_contractual": False,
        "production_effect": False,
        "external_action": False,
        "historical_failure": False,
        "emergency": False,
        "uncertainty": "LOW",
    }
    impact.update(impact_overrides)
    return {
        "schema_version": CONTEXT_SCHEMA,
        "change_id": "RTS-CHANGE-000001",
        "summary": "Compile the minimum governance required for an exact change.",
        "change_kinds": ["CODE"],
        "affected_paths": ["adaptive_governance/compiler.py"],
        "requested_actions": ["WRITE_LOCAL"],
        "impact": impact,
        "estimated_implementation_steps": 4,
    }


class AdaptiveGovernanceTests(unittest.TestCase):
    def test_read_only_documentation_is_g0(self):
        value = context(read_only=True)
        value["change_kinds"] = ["DOCUMENTATION"]
        value["requested_actions"] = ["READ"]
        plan = compile_plan(value)
        self.assertEqual(plan["level"], "G0")
        self.assertEqual(plan["requirements"]["human_approvals"], 0)

    def test_reversible_local_code_is_g1(self):
        self.assertEqual(compile_plan(context())["level"], "G1")

    def test_approval_flow_is_g2(self):
        plan = compile_plan(context(touches_approval_flow=True))
        self.assertEqual(plan["level"], "G2")
        self.assertTrue(plan["requirements"]["preflight"])
        self.assertEqual(plan["requirements"]["human_approvals"], 1)

    def test_adjacent_write_is_g3(self):
        value = context(repository_scope="ADJACENT")
        value["requested_actions"] = ["WRITE_ADJACENT"]
        plan = compile_plan(value)
        self.assertEqual(plan["level"], "G3")
        self.assertTrue(plan["requirements"]["independent_review"])

    def test_financial_change_is_g4(self):
        plan = compile_plan(context(financial_or_contractual=True))
        self.assertEqual(plan["level"], "G4")
        self.assertEqual(plan["requirements"]["human_approvals"], 2)
        self.assertEqual(plan["requirements"]["execution_mode"], "MANUAL")

    def test_emergency_never_lowers_level(self):
        plan = compile_plan(context(financial_or_contractual=True, emergency=True))
        self.assertEqual(plan["level"], "G4")
        self.assertIn("EMERGENCY_DOES_NOT_LOWER_GOVERNANCE", plan["classification_reasons"])

    def test_plan_is_deterministic(self):
        first = compile_plan(context(touches_approval_flow=True))
        second = compile_plan(context(touches_approval_flow=True))
        self.assertEqual(first, second)

    def test_tampered_plan_fails_closed(self):
        plan = compile_plan(context())
        plan["authority"]["merge_authorized"] = True
        with self.assertRaisesRegex(AdaptiveGovernanceError, "authority boundary widened"):
            verify_plan(plan)

    def test_context_mismatch_is_rejected(self):
        plan = compile_plan(context())
        changed = context(touches_approval_flow=True)
        with self.assertRaisesRegex(AdaptiveGovernanceError, "does not match"):
            verify_plan(plan, changed)

    def test_unknown_context_field_is_rejected(self):
        value = context()
        value["surprise"] = True
        with self.assertRaisesRegex(AdaptiveGovernanceError, "unknown fields"):
            compile_plan(value)

    def test_path_escape_is_rejected(self):
        value = context()
        value["affected_paths"] = ["../outside"]
        with self.assertRaisesRegex(AdaptiveGovernanceError, "unsafe path"):
            compile_plan(value)

    def test_tiny_high_risk_change_is_flagged_over_governed(self):
        value = context(repository_scope="ADJACENT")
        value["requested_actions"] = ["WRITE_ADJACENT"]
        value["estimated_implementation_steps"] = 1
        plan = compile_plan(value)
        self.assertEqual(plan["governance_cost"]["status"], "OVER_GOVERNED")

    def test_cli_has_no_authorizing_command(self):
        help_text = build_parser().format_help()
        self.assertIn("compile", help_text)
        self.assertIn("verify", help_text)
        self.assertNotIn("apply", help_text)
        self.assertNotIn("approve", help_text)
        self.assertNotIn("merge", help_text)

    def test_profile_step_budget_is_respected(self):
        for overrides in (
            {},
            {"touches_approval_flow": True},
            {"repository_scope": "ADJACENT"},
            {"financial_or_contractual": True},
        ):
            with self.subTest(overrides=overrides):
                value = context(**overrides)
                if overrides.get("repository_scope") == "ADJACENT":
                    value["requested_actions"] = ["WRITE_ADJACENT"]
                plan = compile_plan(value)
                self.assertLessEqual(len(plan["workflow"]), plan["requirements"]["max_governance_steps"])


if __name__ == "__main__":
    unittest.main()
