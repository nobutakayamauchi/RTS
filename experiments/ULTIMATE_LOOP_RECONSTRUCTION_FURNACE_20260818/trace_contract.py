from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


TRACE_SCHEMA = "ultimate-loop-reconstruction-furnace/trace-v1"
REQUIRED_EVENT_TYPES = frozenset(
    {
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
    }
)


class TraceContractError(ValueError):
    pass


def _exact(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TraceContractError(f"{field} must be a non-empty exact string")
    return value


@dataclass(frozen=True)
class TraceEvent:
    schema_version: str
    run_id: str
    task_id: str
    seq: int
    monotonic_ns: int
    event_type: str
    attempt_id: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "seq": self.seq,
            "monotonic_ns": self.monotonic_ns,
            "event_type": self.event_type,
            "attempt_id": self.attempt_id,
            "payload": dict(self.payload),
        }


def event_fingerprint(event: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_event(event: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "run_id",
        "task_id",
        "seq",
        "monotonic_ns",
        "event_type",
        "attempt_id",
        "payload",
    }
    if not isinstance(event, Mapping) or set(event) != expected:
        raise TraceContractError("trace event shape drift")
    if event["schema_version"] != TRACE_SCHEMA:
        raise TraceContractError("trace schema mismatch")
    for field in ("run_id", "task_id", "event_type", "attempt_id"):
        _exact(event[field], field)
    if not isinstance(event["seq"], int) or event["seq"] < 1:
        raise TraceContractError("seq must be >= 1")
    if not isinstance(event["monotonic_ns"], int) or event["monotonic_ns"] < 0:
        raise TraceContractError("monotonic_ns must be >= 0")
    if not isinstance(event["payload"], Mapping):
        raise TraceContractError("payload mapping required")


def validate_trace(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(events)
    if not rows:
        raise TraceContractError("trace cannot be empty")

    run_id = None
    task_id = None
    prior_seq = 0
    prior_ns = -1
    seen_types: set[str] = set()
    duplicate_fingerprints: list[str] = []

    seen_fingerprints: set[str] = set()
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
        seen_types.add(event["event_type"])

        fp = event_fingerprint(event)
        if fp in seen_fingerprints:
            duplicate_fingerprints.append(fp)
        seen_fingerprints.add(fp)

    missing = sorted(REQUIRED_EVENT_TYPES - seen_types)
    start_ok = rows[0]["event_type"] == "TASK_START"
    end_ok = rows[-1]["event_type"] == "TASK_END"
    complete = not missing and start_ok and end_ok

    return {
        "state": "TRACE_COMPLETE" if complete else "TRACE_INCOMPLETE",
        "complete": complete,
        "missing_event_types": missing,
        "task_start_first": start_ok,
        "task_end_last": end_ok,
        "event_count": len(rows),
        "duplicate_event_fingerprints": duplicate_fingerprints,
    }


def observer_overhead_pct(*, baseline_wall_ns: int, observed_wall_ns: int) -> float:
    if baseline_wall_ns <= 0 or observed_wall_ns < 0:
        raise TraceContractError("wall times invalid")
    return ((observed_wall_ns - baseline_wall_ns) / baseline_wall_ns) * 100.0
