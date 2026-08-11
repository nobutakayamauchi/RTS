#!/usr/bin/env python3
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

SESSION_GAP_MINUTES = 30.0
CONTINUOUS_UNIT_MINUTES = 15.0
OLT_AXES = ("E", "J", "O", "R", "X")

OLT_SCALES = {
    "E": 20.0,
    "J": 8.0,
    "O": 10.0,
    "R": 5.0,
    "X": 4.0,
}

OLT_DISPLAY_WEIGHTS = {
    "E": 0.30,
    "J": 0.35,
    "O": 0.20,
    "R": 0.10,
    "X": 0.05,
}


class OLTError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoadVector:
    E: float
    J: float
    O: float
    R: float
    X: float

    def as_dict(self) -> dict[str, float]:
        return {"E": self.E, "J": self.J, "O": self.O, "R": self.R, "X": self.X}


@dataclass(frozen=True)
class PartialLoadVector:
    """Evidence-bounded OLT vector. None means unobserved, never zero."""

    E: float | None = None
    J: float | None = None
    O: float | None = None
    R: float | None = None
    X: float | None = None

    def as_dict(self) -> dict[str, float | None]:
        return {"E": self.E, "J": self.J, "O": self.O, "R": self.R, "X": self.X}


def _nonnegative_finite(value: float, field: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise OLTError(f"{field} must be a non-negative finite number")
    return value


def activity_load(human_events: int, human_adjacent_gaps_minutes: Iterable[float]) -> float:
    if human_events < 0:
        raise OLTError("human_events must be non-negative")
    continuous = 0.0
    for gap in human_adjacent_gaps_minutes:
        gap = _nonnegative_finite(gap, "gap_minutes")
        if 0 < gap < SESSION_GAP_MINUTES:
            continuous += gap
    return float(human_events) + continuous / CONTINUOUS_UNIT_MINUTES


def decision_load(decision_weights: Iterable[int]) -> float:
    total = 0.0
    for weight in decision_weights:
        if weight not in (1, 2, 3):
            raise OLTError("decision weights must be D1=1, D2=2, or D3=3")
        total += weight
    return total


def orchestration_load(governed_stages: int, governed_elapsed_minutes: float) -> float:
    if governed_stages < 0:
        raise OLTError("governed_stages must be non-negative")
    elapsed = _nonnegative_finite(governed_elapsed_minutes, "governed_elapsed_minutes")
    return float(governed_stages) + elapsed / CONTINUOUS_UNIT_MINUTES


def revision_load(revision_weights: Iterable[int]) -> float:
    total = 0.0
    for weight in revision_weights:
        if weight not in (1, 2, 3):
            raise OLTError("revision weights must be 1, 2, or 3")
        total += weight
    return total


def context_switch_load(projects: Sequence[str], gaps_minutes: Sequence[float]) -> float:
    if len(projects) <= 1:
        return 0.0
    if len(gaps_minutes) != len(projects) - 1:
        raise OLTError("gaps_minutes must have exactly len(projects)-1 items")
    switches = 0
    for previous, current, gap in zip(projects, projects[1:], gaps_minutes):
        gap = _nonnegative_finite(gap, "gap_minutes")
        if previous != current and gap < SESSION_GAP_MINUTES:
            switches += 1
    return float(switches)


def data_quality(human: int, auto: int, unknown: int) -> float:
    if min(human, auto, unknown) < 0:
        raise OLTError("actor counts must be non-negative")
    total = human + auto + unknown
    if total == 0:
        raise OLTError("data quality is undefined for an empty actor set")
    return (human + auto) / total


def automation_rate(human: int, auto: int) -> float:
    if min(human, auto) < 0:
        raise OLTError("actor counts must be non-negative")
    classified = human + auto
    if classified == 0:
        raise OLTError("automation rate is undefined without classified events")
    return auto / classified


def saturation(value: float, scale: float) -> float:
    value = _nonnegative_finite(value, "value")
    scale = float(scale)
    if not math.isfinite(scale) or scale <= 0:
        raise OLTError("scale must be a positive finite number")
    return 1.0 - math.exp(-value / scale)


def display_score(vector: LoadVector) -> float:
    values = vector.as_dict()
    score = 0.0
    for key in OLT_AXES:
        value = _nonnegative_finite(values[key], key)
        score += OLT_DISPLAY_WEIGHTS[key] * saturation(value, OLT_SCALES[key])
    return 100.0 * score


def axis_coverage(vector: PartialLoadVector | Mapping[str, float | None]) -> float:
    values = vector.as_dict() if isinstance(vector, PartialLoadVector) else dict(vector)
    unknown_keys = set(values) - set(OLT_AXES)
    if unknown_keys:
        raise OLTError(f"unknown OLT axes: {sorted(unknown_keys)}")
    observed = 0
    for key in OLT_AXES:
        value = values.get(key)
        if value is None:
            continue
        _nonnegative_finite(value, key)
        observed += 1
    return observed / len(OLT_AXES)


def lower_bound_score(vector: PartialLoadVector | Mapping[str, float | None]) -> float:
    """Score only observed axes; omitted axes remain semantically UNKNOWN, not zero."""
    values = vector.as_dict() if isinstance(vector, PartialLoadVector) else dict(vector)
    unknown_keys = set(values) - set(OLT_AXES)
    if unknown_keys:
        raise OLTError(f"unknown OLT axes: {sorted(unknown_keys)}")
    score = 0.0
    for key in OLT_AXES:
        value = values.get(key)
        if value is None:
            continue
        clean = _nonnegative_finite(value, key)
        score += OLT_DISPLAY_WEIGHTS[key] * saturation(clean, OLT_SCALES[key])
    return 100.0 * score


def amplification_ratio(machine_visible_output: float, governed_stages: int) -> float:
    """Machine-visible output per governed human stage; not a human-effort measure."""
    output = _nonnegative_finite(machine_visible_output, "machine_visible_output")
    if governed_stages <= 0:
        raise OLTError("governed_stages must be positive for amplification ratio")
    return output / governed_stages


def judgment_pressure_ratio(J: float, R: float, O: float) -> float:
    """(J + R) / O. Descriptive workload-shape ratio, not a fatigue score."""
    decision = _nonnegative_finite(J, "J")
    rework = _nonnegative_finite(R, "R")
    orchestration = _nonnegative_finite(O, "O")
    if orchestration <= 0:
        raise OLTError("O must be positive for judgment pressure ratio")
    return (decision + rework) / orchestration


def normalized_vector(vector: LoadVector) -> tuple[float, float, float, float, float]:
    values = vector.as_dict()
    return tuple(values[key] / OLT_SCALES[key] for key in OLT_AXES)


def vector_distance(a: LoadVector, b: LoadVector) -> float:
    """Normalized L1 distance for ETA similarity; deliberately does not use OLT_100."""
    av = normalized_vector(a)
    bv = normalized_vector(b)
    return sum(abs(x - y) for x, y in zip(av, bv))


def work_share(project_E: dict[str, float]) -> dict[str, float]:
    return _share(project_E)


def decision_share(project_J: dict[str, float]) -> dict[str, float]:
    return _share(project_J)


def orchestration_share(project_O: dict[str, float]) -> dict[str, float]:
    return _share(project_O)


def _share(values: dict[str, float]) -> dict[str, float]:
    clean = {k: _nonnegative_finite(v, k) for k, v in values.items()}
    total = sum(clean.values())
    if total <= 0:
        raise OLTError("share is undefined when the total load is zero")
    return {k: v / total for k, v in clean.items()}
