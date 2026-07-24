"""Combined priority, build-value ranking, index validation, and selection gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from freezer.assessment_core import (
    BuildAssessmentError, iter_current_items, load_config, load_current_item, load_json, write_json,
)
from freezer.assessment_store import assessment_state, require_build_now_assessment, verify_histories


def _score(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 5:
        raise BuildAssessmentError(f"{field} must be between 0 and 5")
    return float(value)


def compute_priority_score(item: dict[str, Any], config: dict[str, Any]) -> float:
    priority = item.get("priority")
    if not isinstance(priority, dict):
        raise BuildAssessmentError(f"{item.get('item_id', '<unknown>')}: priority must be an object")
    max_value = float(config["score_scale"]["maximum"])
    benefits = set(config["benefit_fields"])
    costs = set(config["cost_fields"])
    numerator = denominator = 0.0
    for name, weight in config["score_weights"].items():
        if name not in priority:
            raise BuildAssessmentError(f"{item['item_id']}: missing priority field {name}")
        raw = _score(priority[name], field=f"{item['item_id']}.priority.{name}")
        contribution = raw if name in benefits else max_value - raw if name in costs else None
        if contribution is None:
            raise BuildAssessmentError(f"unclassified score field: {name}")
        numerator += contribution * float(weight)
        denominator += max_value * float(weight)
    return round(numerator / denominator * 100, 2) if denominator else 0.0


def build_index_rows(root: Path) -> list[dict[str, Any]]:
    config = load_config(root)
    rankable = set(config["rankable_statuses"])
    rows: list[dict[str, Any]] = []
    for item in iter_current_items(root):
        if item.get("status") not in rankable:
            continue
        priority_score = compute_priority_score(item, config)
        try:
            state = assessment_state(root, item)
        except BuildAssessmentError:
            state = {"state": "INVALID", "assessment": None}
        record = state["assessment"]
        if state["state"] == "CURRENT" and record:
            build_score = record["derived"]["decision_score"]
            ranking_score = round(priority_score * 0.35 + build_score * 0.65, 2)
            recommendation = record["derived"]["recommendation"]
            net_hours = record["derived"]["net_hours"]
            reuse_hours_saved = record["derived"]["reuse_hours_saved"]
            efficiency = record["derived"]["implementation_efficiency"]
        else:
            build_score = net_hours = reuse_hours_saved = efficiency = None
            ranking_score = round(priority_score * 0.35, 2)
            recommendation = "ASSESSMENT_REQUIRED"
        rows.append(
            {
                "item_id": item["item_id"], "version": item["version"], "title": item["title"],
                "status": item["status"], "priority_score": priority_score,
                "assessment_state": state["state"], "build_score": build_score,
                "ranking_score": ranking_score, "recommendation": recommendation,
                "net_hours": net_hours, "reuse_hours_saved": reuse_hours_saved,
                "implementation_efficiency": efficiency, "build_authority": item["build_authority"],
            }
        )
    return sorted(rows, key=lambda row: (-row["ranking_score"], row["item_id"]))


def build_index_payload(root: Path) -> dict[str, Any]:
    from freezer.assessment_core import utc_now
    rows = build_index_rows(root)
    return {
        "generated_at": utc_now(),
        "count": len(rows),
        "policy": {
            "priority_weight": 0.35,
            "build_assessment_weight": 0.65,
            "active_recommendation_required": "BUILD_NOW",
            "github_scan_required": True,
            "implementation_preflight_follows_assessment": True,
            "human_approval_required": True,
        },
        "items": rows,
    }


def rebuild_index(root: Path) -> list[dict[str, Any]]:
    payload = build_index_payload(root)
    write_json(root / "freezer" / "index" / "build_priority.json", payload)
    return payload["items"]


def semantic(payload: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(payload))
    value.pop("generated_at", None)
    return value


def verify_assessments(root: Path) -> list[str]:
    errors = verify_histories(root)
    path = root / "freezer" / "index" / "build_priority.json"
    if not path.exists():
        errors.append("missing build priority index")
    else:
        try:
            if semantic(load_json(path)) != semantic(build_index_payload(root)):
                errors.append("stale build priority index; run: python -m freezer.build_assessment reindex")
        except BuildAssessmentError as exc:
            errors.append(str(exc))
    return list(dict.fromkeys(errors))


def gate_payload(root: Path, item_id: str) -> dict[str, Any]:
    item = load_current_item(root, item_id)
    state = assessment_state(root, item)
    record = state["assessment"]
    recommendation = record["derived"]["recommendation"] if record else None
    try:
        from freezer.preflight import PreflightError, preflight_state
    except ImportError as exc:
        preflight = f"INVALID: {exc}"
    else:
        try:
            preflight = preflight_state(root, item)["state"]
        except PreflightError as exc:
            preflight = f"INVALID: {exc}"
    ready = (
        state["state"] == "CURRENT" and recommendation == "BUILD_NOW" and preflight == "PASS"
        and item.get("build_authority") == "APPROVED"
        and item.get("status") in {"READY", "SELECTED", "IN_PROGRESS"}
    )
    return {
        "item_id": item_id, "item_version": item["version"], "status": item["status"],
        "assessment_state": state["state"], "recommendation": recommendation,
        "decision_score": record["derived"]["decision_score"] if record else None,
        "preflight_state": preflight, "build_authority": item.get("build_authority"),
        "selection_ready": ready,
    }
