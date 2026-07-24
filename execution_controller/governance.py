from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import ControllerError, load_json

DEFAULT_INDEX_PATHS = (
    "asset_manifest/index/assets.json",
    "freezer/index/build_priority.json",
    "freezer/index/items.json",
)

def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_pointer_target(root: Path, pointer_path: Path, expected_path_field: str = "path") -> tuple[dict[str, Any], Path, dict[str, Any]]:
    pointer = load_json(pointer_path)
    relative = pointer.get(expected_path_field)
    if not isinstance(relative, str) or not relative:
        raise ControllerError(f"invalid pointer path: {pointer_path}")
    target = (root / relative).resolve()
    if root not in target.parents:
        raise ControllerError(f"governed pointer escaped repository root: {pointer_path}")
    record = load_json(target)
    return pointer, target, record


def _validate_index_count(document: Any, array_field: str, label: str) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or not isinstance(document.get(array_field), list):
        raise ControllerError(f"{label} must contain {array_field}")
    rows = document[array_field]
    if document.get("count") != len(rows):
        raise ControllerError(f"{label} count mismatch")
    if any(not isinstance(row, dict) for row in rows):
        raise ControllerError(f"{label} rows must be objects")
    return rows


def _unique_by(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise ControllerError(f"{label} row missing {key}")
        if value in result:
            raise ControllerError(f"{label} duplicate {key}: {value}")
        result[value] = row
    return result


def _governed_state(root: Path, authorization: dict[str, Any]) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    assets_path = root / DEFAULT_INDEX_PATHS[0]
    build_path = root / DEFAULT_INDEX_PATHS[1]
    items_path = root / DEFAULT_INDEX_PATHS[2]
    assets_doc = load_json(assets_path)
    build_doc = load_json(build_path)
    items_doc = load_json(items_path)
    _validate_index_count(assets_doc, "assets", "asset index")
    build_rows = _validate_index_count(build_doc, "items", "build-priority index")
    item_rows = _validate_index_count(items_doc, "items", "FREEZER item index")
    builds = _unique_by(build_rows, "item_id", "build-priority index")
    items = _unique_by(item_rows, "item_id", "FREEZER item index")

    item_id = authorization["item_id"]
    item_row = items.get(item_id)
    build_row = builds.get(item_id)
    if item_row is None or build_row is None:
        raise ControllerError(f"{item_id}: missing from governed indexes")

    active = sorted(
        row["item_id"]
        for row in item_rows
        if row.get("status") in {"SELECTED", "IN_PROGRESS"}
    )
    if active != [item_id]:
        raise ControllerError(f"WIP=1 gate failed: active={active!r}")
    if item_row.get("version") != authorization["item_version"]:
        raise ControllerError("authorization item version does not match current index")
    if item_row.get("status") not in {"SELECTED", "IN_PROGRESS"}:
        raise ControllerError("target item is not selected or in progress")
    if item_row.get("build_authority") != "APPROVED":
        raise ControllerError("target item lacks APPROVED build authority")
    if item_row.get("preflight_state") != "PASS":
        raise ControllerError("target item lacks current PASS Preflight")
    if build_row.get("version") != authorization["item_version"]:
        raise ControllerError("build-priority item version mismatch")
    if build_row.get("status") != item_row.get("status"):
        raise ControllerError("build-priority item status mismatch")
    if build_row.get("build_authority") != "APPROVED":
        raise ControllerError("build-priority authority mismatch")
    if build_row.get("assessment_state") != "CURRENT":
        raise ControllerError("Build Assessment is missing or stale")
    if build_row.get("recommendation") != "BUILD_NOW":
        raise ControllerError("Build Assessment does not recommend BUILD_NOW")

    item_pointer_path = root / "freezer" / "items" / item_id / "current.json"
    item_pointer, item_record_path, item_record = _load_pointer_target(root, item_pointer_path)
    if item_pointer.get("current_version") != authorization["item_version"]:
        raise ControllerError("item current pointer version mismatch")
    if item_record.get("item_id") != item_id or item_record.get("version") != authorization["item_version"]:
        raise ControllerError("item record version mismatch")
    if item_record.get("status") != item_row.get("status") or item_record.get("build_authority") != "APPROVED":
        raise ControllerError("item record disagrees with current item index")

    assessment_pointer_path = root / "freezer" / "assessments" / item_id / "current.json"
    assessment_pointer, assessment_record_path, assessment_record = _load_pointer_target(root, assessment_pointer_path)
    if assessment_pointer.get("recommendation") != "BUILD_NOW":
        raise ControllerError("assessment pointer is not BUILD_NOW")
    if assessment_record.get("item_id") != item_id:
        raise ControllerError("assessment record item mismatch")
    if assessment_record.get("derived", {}).get("recommendation") != "BUILD_NOW":
        raise ControllerError("assessment record is not BUILD_NOW")
    if assessment_pointer.get("assessment_id") != assessment_record.get("assessment_id"):
        raise ControllerError("assessment pointer ID mismatch")
    if assessment_pointer.get("item_fingerprint") != assessment_record.get("item_fingerprint"):
        raise ControllerError("assessment pointer fingerprint mismatch")

    preflight_pointer_path = root / "freezer" / "preflights" / item_id / "current.json"
    preflight_pointer, preflight_record_path, preflight_record = _load_pointer_target(root, preflight_pointer_path)
    if preflight_pointer.get("outcome") != "PASS":
        raise ControllerError("Preflight pointer is not PASS")
    if preflight_record.get("item_id") != item_id or preflight_record.get("outcome") != "PASS":
        raise ControllerError("Preflight record is not current PASS")
    if preflight_pointer.get("item_fingerprint") != preflight_record.get("item_fingerprint"):
        raise ControllerError("Preflight pointer fingerprint mismatch")

    paths = [
        assets_path,
        build_path,
        items_path,
        item_pointer_path,
        item_record_path,
        assessment_pointer_path,
        assessment_record_path,
        preflight_pointer_path,
        preflight_record_path,
    ]
    evidence = {
        "wip_count": 1,
        "active_item_ids": active,
        "item_status": item_row["status"],
        "build_authority": item_row["build_authority"],
        "assessment_state": build_row["assessment_state"],
        "assessment_recommendation": build_row["recommendation"],
        "preflight_state": item_row["preflight_state"],
        "human_authorization_supplied": True,
    }
    return evidence, paths
