from __future__ import annotations

import unittest

import rework_learning


def event(i, *, outcome="REWORK", markers=None, task="bank-checkout", source="ssh", operation="runtime-check", from_step="CHECK", to_step="CONFIG"):
    return {
        "event_id": f"e{i}",
        "occurred_at": f"2026-08-21T01:{i:02d}:00Z",
        "task_scope": task,
        "source": source,
        "operation": operation,
        "outcome": outcome,
        "rework_class": "HUMAN_OPERATION" if markers else "WORKFLOW",
        "from_step": from_step,
        "to_step": to_step,
        "markers": markers or [],
        "evidence_refs": [f"trace:{i}"],
    }


class ReworkLearningTests(unittest.TestCase):
    def test_realtime_signals_can_activate_without_history(self):
        case = {
            "mode": "OBSERVE",
            "events": [
                event(1, markers=["MULTI_TAB"]),
                event(2, markers=["PASTE_FAILURE"]),
                event(3, markers=["COMMAND_RETRY"]),
            ],
            "history": {"clusters": []},
        }
        report = rework_learning.evaluate(case)
        self.assertEqual(report["next_mode"], "ASSIST_ACTIVE")
        self.assertTrue(report["difficult_zone"])
        self.assertFalse(report["evidence_policy"]["historical_evidence_used"])
        self.assertIn("CONVERGE_TO_SINGLE_TERMINAL", report["assist_actions"])
        self.assertIn("SPLIT_LONG_COMMANDS", report["assist_actions"])

    def test_history_supports_but_does_not_force_unrelated_scope(self):
        case = {
            "mode": "OBSERVE",
            "events": [event(1, task="new-scope", source="ui", operation="form")],
            "history": {
                "clusters": [
                    {"scope_key": "old-scope|ssh|runtime-check", "rework_count": 99}
                ]
            },
        }
        report = rework_learning.evaluate(case)
        self.assertEqual(report["next_mode"], "OBSERVE")
        self.assertEqual(report["signal_components"]["historical_hits"], 0)

    def test_assist_is_scoped_and_enters_clearing_after_success_tail(self):
        case = {
            "mode": "ASSIST_ACTIVE",
            "events": [
                event(1, markers=["MULTI_TAB"]),
                event(2, outcome="SUCCESS", markers=[], from_step="RUN", to_step="DONE"),
                event(3, outcome="SUCCESS", markers=[], from_step="RUN", to_step="DONE"),
            ],
        }
        report = rework_learning.evaluate(case)
        self.assertEqual(report["next_mode"], "CLEARING")

    def test_clearing_returns_to_observe_after_stable_success(self):
        case = {
            "mode": "CLEARING",
            "events": [
                event(1, outcome="SUCCESS", markers=[], from_step="RUN", to_step="DONE"),
                event(2, outcome="SUCCESS", markers=[], from_step="RUN", to_step="DONE"),
            ],
        }
        report = rework_learning.evaluate(case)
        self.assertEqual(report["next_mode"], "OBSERVE")
        self.assertFalse(report["difficult_zone"])

    def test_meteor_old_learning_does_not_override_current_success(self):
        case = {
            "mode": "OBSERVE",
            "events": [
                event(1, outcome="SUCCESS", markers=[], task="bank-checkout"),
                event(2, outcome="SUCCESS", markers=[], task="bank-checkout"),
            ],
            "history": {
                "clusters": [
                    {"scope_key": "bank-checkout|ssh|runtime-check", "rework_count": 500}
                ]
            },
        }
        report = rework_learning.evaluate(case)
        self.assertEqual(report["next_mode"], "OBSERVE")
        self.assertFalse(report["difficult_zone"])

    def test_meteor_single_multi_tab_event_is_not_universal_rule(self):
        case = {
            "mode": "OBSERVE",
            "events": [event(1, markers=["MULTI_TAB"], task="one-off")],
        }
        report = rework_learning.evaluate(case)
        self.assertEqual(report["next_mode"], "OBSERVE")


if __name__ == "__main__":
    unittest.main()
