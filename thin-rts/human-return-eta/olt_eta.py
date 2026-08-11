#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import olt


class OLTETAError(RuntimeError):
    pass


@dataclass(frozen=True)
class HistoricalRun:
    duration_minutes: float
    load: olt.LoadVector
    task_class: str | None = None
    evidence_strength: str = "STRONG"


EVIDENCE_WEIGHTS = {
    "STRONG": 1.0,
    "MEDIUM": 0.6,
    "WEAK": 0.25,
}


def _positive_finite(value: float, field: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise OLTETAError(f"{field} must be a positive finite number")
    return value


def _evidence_weight(value: str) -> float:
    key = str(value).strip().upper()
    if key not in EVIDENCE_WEIGHTS:
        raise OLTETAError(f"unsupported evidence strength: {value!r}")
    return EVIDENCE_WEIGHTS[key]


def _weighted_percentile(values: list[tuple[float, float]], fraction: float) -> float:
    if not values:
        raise OLTETAError("weighted percentile requires values")
    ordered = sorted((float(v), float(w)) for v, w in values if w > 0)
    if not ordered:
        raise OLTETAError("weighted percentile requires positive weights")
    total = sum(weight for _, weight in ordered)
    threshold = total * fraction
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= threshold:
            return value
    return ordered[-1][0]


def estimate_from_vector(
    runs: Iterable[HistoricalRun],
    target: olt.LoadVector,
    *,
    task_class: str | None = None,
    k: int = 8,
    distance_scale: float = 1.0,
) -> dict:
    if k <= 0:
        raise OLTETAError("k must be positive")
    distance_scale = _positive_finite(distance_scale, "distance_scale")

    # Validate the target through the canonical normalized-vector path.
    olt.normalized_vector(target)

    candidates = []
    for run in runs:
        duration = _positive_finite(run.duration_minutes, "duration_minutes")
        weight = _evidence_weight(run.evidence_strength)
        distance = olt.vector_distance(target, run.load)
        class_match = task_class is not None and run.task_class == task_class

        # Similarity is deliberately bounded and transparent. Exact load matches
        # receive 1.0 before evidence/class weighting; distant vectors decay.
        similarity = math.exp(-distance / distance_scale)
        if class_match:
            similarity *= 1.25
        effective_weight = similarity * weight
        candidates.append(
            {
                "duration": duration,
                "distance": distance,
                "class_match": class_match,
                "effective_weight": effective_weight,
                "evidence_strength": str(run.evidence_strength).strip().upper(),
            }
        )

    candidates.sort(key=lambda row: (row["distance"], row["duration"]))
    neighbors = candidates[:k]
    usable = [row for row in neighbors if row["effective_weight"] > 1e-9]
    if not usable:
        return {
            "basis": "OLT_VECTOR_PRIOR_UNAVAILABLE",
            "neighbors": 0,
            "confidence": "LOW",
            "come_back_after_minutes": None,
        }

    weighted = [(row["duration"], row["effective_weight"]) for row in usable]
    p50 = _weighted_percentile(weighted, 0.50)
    p80 = _weighted_percentile(weighted, 0.80)
    total_effective_weight = sum(row["effective_weight"] for row in usable)
    nearest_distance = usable[0]["distance"]
    matched = sum(1 for row in usable if row["class_match"])

    if len(usable) >= 6 and total_effective_weight >= 3.0 and nearest_distance <= 0.5:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "basis": "OLT_VECTOR_PRIOR",
        "neighbors": len(usable),
        "class_matched_neighbors": matched,
        "effective_weight": round(total_effective_weight, 4),
        "nearest_distance": round(nearest_distance, 4),
        "p50_minutes": round(p50, 2),
        "p80_minutes": round(p80, 2),
        "come_back_after_minutes": max(1, math.ceil(p80)),
        "confidence": confidence,
    }


def blend_with_direct_history(direct: dict, olt_prior: dict) -> dict:
    """Blend an OLT prior only when direct task history is sparse.

    Direct semantically-bound timing remains authoritative. OLT never overrides
    a mature direct estimate; it only nudges cold/low-sample behavior.
    """
    direct_minutes = direct.get("come_back_after_minutes")
    prior_minutes = olt_prior.get("come_back_after_minutes")
    direct_samples = int(direct.get("samples", 0) or 0)

    if prior_minutes is None:
        return dict(direct)
    if direct_minutes is None:
        result = dict(olt_prior)
        result["basis"] = "OLT_VECTOR_PRIOR_ONLY"
        return result

    if direct_samples >= 8:
        result = dict(direct)
        result["olt_prior_minutes"] = prior_minutes
        result["olt_influence"] = 0.0
        return result

    # Prior influence fades as direct observations accumulate.
    prior_weight = max(0.0, min(0.5, (8 - direct_samples) / 16.0))
    blended = (float(direct_minutes) * (1.0 - prior_weight)) + (
        float(prior_minutes) * prior_weight
    )
    result = dict(direct)
    result["come_back_after_minutes"] = max(1, math.ceil(blended))
    result["basis"] = "DIRECT_PLUS_OLT_VECTOR_PRIOR"
    result["direct_minutes"] = direct_minutes
    result["olt_prior_minutes"] = prior_minutes
    result["olt_influence"] = round(prior_weight, 3)
    return result
