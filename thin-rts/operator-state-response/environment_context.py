#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


class EnvironmentContextError(ValueError):
    pass


WEATHER_MODES = {"NOT_ASKED", "DENIED", "EPHEMERAL", "COARSE_LOG"}
NOISE_MODES = {"NOT_ASKED", "DENIED", "DERIVED_DB_ONLY"}


def _finite(value: float | None, field: str) -> float | None:
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        raise EnvironmentContextError(f"{field} must be finite")
    return value


def _range(value: float | None, low: float, high: float, field: str) -> float | None:
    value = _finite(value, field)
    if value is None:
        return None
    if value < low or value > high:
        raise EnvironmentContextError(f"{field} must be in [{low}, {high}]")
    return value


@dataclass(frozen=True)
class EnvironmentConsent:
    """Explicit opt-in state for location/weather and microphone-derived noise.

    Precise coordinates and raw audio are deliberately absent from the persisted schema.
    `EPHEMERAL` means location may be used only long enough to obtain weather and is not logged.
    """

    weather_mode: str = "NOT_ASKED"
    noise_mode: str = "NOT_ASKED"

    def validated(self) -> "EnvironmentConsent":
        weather = self.weather_mode.strip().upper()
        noise = self.noise_mode.strip().upper()
        if weather not in WEATHER_MODES:
            raise EnvironmentContextError(f"unsupported weather_mode: {weather}")
        if noise not in NOISE_MODES:
            raise EnvironmentContextError(f"unsupported noise_mode: {noise}")
        return EnvironmentConsent(weather_mode=weather, noise_mode=noise)


@dataclass(frozen=True)
class EnvironmentObservation:
    observed_at: str | None = None
    weather_source: str | None = None
    coarse_location: str | None = None
    outdoor_temp_c: float | None = None
    outdoor_relative_humidity_pct: float | None = None
    apparent_temp_c: float | None = None
    wind_mps: float | None = None
    precipitation_mm: float | None = None
    cabin_temp_c: float | None = None
    cabin_relative_humidity_pct: float | None = None
    cabin_co2_ppm: float | None = None
    noise_laeq_db: float | None = None
    noise_peak_db: float | None = None
    noise_event_count: int | None = None
    subjective_noise_0_10: float | None = None

    def validated(self) -> "EnvironmentObservation":
        if self.noise_event_count is not None and self.noise_event_count < 0:
            raise EnvironmentContextError("noise_event_count must be nonnegative")
        return EnvironmentObservation(
            observed_at=self.observed_at,
            weather_source=self.weather_source,
            coarse_location=self.coarse_location,
            outdoor_temp_c=_range(self.outdoor_temp_c, -80.0, 70.0, "outdoor_temp_c"),
            outdoor_relative_humidity_pct=_range(
                self.outdoor_relative_humidity_pct, 0.0, 100.0, "outdoor_relative_humidity_pct"
            ),
            apparent_temp_c=_range(self.apparent_temp_c, -100.0, 100.0, "apparent_temp_c"),
            wind_mps=_range(self.wind_mps, 0.0, 150.0, "wind_mps"),
            precipitation_mm=_range(self.precipitation_mm, 0.0, 5000.0, "precipitation_mm"),
            cabin_temp_c=_range(self.cabin_temp_c, -40.0, 80.0, "cabin_temp_c"),
            cabin_relative_humidity_pct=_range(
                self.cabin_relative_humidity_pct, 0.0, 100.0, "cabin_relative_humidity_pct"
            ),
            cabin_co2_ppm=_range(self.cabin_co2_ppm, 0.0, 100000.0, "cabin_co2_ppm"),
            noise_laeq_db=_range(self.noise_laeq_db, 0.0, 160.0, "noise_laeq_db"),
            noise_peak_db=_range(self.noise_peak_db, 0.0, 200.0, "noise_peak_db"),
            noise_event_count=self.noise_event_count,
            subjective_noise_0_10=_range(
                self.subjective_noise_0_10, 0.0, 10.0, "subjective_noise_0_10"
            ),
        )


def environment_features(observation: EnvironmentObservation | None) -> dict[str, float | int | None]:
    """Return prediction candidates without converting them into fatigue/diagnosis points."""
    if observation is None:
        return {}
    obs = observation.validated()
    return {
        "outdoor_temp_c": obs.outdoor_temp_c,
        "outdoor_relative_humidity_pct": obs.outdoor_relative_humidity_pct,
        "apparent_temp_c": obs.apparent_temp_c,
        "wind_mps": obs.wind_mps,
        "precipitation_mm": obs.precipitation_mm,
        "cabin_temp_c": obs.cabin_temp_c,
        "cabin_relative_humidity_pct": obs.cabin_relative_humidity_pct,
        "cabin_co2_ppm": obs.cabin_co2_ppm,
        "noise_laeq_db": obs.noise_laeq_db,
        "noise_peak_db": obs.noise_peak_db,
        "noise_event_count": obs.noise_event_count,
        "subjective_noise_0_10": obs.subjective_noise_0_10,
    }


def minimized_environment_record(
    observation: EnvironmentObservation | None,
    consent: EnvironmentConsent,
) -> Mapping[str, object] | None:
    """Create a privacy-minimized record.

    Location is persisted only in COARSE_LOG mode. In EPHEMERAL mode the location used for the
    weather query must already have been discarded by the external adapter. Raw audio is not part
    of this API at all; only derived dB summaries can enter when explicitly permitted.
    """
    if observation is None:
        return None
    consent = consent.validated()
    obs = observation.validated()

    record: dict[str, object] = {
        "observed_at": obs.observed_at,
        "weather_source": obs.weather_source,
        "features": environment_features(obs),
    }
    if consent.weather_mode == "COARSE_LOG" and obs.coarse_location:
        record["coarse_location"] = obs.coarse_location
    if consent.weather_mode in {"NOT_ASKED", "DENIED"}:
        for key in (
            "outdoor_temp_c",
            "outdoor_relative_humidity_pct",
            "apparent_temp_c",
            "wind_mps",
            "precipitation_mm",
        ):
            record["features"].pop(key, None)  # type: ignore[index]
        record["weather_source"] = None
    if consent.noise_mode != "DERIVED_DB_ONLY":
        for key in ("noise_laeq_db", "noise_peak_db", "noise_event_count"):
            record["features"].pop(key, None)  # type: ignore[index]
    return record
