#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from statistics import median
from typing import Iterable, Mapping


class VitalsModelError(ValueError):
    pass


# These are deliberately broad measurement-sanity bounds, not clinical normal/abnormal thresholds.
MEASUREMENT_SANITY_BOUNDS = {
    "heart_rate_bpm": (1.0, 400.0),
    "temperature_c": (20.0, 50.0),
    "spo2_pct": (0.0, 100.0),
    "systolic_mm_hg": (1.0, 400.0),
    "diastolic_mm_hg": (1.0, 300.0),
    "respiratory_rate_bpm": (1.0, 150.0),
}


def _measurement(value: float, field: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise VitalsModelError(f"{field} must be finite")
    low, high = MEASUREMENT_SANITY_BOUNDS[field]
    if value < low or value > high:
        raise VitalsModelError(
            f"{field} is outside broad measurement-sanity bounds; verify the measurement rather than classifying it"
        )
    return value


@dataclass(frozen=True)
class Vitals:
    heart_rate_bpm: float | None = None
    temperature_c: float | None = None
    spo2_pct: float | None = None
    systolic_mm_hg: float | None = None
    diastolic_mm_hg: float | None = None
    respiratory_rate_bpm: float | None = None

    def values(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for key, raw in asdict(self).items():
            if raw is None:
                continue
            out[key] = _measurement(raw, key)
        return out


def _robust_z(value: float, history: Iterable[float], field: str, min_samples: int = 5) -> float | None:
    samples = [_measurement(v, field) for v in history]
    if len(samples) < min_samples:
        return None
    center = median(samples)
    mad = median(abs(v - center) for v in samples)
    if mad <= 0:
        return None
    return 0.67448975 * (value - center) / mad


def personal_vital_deviation(
    current: Vitals | None,
    baseline: Mapping[str, Iterable[float]],
) -> dict[str, float | None]:
    """Return personal-baseline robust z values.

    These values are observational features only. They do not diagnose disease and do not use
    universal clinical thresholds. Direction is preserved (e.g. negative SpO2 z stays negative).
    Broad sanity bounds only reject likely invalid measurements.
    """
    keys = tuple(Vitals.__dataclass_fields__)
    result: dict[str, float | None] = {key: None for key in keys}
    if current is None:
        return result
    for key, value in current.values().items():
        z = _robust_z(value, baseline.get(key, ()), key)
        result[key] = None if z is None else round(z, 4)
    return result
