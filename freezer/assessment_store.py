"""Append-only storage and lifecycle checks for FREEZER build assessments."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from freezer.assessment_core import (
    BuildAssessmentError, ITEM_ID_PREFIX, all_item_ids, derive, item_fingerprint,
    load_current_item, load_json, utc_now, validate_input, validate_record, write_json,
)


def assessment_root(root: Path, item_id: str) -> Path:
    return root / "freezer" / "assessments" / item_id


def assessment_path(root: Path, item_id: str, version: int) -> Path:
    return assessment_root(root, item_id) / f"ba{version:03d}.json"


def assessment_current_path(root: Path, item_id: str) -> Path:
    return assessment_root(root, item_id) / "current.json"


def all_assessment_item_ids(root: Path) -> list[str]:
    base = root / "freezer" / "assessments"
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and p.name.startswith(ITEM_ID_PREFIX))


def load_current_assessment(root: Path, item_id: str) -> dict[str, Any]:
    pointer = load_json(assessment_current_path(root, item_id))
    version = pointer.get("current_assessment_version")
    if pointer.get("item_id") != item_id or not isinstance(version, int):
        raise BuildAssessmentError(f"{item_id}: invalid assessment current pointer")
    path = assessment_path(root, item_id, version)
    record = load_json(path)
    validate_record(record)
    if record["item_id"] != item_id or record["assessment_version"] != version:
        raise BuildAssessmentError(f"{item_id}: assessment pointer/version mismatch")
    if pointer.get("path") != path.relative_to(root).as_posix():
        raise BuildAssessmentError(f"{item_id}: assessment pointer path mismatch")
    if pointer.get("assessment_id") != record["assessment_id"]:
        raise BuildAssessmentError(f"{item_id}: assessment pointer id mismatch")
    if pointer.get("recommendation") != record["derived"]["recommendation"]:
        raise BuildAssessmentError(f"{item_id}: assessment pointer recommendation mismatch")
    if pointer.get("item_fingerprint") != record["item_fingerprint"]:
        raise BuildAssessmentError(f"{item_id}: assessment pointer fingerprint mismatch")
    return record


def create_assessment(root: Path, item_id: str, source: Path) -> dict[str, Any]:
    item = load_current_item(root, item_id)
    raw = load_json(source)
    validate_input(raw)
    pointer_path = assessment_current_path(root, item_id)
    if pointer_path.exists():
        version = load_json(pointer_path).get("current_assessment_version")
        if not isinstance(version, int) or version < 1:
            raise BuildAssessmentError(f"{item_id}: invalid current assessment pointer")
        version += 1
    else:
        version = 1
    record = dict(raw)
    record.update(
        {
            "assessment_id": f"RTS-BA-{item_id.removeprefix(ITEM_ID_PREFIX)}-{version:03d}",
            "item_id": item_id,
            "assessment_version": version,
            "item_version_snapshot": item["version"],
            "item_fingerprint": item_fingerprint(item),
            "derived": derive(raw),
            "created_at": utc_now(),
        }
    )
    validate_record(record)
    destination = assessment_path(root, item_id, version)
    if destination.exists():
        raise BuildAssessmentError(f"refusing to overwrite immutable assessment: {destination}")
    write_json(destination, record)
    write_json(
        pointer_path,
        {
            "item_id": item_id,
            "current_assessment_version": version,
            "path": destination.relative_to(root).as_posix(),
            "assessment_id": record["assessment_id"],
            "recommendation": record["derived"]["recommendation"],
            "decision_score": record["derived"]["decision_score"],
            "item_fingerprint": record["item_fingerprint"],
            "updated_at": record["created_at"],
        },
    )
    return record


def assessment_state(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    pointer = assessment_current_path(root, item["item_id"])
    if not pointer.exists():
        return {"state": "MISSING", "assessment": None}
    record = load_current_assessment(root, item["item_id"])
    if record["item_fingerprint"] != item_fingerprint(item):
        return {"state": "STALE", "assessment": record}
    return {"state": "CURRENT", "assessment": record}


def require_build_now_assessment(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    state = assessment_state(root, item)
    if state["state"] != "CURRENT":
        raise BuildAssessmentError(
            f"{item['item_id']}: active work requires a current build assessment; state={state['state']}"
        )
    record = state["assessment"]
    recommendation = record["derived"]["recommendation"]
    if recommendation != "BUILD_NOW":
        raise BuildAssessmentError(
            f"{item['item_id']}: active work requires recommendation=BUILD_NOW; recommendation={recommendation}"
        )
    return record


def verify_histories(root: Path) -> list[str]:
    errors: list[str] = []
    for item_id in all_assessment_item_ids(root):
        try:
            load_current_item(root, item_id)
            pointer = load_json(assessment_current_path(root, item_id))
            current = load_current_assessment(root, item_id)
            versions = sorted(assessment_root(root, item_id).glob("ba*.json"))
            actual = [int(path.stem[2:]) for path in versions]
            expected = list(range(1, current["assessment_version"] + 1))
            if actual != expected:
                errors.append(
                    f"{item_id}: non-contiguous assessment history; expected={expected}, actual={actual}"
                )
            if pointer.get("current_assessment_version") != current["assessment_version"]:
                errors.append(f"{item_id}: assessment pointer/version mismatch")
            for path in versions:
                validate_record(load_json(path))
        except BuildAssessmentError as exc:
            errors.append(str(exc))
    for item_id in all_item_ids(root):
        try:
            item = load_current_item(root, item_id)
            if item.get("status") in {"SELECTED", "IN_PROGRESS"}:
                require_build_now_assessment(root, item)
        except BuildAssessmentError as exc:
            errors.append(str(exc))
    return list(dict.fromkeys(errors))
