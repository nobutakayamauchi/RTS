#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


class WearableContextError(ValueError):
    pass


CONSENT_MODES = {"NOT_ASKED", "DENIED", "SUMMARY_ONLY", "DERIVED_ONLY"}


def _finite(value: float | None, field: str) -> float | None:
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        raise WearableContextError(f"{field} must be finite")
    return value


def _range(value: float | None, low: float, high: float, field: str) -> float | None:
    value = _finite(value, field)
    if value is None:
        return None
    if value < low or value > high:
        raise WearableContextError(f"{field} must be in [{low}, {high}]")
    return value


@dataclass(frozen=True)
class WearableConsent:
    mode: str = "NOT_ASKED"

    def validated(self) -> "WearableConsent":
        mode = self.mode.strip().upper()
        if mode not in CONSENT_MODES:
            raise WearableContextError(f"unsupported wearable consent mode: {mode}")
        return WearableConsent(mode=mode)


@dataclass(frozen=True)
class WearableObservation:
    observed_at: str | None = None
    source_adapter: str | None = None
    source_device_class: str | None = None
    sleep_duration_minutes: float | None = None
    sleep_efficiency_pct: float | None = None
    deep_sleep_minutes: float | None = None
    rem_sleep_minutes: float | None = None
    awake_minutes: float | None = None
    resting_heart_rate_bpm: float | None = None
    overnight_hrv_ms: float | None = None
    respiratory_rate_bpm: float | None = None
    oxygen_saturation_pct: float | None = None
    temperature_deviation_c: float | None = None
    vendor_readiness_score: float | None = None
    vendor_sleep_score: float | None = None

    def validated(self) -> "WearableObservation":
        return WearableObservation(
            observed_at=self.observed_at,
            source_adapter=self.source_adapter,
            source_device_class=self.source_device_class,
            sleep_duration_minutes=_range(self.sleep_duration_minutes, 0.0, 24.0 * 60.0, "sleep_duration_minutes"),
            sleep_efficiency_pct=_range(self.sleep_efficiency_pct, 0.0, 100.0, "sleep_efficiency_pct"),
            deep_sleep_minutes=_range(self.deep_sleep_minutes, 0.0, 24.0 * 60.0, "deep_sleep_minutes"),
            rem_sleep_minutes=_range(self.rem_sleep_minutes, 0.0, 24.0 * 60.0, "rem_sleep_minutes"),
            awake_minutes=_range(self.awake_minutes, 0.0, 24.0 * 60.0, "awake_minutes"),
            resting_heart_rate_bpm=_range(self.resting_heart_rate_bpm, 20.0, 260.0, "resting_heart_rate_bpm"),
            overnight_hrv_ms=_range(self.overnight_hrv_ms, 0.0, 1000.0, "overnight_hrv_ms"),
            respiratory_rate_bpm=_range(self.respiratory_rate_bpm, 2.0, 80.0, "respiratory_rate_bpm"),
            oxygen_saturation_pct=_range(self.oxygen_saturation_pct, 0.0, 100.0, "oxygen_saturation_pct"),
            temperature_deviation_c=_range(self.temperature_deviation_c, -15.0, 15.0, "temperature_deviation_c"),
            vendor_readiness_score=_range(self.vendor_readiness_score, 0.0, 100.0, "vendor_readiness_score"),
            vendor_sleep_score=_range(self.vendor_sleep_score, 0.0, 100.0, "vendor_sleep_score"),
        )


def canonical_features(observation: WearableObservation | None) -> dict[str, float | None]:
    if observation is None:
        return {}
    obs = observation.validated()
    return {
        "sleep_duration_minutes": obs.sleep_duration_minutes,
        "sleep_efficiency_pct": obs.sleep_efficiency_pct,
        "deep_sleep_minutes": obs.deep_sleep_minutes,
        "rem_sleep_minutes": obs.rem_sleep_minutes,
        "awake_minutes": obs.awake_minutes,
        "resting_heart_rate_bpm": obs.resting_heart_rate_bpm,
        "overnight_hrv_ms": obs.overnight_hrv_ms,
        "respiratory_rate_bpm": obs.respiratory_rate_bpm,
        "oxygen_saturation_pct": obs.oxygen_saturation_pct,
        "temperature_deviation_c": obs.temperature_deviation_c,
        "vendor_readiness_score": obs.vendor_readiness_score,
        "vendor_sleep_score": obs.vendor_sleep_score,
    }


def minimized_wearable_record(
    observation: WearableObservation | None,
    consent: WearableConsent,
) -> Mapping[str, object] | None:
    """Return a privacy-minimized wearable record.

    Vendor scores are preserved as vendor-derived values only. They are never interpreted here as
    fatigue, diagnosis, or percent impairment. DERIVED_ONLY excludes vendor scores and keeps only
    canonical physiological/sleep features. SUMMARY_ONLY may retain vendor scores for later held-out
    comparison, but downstream models must avoid double counting a vendor score and its contributors.
    """
    if observation is None:
        return None
    consent = consent.validated()
    if consent.mode in {"NOT_ASKED", "DENIED"}:
        return None

    obs = observation.validated()
    features = canonical_features(obs)
    if consent.mode == "DERIVED_ONLY":
        features.pop("vendor_readiness_score", None)
        features.pop("vendor_sleep_score", None)

    return {
        "observed_at": obs.observed_at,
        "source_adapter": obs.source_adapter,
        "source_device_class": obs.source_device_class,
        "features": features,
        "semantics": "wellness_observation_not_diagnosis",
    }
