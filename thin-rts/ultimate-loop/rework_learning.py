from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_CLASSES = {"IMPLEMENTATION", "HUMAN_OPERATION", "WORKFLOW"}
VALID_MODES = {"OBSERVE", "ASSIST_ACTIVE", "CLEARING"}

DEFAULT_POLICY = {
    "recent_window_events": 8,
    "assist_repetition_threshold": 3,
    "assist_backtrack_threshold": 2,
    "assist_signal_threshold": 3,
    "clear_success_threshold": 2,
    "historical_support_weight": 1,
}


@dataclass(frozen=True)
class Event:
    event_id: str
    occurred_at: str
    task_scope: str
    source: str
    operation: str
    outcome: str
    rework_class: str
    from_step: str
    to_step: str
    markers: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        rework_class = str(data.get("rework_class", "WORKFLOW"))
        if rework_class not in VALID_CLASSES:
            raise ValueError(f"invalid rework_class: {rework_class}")
        occurred_at = str(data.get("occurred_at", ""))
        if not occurred_at:
            raise ValueError("occurred_at is required")
        _parse_time(occurred_at)
        return cls(
            event_id=str(data.get("event_id", "")),
            occurred_at=occurred_at,
            task_scope=str(data.get("task_scope", "")),
            source=str(data.get("source", "")),
            operation=str(data.get("operation", "")),
            outcome=str(data.get("outcome", "UNKNOWN")),
            rework_class=rework_class,
            from_step=str(data.get("from_step", "")),
            to_step=str(data.get("to_step", "")),
            markers=tuple(str(x) for x in (data.get("markers") or [])),
            evidence_refs=tuple(str(x) for x in (data.get("evidence_refs") or [])),
        )


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _policy(case: dict[str, Any]) -> dict[str, int]:
    policy = dict(DEFAULT_POLICY)
    for key, value in (case.get("policy") or {}).items():
        if key in policy:
            policy[key] = int(value)
    if policy["recent_window_events"] < 1:
        raise ValueError("recent_window_events must be >= 1")
    return policy


def _scope_key(event: Event) -> tuple[str, str, str]:
    return event.task_scope, event.source, event.operation


def _signal_score(events: list[Event], history: dict[str, Any], policy: dict[str, int]) -> tuple[int, dict[str, int]]:
    repetitions = Counter(_scope_key(event) for event in events)
    backtracks = Counter((event.task_scope, event.from_step, event.to_step) for event in events if event.from_step and event.to_step and event.from_step != event.to_step)
    marker_counts = Counter(marker for event in events for marker in event.markers)

    repeated_scope_hits = sum(1 for count in repetitions.values() if count >= policy["assist_repetition_threshold"])
    backtrack_hits = sum(1 for count in backtracks.values() if count >= policy["assist_backtrack_threshold"])
    human_friction_hits = sum(
        marker_counts.get(marker, 0)
        for marker in (
            "MULTI_TAB",
            "PASTE_FAILURE",
            "REPEATED_SCREENSHOT",
            "REPEATED_STATE_DUMP",
            "COMMAND_RETRY",
        )
    )

    historical_hits = 0
    historical_clusters = history.get("clusters") or []
    active_keys = {"|".join(_scope_key(event)) for event in events}
    for cluster in historical_clusters:
        key = str(cluster.get("scope_key", ""))
        if key in active_keys and int(cluster.get("rework_count", 0)) > 0:
            historical_hits += policy["historical_support_weight"]

    components = {
        "repeated_scope_hits": repeated_scope_hits,
        "backtrack_hits": backtrack_hits,
        "human_friction_hits": human_friction_hits,
        "historical_hits": historical_hits,
    }
    score = repeated_scope_hits + backtrack_hits + human_friction_hits + historical_hits
    return score, components


def _assist_actions(events: list[Event]) -> list[str]:
    markers = {marker for event in events for marker in event.markers}
    actions: list[str] = []
    if "MULTI_TAB" in markers:
        actions.append("CONVERGE_TO_SINGLE_TERMINAL")
    if "PASTE_FAILURE" in markers or "COMMAND_RETRY" in markers:
        actions.append("SPLIT_LONG_COMMANDS")
    if "REPEATED_SCREENSHOT" in markers or "REPEATED_STATE_DUMP" in markers:
        actions.append("PREFER_AGGREGATED_STATE_DUMP")
    if any(event.rework_class == "IMPLEMENTATION" for event in events):
        actions.append("REOPEN_SMALLEST_IMPLEMENTATION_GATE")
    if any(event.rework_class == "WORKFLOW" for event in events):
        actions.append("REVIEW_WORKFLOW_SEQUENCE")
    if any(event.rework_class == "HUMAN_OPERATION" for event in events):
        actions.append("ADD_BOUNDED_OPERATION_GUIDANCE")
    return sorted(set(actions))


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    policy = _policy(case)
    mode = str(case.get("mode", "OBSERVE"))
    if mode not in VALID_MODES:
        raise ValueError(f"invalid mode: {mode}")

    events = [Event.from_dict(raw) for raw in (case.get("events") or [])]
    events.sort(key=lambda event: _parse_time(event.occurred_at))
    recent = events[-policy["recent_window_events"] :]
    history = case.get("history") or {}

    score, components = _signal_score(recent, history, policy)
    rework_events = [event for event in recent if event.outcome in {"REWORK", "FAILED", "RETRY"}]
    success_tail = 0
    for event in reversed(recent):
        if event.outcome == "SUCCESS":
            success_tail += 1
        else:
            break

    difficult_zone = score >= policy["assist_signal_threshold"] and bool(rework_events)
    next_mode = mode
    reasons: list[str] = []

    if mode == "OBSERVE" and difficult_zone:
        next_mode = "ASSIST_ACTIVE"
        reasons.append("Current rework signals crossed the bounded assist threshold.")
    elif mode == "ASSIST_ACTIVE":
        if success_tail >= policy["clear_success_threshold"]:
            next_mode = "CLEARING"
            reasons.append("The assisted scope has a success tail; enter clearing before disabling assist.")
        else:
            reasons.append("Assist remains scoped to the active difficult zone.")
    elif mode == "CLEARING":
        if difficult_zone:
            next_mode = "ASSIST_ACTIVE"
            reasons.append("Rework recurred during clearing; restore bounded assist.")
        elif success_tail >= policy["clear_success_threshold"]:
            next_mode = "OBSERVE"
            reasons.append("The difficult zone cleared without recurrent rework; return to observe.")

    clusters: dict[tuple[str, str, str], list[Event]] = defaultdict(list)
    for event in rework_events:
        clusters[_scope_key(event)].append(event)

    knowledge = [
        {
            "scope_key": "|".join(key),
            "rework_count": len(items),
            "classes": sorted({item.rework_class for item in items}),
            "markers": sorted({marker for item in items for marker in item.markers}),
            "evidence_refs": sorted({ref for item in items for ref in item.evidence_refs}),
        }
        for key, items in sorted(clusters.items())
    ]

    return {
        "schema": "ultimate-loop-rework-learning-report/v0",
        "mode": mode,
        "next_mode": next_mode,
        "difficult_zone": difficult_zone,
        "signal_score": score,
        "signal_components": components,
        "assist_actions": _assist_actions(rework_events) if next_mode == "ASSIST_ACTIVE" else [],
        "knowledge_candidates": knowledge,
        "reasons": reasons,
        "evidence_policy": {
            "raw_event_count": len(events),
            "recent_event_count": len(recent),
            "historical_evidence_used": components["historical_hits"] > 0,
            "note": "Historical evidence raises confidence but is not required for realtime assist activation.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate optional Ultimate Loop rework-learning assist state")
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(case), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
