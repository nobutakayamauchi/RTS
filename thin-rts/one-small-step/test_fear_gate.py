import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).parent

core_spec = importlib.util.spec_from_file_location("one_small_step", ROOT / "one_small_step.py")
core = importlib.util.module_from_spec(core_spec)
core_spec.loader.exec_module(core)

gate_spec = importlib.util.spec_from_file_location("fear_gate", ROOT / "fear_gate.py")
gate = importlib.util.module_from_spec(gate_spec)
gate_spec.loader.exec_module(gate)


def base(**extra):
    case = {
        "case_id": "fear",
        "profile": {"capabilities": ["write"], "constraints": ["limited time"], "current_state": "uncertain"},
        "resources": ["phone", "AI"],
        "brain_dump": ["need income"],
        "goal": {"status": "HYPOTHESIS", "statement": "Get one client conversation", "success_measure": "one qualified conversation", "metric_validity": "SUPPORTED"},
    }
    case.update(extra)
    return case


class FearGateTests(unittest.TestCase):
    def test_unbounded_fear_routes_to_risk_decomposition(self):
        r = gate.apply_fear_gate(base(fear={"active": True, "feared_loss": "rejection"}), core.evaluate)
        self.assertEqual(r["phase"], "RISK_BOUNDING")
        self.assertEqual(r["next_step_kind"], "DECOMPOSE_FEAR_AND_BOUND_RISK")
        self.assertIn("FEAR_NOT_BOUNDED", r["blocking_states"])

    def test_bounded_fear_can_proceed_to_small_experiment(self):
        r = gate.apply_fear_gate(base(
            fear={
                "active": True,
                "feared_loss": "rejection",
                "reversibility": "REVERSIBLE",
                "cost_of_inaction": "no learning signal",
                "bounded_experiment": "send one low-friction message",
            },
            step_plan={
                "action": "send one low-friction message",
                "expected_signal": "reply or no reply",
                "review_boundary": "after one message",
                "stop_or_change_rule": "review before sending more",
            },
        ), core.evaluate)
        self.assertEqual(r["phase"], "ONE_SMALL_STEP")
        self.assertEqual(r["next_step_kind"], "ACT_AND_OBSERVE")


if __name__ == "__main__":
    unittest.main()
