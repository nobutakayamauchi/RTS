from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import ControllerError, validate_usage
from .store import append_event

def _project_usage(current: dict[str, int], *, attempt: bool = False, delta: dict[str, int] | None = None, event: bool = True) -> dict[str, int]:
    projected = dict(validate_usage(current))
    if attempt:
        projected["attempts"] += 1
    if delta:
        projected["elapsed_seconds"] += delta["elapsed_seconds"]
        projected["changed_files"] += delta["changed_files"]
        projected["changed_bytes"] += delta["changed_bytes"]
    if event:
        projected["events"] += 1
    return projected


def _budget_excess(usage: dict[str, int], budgets: dict[str, int]) -> list[str]:
    mapping = {
        "attempts": "max_attempts",
        "elapsed_seconds": "max_elapsed_seconds",
        "changed_files": "max_changed_files",
        "changed_bytes": "max_changed_bytes",
        "events": "max_events",
    }
    return [
        field
        for field, budget_field in mapping.items()
        if usage[field] > budgets[budget_field]
    ]


def _append(
    state_dir: Path,
    plan: dict[str, Any],
    authorization: dict[str, Any],
    *,
    event_type: str,
    before: str,
    after: str,
    attempt: int,
    usage: dict[str, int],
    timestamp: str,
    summary: str,
) -> dict[str, Any]:
    excess = _budget_excess(usage, plan["budgets"])
    if excess:
        raise ControllerError(f"event would exceed budget: {', '.join(excess)}")
    return append_event(
        state_dir,
        plan["plan_id"],
        plan_id=plan["plan_id"],
        authorization_fingerprint=authorization["authorization_fingerprint"],
        event_type=event_type,
        state_before=before,
        state_after=after,
        attempt=attempt,
        usage=usage,
        timestamp=timestamp,
        summary=summary,
    )
