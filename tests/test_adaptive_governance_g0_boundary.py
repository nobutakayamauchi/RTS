from __future__ import annotations

import unittest

from adaptive_governance.compiler import compile_plan
from adaptive_governance.models import CONTEXT_SCHEMA


def base_context() -> dict:
    return {
        "schema_version": CONTEXT_SCHEMA,
        "change_id": "RTS-CHANGE-G0-BOUNDARY-001",
        "summary": "Verify that G0 remains strictly local and read-only.",
        "change_kinds": ["DOCUMENTATION"],
        "affected_paths": ["docs/example.md"],
        "requested_actions": ["READ"],
        "impact": {
            "read_only": True,
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
        },
        "estimated_implementation_steps": 1,
    }


class AdaptiveGovernanceG0BoundaryTests(unittest.TestCase):
    def test_exact_local_read_only_documentation_is_g0(self) -> None:
        self.assertEqual(compile_plan(base_context())["level"], "G0")

    def test_non_read_only_documentation_is_not_g0(self) -> None:
        value = base_context()
        value["impact"]["read_only"] = False
        self.assertEqual(compile_plan(value)["level"], "G1")

    def test_adjacent_read_only_documentation_is_g3(self) -> None:
        value = base_context()
        value["impact"]["repository_scope"] = "ADJACENT"
        self.assertEqual(compile_plan(value)["level"], "G3")


if __name__ == "__main__":
    unittest.main()
