#!/usr/bin/env python3
"""Implementation preflight gate for RTS FREEZER candidates.

A candidate must have a current PASS preflight whose fingerprint still matches
its substantive plan before it may move to SELECTED or IN_PROGRESS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
ITEM_ID_PREFIX = "RTS-FRZ-"
OUTCOMES = {"PASS", "DECOMPOSE_REQUIRED", "BLOCKED", "RESEARCH_REQUIRED"}
VOLATILE_ITEM_FIELDS = {
    "version",
    "status",
    "build_authority",
    "created_at",
    "updated_at",
    "supersedes",
}
REQUIRED_ASSESSMENT_FIELDS = {
    "affected_boundaries",
    "existing_assumptions",
    "data_migration",
    "external_interfaces",
    "approval_changes",
    "public_documents",
    "regression_tests",
    "hidden_dependencies",
    "rollback_boundary",
    "completion_conditions",
    "decomposition",
    "risks",
}


class PreflightError(RuntimeError):
    """Raised for invalid or stale preflight records."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreflightError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PreflightError(f"invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def item_current_path(root: Path, item_id: str) -> Path:
    return root / "freezer" / "items" / item_id / "current.json"


def load_current_item(root: Path, item_id: str) -> dict[str, Any]:
    pointer = load_json(item_current_path(root, item_id))
    version = pointer.get("current_version")
    if pointer.get("item_id") != item_id or not isinstance(version, int):
        raise PreflightError(f"{item_id}: invalid item current pointer")
    return load_json(root / "freezer" / "items" / item_id / f"v{version:03d}.json")


def canonical_plan(item: dict[str, Any]) -> dict[str, Any]:
    """Return the substantive plan used to invalidate stale preflights."""

    return {
        key: value
        for key, value in item.items()
        if key not in VOLATILE_ITEM_FIELDS
    }


def item_fingerprint(item: dict[str, Any]) -> str:
    payload = json.dumps(
        canonical_plan(item),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def preflight_root(root: Path, item_id: str) -> Path:
    return root / "freezer" / "preflights" / item_id


def preflight_path(root: Path, item_id: str, version: int) -> Path:
    return preflight_root(root, item_id) / f"pf{version:03d}.json"


def preflight_current_path(root: Path, item_id: str) -> Path:
    return preflight_root(root, item_id) / "current.json"


def all_preflight_item_ids(root: Path) -> list[str]:
    base = root / "freezer" / "preflights"
    if not base.exists():
        return []
    return sorted(
        path.name
        for path in base.iterdir()
        if path.is_dir() and path.name.startswith(ITEM_ID_PREFIX)
    )


def load_current_preflight(root: Path, item_id: str) -> dict[str, Any]:
    pointer = load_json(preflight_current_path(root, item_id))
    version = pointer.get("current_preflight_version")
    if pointer.get("item_id") != item_id or not isinstance(version, int):
        raise PreflightError(f"{item_id}: invalid preflight current pointer")
    return load_json(preflight_path(root, item_id, version))


def validate_string_list(record: dict[str, Any], field: str) -> None:
    value = record[field]
    if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
        raise PreflightError(f"{record.get('item_id', '<unknown>')}: {field} must be a string list")


def validate_preflight(record: dict[str, Any]) -> None:
    required = {
        "preflight_id",
        "item_id",
        "preflight_version",
        "item_version_snapshot",
        "item_fingerprint",
        "outcome",
        "assessor",
        "rationale",
        "created_at",
        *REQUIRED_ASSESSMENT_FIELDS,
    }
    missing = sorted(required - record.keys())
    if missing:
        raise PreflightError(
            f"{record.get('item_id', '<unknown>')}: missing preflight fields: {', '.join(missing)}"
        )

    item_id = record["item_id"]
    if not isinstance(item_id, str) or not item_id.startswith(ITEM_ID_PREFIX):
        raise PreflightError(f"invalid preflight item_id: {item_id!r}")
    if record["outcome"] not in OUTCOMES:
        raise PreflightError(f"{item_id}: invalid preflight outcome={record['outcome']!r}")
    if not isinstance(record["preflight_version"], int) or record["preflight_version"] < 1:
        raise PreflightError(f"{item_id}: invalid preflight_version")
    if not isinstance(record["item_version_snapshot"], int) or record["item_version_snapshot"] < 1:
        raise PreflightError(f"{item_id}: invalid item_version_snapshot")
    fingerprint = record["item_fingerprint"]
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise PreflightError(f"{item_id}: invalid item_fingerprint")
    if not isinstance(record["assessor"], str) or not record["assessor"].strip():
        raise PreflightError(f"{item_id}: assessor is required")
    if not isinstance(record["rationale"], str) or not record["rationale"].strip():
        raise PreflightError(f"{item_id}: rationale is required")

    for field in (
        "affected_boundaries",
        "existing_assumptions",
        "external_interfaces",
        "approval_changes",
        "public_documents",
        "regression_tests",
        "hidden_dependencies",
        "completion_conditions",
        "risks",
    ):
        validate_string_list(record, field)

    migration = record["data_migration"]
    if not isinstance(migration, dict) or not isinstance(migration.get("required"), bool):
        raise PreflightError(f"{item_id}: data_migration requires boolean required")
    if not isinstance(migration.get("notes", ""), str):
        raise PreflightError(f"{item_id}: data_migration notes must be a string")

    decomposition = record["decomposition"]
    if not isinstance(decomposition, dict) or not isinstance(decomposition.get("required"), bool):
        raise PreflightError(f"{item_id}: decomposition requires boolean required")
    children = decomposition.get("child_candidates", [])
    if not isinstance(children, list) or any(not isinstance(entry, str) for entry in children):
        raise PreflightError(f"{item_id}: decomposition child_candidates must be a string list")
    if decomposition["required"] and not children:
        raise PreflightError(f"{item_id}: required decomposition must name child candidates")

    if not isinstance(record["rollback_boundary"], str) or not record["rollback_boundary"].strip():
        raise PreflightError(f"{item_id}: rollback_boundary is required")

    if record["outcome"] == "PASS":
        if decomposition["required"]:
            raise PreflightError(f"{item_id}: PASS cannot require decomposition")
        if not record["affected_boundaries"]:
            raise PreflightError(f"{item_id}: PASS requires affected_boundaries")
        if not record["regression_tests"]:
            raise PreflightError(f"{item_id}: PASS requires regression_tests")
        if not record["completion_conditions"]:
            raise PreflightError(f"{item_id}: PASS requires completion_conditions")
    elif record["outcome"] == "DECOMPOSE_REQUIRED" and not decomposition["required"]:
        raise PreflightError(f"{item_id}: DECOMPOSE_REQUIRED requires decomposition.required=true")


def create_preflight(root: Path, item_id: str, source: Path) -> dict[str, Any]:
    item = load_current_item(root, item_id)
    raw = load_json(source)
    pointer_path = preflight_current_path(root, item_id)
    if pointer_path.exists():
        current = load_json(pointer_path)
        version = int(current["current_preflight_version"]) + 1
    else:
        version = 1

    record = dict(raw)
    record.update(
        {
            "preflight_id": f"RTS-PF-{item_id.removeprefix(ITEM_ID_PREFIX)}-{version:03d}",
            "item_id": item_id,
            "preflight_version": version,
            "item_version_snapshot": item["version"],
            "item_fingerprint": item_fingerprint(item),
            "created_at": utc_now(),
        }
    )
    validate_preflight(record)

    destination = preflight_path(root, item_id, version)
    if destination.exists():
        raise PreflightError(f"refusing to overwrite immutable preflight: {destination}")
    write_json(destination, record)
    write_json(
        pointer_path,
        {
            "item_id": item_id,
            "current_preflight_version": version,
            "path": destination.relative_to(root).as_posix(),
            "outcome": record["outcome"],
            "item_fingerprint": record["item_fingerprint"],
            "updated_at": record["created_at"],
        },
    )
    return record


def preflight_state(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    pointer = preflight_current_path(root, item["item_id"])
    if not pointer.exists():
        return {"state": "MISSING", "preflight": None}
    record = load_current_preflight(root, item["item_id"])
    validate_preflight(record)
    if record["item_fingerprint"] != item_fingerprint(item):
        return {"state": "STALE", "preflight": record}
    return {"state": record["outcome"], "preflight": record}


def require_passing_preflight(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    state = preflight_state(root, item)
    if state["state"] != "PASS":
        raise PreflightError(
            f"{item['item_id']}: SELECTED/IN_PROGRESS requires a current PASS preflight; "
            f"state={state['state']}"
        )
    return state["preflight"]


def verify_preflights(root: Path) -> list[str]:
    errors: list[str] = []
    for item_id in all_preflight_item_ids(root):
        try:
            item = load_current_item(root, item_id)
            pointer = load_json(preflight_current_path(root, item_id))
            current = load_current_preflight(root, item_id)
            validate_preflight(current)
            if current["preflight_version"] != pointer["current_preflight_version"]:
                errors.append(f"{item_id}: preflight pointer/version mismatch")
            versions = sorted(preflight_root(root, item_id).glob("pf*.json"))
            actual = [int(path.stem[2:]) for path in versions]
            expected = list(range(1, current["preflight_version"] + 1))
            if actual != expected:
                errors.append(
                    f"{item_id}: non-contiguous preflight history; expected={expected}, actual={actual}"
                )
            if item["status"] in {"SELECTED", "IN_PROGRESS"}:
                require_passing_preflight(root, item)
        except PreflightError as exc:
            errors.append(str(exc))
    return errors


def command_show(root: Path, item_id: str) -> None:
    print(json.dumps(load_current_preflight(root, item_id), ensure_ascii=False, indent=2))


def command_history(root: Path, item_id: str) -> None:
    directory = preflight_root(root, item_id)
    if not directory.exists():
        raise PreflightError(f"{item_id}: no preflight history")
    for path in sorted(directory.glob("pf*.json")):
        record = load_json(path)
        print(
            f"{path.stem}\t{record['created_at']}\t{record['outcome']}\t"
            f"item-v{record['item_version_snapshot']:03d}"
        )


def command_status(root: Path, item_id: str) -> None:
    item = load_current_item(root, item_id)
    state = preflight_state(root, item)
    record = state["preflight"]
    payload = {
        "item_id": item_id,
        "item_version": item["version"],
        "state": state["state"],
        "preflight_id": record["preflight_id"] if record else None,
        "selection_ready": state["state"] == "PASS",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="append an immutable implementation preflight")
    create.add_argument("item_id")
    create.add_argument("--input", type=Path, required=True)

    show = sub.add_parser("show", help="show the latest preflight")
    show.add_argument("item_id")

    history = sub.add_parser("history", help="show preflight history")
    history.add_argument("item_id")

    status = sub.add_parser("status", help="show whether the current item plan may be selected")
    status.add_argument("item_id")

    sub.add_parser("verify", help="validate all preflight records")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "create":
            record = create_preflight(root, args.item_id, args.input.resolve())
            print(record["preflight_id"])
        elif args.command == "show":
            command_show(root, args.item_id)
        elif args.command == "history":
            command_history(root, args.item_id)
        elif args.command == "status":
            command_status(root, args.item_id)
        elif args.command == "verify":
            errors = verify_preflights(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("FREEZER preflight verification passed")
        else:
            raise PreflightError(f"unknown command: {args.command}")
    except PreflightError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
