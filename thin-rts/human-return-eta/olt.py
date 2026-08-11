#!/usr/bin/env python3
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

SESSION_GAP_MINUTES = 30.0
CONTINUOUS_UNIT_MINUTES = 15.0

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
    for key in ("E", "J", "O", "R", "X"):
        value = _nonnegative_finite(values[key], key)
        score += OLT_DISPLAY_WEIGHTS[key] * saturation(value, OLT_SCALES[key])
    return 100.0 * score


def normalized_vector(vector: LoadVector) -> tuple[float, float, float, float, float]:
    values = vector.as_dict()
    return tuple(values[key] / OLT_SCALES[key] for key in ("E", "J", "O", "R", "X"))


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
