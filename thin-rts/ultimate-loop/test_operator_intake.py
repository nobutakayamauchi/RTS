from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "operator_intake.py"
PACK_PATH = HERE / "intake" / "osaru-mine" / "universal-operators-v1.json"

spec = importlib.util.spec_from_file_location("operator_intake", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["operator_intake"] = module
spec.loader.exec_module(module)


class OperatorIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))

    def test_valid_pack_is_admitted_without_promotion_authority(self):
        report = module.evaluate(copy.deepcopy(self.pack))
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(report["operator_count"], 20)
        self.assertTrue(report["source_task_coverage_complete"])
        self.assertFalse(report["canonical_promotion_authorized"])
        self.assertEqual(report["disposition"], "ADMIT_AS_CHALLENGER_KNOWLEDGE")

    def test_pack_cannot_self_authorize(self):
        pack = copy.deepcopy(self.pack)
        pack["authority_effect"] = "PROMOTE"
        report = module.evaluate(pack)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertIn("AUTHORITY_EFFECT_NOT_NONE", report["blocking_states"])

    def test_all_100_source_tasks_must_remain_covered(self):
        pack = copy.deepcopy(self.pack)
        for op in pack["operators"]:
            op["source_tasks"] = [n for n in op["source_tasks"] if n != 100]
        report = module.evaluate(pack)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertIn("SOURCE_COVERAGE_INCOMPLETE", report["blocking_states"])

    def test_domain_literal_cannot_reenter_universal_definition(self):
        pack = copy.deepcopy(self.pack)
        pack["operators"][0]["purpose"] = "Use YouTube as the universal channel."
        report = module.evaluate(pack)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertTrue(
            any(state.startswith("DOMAIN_LITERAL_LEAK:") for state in report["blocking_states"])
        )

    def test_extension_must_reference_known_operators(self):
        pack = copy.deepcopy(self.pack)
        pack["candidate_extensions"][0]["source_operators"].append("OP99_DOES_NOT_EXIST")
        report = module.evaluate(pack)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertTrue(
            any(state.startswith("EXTENSION_UNKNOWN_OPERATOR:") for state in report["blocking_states"])
        )


if __name__ == "__main__":
    unittest.main()
