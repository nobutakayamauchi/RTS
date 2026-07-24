from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    CHECKPOINT_SCHEMA_VERSION,
    EVENT_SCHEMA_VERSION,
    TERMINAL_STATES,
    ControllerError,
    canonical_json,
    expect_digest,
    expect_exact_object,
    expect_nonempty_string,
    expect_safe_id,
    load_json,
    pretty_json,
    sha256_value,
    validate_transition,
    validate_usage,
)

GENESIS_HASH = "0" * 64
EVENT_FIELDS = {
    "schema_version",
    "sequence",
    "event_id",
    "previous_event_hash",
    "event_hash",
    "event_type",
    "state_before",
    "state_after",
    "attempt",
    "usage",
    "timestamp",
    "summary",
}
CHECKPOINT_FIELDS = {
    "schema_version",
    "run_id",
    "plan_id",
    "plan_fingerprint",
    "authorization_fingerprint",
    "latest_sequence",
    "latest_event_hash",
    "state",
    "attempt",
    "usage",
}


def _run_dir(state_dir: Path, run_id: str) -> Path:
    expect_safe_id(run_id, "run_id")
    base = state_dir.resolve()
    target = (base / run_id).resolve()
    if target.parent != base:
        raise ControllerError("run path escaped state_dir")
    return target


def event_path(state_dir: Path, run_id: str) -> Path:
    return _run_dir(state_dir, run_id) / "events.jsonl"


def checkpoint_path(state_dir: Path, run_id: str) -> Path:
    return _run_dir(state_dir, run_id) / "checkpoint.json"


def read_events(state_dir: Path, run_id: str) -> list[dict[str, Any]]:
    path = event_path(state_dir, run_id)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ControllerError(f"blank event line at {line_number}")
        import json
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ControllerError(f"invalid event JSON at line {line_number}: {exc}") from exc
        rows.append(value)
    return rows


def _event_material(event: dict[str, Any]) -> dict[str, Any]:
    material = dict(event)
    material.pop("event_hash", None)
    material.pop("event_id", None)
    return material


def validate_event(event: Any, previous: dict[str, Any] | None) -> dict[str, Any]:
    event = expect_exact_object(event, EVENT_FIELDS, "event")
    if event["schema_version"] != EVENT_SCHEMA_VERSION:
        raise ControllerError("event schema_version mismatch")
    if isinstance(event["sequence"], bool) or not isinstance(event["sequence"], int) or event["sequence"] < 1:
        raise ControllerError("event.sequence must be a positive integer")
    expected_sequence = 1 if previous is None else previous["sequence"] + 1
    if event["sequence"] != expected_sequence:
        raise ControllerError("event sequence mismatch")
    expected_previous = GENESIS_HASH if previous is None else previous["event_hash"]
    if event["previous_event_hash"] != expected_previous:
        raise ControllerError("event previous hash mismatch")
    expect_digest(event["event_hash"], "event.event_hash")
    expect_digest(event["event_id"], "event.event_id")
    if event["state_before"] == event["state_after"]:
        if event["state_before"] != "RUNNING" or event["event_type"] != "RETRYABLE_FAILURE":
            raise ControllerError("same-state event is allowed only for retryable failure")
    else:
        validate_transition(event["state_before"], event["state_after"])
    if isinstance(event["attempt"], bool) or not isinstance(event["attempt"], int) or event["attempt"] < 0:
        raise ControllerError("event.attempt must be a non-negative integer")
    validate_usage(event["usage"], "event.usage")
    expect_nonempty_string(event["event_type"], "event.event_type")
    expect_nonempty_string(event["timestamp"], "event.timestamp")
    expect_nonempty_string(event["summary"], "event.summary")
    material = _event_material(event)
    expected_hash = sha256_value(material)
    if event["event_hash"] != expected_hash:
        raise ControllerError("event hash mismatch")
    expected_id = sha256_value({"event_hash": event["event_hash"], "sequence": event["sequence"]})
    if event["event_id"] != expected_id:
        raise ControllerError("event ID mismatch")
    if previous is not None:
        previous_usage = validate_usage(previous["usage"], "previous event.usage")
        for field, number in event["usage"].items():
            if number < previous_usage[field]:
                raise ControllerError(f"event usage decreased: {field}")
    return event


def verify_chain(state_dir: Path, run_id: str) -> list[dict[str, Any]]:
    rows = read_events(state_dir, run_id)
    previous = None
    for row in rows:
        validate_event(row, previous)
        previous = row
    return rows


def load_checkpoint(state_dir: Path, run_id: str) -> dict[str, Any]:
    checkpoint = expect_exact_object(load_json(checkpoint_path(state_dir, run_id)), CHECKPOINT_FIELDS, "checkpoint")
    if checkpoint["schema_version"] != CHECKPOINT_SCHEMA_VERSION:
        raise ControllerError("checkpoint schema_version mismatch")
    if checkpoint["run_id"] != run_id:
        raise ControllerError("checkpoint run_id mismatch")
    for field in ("plan_id", "plan_fingerprint", "authorization_fingerprint", "latest_event_hash"):
        expect_digest(checkpoint[field], f"checkpoint.{field}")
    if isinstance(checkpoint["latest_sequence"], bool) or not isinstance(checkpoint["latest_sequence"], int) or checkpoint["latest_sequence"] < 1:
        raise ControllerError("checkpoint.latest_sequence must be positive")
    if isinstance(checkpoint["attempt"], bool) or not isinstance(checkpoint["attempt"], int) or checkpoint["attempt"] < 0:
        raise ControllerError("checkpoint.attempt must be non-negative")
    validate_usage(checkpoint["usage"], "checkpoint.usage")
    return checkpoint


def verify_checkpoint(state_dir: Path, run_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = verify_chain(state_dir, run_id)
    if not rows:
        raise ControllerError("run has no events")
    checkpoint = load_checkpoint(state_dir, run_id)
    latest = rows[-1]
    expected = {
        "latest_sequence": latest["sequence"],
        "latest_event_hash": latest["event_hash"],
        "state": latest["state_after"],
        "attempt": latest["attempt"],
        "usage": latest["usage"],
    }
    for field, value in expected.items():
        if checkpoint[field] != value:
            raise ControllerError(f"checkpoint disagrees with event log: {field}")
    return rows, checkpoint


def append_event(
    state_dir: Path,
    run_id: str,
    *,
    plan_id: str,
    authorization_fingerprint: str,
    event_type: str,
    state_before: str,
    state_after: str,
    attempt: int,
    usage: dict[str, int],
    timestamp: str,
    summary: str,
) -> dict[str, Any]:
    run_dir = _run_dir(state_dir, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = verify_chain(state_dir, run_id)
    if rows:
        verify_checkpoint(state_dir, run_id)
    previous = rows[-1] if rows else None
    if previous and previous["state_after"] in TERMINAL_STATES:
        raise ControllerError("terminal run is immutable")
    sequence = 1 if previous is None else previous["sequence"] + 1
    event = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "sequence": sequence,
        "event_id": "0" * 64,
        "previous_event_hash": GENESIS_HASH if previous is None else previous["event_hash"],
        "event_hash": "0" * 64,
        "event_type": event_type,
        "state_before": state_before,
        "state_after": state_after,
        "attempt": attempt,
        "usage": validate_usage(usage),
        "timestamp": timestamp,
        "summary": summary,
    }
    event["event_hash"] = sha256_value(_event_material(event))
    event["event_id"] = sha256_value({"event_hash": event["event_hash"], "sequence": sequence})
    validate_event(event, previous)
    with event_path(state_dir, run_id).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(event) + "\n")
    checkpoint = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "run_id": run_id,
        "plan_id": plan_id,
        "plan_fingerprint": plan_id,
        "authorization_fingerprint": authorization_fingerprint,
        "latest_sequence": sequence,
        "latest_event_hash": event["event_hash"],
        "state": state_after,
        "attempt": attempt,
        "usage": event["usage"],
    }
    checkpoint_path(state_dir, run_id).write_text(pretty_json(checkpoint), encoding="utf-8")
    verify_checkpoint(state_dir, run_id)
    return event
