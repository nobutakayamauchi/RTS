#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Iterable

import olt

ACTOR_CLASSES = {"HUMAN", "AUTO", "UNKNOWN"}
BURST_GAP_MINUTES = 10.0


class OLTIngestError(RuntimeError):
    pass


@dataclass(frozen=True)
class Event:
    timestamp: datetime
    project: str
    actor_class: str
    event_type: str
    evidence_ref: str
    decision_severity: int | None = None
    rework_severity: int | None = None
    governed_stage_id: str | None = None
    gate_elapsed_min: float | None = None


@dataclass(frozen=True)
class WindowAggregate:
    load: olt.LoadVector
    human_events: int
    auto_events: int
    unknown_events: int
    resolved_coverage: float
    automation_ratio: float | None
    active_minutes: float
    sessions: int
    bursts: int
    governed_stages: int
    gate_minutes: float


def _parse_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        try:
            dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise OLTIngestError(f"invalid timestamp: {value!r}") from exc
    else:
        raise OLTIngestError("timestamp must be timezone-aware ISO-8601 or datetime")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise OLTIngestError("timestamp must be timezone-aware")
    return dt


def _severity(value: object, field: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise OLTIngestError(f"{field} must be 1, 2, or 3")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise OLTIngestError(f"{field} must be 1, 2, or 3") from exc
    if number not in (1, 2, 3):
        raise OLTIngestError(f"{field} must be 1, 2, or 3")
    return number


def _nonnegative_optional(value: object, field: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise OLTIngestError(f"{field} must be a non-negative finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise OLTIngestError(f"{field} must be a non-negative finite number") from exc
    if not math.isfinite(number) or number < 0:
        raise OLTIngestError(f"{field} must be a non-negative finite number")
    return number


def normalize_event(record: object) -> Event:
    if not isinstance(record, dict):
        raise OLTIngestError("event record must be an object")

    project = str(record.get("project", "")).strip()
    actor = str(record.get("actor_class", "")).strip().upper()
    event_type = str(record.get("event_type", "")).strip().lower()
    evidence_ref = str(record.get("evidence_ref", "")).strip()
    if not project:
        raise OLTIngestError("project is required")
    if actor not in ACTOR_CLASSES:
        raise OLTIngestError("actor_class must be HUMAN, AUTO, or UNKNOWN")
    if not event_type:
        raise OLTIngestError("event_type is required")
    if not evidence_ref:
        raise OLTIngestError("evidence_ref is required")

    decision = _severity(record.get("decision_severity"), "decision_severity")
    rework = _severity(record.get("rework_severity"), "rework_severity")
    stage_id_raw = record.get("governed_stage_id")
    stage_id = None if stage_id_raw is None else str(stage_id_raw).strip() or None
    gate = _nonnegative_optional(record.get("gate_elapsed_min"), "gate_elapsed_min")

    # Semantic loads must not be manufactured from AUTO/UNKNOWN rows.
    if actor != "HUMAN" and (decision is not None or rework is not None):
        raise OLTIngestError("decision/rework severity requires HUMAN evidence")
    if gate is not None and stage_id is None:
        raise OLTIngestError("gate_elapsed_min requires governed_stage_id")

    return Event(
        timestamp=_parse_timestamp(record.get("timestamp")),
        project=project,
        actor_class=actor,
        event_type=event_type,
        evidence_ref=evidence_ref,
        decision_severity=decision,
        rework_severity=rework,
        governed_stage_id=stage_id,
        gate_elapsed_min=gate,
    )


def _gaps_minutes(events: list[Event]) -> list[float]:
    gaps: list[float] = []
    for previous, current in zip(events, events[1:]):
        minutes = (current.timestamp - previous.timestamp).total_seconds() / 60.0
        if minutes <= 0:
            raise OLTIngestError("event timestamps must be strictly increasing after deduplication")
        gaps.append(minutes)
    return gaps


def _session_and_burst_counts(human_events: list[Event]) -> tuple[int, int]:
    if not human_events:
        return 0, 0
    sessions = 1
    bursts = 1
    for gap in _gaps_minutes(human_events):
        if gap >= olt.SESSION_GAP_MINUTES:
            sessions += 1
            bursts += 1
        elif gap >= BURST_GAP_MINUTES:
            bursts += 1
    return sessions, bursts


def aggregate_window(events: Iterable[Event]) -> WindowAggregate:
    rows = sorted(list(events), key=lambda event: event.timestamp)
    if not rows:
        raise OLTIngestError("window requires at least one event")

    # Exact duplicate source rows collapse; conflicting same-time rows remain visible
    # and fail later rather than being silently rewritten.
    deduped: list[Event] = []
    seen: set[Event] = set()
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        deduped.append(row)
    rows = deduped

    human = [row for row in rows if row.actor_class == "HUMAN"]
    auto_count = sum(row.actor_class == "AUTO" for row in rows)
    unknown_count = sum(row.actor_class == "UNKNOWN" for row in rows)

    human_gaps = _gaps_minutes(human) if len(human) >= 2 else []
    eligible_active = [gap for gap in human_gaps if gap < olt.SESSION_GAP_MINUTES]
    E = olt.activity_load(len(human), eligible_active)
    active_minutes = sum(eligible_active)
    sessions, bursts = _session_and_burst_counts(human)

    J = olt.decision_load(
        row.decision_severity for row in human if row.decision_severity is not None
    )
    R = olt.revision_load(
        row.rework_severity for row in human if row.rework_severity is not None
    )

    # Each governed stage is counted once. Gate elapsed is accepted once per stage;
    # conflicting duplicate values fail closed so overlaps/pre-aggregation are not hidden.
    stage_gate: dict[str, float | None] = {}
    for row in rows:
        if row.governed_stage_id is None:
            continue
        previous = stage_gate.get(row.governed_stage_id)
        if row.governed_stage_id not in stage_gate:
            stage_gate[row.governed_stage_id] = row.gate_elapsed_min
        elif row.gate_elapsed_min is not None:
            if previous is None:
                stage_gate[row.governed_stage_id] = row.gate_elapsed_min
            elif not math.isclose(previous, row.gate_elapsed_min, rel_tol=0.0, abs_tol=1e-9):
                raise OLTIngestError(
                    f"conflicting gate_elapsed_min for governed stage {row.governed_stage_id!r}"
                )
    gate_minutes = sum(value or 0.0 for value in stage_gate.values())
    O = olt.orchestration_load(len(stage_gate), gate_minutes)

    # Context switching is an operator load, so AUTO/UNKNOWN output does not create
    # human switches by itself.
    X = 0.0
    if len(human) >= 2:
        X = olt.context_switch_load(
            [row.project for row in human],
            human_gaps,
        )

    resolved = olt.data_quality(len(human), auto_count, unknown_count)
    classified = len(human) + auto_count
    automation = None if classified == 0 else olt.automation_rate(len(human), auto_count)

    return WindowAggregate(
        load=olt.LoadVector(E=E, J=J, O=O, R=R, X=X),
        human_events=len(human),
        auto_events=auto_count,
        unknown_events=unknown_count,
        resolved_coverage=resolved,
        automation_ratio=automation,
        active_minutes=active_minutes,
        sessions=sessions,
        bursts=bursts,
        governed_stages=len(stage_gate),
        gate_minutes=gate_minutes,
    )
