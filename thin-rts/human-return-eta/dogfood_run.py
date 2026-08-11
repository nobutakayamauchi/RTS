"""Dogfood record contract for Human Return ETA + Decision Sentinel.

The contract separates:
- decision/launch time,
- predicted return time,
- first machine/human-required time,
- observed human return time,
- later revision outcome.

This prevents the ETA from learning operator overshoot as if it were machine readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from decision_sentinel import DecisionState, review_pressure, classify_revision_outcome


class DogfoodRunError(ValueError):
    pass


def _parse_time(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise DogfoodRunError(f"{field} must be a non-empty ISO-8601 string")
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise DogfoodRunError(f"invalid {field}: {value!r}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise DogfoodRunError(f"{field} must be timezone-aware")
    return dt


def _positive(value: float, field: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise DogfoodRunError(f"{field} must be a positive finite number")
    return value


@dataclass(frozen=True)
class LaunchSnapshot:
    task_class: str
    decision_hinge_at: str
    predicted_return_minutes: float
    decision_state: DecisionState
    known_governed_stages: float = 0.0


def start_record(snapshot: LaunchSnapshot) -> dict[str, object]:
    if not isinstance(snapshot.task_class, str) or not snapshot.task_class.strip():
        raise DogfoodRunError("task_class must be non-empty")
    hinge = _parse_time(snapshot.decision_hinge_at, "decision_hinge_at")
    predicted = _positive(snapshot.predicted_return_minutes, "predicted_return_minutes")
    stages = float(snapshot.known_governed_stages)
    if not math.isfinite(stages) or stages < 0:
        raise DogfoodRunError("known_governed_stages must be finite and nonnegative")
    sentinel = review_pressure(snapshot.decision_state)
    return {
        "schema": "thin-rts-human-return-dogfood/v0.1",
        "task_class": snapshot.task_class.strip(),
        "decision_hinge_at": hinge.isoformat(),
        "launch": {
            "predicted_return_minutes": predicted,
            "known_governed_stages": stages,
            "decision_severity": snapshot.decision_state.severity,
            "evidence_quality": snapshot.decision_state.evidence_quality,
            "axis_coverage": snapshot.decision_state.axis_coverage,
            "recent_revision_load": snapshot.decision_state.recent_revision_load,
            "recent_context_switch_load": snapshot.decision_state.recent_context_switch_load,
            "unresolved_counterevidence": snapshot.decision_state.unresolved_counterevidence,
            "irreversible": snapshot.decision_state.irreversible,
        },
        "sentinel": sentinel,
        "outcome": None,
    }


def complete_record(
    record: dict[str, object],
    *,
    human_required_at: str,
    terminal: str,
    observed_human_return_at: str | None = None,
    revision_outcome: str = "UNKNOWN",
) -> dict[str, object]:
    if record.get("schema") != "thin-rts-human-return-dogfood/v0.1":
        raise DogfoodRunError("unsupported dogfood record schema")
    if record.get("outcome") is not None:
        raise DogfoodRunError("dogfood record is already completed")
    hinge = _parse_time(str(record.get("decision_hinge_at")), "decision_hinge_at")
    required = _parse_time(human_required_at, "human_required_at")
    if required <= hinge:
        raise DogfoodRunError("human_required_at must be after decision_hinge_at")

    launch = record.get("launch")
    if not isinstance(launch, dict):
        raise DogfoodRunError("launch section is missing")
    predicted = _positive(float(launch.get("predicted_return_minutes", 0)), "predicted_return_minutes")
    target_minutes = (required - hinge).total_seconds() / 60.0
    prediction_delta = predicted - target_minutes

    observed_return = None
    observed_delta = None
    if observed_human_return_at is not None:
        observed_return = _parse_time(observed_human_return_at, "observed_human_return_at")
        if observed_return <= hinge:
            raise DogfoodRunError("observed_human_return_at must be after decision_hinge_at")
        observed_delta = (observed_return - required).total_seconds() / 60.0

    terminal_value = str(terminal).strip().upper()
    if not terminal_value:
        raise DogfoodRunError("terminal must be non-empty")

    result = dict(record)
    result["outcome"] = {
        "human_required_at": required.isoformat(),
        "observed_human_return_at": None if observed_return is None else observed_return.isoformat(),
        "terminal": terminal_value,
        "revision_outcome": str(revision_outcome).strip().upper(),
        "revision_label_semantics": classify_revision_outcome(revision_outcome),
        "target_return_minutes": round(target_minutes, 6),
        "prediction_delta_minutes": round(prediction_delta, 6),
        "early_return_prediction_waste_minutes": round(max(0.0, -prediction_delta), 6),
        "late_return_prediction_waste_minutes": round(max(0.0, prediction_delta), 6),
        "observed_human_delta_from_required_minutes": (
            None if observed_delta is None else round(observed_delta, 6)
        ),
    }
    return result


def eta_training_record(record: dict[str, object], *, evidence_strength: str = "STRONG") -> dict[str, object]:
    """Convert a completed dogfood run into the existing ETA observation contract.

    The ETA target uses human_required_at, not observed_human_return_at.
    """
    outcome = record.get("outcome")
    if not isinstance(outcome, dict):
        raise DogfoodRunError("dogfood record must be completed first")
    return {
        "task_class": record["task_class"],
        "started_at": record["decision_hinge_at"],
        "human_hinge_at": outcome["human_required_at"],
        "terminal": outcome["terminal"],
        "evidence_strength": str(evidence_strength).strip().upper(),
        "source": "dogfood-human-required-v0.1",
    }
