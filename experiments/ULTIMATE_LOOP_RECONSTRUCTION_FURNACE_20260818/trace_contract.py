from __future__ import annotations

import json
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

TRACE_SCHEMA = "ultimate-loop-reconstruction-furnace/trace-v2"

BASE_REQUIRED_EVENT_TYPES = (
    "TASK_START",
    "REPO_DISCOVERY_START",
    "REPO_DISCOVERY_END",
    "REPO_MODEL_REVISION",
    "FIRST_ACTIONABLE_HYPOTHESIS",
    "HYPOTHESIS_EVIDENCE",
    "DA_FINDING",
    "COUNTER_DA_FINDING",
    "OBSERVER_OVERHEAD",
    "TASK_END",
)

COUNTED_EVENT_TYPES = {
    "patch_attempts": "PATCH_ATTEMPT",
    "tests": "TEST_RESULT",
    "failure_signatures": "FAILURE_SIGNATURE",
    "hypothesis_reopens": "HYPOTHESIS_REOPEN",
    "model_revisions": "MODEL_REVISION",
    "root_cause_classifications": "ROOT_CAUSE_CLASSIFICATION",
    "invariant_candidates": "INVARIANT_CANDIDATE",
    "invariant_decisions": "INVARIANT_DECISION",
    "method_memory_reuse": "METHOD_MEMORY_REUSE",
    "false_transfer": "FALSE_TRANSFER",
    "human_touches": "HUMAN_TOUCH",
    "tool_invocations": "TOOL_INVOCATION",
}

KNOWN_EVENT_TYPES = frozenset(BASE_REQUIRED_EVENT_TYPES) | frozenset(COUNTED_EVENT_TYPES.values())

PAYLOAD_REQUIRED_KEYS = {
    "TASK_START": {"subject"},
    "REPO_DISCOVERY_START": {"scope"},
    "REPO_DISCOVERY_END": {"evidence_refs"},
    "REPO_MODEL_REVISION": {"revision_id", "evidence_refs"},
    "FIRST_ACTIONABLE_HYPOTHESIS": {"hypothesis_id", "statement", "evidence_refs"},
    "HYPOTHESIS_EVIDENCE": {"hypothesis_id", "direction", "evidence_refs"},
    "DA_FINDING": {"finding_id", "target_id", "statement"},
    "COUNTER_DA_FINDING": {"finding_id", "target_id", "statement"},
    "PATCH_ATTEMPT": {"patch_id", "patch_sha256"},
    "TEST_RESULT": {"test_id", "classification", "evidence_refs"},
    "FAILURE_SIGNATURE": {"signature", "evidence_refs"},
    "HYPOTHESIS_REOPEN": {"hypothesis_id", "reason"},
    "MODEL_REVISION": {"revision_id", "reason"},
    "ROOT_CAUSE_CLASSIFICATION": {"candidate_id", "classification", "evidence_refs"},
    "INVARIANT_CANDIDATE": {"invariant_id", "statement"},
    "INVARIANT_DECISION": {"invariant_id", "decision"},
    "METHOD_MEMORY_REUSE": {"memory_id", "source_task_ids"},
    "FALSE_TRANSFER": {"memory_id", "impact"},
    "HUMAN_TOUCH": {"action"},
    "TOOL_INVOCATION": {"tool_class"},
    "OBSERVER_OVERHEAD": {"wall_ns", "cpu_ns", "bytes_written"},
    "TASK_END": {"result", "event_counts"},
}

TASK_RESULTS = frozenset({"PASS", "FAIL", "INVALID", "STOPPED"})
FORBIDDEN_TRACE_KEYS = frozenset({
    "patch", "test_patch", "hints_text", "all_hints_text", "pull_number",
    "issue_numbers", "commit_url", "commit_urls", "FAIL_TO_PASS",
    "PASS_TO_PASS", "log_parser",
})


class TraceContractError(ValueError):
    pass


def _exact(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TraceContractError(f"{field} must be a non-empty exact string")
    return value


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise TraceContractError(f"{field} must be a list")
    return [_exact(item, field) for item in value]


def _forbidden_key_scan(value: Any) -> list[str]:
    found: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                if isinstance(key, str) and key in FORBIDDEN_TRACE_KEYS:
                    found.add(key)
                visit(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                visit(child)

    visit(value)
    return sorted(found)


def _validate_payload(event_type: str, payload: Mapping[str, Any]) -> None:
    leaked = _forbidden_key_scan(payload)
    if leaked:
        raise TraceContractError(f"forbidden benchmark fields leaked into trace: {leaked}")
    missing = PAYLOAD_REQUIRED_KEYS[event_type] - set(payload)
    if missing:
        raise TraceContractError(f"{event_type} payload missing keys: {sorted(missing)}")
    try:
        json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TraceContractError("payload must be canonical-JSON serializable") from exc

    if "evidence_refs" in payload:
        refs = _string_list(payload["evidence_refs"], "evidence_refs")
        if event_type != "REPO_DISCOVERY_END" and not refs:
            raise TraceContractError(f"{event_type} requires evidence_refs")
    if event_type == "HYPOTHESIS_EVIDENCE" and payload["direction"] not in {"SUPPORT", "REFUTE", "MIXED"}:
        raise TraceContractError("HYPOTHESIS_EVIDENCE direction invalid")
    if event_type == "PATCH_ATTEMPT":
        digest = payload["patch_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
            raise TraceContractError("PATCH_ATTEMPT patch_sha256 invalid")
    if event_type == "TEST_RESULT" and payload["classification"] not in {"PASS", "FAIL", "BLOCKED", "ERROR"}:
        raise TraceContractError("TEST_RESULT classification invalid")
    if event_type == "INVARIANT_DECISION" and payload["decision"] not in {"PROMOTE", "REJECT", "DEFER"}:
        raise TraceContractError("INVARIANT_DECISION decision invalid")
    if event_type == "TASK_END":
        if payload["result"] not in TASK_RESULTS:
            raise TraceContractError("TASK_END result invalid")
        counts = payload["event_counts"]
        if not isinstance(counts, Mapping) or set(counts) != set(COUNTED_EVENT_TYPES):
            raise TraceContractError("TASK_END event_counts shape drift")
        if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in counts.values()):
            raise TraceContractError("TASK_END event_counts must be non-negative integers")


def validate_event(event: Mapping[str, Any]) -> None:
    expected = {
        "schema_version", "run_id", "task_id", "seq", "monotonic_ns",
        "event_type", "attempt_id", "payload",
    }
    if not isinstance(event, Mapping) or set(event) != expected:
        raise TraceContractError("trace event shape drift")
    if event["schema_version"] != TRACE_SCHEMA:
        raise TraceContractError("trace schema mismatch")
    for field in ("run_id", "task_id", "event_type", "attempt_id"):
        _exact(event[field], field)
    if event["event_type"] not in KNOWN_EVENT_TYPES:
        raise TraceContractError("unknown event_type")
    if not isinstance(event["seq"], int) or isinstance(event["seq"], bool) or event["seq"] < 1:
        raise TraceContractError("seq must be >= 1")
    if not isinstance(event["monotonic_ns"], int) or isinstance(event["monotonic_ns"], bool) or event["monotonic_ns"] < 0:
        raise TraceContractError("monotonic_ns must be >= 0")
    if not isinstance(event["payload"], Mapping):
        raise TraceContractError("payload mapping required")
    _validate_payload(event["event_type"], event["payload"])


def _first_index(rows: list[Mapping[str, Any]], event_type: str) -> int | None:
    for idx, row in enumerate(rows):
        if row["event_type"] == event_type:
            return idx
    return None


def validate_trace(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(events)
    if not rows:
        raise TraceContractError("trace cannot be empty")

    run_id = None
    task_id = None
    prior_seq = 0
    prior_ns = -1
    type_counts: Counter[str] = Counter()

    for event in rows:
        validate_event(event)
        if run_id is None:
            run_id = event["run_id"]
            task_id = event["task_id"]
        elif event["run_id"] != run_id or event["task_id"] != task_id:
            raise TraceContractError("trace crossed run/task boundary")
        if event["seq"] != prior_seq + 1:
            raise TraceContractError("trace sequence gap or reorder")
        if event["monotonic_ns"] < prior_ns:
            raise TraceContractError("monotonic timestamp regressed")
        prior_seq = event["seq"]
        prior_ns = event["monotonic_ns"]
        type_counts[event["event_type"]] += 1

    missing = [typ for typ in BASE_REQUIRED_EVENT_TYPES if type_counts[typ] == 0]
    start_ok = rows[0]["event_type"] == "TASK_START" and type_counts["TASK_START"] == 1
    end_ok = rows[-1]["event_type"] == "TASK_END" and type_counts["TASK_END"] == 1

    order_errors: list[str] = []
    chain = [
        "TASK_START", "REPO_DISCOVERY_START", "REPO_DISCOVERY_END",
        "REPO_MODEL_REVISION", "FIRST_ACTIONABLE_HYPOTHESIS",
        "HYPOTHESIS_EVIDENCE", "DA_FINDING", "COUNTER_DA_FINDING",
    ]
    present_chain = [(typ, _first_index(rows, typ)) for typ in chain]
    for (left, li), (right, ri) in zip(present_chain, present_chain[1:]):
        if li is not None and ri is not None and li >= ri:
            order_errors.append(f"{left}_NOT_BEFORE_{right}")
    patch_idx = _first_index(rows, "PATCH_ATTEMPT")
    cda_idx = _first_index(rows, "COUNTER_DA_FINDING")
    if patch_idx is not None and cda_idx is not None and patch_idx <= cda_idx:
        order_errors.append("PATCH_BEFORE_COUNTER_DA")
    test_idx = _first_index(rows, "TEST_RESULT")
    if test_idx is not None and patch_idx is None:
        order_errors.append("TEST_WITHOUT_PATCH")
    elif test_idx is not None and patch_idx is not None and test_idx <= patch_idx:
        order_errors.append("TEST_BEFORE_PATCH")

    prior_patches_by_attempt: set[str] = set()
    for row in rows:
        if row["event_type"] == "PATCH_ATTEMPT":
            prior_patches_by_attempt.add(row["attempt_id"])
        elif row["event_type"] == "TEST_RESULT" and row["attempt_id"] not in prior_patches_by_attempt:
            order_errors.append(f"TEST_WITHOUT_PRIOR_PATCH_FOR_ATTEMPT:{row['attempt_id']}")

    declared = rows[-1]["payload"]["event_counts"] if end_ok else None
    count_mismatches: list[str] = []
    if declared is not None:
        for metric, event_type in COUNTED_EVENT_TYPES.items():
            actual = type_counts[event_type]
            if declared[metric] != actual:
                count_mismatches.append(f"{metric}:declared={declared[metric]} actual={actual}")

    complete = not missing and start_ok and end_ok and not order_errors and not count_mismatches
    return {
        "state": "TRACE_COMPLETE" if complete else "TRACE_INCOMPLETE",
        "complete": complete,
        "missing_event_types": missing,
        "task_start_first": start_ok,
        "task_end_last": end_ok,
        "event_count": len(rows),
        "event_type_counts": dict(sorted(type_counts.items())),
        "count_mismatches": count_mismatches,
        "order_errors": order_errors,
    }


def observer_overhead_pct(*, baseline_wall_ns: int, observed_wall_ns: int) -> float:
    if baseline_wall_ns <= 0 or observed_wall_ns < 0:
        raise TraceContractError("wall times invalid")
    raw = ((observed_wall_ns - baseline_wall_ns) / baseline_wall_ns) * 100.0
    return max(0.0, raw)


class TraceRecorder:
    """Thread-safe Stage 0 recorder used to test loss/reorder under burst load."""

    def __init__(self, *, run_id: str, task_id: str, sink: str | Path | None = None) -> None:
        self.run_id = _exact(run_id, "run_id")
        self.task_id = _exact(task_id, "task_id")
        self._lock = threading.Lock()
        self._seq = 0
        self._events: list[dict[str, Any]] = []
        self._bytes_written = 0
        self._write_wall_ns = 0
        self._sink = Path(sink) if sink is not None else None
        if self._sink is not None:
            self._sink.parent.mkdir(parents=True, exist_ok=True)
            self._sink.write_text("", encoding="utf-8")

    def emit(self, event_type: str, *, attempt_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        started = time.perf_counter_ns()
        with self._lock:
            self._seq += 1
            frozen_payload = json.loads(json.dumps(dict(payload), sort_keys=True, ensure_ascii=False))
            row = {
                "schema_version": TRACE_SCHEMA,
                "run_id": self.run_id,
                "task_id": self.task_id,
                "seq": self._seq,
                "monotonic_ns": time.monotonic_ns(),
                "event_type": event_type,
                "attempt_id": attempt_id,
                "payload": frozen_payload,
            }
            validate_event(row)
            self._events.append(row)
            if self._sink is not None:
                encoded = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
                with self._sink.open("a", encoding="utf-8") as handle:
                    handle.write(encoded)
                    handle.flush()
                self._bytes_written += len(encoded.encode("utf-8"))
            self._write_wall_ns += time.perf_counter_ns() - started
        return json.loads(json.dumps(row, sort_keys=True, ensure_ascii=False))

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return json.loads(json.dumps(self._events, sort_keys=True, ensure_ascii=False))

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "events_emitted": self._seq,
                "events_captured": len(self._events),
                "bytes_written": self._bytes_written,
                "write_wall_ns": self._write_wall_ns,
            }


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise TraceContractError("JSONL trace row must be object")
        rows.append(value)
    return rows
