from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .models import (
    ACTIVE_STATUSES,
    AUTHORITY,
    SCHEMA_VERSION,
    LoopCoreError,
    canonical_json,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_evaluation,
    validate_optional_records,
)

DEFAULT_INPUTS = (
    "asset_manifest/index/assets.json",
    "freezer/index/build_priority.json",
    "freezer/index/items.json",
)
EXECUTION_REQUIRED = {
    "skill_id",
    "drive_id",
    "pack_id",
    "trigger",
    "result",
    "timestamp",
}
EVIDENCE_REQUIRED = {
    "evidence_id",
    "source_type",
    "source_ref",
    "retrieved_at",
}


def _validate_items_index(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise LoopCoreError("freezer items index must contain an items array")
    items = data["items"]
    if data.get("count") != len(items):
        raise LoopCoreError("freezer items index count mismatch")
    seen: set[str] = set()
    required = {
        "item_id",
        "version",
        "title",
        "status",
        "build_authority",
        "preflight_state",
    }
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise LoopCoreError(f"freezer items[{index}] must be an object")
        missing = sorted(required - item.keys())
        if missing:
            raise LoopCoreError(
                f"freezer items[{index}] missing fields: {', '.join(missing)}"
            )
        item_id = item["item_id"]
        if not isinstance(item_id, str) or item_id in seen:
            raise LoopCoreError("freezer item IDs must be unique strings")
        seen.add(item_id)
    return items


def _validate_build_index(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise LoopCoreError("build priority index must contain an items array")
    rows = data["items"]
    if data.get("count") != len(rows):
        raise LoopCoreError("build priority index count mismatch")
    required = {
        "item_id",
        "status",
        "recommendation",
        "build_authority",
        "ranking_score",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise LoopCoreError(f"build priority items[{index}] must be an object")
        missing = sorted(required - row.keys())
        if missing:
            raise LoopCoreError(
                f"build priority items[{index}] missing fields: {', '.join(missing)}"
            )
    return rows


def _validate_assets_index(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("assets"), list):
        raise LoopCoreError("asset index must contain an assets array")
    assets = data["assets"]
    if data.get("count") != len(assets):
        raise LoopCoreError("asset index count mismatch")
    seen: set[str] = set()
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict) or not isinstance(asset.get("asset_id"), str):
            raise LoopCoreError(f"assets[{index}] requires asset_id")
        if asset["asset_id"] in seen:
            raise LoopCoreError("asset IDs must be unique")
        seen.add(asset["asset_id"])
    return assets


def _derive_as_of(documents: list[dict[str, Any]], explicit: str | None) -> str:
    if explicit:
        return explicit
    values = [
        document.get("generated_at")
        for document in documents
        if isinstance(document.get("generated_at"), str)
    ]
    return max(values) if values else "UNSPECIFIED"


def _candidate_recommendation(
    build_rows: list[dict[str, Any]],
    items_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str | None, str, str, str, list[str], str, str]:
    for row in build_rows:
        item_id = row["item_id"]
        item = items_by_id.get(item_id)
        if item is None:
            raise LoopCoreError(f"build candidate missing from item index: {item_id}")
        if item["status"] in {"COMPLETED", "REJECTED"}:
            continue
        recommendation = row["recommendation"]
        preflight = item.get("preflight_state", "MISSING")
        authority = item.get("build_authority")
        if recommendation == "ASSESSMENT_REQUIRED":
            return (
                "RUN_BUILD_ASSESSMENT",
                item_id,
                f"{item_id} is the highest-ranked incomplete candidate and has no current Build Assessment.",
                "A current assessment is recorded with a deterministic recommendation.",
                "Keep the item FROZEN and inspect missing GitHub evidence.",
                ["assessment inputs are incomplete", "license status is unknown"],
                "BLOCKED",
                "WARNING",
            )
        if recommendation == "BUILD_NOW":
            if authority != "APPROVED":
                return (
                    "REQUEST_HUMAN_APPROVAL",
                    item_id,
                    f"{item_id} is BUILD_NOW but lacks explicit human build authority.",
                    "The operator records APPROVED authority without starting implementation.",
                    "Leave the item FROZEN.",
                    ["approval is denied", "scope changes before approval"],
                    "NORMAL",
                    "NORMAL",
                )
            if preflight != "PASS":
                return (
                    "RUN_IMPLEMENTATION_PREFLIGHT",
                    item_id,
                    f"{item_id} is assessed and approved but its current Preflight state is {preflight}.",
                    "A current PASS, DECOMPOSE_REQUIRED, BLOCKED, or RESEARCH_REQUIRED Preflight is recorded.",
                    "Leave the item out of SELECTED and IN_PROGRESS.",
                    [
                        "ground survey finds hidden dependencies",
                        "scope is not reversible",
                    ],
                    "BLOCKED",
                    "WARNING",
                )
            return (
                "REVIEW_FOR_SELECTION",
                item_id,
                f"{item_id} is BUILD_NOW, APPROVED, and has a current PASS Preflight; selection still requires an operator decision.",
                "The operator either selects exactly one item or records a reason to defer.",
                "Keep the item FROZEN until a selection decision is recorded.",
                ["another item becomes active", "input indexes become stale"],
                "NORMAL",
                "NORMAL",
            )
        return (
            "REVIEW_DEFERRED_CANDIDATE",
            item_id,
            f"{item_id} is the highest-ranked incomplete candidate with recommendation {recommendation}.",
            "The candidate is explicitly kept, researched, decomposed, or rejected.",
            "Run a fresh assessment when material inputs change.",
            ["recommendation becomes stale", "dependency state changes"],
            "STALL",
            "NORMAL",
        )
    return (
        "CAPTURE_NEW_CANDIDATE",
        None,
        "No incomplete candidate is present in the build-priority index.",
        "A new governed candidate is captured or the queue is intentionally left empty.",
        "Verify that completed/rejected filtering is correct.",
        ["derived indexes are stale"],
        "STALL",
        "WARNING",
    )


def evaluate(
    root: Path,
    *,
    execution_records_path: Path | None = None,
    evidence_refs_path: Path | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    paths = [root / relative for relative in DEFAULT_INPUTS]
    documents = [load_json(path) for path in paths]
    assets = _validate_assets_index(documents[0])
    build_rows = _validate_build_index(documents[1])
    items = _validate_items_index(documents[2])
    items_by_id = {item["item_id"]: item for item in items}

    optional_paths: list[Path] = []
    unverified: list[str] = []
    assumed: list[str] = []
    if execution_records_path is not None:
        path = execution_records_path.resolve()
        records = validate_optional_records(
            load_json(path),
            EXECUTION_REQUIRED,
            "execution records",
        )
        optional_paths.append(path)
        unverified.append(
            f"{len(records)} execution record(s) passed shape validation; full evidence linkage is undefined"
        )
    else:
        assumed.append("no execution-record feed was supplied")
    if evidence_refs_path is not None:
        path = evidence_refs_path.resolve()
        records = validate_optional_records(
            load_json(path),
            EVIDENCE_REQUIRED,
            "evidence references",
        )
        optional_paths.append(path)
        unverified.append(
            f"{len(records)} evidence reference(s) passed shape validation; retrieval was not independently verified"
        )
    else:
        assumed.append("no evidence-reference feed was supplied")

    input_paths = paths + optional_paths
    input_rows = []
    for path in sorted(input_paths, key=lambda candidate: candidate.as_posix()):
        try:
            display = path.relative_to(root).as_posix()
        except ValueError:
            display = path.as_posix()
        input_rows.append({"path": display, "sha256": sha256_file(path)})

    active = sorted(
        item["item_id"]
        for item in items
        if item["status"] in ACTIVE_STATUSES
    )
    if len(active) > 1:
        action = "REDUCE_WIP"
        item_id = None
        why = (
            f"{len(active)} items are active, exceeding the WIP=1 governance boundary: "
            f"{', '.join(active)}."
        )
        success = "Exactly one or zero items remains SELECTED/IN_PROGRESS."
        fallback = "Pause all active items and request operator review."
        stops = [
            "active item ownership is unclear",
            "a rollback boundary is missing",
        ]
        state, audit = "OVERLOAD", "CRITICAL"
    elif len(active) == 1:
        item_id = active[0]
        item = items_by_id[item_id]
        if item["status"] == "IN_PROGRESS":
            action = "CONTINUE_OR_VERIFY_ACTIVE_ITEM"
            success = (
                "The active item reaches a verified checkpoint or is explicitly paused."
            )
        else:
            action = "REVIEW_SELECTED_ITEM"
            success = (
                "The selected item is either started under existing gates or returned to FROZEN."
            )
        why = (
            f"{item_id} is the only active item with status {item['status']}; "
            "no second item may be started."
        )
        fallback = "Pause the item and preserve its current checkpoint."
        stops = [
            "Preflight becomes stale",
            "build authority is revoked",
            "WIP rises above one",
        ]
        state, audit = "FOCUS", "NORMAL"
    else:
        (
            action,
            item_id,
            why,
            success,
            fallback,
            stops,
            state,
            audit,
        ) = _candidate_recommendation(build_rows, items_by_id)

    verified = [
        f"validated {len(items)} current FREEZER item index entries",
        f"validated {len(build_rows)} build-priority entries",
        f"validated {len(assets)} Asset Manifest entries",
        f"observed WIP count {len(active)} from governed item statuses",
    ]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": "0" * 64,
        "as_of": _derive_as_of(documents, as_of),
        "authority": AUTHORITY,
        "implementation_authority_granted": False,
        "inputs": input_rows,
        "wip": {"count": len(active), "active_item_ids": active},
        "state": state,
        "audit_level": audit,
        "evidence": {
            "verified": verified,
            "unverified": unverified,
            "assumed": assumed,
        },
        "recommendation": {
            "action": action,
            "item_id": item_id,
            "why": why,
            "success_condition": success,
            "fallback": fallback,
            "stop_conditions": stops,
        },
    }
    material = copy.deepcopy(payload)
    material.pop("evaluation_id")
    payload["evaluation_id"] = sha256_bytes(
        canonical_json(material).encode("utf-8")
    )
    validate_evaluation(payload)
    return payload
