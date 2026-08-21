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
REWORK_OUTCOMES = {"REWORK", "FAILED", "RETRY"}

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

        task_scope = str(data.get("task_scope", "")).strip()
        source = str(data.get("source", "")).strip()
        operation = str(data.get("operation", "")).strip()
        if not task_scope or not source or not operation:
            raise ValueError("task_scope, source, and operation are required to prevent cross-scope learning")

        return cls(
            event_id=str(data.get("event_id", "")),
            occurred_at=occurred_at,
            task_scope=task_scope,
            source=source,
            operation=operation,
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
    if policy["assist_signal_threshold"] < 1 or policy["clear_success_threshold"] < 1:
        raise ValueError("assist and clearing thresholds must be >= 1")
    return policy


def _scope_key(event: Event) -> tuple[str, str, str]:
    return event.task_scope, event.source, event.operation


def _scope_text(key: tuple[str, str, str]) -> str:
    return "|".join(key)


def _history_hit(scope_key: tuple[str, str, str], history: dict[str, Any], policy: dict[str, int]) -> int:
    wanted = _scope_text(scope_key)
    for cluster in history.get("clusters") or []:
        if str(cluster.get("scope_key", "")) == wanted and int(cluster.get("rework_count", 0)) > 0:
            return policy["historical_support_weight"]
    return 0


def _scope_signal(events: list[Event], history: dict[str, Any], policy: dict[str, int]) -> tuple[int, dict[str, int]]:
    if not events:
        return 0, {
            "repeated_scope_hits": 0,
            "backtrack_hits": 0,
            "human_friction_hits": 0,
            "historical_hits": 0,
        }

    scope_key = _scope_key(events[0])
    if any(_scope_key(event) != scope_key for event in events):
        raise ValueError("_scope_signal accepts exactly one scope")

    repetitions = len(events)
    backtracks = Counter(
        (event.from_step, event.to_step)
        for event in events
        if event.from_step and event.to_step and event.from_step != event.to_step
    )
    marker_counts = Counter(marker for event in events for marker in event.markers)

    repeated_scope_hits = int(repetitions >= policy["assist_repetition_threshold"])
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
    historical_hits = _history_hit(scope_key, history, policy)

    components = {
        "repeated_scope_hits": repeated_scope_hits,
        "backtrack_hits": backtrack_hits,
        "human_friction_hits": human_friction_hits,
        "historical_hits": historical_hits,
    }
    return sum(components.values()), components


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


def _success_tail(events: list[Event]) -> int:
    count = 0
    for event in reversed(events):
        if event.outcome == "SUCCESS":
            count += 1
        else:
            break
    return count


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    policy = _policy(case)
    mode = str(case.get("mode", "OBSERVE"))
    if mode not in VALID_MODES:
        raise ValueError(f"invalid mode: {mode}")

    events = [Event.from_dict(raw) for raw in (case.get("events") or [])]
    events.sort(key=lambda event: _parse_time(event.occurred_at))
    recent = events[-policy["recent_window_events"] :]
    history = case.get("history") or {}

    by_scope: dict[tuple[str, str, str], list[Event]] = defaultdict(list)
    for event in recent:
        by_scope[_scope_key(event)].append(event)

    scope_reports: dict[str, dict[str, Any]] = {}
    for key, scoped_events in by_scope.items():
        score, components = _scope_signal(scoped_events, history, policy)
        scoped_rework = [event for event in scoped_events if event.outcome in REWORK_OUTCOMES]
        scope_reports[_scope_text(key)] = {
            "signal_score": score,
            "signal_components": components,
            "rework_count": len(scoped_rework),
            "success_tail": _success_tail(scoped_events),
            "difficult_zone": score >= policy["assist_signal_threshold"] and bool(scoped_rework),
        }

    requested_active_scope = str(case.get("active_scope") or "").strip()
    if mode in {"ASSIST_ACTIVE", "CLEARING"} and requested_active_scope:
        active_scope = requested_active_scope
    else:
        ranked = sorted(
            scope_reports.items(),
            key=lambda item: (item[1]["difficult_zone"], item[1]["signal_score"], item[1]["rework_count"]),
            reverse=True,
        )
        active_scope = ranked[0][0] if ranked else None

    active_report = scope_reports.get(active_scope or "", {
        "signal_score": 0,
        "signal_components": {
            "repeated_scope_hits": 0,
            "backtrack_hits": 0,
            "human_friction_hits": 0,
            "historical_hits": 0,
        },
        "rework_count": 0,
        "success_tail": 0,
        "difficult_zone": False,
    })
    active_events = [event for event in recent if _scope_text(_scope_key(event)) == active_scope]
    active_rework = [event for event in active_events if event.outcome in REWORK_OUTCOMES]

    difficult_zone = bool(active_report["difficult_zone"])
    next_mode = mode
    reasons: list[str] = []

    if mode == "OBSERVE" and difficult_zone:
        next_mode = "ASSIST_ACTIVE"
        reasons.append("One bounded scope crossed the assist threshold; unrelated scopes were not aggregated.")
    elif mode == "ASSIST_ACTIVE":
        if active_report["success_tail"] >= policy["clear_success_threshold"]:
            next_mode = "CLEARING"
            reasons.append("The assisted scope has a success tail; enter clearing before disabling assist.")
        else:
            reasons.append("Assist remains scoped to the active difficult zone.")
    elif mode == "CLEARING":
        if difficult_zone:
            next_mode = "ASSIST_ACTIVE"
            reasons.append("Rework recurred in the same active scope during clearing; restore bounded assist.")
        elif active_report["success_tail"] >= policy["clear_success_threshold"]:
            next_mode = "OBSERVE"
            reasons.append("The active difficult zone cleared without recurrent rework; return to observe.")

    clusters: dict[tuple[str, str, str], list[Event]] = defaultdict(list)
    for event in recent:
        if event.outcome in REWORK_OUTCOMES:
            clusters[_scope_key(event)].append(event)

    knowledge = [
        {
            "scope_key": _scope_text(key),
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
        "active_scope": active_scope,
        "difficult_zone": difficult_zone,
        "signal_score": active_report["signal_score"],
        "signal_components": active_report["signal_components"],
        "scope_reports": scope_reports,
        "assist_actions": _assist_actions(active_rework) if next_mode == "ASSIST_ACTIVE" else [],
        "knowledge_candidates": knowledge,
        "reasons": reasons,
        "evidence_policy": {
            "raw_event_count": len(events),
            "recent_event_count": len(recent),
            "historical_evidence_used": active_report["signal_components"]["historical_hits"] > 0,
            "note": "Historical evidence raises confidence only inside a matching scope and is not required for realtime activation.",
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
