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


class ETAError(RuntimeError):
    pass


@dataclass(frozen=True)
class Observation:
    task_class: str
    started_at: datetime
    human_hinge_at: datetime
    terminal: str
    duration_minutes: float


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
    return Observation(
        task_class=task_class.strip(),
        started_at=start,
        human_hinge_at=hinge,
        terminal=terminal.strip().upper(),
        duration_minutes=seconds / 60.0,
    )


def load_jsonl(path: Path) -> list[Observation]:
    observations: list[Observation] = []
    seen: set[tuple[str, str, str, str]] = set()
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


def confidence(values: list[float]) -> str:
    n = len(values)
    if n < 3:
        return "LOW"
    med = median(values)
    p20 = percentile_nearest_rank(values, 0.20)
    p80 = percentile_nearest_rank(values, 0.80)
    spread_ratio = (p80 - p20) / med if med > 0 else float("inf")
    if n >= 8 and spread_ratio <= 0.50:
        return "HIGH"
    if n >= 4 and spread_ratio <= 1.00:
        return "MEDIUM"
    return "LOW"


def estimate(
    observations: Iterable[Observation],
    task_class: str,
    *,
    window: int = DEFAULT_WINDOW,
    fallback_minutes: int = DEFAULT_FALLBACK_MINUTES,
) -> dict:
    if window <= 0:
        raise ETAError("window must be positive")
    if fallback_minutes <= 0:
        raise ETAError("fallback_minutes must be positive")

    selected = [o for o in observations if o.task_class == task_class]
    selected.sort(key=lambda o: o.human_hinge_at)
    selected = selected[-window:]

    if not selected:
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
    med = median(values)
    p20 = percentile_nearest_rank(values, 0.20)
    p80 = percentile_nearest_rank(values, 0.80)
    p90 = percentile_nearest_rank(values, 0.90)
    come_back = max(1, math.ceil(p80))
    late_after = max(come_back + 2, math.ceil(p90), math.ceil(come_back * 1.25))

    return {
        "task_class": task_class,
        "samples": len(values),
        "confidence": confidence(values),
        "median_minutes": round(med, 2),
        "p80_minutes": round(p80, 2),
        "come_back_after_minutes": come_back,
        "expected_range_minutes": [max(1, math.floor(p20)), max(1, math.ceil(p80))],
        "late_after_minutes": late_after,
        "wake_early_on": EARLY_WAKE_TERMINALS,
        "basis": "RECENT_CLASS_HISTORY",
        "window": window,
        "terminal_mix": sorted({o.terminal for o in selected}),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Estimate when a human should return to an unattended development task")
    p.add_argument("--history", required=True, help="JSONL timestamp history")
    p.add_argument("--task-class", required=True)
    p.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    p.add_argument("--fallback-minutes", type=int, default=DEFAULT_FALLBACK_MINUTES)
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
        )
    except (OSError, ETAError) as e:
        print(json.dumps({"goal": "ERROR", "error": str(e)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
