#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from statistics import median
from typing import Iterable, Mapping


class VitalsModelError(ValueError):
    pass


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
            value = float(raw)
            if not math.isfinite(value):
                raise VitalsModelError(f"{key} must be finite")
            out[key] = value
        return out


def _robust_z(value: float, history: Iterable[float], min_samples: int = 5) -> float | None:
    samples = [float(v) for v in history]
    if len(samples) < min_samples or not all(math.isfinite(v) for v in samples):
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
    universal medical thresholds. Direction is preserved (e.g. negative SpO2 z stays negative).
    """
    keys = tuple(Vitals.__dataclass_fields__)
    result: dict[str, float | None] = {key: None for key in keys}
    if current is None:
        return result
    for key, value in current.values().items():
        z = _robust_z(value, baseline.get(key, ()))
        result[key] = None if z is None else round(z, 4)
    return result
