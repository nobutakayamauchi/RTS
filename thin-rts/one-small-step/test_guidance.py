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


class GuidanceTests(unittest.TestCase):
    def test_canonical_entrypoint_does_not_bypass_fear_gate(self):
        r = guidance.evaluate(base(fear={"active": True, "feared_loss": "rejection"}))
        self.assertEqual(r["phase"], "RISK_BOUNDING")

    def test_canonical_entrypoint_preserves_core_orientation_precedence(self):
        r = guidance.evaluate({"case_id": "lost", "fear": {"active": True}})
        self.assertEqual(r["phase"], "SELF_PROFILE")


if __name__ == "__main__":
    unittest.main()
