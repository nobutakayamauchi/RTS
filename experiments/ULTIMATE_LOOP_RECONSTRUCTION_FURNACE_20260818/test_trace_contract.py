from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("trace_contract.py")
spec = importlib.util.spec_from_file_location("reconstruction_furnace_trace_contract", MODULE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def event(seq: int, event_type: str, *, ns: int | None = None) -> dict:
    return {
        "schema_version": mod.TRACE_SCHEMA,
        "run_id": "RUN-1",
        "task_id": "TASK-1",
        "seq": seq,
        "monotonic_ns": seq * 100 if ns is None else ns,
        "event_type": event_type,
        "attempt_id": "ATTEMPT-1",
        "payload": {},
    }


class TraceContractTests(unittest.TestCase):
    def complete_trace(self) -> list[dict]:
        return [
            event(i, typ)
            for i, typ in enumerate(
                [
                    "TASK_START",
                    "REPO_DISCOVERY_START",
                    "REPO_DISCOVERY_END",
                    "REPO_MODEL_REVISION",
                    "FIRST_ACTIONABLE_HYPOTHESIS",
                    "HYPOTHESIS_EVIDENCE",
                    "DA_FINDING",
                    "COUNTER_DA_FINDING",
                    "PATCH_ATTEMPT",
                    "TEST_RESULT",
                    "FAILURE_SIGNATURE",
                    "HYPOTHESIS_REOPEN",
                    "MODEL_REVISION",
                    "ROOT_CAUSE_CLASSIFICATION",
                    "INVARIANT_CANDIDATE",
                    "INVARIANT_DECISION",
                    "METHOD_MEMORY_REUSE",
                    "FALSE_TRANSFER",
                    "HUMAN_TOUCH",
                    "TOOL_INVOCATION",
                    "OBSERVER_OVERHEAD",
                    "TASK_END",
                ],
                1,
            )
        ]

    def test_complete_trace_passes(self) -> None:
        result = mod.validate_trace(self.complete_trace())
        self.assertTrue(result["complete"])
        self.assertEqual(result["state"], "TRACE_COMPLETE")

    def test_missing_event_is_incomplete_not_silently_passed(self) -> None:
        rows = [row for row in self.complete_trace() if row["event_type"] != "DA_FINDING"]
        for i, row in enumerate(rows, 1):
            row["seq"] = i
            row["monotonic_ns"] = i * 100
        result = mod.validate_trace(rows)
        self.assertFalse(result["complete"])
        self.assertIn("DA_FINDING", result["missing_event_types"])

    def test_sequence_gap_fails_closed(self) -> None:
        rows = self.complete_trace()
        rows[5]["seq"] = 999
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_monotonic_regression_fails_closed(self) -> None:
        rows = self.complete_trace()
        rows[5]["monotonic_ns"] = 0
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_cross_task_trace_fails_closed(self) -> None:
        rows = self.complete_trace()
        rows[4]["task_id"] = "TASK-OTHER"
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_observer_overhead_can_be_negative_if_noise_wins(self) -> None:
        self.assertEqual(
            mod.observer_overhead_pct(
                baseline_wall_ns=100,
                observed_wall_ns=90,
            ),
            -10.0,
        )


if __name__ == "__main__":
    unittest.main()
