#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).with_name("status_effect_catalog.json")
AXES = ("judgment", "reaction", "accuracy", "operation")
GRADE_ORDER = {"UNKNOWN": 0, "CAUTION": 1, "MODERATE": 2, "HIGH": 3}


class EffectCatalogError(ValueError):
    pass


@dataclass(frozen=True)
class AxisImpact:
    grade: str
    evidence_ids: tuple[str, ...]
    details: tuple[str, ...]


@dataclass(frozen=True)
class PerformanceImpact:
    axes: dict[str, AxisImpact]
    matched_profiles: tuple[str, ...]
    comparative_references: tuple[str, ...]
    notes: tuple[str, ...]


def _load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "operator-state-effect-catalog/v0":
        raise EffectCatalogError("unexpected effect catalog schema")
    if not isinstance(data.get("profiles"), list):
        raise EffectCatalogError("effect catalog profiles must be a list")
    return data


def _matches(profile: dict[str, Any], *, sleep_hours_24h: float | None,
             continuous_awake_hours: float | None, sleep_restriction_nights: int | None) -> bool:
    trigger = profile.get("trigger", {})
    field = trigger.get("field")
    if field == "sleep_hours_24h":
        if sleep_hours_24h is None:
            return False
        value = float(sleep_hours_24h)
        if "min_inclusive" in trigger and value < float(trigger["min_inclusive"]):
            return False
        if "max_inclusive" in trigger and value > float(trigger["max_inclusive"]):
            return False
        if "approx_value" in trigger and abs(value - float(trigger["approx_value"])) > 0.75:
            return False
        required_nights = trigger.get("requires_min_nights")
        if required_nights is not None:
            if sleep_restriction_nights is None or sleep_restriction_nights < int(required_nights):
                return False
        return True
    if field == "continuous_awake_hours":
        if continuous_awake_hours is None:
            return False
        value = float(continuous_awake_hours)
        return float(trigger.get("min_inclusive", value)) <= value <= float(trigger.get("max_inclusive", value))
    return False


def _merge_grade(current: str, incoming: str) -> str:
    if incoming not in GRADE_ORDER:
        raise EffectCatalogError(f"unknown effect grade: {incoming}")
    if current not in GRADE_ORDER:
        raise EffectCatalogError(f"unknown effect grade: {current}")
    return incoming if GRADE_ORDER[incoming] > GRADE_ORDER[current] else current


def estimate_performance_impact(
    *,
    sleep_hours_24h: float | None = None,
    continuous_awake_hours: float | None = None,
    sleep_restriction_nights: int | None = None,
    catalog_path: Path = CATALOG_PATH,
) -> PerformanceImpact:
    """Return an evidence-bounded performance prior.

    Grades are ordinal evidence flags, not percent loss of ability. Population studies can add a
    prior for a domain but cannot diagnose the operator or override personal longitudinal evidence.
    """
    catalog = _load_catalog(catalog_path)
    grades = {axis: "UNKNOWN" for axis in AXES}
    ids = {axis: [] for axis in AXES}
    details = {axis: [] for axis in AXES}
    matched: list[str] = []
    comparisons: list[str] = []
    notes: list[str] = []

    for profile in catalog["profiles"]:
        if not _matches(
            profile,
            sleep_hours_24h=sleep_hours_24h,
            continuous_awake_hours=continuous_awake_hours,
            sleep_restriction_nights=sleep_restriction_nights,
        ):
            continue
        profile_id = str(profile["id"])
        matched.append(profile_id)
        for axis in AXES:
            effect = profile.get("effects", {}).get(axis)
            if not effect:
                continue
            grade = str(effect.get("grade", "UNKNOWN")).upper()
            grades[axis] = _merge_grade(grades[axis], grade)
            ids[axis].append(profile_id)
            detail = effect.get("detail")
            if detail:
                details[axis].append(str(detail))
            metric = effect.get("metric")
            value = effect.get("value")
            endpoint = effect.get("endpoint")
            if metric is not None and value is not None:
                metric_text = f"{metric}={value}"
                if endpoint:
                    metric_text += f" ({endpoint})"
                details[axis].append(metric_text)

        comparison = profile.get("comparative_reference")
        if comparison:
            if comparison.get("type") == "blood_alcohol_concentration":
                comparisons.append(
                    f"BAC {comparison.get('value_percent')}% comparator: {comparison.get('semantics')}"
                )

    if sleep_hours_24h is not None and sleep_hours_24h <= 6 and sleep_restriction_nights is None:
        notes.append("sleep_duration_match_without_multiday_history")
    if continuous_awake_hours is None:
        notes.append("continuous_awake_hours_unknown_no_alcohol_comparator_match")
    if not matched:
        notes.append("no_catalog_profile_matched")

    return PerformanceImpact(
        axes={
            axis: AxisImpact(
                grade=grades[axis],
                evidence_ids=tuple(ids[axis]),
                details=tuple(details[axis]),
            )
            for axis in AXES
        },
        matched_profiles=tuple(matched),
        comparative_references=tuple(comparisons),
        notes=tuple(notes),
    )
