#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import math
from statistics import median
from typing import Iterable, Mapping


class StateModelError(ValueError):
    pass


BEHAVIOR_FEATURES = ("typo_rate", "correction_rate", "loop_rate", "reversal_rate")
NONURGENT_STATUS_WEIGHTS = {
    "headache": 3.0,
    "nausea": 3.0,
    "dizziness": 3.0,
    "weakness": 3.0,
    "feverish": 3.0,
    "pain": 2.0,
    "illness": 3.0,
    "sleep_debt": 3.0,
}


def _finite(value: float, field: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise StateModelError(f"{field} must be finite")
    return value


def _range(value: float, low: float, high: float, field: str) -> float:
    value = _finite(value, field)
    if value < low or value > high:
        raise StateModelError(f"{field} must be in [{low}, {high}]")
    return value


def _optional_range(value: float | None, low: float, high: float, field: str) -> float | None:
    if value is None:
        return None
    return _range(value, low, high, field)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class BehaviorMetrics:
    characters: int | None = None
    typo_count: int | None = None
    correction_count: int | None = None
    message_count: int | None = None
    loop_count: int | None = None
    reversal_count: int | None = None

    def features(self) -> dict[str, float]:
        values: dict[str, float] = {}
        if self.characters is not None:
            if self.characters <= 0:
                raise StateModelError("characters must be positive when present")
            if self.typo_count is not None:
                if self.typo_count < 0:
                    raise StateModelError("typo_count must be nonnegative")
                values["typo_rate"] = self.typo_count / self.characters
            if self.correction_count is not None:
                if self.correction_count < 0:
                    raise StateModelError("correction_count must be nonnegative")
                values["correction_rate"] = self.correction_count / self.characters
        if self.message_count is not None:
            if self.message_count <= 0:
                raise StateModelError("message_count must be positive when present")
            if self.loop_count is not None:
                if self.loop_count < 0:
                    raise StateModelError("loop_count must be nonnegative")
                values["loop_rate"] = self.loop_count / self.message_count
            if self.reversal_count is not None:
                if self.reversal_count < 0:
                    raise StateModelError("reversal_count must be nonnegative")
                values["reversal_rate"] = self.reversal_count / self.message_count
        return values


@dataclass(frozen=True)
class OperatorStateInput:
    sleep_hours_24h: float | None = None
    subjective_fatigue_0_10: float | None = None
    subjective_recovery_0_10: float | None = None
    bad_status: tuple[str, ...] = ()
    bad_status_assessed: bool = False
    recovery_events: tuple[str, ...] = ()
    behavior: BehaviorMetrics | None = None
    behavior_baseline: Mapping[str, Iterable[float]] = field(default_factory=dict)
    workload_pressure_0_1: float | None = None


@dataclass(frozen=True)
class FatigueEstimate:
    operational_fatigue_100: float
    band: str
    confidence: str
    evidence_coverage: float
    components: dict[str, float | None]
    behavior_z: dict[str, float | None]
    notes: tuple[str, ...]


def robust_z(value: float, history: Iterable[float], *, min_samples: int = 5) -> float | None:
    samples = [_finite(v, "baseline sample") for v in history]
    if len(samples) < min_samples:
        return None
    center = median(samples)
    deviations = [abs(v - center) for v in samples]
    mad = median(deviations)
    if mad <= 0:
        return None
    return 0.67448975 * (value - center) / mad


def behavior_anomaly(
    behavior: BehaviorMetrics | None,
    baseline: Mapping[str, Iterable[float]],
) -> tuple[float | None, dict[str, float | None]]:
    if behavior is None:
        return None, {key: None for key in BEHAVIOR_FEATURES}
    current = behavior.features()
    zscores: dict[str, float | None] = {}
    positive: list[float] = []
    for key in BEHAVIOR_FEATURES:
        if key not in current:
            zscores[key] = None
            continue
        z = robust_z(current[key], baseline.get(key, ()))
        zscores[key] = None if z is None else round(z, 4)
        if z is not None and z > 0:
            positive.append(min(4.0, z))
    if not positive:
        calibrated = any(v is not None for v in zscores.values())
        return (0.0 if calibrated else None), zscores
    return (sum(positive) / len(positive)) / 4.0, zscores


def estimate_fatigue(state: OperatorStateInput) -> FatigueEstimate:
    """Operational fatigue heuristic, not a medical diagnosis.

    Population evidence supplies only weak priors. Personal longitudinal calibration is required
    before behavioral features contribute. `bad_status_assessed` distinguishes confirmed-none from
    not-yet-asked, so evidence coverage cannot rise merely because an empty tuple is the default.
    """
    sleep = _optional_range(state.sleep_hours_24h, 0.0, 24.0, "sleep_hours_24h")
    subjective = _optional_range(
        state.subjective_fatigue_0_10, 0.0, 10.0, "subjective_fatigue_0_10"
    )
    recovery = _optional_range(
        state.subjective_recovery_0_10, 0.0, 10.0, "subjective_recovery_0_10"
    )
    workload = _optional_range(
        state.workload_pressure_0_1, 0.0, 1.0, "workload_pressure_0_1"
    )

    components: dict[str, float | None] = {
        "sleep_shortfall": None,
        "subjective_fatigue": None,
        "bad_status": None,
        "behavior_anomaly": None,
        "workload_pressure": None,
        "recovery_credit": None,
    }
    observed_weight = 0.0
    possible_weight = 115.0
    burden = 0.0
    notes: list[str] = []

    if sleep is not None:
        # MHLW adult guidance uses >=6 h as a rough target, with explicit individual differences.
        shortfall = max(0.0, 6.0 - sleep) / 6.0
        components["sleep_shortfall"] = round(25.0 * shortfall, 3)
        burden += 25.0 * shortfall
        observed_weight += 25.0
        if sleep < 6.0:
            notes.append("sleep_below_6h_rough_target")

    if subjective is not None:
        components["subjective_fatigue"] = round(25.0 * subjective / 10.0, 3)
        burden += 25.0 * subjective / 10.0
        observed_weight += 25.0

    normalized_status = tuple(str(tag).strip().lower() for tag in state.bad_status if str(tag).strip())
    recognized_status = tuple(tag for tag in normalized_status if tag in NONURGENT_STATUS_WEIGHTS)
    if state.bad_status_assessed or normalized_status:
        status_score = min(15.0, sum(NONURGENT_STATUS_WEIGHTS[tag] for tag in recognized_status))
        components["bad_status"] = round(status_score, 3)
        burden += status_score
        observed_weight += 15.0
        if normalized_status and not recognized_status:
            notes.append("reported_status_not_in_fatigue_prior")
    else:
        notes.append("bad_status_unassessed")

    anomaly, zscores = behavior_anomaly(state.behavior, state.behavior_baseline)
    if anomaly is not None:
        components["behavior_anomaly"] = round(20.0 * anomaly, 3)
        burden += 20.0 * anomaly
        observed_weight += 20.0
        if anomaly >= 0.5:
            notes.append("behavior_above_personal_baseline")
    else:
        notes.append("behavior_uncalibrated")

    if workload is not None:
        components["workload_pressure"] = round(15.0 * workload, 3)
        burden += 15.0 * workload
        observed_weight += 15.0

    credit = 0.0
    if recovery is not None:
        credit = 15.0 * recovery / 10.0
        components["recovery_credit"] = round(credit, 3)
        observed_weight += 15.0
    elif state.recovery_events:
        # Events are logged but do not receive assumed physiological credit without a reported effect.
        notes.append("recovery_event_logged_effect_unmeasured")

    score = _clamp(burden - credit)
    coverage = min(1.0, observed_weight / possible_weight)
    confidence = "MEDIUM" if coverage >= 0.75 else "LOW"
    if score < 35:
        band = "GREEN"
    elif score < 65:
        band = "AMBER"
    else:
        band = "RED"

    return FatigueEstimate(
        operational_fatigue_100=round(score, 1),
        band=band,
        confidence=confidence,
        evidence_coverage=round(coverage, 3),
        components=components,
        behavior_z=zscores,
        notes=tuple(notes),
    )
