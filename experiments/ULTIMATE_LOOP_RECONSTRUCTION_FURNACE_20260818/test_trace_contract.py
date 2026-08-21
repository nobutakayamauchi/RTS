from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
import threading
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("trace_contract.py")
spec = importlib.util.spec_from_file_location("reconstruction_furnace_trace_contract", MODULE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def payload(event_type: str, *, tool_id: int = 0) -> dict:
    values = {
        "TASK_START": {"subject": "blind repair"},
        "REPO_DISCOVERY_START": {"scope": "repository"},
        "REPO_DISCOVERY_END": {"evidence_refs": ["repo-map"]},
        "REPO_MODEL_REVISION": {"revision_id": "RM-1", "evidence_refs": ["repo-map"]},
        "FIRST_ACTIONABLE_HYPOTHESIS": {"hypothesis_id": "H-1", "statement": "candidate", "evidence_refs": ["ev-1"]},
        "HYPOTHESIS_EVIDENCE": {"hypothesis_id": "H-1", "direction": "SUPPORT", "evidence_refs": ["ev-1"]},
        "DA_FINDING": {"finding_id": "DA-1", "target_id": "H-1", "statement": "attack"},
        "COUNTER_DA_FINDING": {"finding_id": "CDA-1", "target_id": "DA-1", "statement": "counter"},
        "PATCH_ATTEMPT": {"patch_id": "P-1", "patch_sha256": "a" * 64},
        "TEST_RESULT": {"test_id": "T-1", "classification": "PASS", "evidence_refs": ["testlog"]},
        "FAILURE_SIGNATURE": {"signature": "sig", "evidence_refs": ["testlog"]},
        "HYPOTHESIS_REOPEN": {"hypothesis_id": "H-1", "reason": "failed"},
        "MODEL_REVISION": {"revision_id": "RM-2", "reason": "new evidence"},
        "ROOT_CAUSE_CLASSIFICATION": {"candidate_id": "RC-1", "classification": "LOGIC", "evidence_refs": ["ev-2"]},
        "INVARIANT_CANDIDATE": {"invariant_id": "I-1", "statement": "x"},
        "INVARIANT_DECISION": {"invariant_id": "I-1", "decision": "PROMOTE"},
        "METHOD_MEMORY_REUSE": {"memory_id": "M-1", "source_task_ids": ["OLD-1"]},
        "FALSE_TRANSFER": {"memory_id": "M-1", "impact": "misled"},
        "HUMAN_TOUCH": {"action": "none"},
        "TOOL_INVOCATION": {"tool_class": f"repo-read-{tool_id}"},
        "OBSERVER_OVERHEAD": {"wall_ns": 10, "cpu_ns": 5, "bytes_written": 100},
    }
    return values[event_type]


def make_trace(*, include_failure: bool = False, tools: int = 1) -> list[dict]:
    types = [
        "TASK_START", "REPO_DISCOVERY_START", "REPO_DISCOVERY_END",
        "REPO_MODEL_REVISION", "FIRST_ACTIONABLE_HYPOTHESIS",
        "HYPOTHESIS_EVIDENCE", "DA_FINDING", "COUNTER_DA_FINDING",
        "PATCH_ATTEMPT", "TEST_RESULT",
    ]
    if include_failure:
        types += ["FAILURE_SIGNATURE", "HYPOTHESIS_REOPEN", "MODEL_REVISION"]
    rows = []
    counts = {key: 0 for key in mod.COUNTED_EVENT_TYPES}
    for typ in types:
        for key, mapped in mod.COUNTED_EVENT_TYPES.items():
            if mapped == typ:
                counts[key] += 1
        rows.append({
            "schema_version": mod.TRACE_SCHEMA,
            "run_id": "RUN-1",
            "task_id": "TASK-1",
            "seq": 0,
            "monotonic_ns": 0,
            "event_type": typ,
            "attempt_id": "ATTEMPT-1",
            "payload": payload(typ),
        })
    for i in range(tools):
        counts["tool_invocations"] += 1
        rows.append({
            "schema_version": mod.TRACE_SCHEMA,
            "run_id": "RUN-1",
            "task_id": "TASK-1",
            "seq": 0,
            "monotonic_ns": 0,
            "event_type": "TOOL_INVOCATION",
            "attempt_id": "ATTEMPT-1",
            "payload": payload("TOOL_INVOCATION", tool_id=i),
        })
    rows.append({
        "schema_version": mod.TRACE_SCHEMA,
        "run_id": "RUN-1",
        "task_id": "TASK-1",
        "seq": 0,
        "monotonic_ns": 0,
        "event_type": "OBSERVER_OVERHEAD",
        "attempt_id": "ATTEMPT-1",
        "payload": payload("OBSERVER_OVERHEAD"),
    })
    for i, row in enumerate(rows, 1):
        row["seq"] = i
        row["monotonic_ns"] = i * 100
    rows.append({
        "schema_version": mod.TRACE_SCHEMA,
        "run_id": "RUN-1",
        "task_id": "TASK-1",
        "seq": len(rows) + 1,
        "monotonic_ns": (len(rows) + 1) * 100,
        "event_type": "TASK_END",
        "attempt_id": "ATTEMPT-1",
        "payload": {"result": "PASS", "event_counts": counts},
    })
    return rows


class TraceContractTests(unittest.TestCase):
    def test_clean_first_pass_trace_does_not_need_fake_failure_events(self) -> None:
        result = mod.validate_trace(make_trace(include_failure=False))
        self.assertTrue(result["complete"])
        self.assertEqual(result["event_type_counts"].get("FAILURE_SIGNATURE", 0), 0)

    def test_empty_payload_spoof_fails_closed(self) -> None:
        rows = make_trace()
        rows[4]["payload"] = {}
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_declared_counts_must_match_observed_events(self) -> None:
        rows = make_trace(tools=3)
        rows[-1]["payload"]["event_counts"]["tool_invocations"] = 2
        result = mod.validate_trace(rows)
        self.assertFalse(result["complete"])
        self.assertTrue(result["count_mismatches"])

    def test_patch_before_counter_da_is_incomplete(self) -> None:
        rows = make_trace()
        patch = next(i for i, x in enumerate(rows) if x["event_type"] == "PATCH_ATTEMPT")
        cda = next(i for i, x in enumerate(rows) if x["event_type"] == "COUNTER_DA_FINDING")
        rows[patch], rows[cda] = rows[cda], rows[patch]
        for i, row in enumerate(rows, 1):
            row["seq"] = i
            row["monotonic_ns"] = i * 100
        result = mod.validate_trace(rows)
        self.assertFalse(result["complete"])
        self.assertIn("PATCH_BEFORE_COUNTER_DA", result["order_errors"])

    def test_sequence_gap_fails_closed(self) -> None:
        rows = make_trace()
        rows[5]["seq"] = 999
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_cross_task_trace_fails_closed(self) -> None:
        rows = make_trace()
        rows[4]["task_id"] = "TASK-OTHER"
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_negative_timing_noise_does_not_claim_negative_overhead(self) -> None:
        self.assertEqual(mod.observer_overhead_pct(baseline_wall_ns=100, observed_wall_ns=90), 0.0)

    def test_burst_recorder_captures_every_event_in_order_and_replays(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sink = pathlib.Path(td) / "trace.jsonl"
            rec = mod.TraceRecorder(run_id="RUN-BURST", task_id="TASK-BURST", sink=sink)
            for typ in [
                "TASK_START", "REPO_DISCOVERY_START", "REPO_DISCOVERY_END",
                "REPO_MODEL_REVISION", "FIRST_ACTIONABLE_HYPOTHESIS",
                "HYPOTHESIS_EVIDENCE", "DA_FINDING", "COUNTER_DA_FINDING",
            ]:
                rec.emit(typ, attempt_id="A-1", payload=payload(typ))
            threads = 8
            per_thread = 250

            def worker(tid: int) -> None:
                for i in range(per_thread):
                    rec.emit(
                        "TOOL_INVOCATION",
                        attempt_id="A-1",
                        payload={"tool_class": f"t{tid}-{i}"},
                    )

            workers = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
            for worker_thread in workers:
                worker_thread.start()
            for worker_thread in workers:
                worker_thread.join()

            rec.emit("PATCH_ATTEMPT", attempt_id="A-1", payload=payload("PATCH_ATTEMPT"))
            rec.emit("TEST_RESULT", attempt_id="A-1", payload=payload("TEST_RESULT"))
            stats_before = rec.stats()
            rec.emit(
                "OBSERVER_OVERHEAD",
                attempt_id="A-1",
                payload={
                    "wall_ns": stats_before["write_wall_ns"],
                    "cpu_ns": 0,
                    "bytes_written": stats_before["bytes_written"],
                },
            )
            counts = {key: 0 for key in mod.COUNTED_EVENT_TYPES}
            counts["tool_invocations"] = threads * per_thread
            counts["patch_attempts"] = 1
            counts["tests"] = 1
            rec.emit(
                "TASK_END",
                attempt_id="A-1",
                payload={"result": "PASS", "event_counts": counts},
            )

            memory_rows = rec.snapshot()
            disk_rows = mod.load_jsonl(sink)
            self.assertEqual(len(memory_rows), len(disk_rows))
            self.assertEqual([row["seq"] for row in disk_rows], list(range(1, len(disk_rows) + 1)))
            self.assertEqual(rec.stats()["events_emitted"], rec.stats()["events_captured"])
            result = mod.validate_trace(disk_rows)
            self.assertTrue(result["complete"])
            self.assertEqual(result["event_type_counts"]["TOOL_INVOCATION"], threads * per_thread)

    def test_nested_forbidden_benchmark_key_fails_closed(self) -> None:
        rows = make_trace()
        rows[6]["payload"]["nested"] = {"patch": "gold"}
        with self.assertRaises(mod.TraceContractError):
            mod.validate_trace(rows)

    def test_second_task_end_cannot_hide_early_end(self) -> None:
        rows = make_trace()
        duplicate = dict(rows[-1])
        duplicate["seq"] = rows[-1]["seq"]
        duplicate["monotonic_ns"] = rows[-1]["monotonic_ns"]
        rows.insert(-1, duplicate)
        for i, row in enumerate(rows, 1):
            row["seq"] = i
            row["monotonic_ns"] = i * 100
        result = mod.validate_trace(rows)
        self.assertFalse(result["complete"])
        self.assertFalse(result["task_end_last"])

    def test_test_result_must_bind_to_prior_patch_attempt(self) -> None:
        rows = make_trace()
        test_row = next(row for row in rows if row["event_type"] == "TEST_RESULT")
        test_row["attempt_id"] = "ATTEMPT-OTHER"
        result = mod.validate_trace(rows)
        self.assertFalse(result["complete"])
        self.assertTrue(any("ATTEMPT-OTHER" in err for err in result["order_errors"]))

    def test_recorder_freezes_nested_payload_against_caller_mutation(self) -> None:
        rec = mod.TraceRecorder(run_id="RUN-FREEZE", task_id="TASK-FREEZE")
        original = {"subject": "blind repair", "extra": {"notes": ["before"]}}
        rec.emit("TASK_START", attempt_id="A-1", payload=original)
        original["extra"]["notes"][0] = "after"
        self.assertEqual(rec.snapshot()[0]["payload"]["extra"]["notes"], ["before"])


if __name__ == "__main__":
    unittest.main()
