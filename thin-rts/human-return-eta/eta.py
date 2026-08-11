#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Iterable

DEFAULT_FALLBACK_MINUTES = 10
DEFAULT_WINDOW = 20
EARLY_WAKE_TERMINALS = ["ERROR", "APPROVAL_REQUIRED", "HUMAN_ACTION_REQUIRED"]
EVIDENCE_WEIGHTS = {"STRONG": 1.0, "MEDIUM": 0.6, "WEAK": 0.25}


class ETAError(RuntimeError):
    pass


@dataclass(frozen=True)
class Observation:
    task_class: str
    started_at: datetime
    human_hinge_at: datetime
    terminal: str
    duration_minutes: float
    weighted_chunks: float | None
    evidence_strength: str
    source: str | None


def parse_time(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ETAError(f"{field} must be a non-empty ISO-8601 string")
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as e:
        raise ETAError(f"invalid {field}: {value!r}") from e
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ETAError(f"{field} must be timezone-aware")
    return dt


def normalize_record(record: object) -> Observation:
    if not isinstance(record, dict):
        raise ETAError("history record must be an object")
    task_class = record.get("task_class")
    terminal = record.get("terminal")
    if not isinstance(task_class, str) or not task_class.strip():
        raise ETAError("task_class must be a non-empty string")
    if not isinstance(terminal, str) or not terminal.strip():
        raise ETAError("terminal must be a non-empty string")
    start = parse_time(record.get("started_at"), "started_at")
    hinge = parse_time(record.get("human_hinge_at"), "human_hinge_at")
    seconds = (hinge - start).total_seconds()
    if seconds <= 0:
        raise ETAError("human_hinge_at must be later than started_at")

    weighted_chunks_raw = record.get("weighted_chunks")
    weighted_chunks: float | None = None
    if weighted_chunks_raw is not None:
        if isinstance(weighted_chunks_raw, bool) or not isinstance(weighted_chunks_raw, (int, float)):
            raise ETAError("weighted_chunks must be a positive number when present")
        weighted_chunks = float(weighted_chunks_raw)
        if not math.isfinite(weighted_chunks) or weighted_chunks <= 0:
            raise ETAError("weighted_chunks must be a positive finite number")

    strength = str(record.get("evidence_strength", "STRONG")).strip().upper()
    if strength not in EVIDENCE_WEIGHTS:
        raise ETAError(f"unsupported evidence_strength: {strength!r}")

    source_raw = record.get("source")
    source = None if source_raw is None else str(source_raw).strip() or None

    return Observation(
        task_class=task_class.strip(),
        started_at=start,
        human_hinge_at=hinge,
        terminal=terminal.strip().upper(),
        duration_minutes=seconds / 60.0,
        weighted_chunks=weighted_chunks,
        evidence_strength=strength,
        source=source,
    )


def load_jsonl(path: Path) -> list[Observation]:
    observations: list[Observation] = []
    seen: set[tuple[str, str, str, str, float | None, str]] = set()
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                obs = normalize_record(record)
            except (json.JSONDecodeError, ETAError) as e:
                raise ETAError(f"{path}:{lineno}: {e}") from e
            identity = (
                obs.task_class,
                obs.started_at.isoformat(),
                obs.human_hinge_at.isoformat(),
                obs.terminal,
                obs.weighted_chunks,
                obs.evidence_strength,
            )
            if identity in seen:
                continue
            seen.add(identity)
            observations.append(obs)
    return observations


def percentile_nearest_rank(values: list[float], fraction: float) -> float:
    if not values:
        raise ETAError("percentile requires at least one value")
    if not (0 < fraction <= 1):
        raise ETAError("fraction must be in (0,1]")
    ordered = sorted(values)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


def weighted_percentile(values: list[tuple[float, float]], fraction: float) -> float:
    if not values:
        raise ETAError("weighted percentile requires at least one value")
    if not (0 < fraction <= 1):
        raise ETAError("fraction must be in (0,1]")
    clean = [(float(v), float(w)) for v, w in values if w > 0]
    if not clean:
        raise ETAError("weighted percentile requires positive weights")
    clean.sort(key=lambda item: item[0])
    total = sum(w for _, w in clean)
    threshold = fraction * total
    cumulative = 0.0
    for value, weight in clean:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return clean[-1][0]


def confidence(values: list[float], effective_samples: float | None = None) -> str:
    n = len(values)
    effective = float(n) if effective_samples is None else effective_samples
    if n < 3 or effective < 2.0:
        return "LOW"
    med = median(values)
    p20 = percentile_nearest_rank(values, 0.20)
    p80 = percentile_nearest_rank(values, 0.80)
    spread_ratio = (p80 - p20) / med if med > 0 else float("inf")
    if n >= 8 and effective >= 6.0 and spread_ratio <= 0.50:
        return "HIGH"
    if n >= 4 and effective >= 3.0 and spread_ratio <= 1.00:
        return "MEDIUM"
    return "LOW"


def _strength_weight(obs: Observation) -> float:
    return EVIDENCE_WEIGHTS[obs.evidence_strength]


def _validate_positive_optional(value: float | None, field: str) -> float | None:
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ETAError(f"{field} must be a positive finite number")
    return value


def estimate(
    observations: Iterable[Observation],
    task_class: str,
    *,
    window: int = DEFAULT_WINDOW,
    fallback_minutes: int = DEFAULT_FALLBACK_MINUTES,
    target_chunks: float | None = None,
    prior_minutes_per_chunk: float | None = None,
) -> dict:
    if window <= 0:
        raise ETAError("window must be positive")
    if fallback_minutes <= 0:
        raise ETAError("fallback_minutes must be positive")
    target_chunks = _validate_positive_optional(target_chunks, "target_chunks")
    prior_minutes_per_chunk = _validate_positive_optional(
        prior_minutes_per_chunk, "prior_minutes_per_chunk"
    )

    all_observations = list(observations)
    selected = [o for o in all_observations if o.task_class == task_class]
    selected.sort(key=lambda o: o.human_hinge_at)
    selected = selected[-window:]

    chunk_rates_same_class = [
        (o.duration_minutes / o.weighted_chunks, _strength_weight(o))
        for o in selected
        if o.weighted_chunks is not None
    ]
    chunk_rates_global = [
        (o.duration_minutes / o.weighted_chunks, _strength_weight(o))
        for o in all_observations
        if o.weighted_chunks is not None
    ]

    chunk_rate_source = None
    chunk_rate_p80 = None
    if chunk_rates_same_class:
        chunk_rate_p80 = weighted_percentile(chunk_rates_same_class, 0.80)
        chunk_rate_source = "SAME_CLASS_HISTORY"
    elif chunk_rates_global:
        chunk_rate_p80 = weighted_percentile(chunk_rates_global, 0.80)
        chunk_rate_source = "GLOBAL_CHUNK_HISTORY"
    elif prior_minutes_per_chunk is not None:
        chunk_rate_p80 = prior_minutes_per_chunk
        chunk_rate_source = "EXPLICIT_CHUNK_PRIOR"

    chunk_estimate = None
    if target_chunks is not None and chunk_rate_p80 is not None:
        chunk_estimate = target_chunks * chunk_rate_p80

    if not selected:
        if chunk_estimate is not None:
            come_back = max(1, math.ceil(chunk_estimate))
            return {
                "task_class": task_class,
                "samples": 0,
                "confidence": "LOW",
                "come_back_after_minutes": come_back,
                "expected_range_minutes": None,
                "late_after_minutes": max(come_back + 2, math.ceil(come_back * 1.5)),
                "wake_early_on": EARLY_WAKE_TERMINALS,
                "basis": "CHUNK_PRIOR_ONLY",
                "target_weighted_chunks": round(target_chunks, 3),
                "chunk_minutes_per_unit_p80": round(chunk_rate_p80, 4),
                "chunk_rate_source": chunk_rate_source,
            }
        return {
            "task_class": task_class,
            "samples": 0,
            "confidence": "LOW",
            "come_back_after_minutes": fallback_minutes,
            "expected_range_minutes": None,
            "late_after_minutes": max(fallback_minutes + 5, math.ceil(fallback_minutes * 1.5)),
            "wake_early_on": EARLY_WAKE_TERMINALS,
            "basis": "COLD_START_FALLBACK",
        }

    values = [o.duration_minutes for o in selected]
    weighted_values = [(o.duration_minutes, _strength_weight(o)) for o in selected]
    effective_samples = sum(_strength_weight(o) for o in selected)
    med = median(values)
    p20 = weighted_percentile(weighted_values, 0.20)
    p80 = weighted_percentile(weighted_values, 0.80)
    p90 = weighted_percentile(weighted_values, 0.90)

    scaled_empirical = p80
    class_chunk_values = [
        (o.weighted_chunks, _strength_weight(o))
        for o in selected
        if o.weighted_chunks is not None
    ]
    historical_chunk_median = None
    if target_chunks is not None and class_chunk_values:
        historical_chunk_median = weighted_percentile(class_chunk_values, 0.50)
        if historical_chunk_median > 0:
            scaled_empirical = p80 * (target_chunks / historical_chunk_median)

    if chunk_estimate is not None:
        empirical_weight = min(0.75, effective_samples / (effective_samples + 3.0))
        blended = (scaled_empirical * empirical_weight) + (
            chunk_estimate * (1.0 - empirical_weight)
        )
        conservative = max(blended, min(scaled_empirical, chunk_estimate))
        come_back = max(1, math.ceil(conservative))
        basis = "HYBRID_GIT_TIME_AND_CHUNK"
    else:
        come_back = max(1, math.ceil(p80))
        basis = "RECENT_CLASS_HISTORY"

    late_after = max(come_back + 2, math.ceil(p90), math.ceil(come_back * 1.25))
    result = {
        "task_class": task_class,
        "samples": len(values),
        "effective_samples": round(effective_samples, 2),
        "confidence": confidence(values, effective_samples),
        "median_minutes": round(med, 2),
        "p80_minutes": round(p80, 2),
        "come_back_after_minutes": come_back,
        "expected_range_minutes": [max(1, math.floor(p20)), max(1, math.ceil(max(p80, come_back)))],
        "late_after_minutes": late_after,
        "wake_early_on": EARLY_WAKE_TERMINALS,
        "basis": basis,
        "window": window,
        "terminal_mix": sorted({o.terminal for o in selected}),
        "evidence_mix": sorted({o.evidence_strength for o in selected}),
    }
    if target_chunks is not None:
        result["target_weighted_chunks"] = round(target_chunks, 3)
    if chunk_rate_p80 is not None:
        result["chunk_minutes_per_unit_p80"] = round(chunk_rate_p80, 4)
        result["chunk_rate_source"] = chunk_rate_source
    if chunk_estimate is not None:
        result["chunk_estimate_minutes"] = round(chunk_estimate, 2)
        result["scaled_empirical_minutes"] = round(scaled_empirical, 2)
    if historical_chunk_median is not None:
        result["historical_chunk_median"] = round(historical_chunk_median, 3)
    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Estimate when a human should return to an unattended development task")
    p.add_argument("--history", required=True, help="JSONL timestamp history")
    p.add_argument("--task-class", required=True)
    p.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    p.add_argument("--fallback-minutes", type=int, default=DEFAULT_FALLBACK_MINUTES)
    p.add_argument("--target-chunks", type=float)
    p.add_argument("--prior-minutes-per-chunk", type=float)
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        observations = load_jsonl(Path(args.history))
        result = estimate(
            observations,
            args.task_class,
            window=args.window,
            fallback_minutes=args.fallback_minutes,
            target_chunks=args.target_chunks,
            prior_minutes_per_chunk=args.prior_minutes_per_chunk,
        )
    except (OSError, ETAError) as e:
        print(json.dumps({"goal": "ERROR", "error": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
