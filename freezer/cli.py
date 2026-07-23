#!/usr/bin/env python3
"""RTS FREEZER v1: versioned deferred-work registry and priority queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from freezer.preflight import (
    PreflightError,
    preflight_state,
    require_passing_preflight,
    verify_preflights,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
ITEM_ID_PREFIX = "RTS-FRZ-"
ITEM_TYPES = {"feature", "research", "product", "architecture", "process", "risk"}
ITEM_STATUSES = {
    "CAPTURED",
    "NORMALIZED",
    "SCORED",
    "READY",
    "SELECTED",
    "IN_PROGRESS",
    "VERIFIED",
    "COMPLETED",
    "BLOCKED",
    "FROZEN",
    "RESEARCH_REQUIRED",
    "REJECTED",
}
BUILD_AUTHORITIES = {"NOT_APPROVED", "APPROVED"}
RECALL_MODES = {"MANUAL", "CONDITION_WATCH"}


class FreezerError(RuntimeError):
    """Raised for invalid FREEZER operations."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FreezerError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FreezerError(f"invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def deep_merge(base: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge revision fields without discarding nested score data."""

    merged = dict(base)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def config_path(root: Path) -> Path:
    return root / "freezer" / "config.json"


def items_root(root: Path) -> Path:
    return root / "freezer" / "items"


def load_config(root: Path) -> dict[str, Any]:
    return load_json(config_path(root))


def validate_item(item: dict[str, Any], config: dict[str, Any]) -> None:
    required = {
        "item_id",
        "version",
        "title",
        "type",
        "status",
        "summary",
        "original_problem",
        "why_it_matters",
        "reason_frozen",
        "preserved_value",
        "priority",
        "trigger_conditions",
        "negative_triggers",
        "dependencies",
        "source_refs",
        "possible_destinations",
        "estimated_hours",
        "tags",
        "build_authority",
        "recall_mode",
        "created_at",
        "updated_at",
    }
    missing = sorted(required - item.keys())
    if missing:
        raise FreezerError(
            f"{item.get('item_id', '<unknown>')}: missing fields: {', '.join(missing)}"
        )

    item_id = item["item_id"]
    if not isinstance(item_id, str) or not item_id.startswith(ITEM_ID_PREFIX):
        raise FreezerError(f"invalid item_id: {item_id!r}")
    suffix = item_id.removeprefix(ITEM_ID_PREFIX)
    if len(suffix) != 6 or not suffix.isdigit():
        raise FreezerError(f"invalid item_id: {item_id!r}")
    if not isinstance(item["version"], int) or item["version"] < 1:
        raise FreezerError(f"{item_id}: version must be a positive integer")

    enum_checks = {
        "type": ITEM_TYPES,
        "status": ITEM_STATUSES,
        "build_authority": BUILD_AUTHORITIES,
        "recall_mode": RECALL_MODES,
    }
    for field, allowed in enum_checks.items():
        if item[field] not in allowed:
            raise FreezerError(
                f"{item_id}: invalid {field}={item[field]!r}; allowed={sorted(allowed)}"
            )

    priority = item["priority"]
    if not isinstance(priority, dict):
        raise FreezerError(f"{item_id}: priority must be an object")
    score_min = config["score_scale"]["minimum"]
    score_max = config["score_scale"]["maximum"]
    expected = set(config["score_weights"])
    if set(priority) != expected:
        missing_scores = sorted(expected - set(priority))
        extra_scores = sorted(set(priority) - expected)
        raise FreezerError(
            f"{item_id}: priority fields mismatch; missing={missing_scores}, extra={extra_scores}"
        )
    for name, value in priority.items():
        if not isinstance(value, (int, float)) or not score_min <= value <= score_max:
            raise FreezerError(f"{item_id}: {name} must be between {score_min} and {score_max}")

    hours = item["estimated_hours"]
    if not isinstance(hours, dict) or "minimum" not in hours or "maximum" not in hours:
        raise FreezerError(f"{item_id}: estimated_hours requires minimum and maximum")
    if hours["minimum"] < 0 or hours["maximum"] < hours["minimum"]:
        raise FreezerError(f"{item_id}: invalid estimated_hours range")


def compute_score(item: dict[str, Any], config: dict[str, Any]) -> float:
    """Return a deterministic 0-100 priority score."""

    max_value = config["score_scale"]["maximum"]
    weights = config["score_weights"]
    benefits = set(config["benefit_fields"])
    costs = set(config["cost_fields"])
    numerator = 0.0
    denominator = 0.0
    for name, weight in weights.items():
        raw = float(item["priority"][name])
        if name in benefits:
            contribution = raw
        elif name in costs:
            contribution = max_value - raw
        else:
            raise FreezerError(f"unclassified score field: {name}")
        numerator += contribution * float(weight)
        denominator += max_value * float(weight)
    return round((numerator / denominator) * 100.0, 2) if denominator else 0.0


def version_path(root: Path, item_id: str, version: int) -> Path:
    return items_root(root) / item_id / f"v{version:03d}.json"


def current_path(root: Path, item_id: str) -> Path:
    return items_root(root) / item_id / "current.json"


def all_item_ids(root: Path) -> list[str]:
    base = items_root(root)
    if not base.exists():
        return []
    return sorted(
        path.name
        for path in base.iterdir()
        if path.is_dir() and path.name.startswith(ITEM_ID_PREFIX)
    )


def load_current(root: Path, item_id: str) -> dict[str, Any]:
    pointer = load_json(current_path(root, item_id))
    if pointer.get("item_id") != item_id:
        raise FreezerError(f"{item_id}: current pointer item_id mismatch")
    version = pointer.get("current_version")
    if not isinstance(version, int):
        raise FreezerError(f"{item_id}: invalid current_version")
    return load_json(version_path(root, item_id, version))


def iter_current_items(root: Path) -> Iterable[dict[str, Any]]:
    for item_id in all_item_ids(root):
        yield load_current(root, item_id)


def next_item_id(root: Path) -> str:
    numbers = [
        int(item_id.removeprefix(ITEM_ID_PREFIX))
        for item_id in all_item_ids(root)
    ]
    return f"{ITEM_ID_PREFIX}{(max(numbers, default=0) + 1):06d}"


def prepare_input_item(
    raw: dict[str, Any],
    *,
    item_id: str,
    version: int,
    created_at: str,
) -> dict[str, Any]:
    item = dict(raw)
    item["item_id"] = item_id
    item["version"] = version
    item["created_at"] = created_at
    item["updated_at"] = utc_now()
    item.setdefault("supersedes", None if version == 1 else f"v{version - 1:03d}")
    return item


def validate_runtime_constraints(root: Path, item: dict[str, Any], config: dict[str, Any]) -> None:
    status = item["status"]
    if status in {"SELECTED", "IN_PROGRESS"}:
        if item["build_authority"] != "APPROVED":
            raise FreezerError(
                f"{item['item_id']}: {status} requires build_authority=APPROVED"
            )
        try:
            require_passing_preflight(root, item)
        except PreflightError as exc:
            raise FreezerError(str(exc)) from exc

    if status == "IN_PROGRESS":
        active = [
            existing["item_id"]
            for existing in iter_current_items(root)
            if existing["item_id"] != item["item_id"]
            and existing["status"] == "IN_PROGRESS"
        ]
        if len(active) >= int(config["work_in_progress_limit"]):
            raise FreezerError(
                f"work-in-progress limit reached; active={active}, "
                f"limit={config['work_in_progress_limit']}"
            )


def save_new_version(root: Path, item: dict[str, Any]) -> Path:
    config = load_config(root)
    validate_item(item, config)
    validate_runtime_constraints(root, item, config)
    destination = version_path(root, item["item_id"], item["version"])
    if destination.exists():
        raise FreezerError(f"refusing to overwrite immutable version: {destination}")
    write_json(destination, item)
    write_json(
        current_path(root, item["item_id"]),
        {
            "item_id": item["item_id"],
            "current_version": item["version"],
            "path": destination.relative_to(root).as_posix(),
            "updated_at": item["updated_at"],
        },
    )
    return destination


def add_item(root: Path, source: Path) -> dict[str, Any]:
    raw = load_json(source)
    item_id = raw.get("item_id") or next_item_id(root)
    if current_path(root, item_id).exists():
        raise FreezerError(f"{item_id} already exists; use revise")
    now = utc_now()
    item = prepare_input_item(raw, item_id=item_id, version=1, created_at=now)
    save_new_version(root, item)
    rebuild(root)
    return item


def revise_item(root: Path, item_id: str, source: Path) -> dict[str, Any]:
    current = load_current(root, item_id)
    changes = load_json(source)
    forbidden = {"item_id", "version", "created_at"}
    touched = sorted(forbidden & changes.keys())
    if touched:
        raise FreezerError(f"revision cannot replace immutable fields: {', '.join(touched)}")
    revised = deep_merge(current, changes)
    revised = prepare_input_item(
        revised,
        item_id=item_id,
        version=current["version"] + 1,
        created_at=current["created_at"],
    )
    revised["supersedes"] = f"v{current['version']:03d}"
    save_new_version(root, revised)
    rebuild(root)
    return revised


def index_entry(root: Path, item: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    try:
        gate = preflight_state(root, item)["state"]
    except PreflightError:
        gate = "INVALID"
    return {
        "item_id": item["item_id"],
        "version": item["version"],
        "title": item["title"],
        "type": item["type"],
        "status": item["status"],
        "priority_score": compute_score(item, config),
        "estimated_hours": item["estimated_hours"],
        "tags": item["tags"],
        "build_authority": item["build_authority"],
        "preflight_state": gate,
        "updated_at": item["updated_at"],
    }


def tracked_files(root: Path) -> list[Path]:
    freezer_root = root / "freezer"
    files: list[Path] = []
    for path in freezer_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if relative == "freezer/manifests/manifest.sha256":
            continue
        if relative.startswith("freezer/recall/"):
            continue
        files.append(path)
    return sorted(files)


def rebuild_manifest(root: Path) -> None:
    lines = []
    for path in tracked_files(root):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    manifest = root / "freezer" / "manifests" / "manifest.sha256"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rebuild(root: Path) -> list[dict[str, Any]]:
    config = load_config(root)
    entries: list[dict[str, Any]] = []
    for item in iter_current_items(root):
        validate_item(item, config)
        entries.append(index_entry(root, item, config))

    by_id = sorted(entries, key=lambda row: row["item_id"])
    rankable_statuses = set(config["rankable_statuses"])
    by_priority = sorted(
        (row for row in entries if row["status"] in rankable_statuses),
        key=lambda row: (-row["priority_score"], row["item_id"]),
    )
    index_dir = root / "freezer" / "index"
    write_json(
        index_dir / "items.json",
        {"generated_at": utc_now(), "count": len(by_id), "items": by_id},
    )
    write_json(
        index_dir / "priority.json",
        {
            "generated_at": utc_now(),
            "count": len(by_priority),
            "policy": {
                "work_in_progress_limit": config["work_in_progress_limit"],
                "human_approval_required": config["selection_policy"]["human_approval_required"],
                "implementation_preflight_required": True,
                "auto_start": config["selection_policy"]["auto_start"],
            },
            "items": by_priority,
        },
    )
    rebuild_manifest(root)
    return by_priority


def verify_manifest(root: Path) -> list[str]:
    manifest = root / "freezer" / "manifests" / "manifest.sha256"
    if not manifest.exists():
        return ["missing manifest"]
    errors: list[str] = []
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        expected[relative] = digest

    current_paths = {path.relative_to(root).as_posix(): path for path in tracked_files(root)}
    if set(expected) != set(current_paths):
        missing = sorted(set(current_paths) - set(expected))
        stale = sorted(set(expected) - set(current_paths))
        if missing:
            errors.append(f"manifest missing paths: {missing}")
        if stale:
            errors.append(f"manifest has stale paths: {stale}")
    for relative, path in current_paths.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected.get(relative) != actual:
            errors.append(f"hash mismatch: {relative}")
    return errors


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    config = load_config(root)
    for item_id in all_item_ids(root):
        try:
            pointer = load_json(current_path(root, item_id))
            item = load_current(root, item_id)
            validate_item(item, config)
            validate_runtime_constraints(root, item, config)
            if item["version"] != pointer["current_version"]:
                errors.append(f"{item_id}: pointer/version mismatch")
            versions = sorted((items_root(root) / item_id).glob("v*.json"))
            expected_versions = list(range(1, item["version"] + 1))
            actual_versions = [int(path.stem[1:]) for path in versions]
            if actual_versions != expected_versions:
                errors.append(
                    f"{item_id}: non-contiguous history; "
                    f"expected={expected_versions}, actual={actual_versions}"
                )
        except FreezerError as exc:
            errors.append(str(exc))
    errors.extend(verify_preflights(root))
    errors.extend(verify_manifest(root))
    return errors


def recall_markdown(item: dict[str, Any], config: dict[str, Any], gate: str) -> str:
    score = compute_score(item, config)
    bullets = lambda values: "\n".join(f"- {value}" for value in values) or "- none"
    return f"""# FREEZER Recall Packet — {item['item_id']}

## Current state
- Title: {item['title']}
- Version: v{item['version']:03d}
- Status: {item['status']}
- Priority score: {score:.2f}
- Build authority: {item['build_authority']}
- Implementation preflight: {gate}
- Recall mode: {item['recall_mode']}
- Estimated effort: {item['estimated_hours']['minimum']}–{item['estimated_hours']['maximum']} hours

## Summary
{item['summary']}

## Original problem
{item['original_problem']}

## Why it matters
{item['why_it_matters']}

## Reason frozen
{item['reason_frozen']}

## Preserved value
{bullets(item['preserved_value'])}

## Trigger conditions
{bullets(item['trigger_conditions'])}

## Negative triggers
{bullets(item['negative_triggers'])}

## Dependencies
{bullets(item['dependencies'])}

## Possible destinations
{bullets(item['possible_destinations'])}

## Sources
{bullets(item['source_refs'])}

## Human and ground-survey gates
This packet does not authorize implementation. Re-score all candidates, review the top candidates,
complete a current PASS implementation preflight, and obtain explicit human approval before changing
this item to SELECTED or IN_PROGRESS.
"""


def command_list(root: Path, args: argparse.Namespace) -> None:
    data = load_json(root / "freezer" / "index" / "priority.json")
    rows = data["items"]
    if args.status:
        rows = [row for row in rows if row["status"] == args.status]
    if args.tag:
        rows = [row for row in rows if args.tag in row["tags"]]
    rows = rows[: args.limit]
    print("RANK\tSCORE\tSTATUS\tPREFLIGHT\tITEM_ID\tTITLE\tHOURS")
    for rank, row in enumerate(rows, start=1):
        hours = row["estimated_hours"]
        print(
            f"{rank}\t{row['priority_score']:.2f}\t{row['status']}\t"
            f"{row.get('preflight_state', 'MISSING')}\t{row['item_id']}\t"
            f"{row['title']}\t{hours['minimum']}-{hours['maximum']}"
        )


def command_show(root: Path, item_id: str) -> None:
    print(json.dumps(load_current(root, item_id), ensure_ascii=False, indent=2))


def command_history(root: Path, item_id: str) -> None:
    directory = items_root(root) / item_id
    if not directory.exists():
        raise FreezerError(f"unknown item: {item_id}")
    for path in sorted(directory.glob("v*.json")):
        item = load_json(path)
        print(f"{path.stem}\t{item['updated_at']}\t{item['status']}\t{item['title']}")


def command_recall(root: Path, item_id: str, output: str | None) -> None:
    item = load_current(root, item_id)
    try:
        gate = preflight_state(root, item)["state"]
    except PreflightError:
        gate = "INVALID"
    text = recall_markdown(item, load_config(root), gate)
    if output:
        path = Path(output)
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="repository root (default: inferred from the freezer package)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a new item from a JSON file")
    add.add_argument("--input", type=Path, required=True)

    revise = sub.add_parser("revise", help="append a new immutable version")
    revise.add_argument("item_id")
    revise.add_argument("--input", type=Path, required=True)

    listing = sub.add_parser("list", help="list current items by priority")
    listing.add_argument("--status")
    listing.add_argument("--tag")
    listing.add_argument("--limit", type=int, default=100)

    show = sub.add_parser("show", help="show the current item")
    show.add_argument("item_id")

    history = sub.add_parser("history", help="show immutable version history")
    history.add_argument("item_id")

    recall = sub.add_parser("recall", help="render a complete recall packet")
    recall.add_argument("item_id")
    recall.add_argument("--output")

    sub.add_parser("reindex", help="recalculate priorities and rebuild indexes")
    sub.add_parser("verify", help="validate items, preflights, version history, and manifest")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "add":
            item = add_item(root, args.input.resolve())
            print(item["item_id"])
        elif args.command == "revise":
            item = revise_item(root, args.item_id, args.input.resolve())
            print(f"{item['item_id']} v{item['version']:03d}")
        elif args.command == "list":
            command_list(root, args)
        elif args.command == "show":
            command_show(root, args.item_id)
        elif args.command == "history":
            command_history(root, args.item_id)
        elif args.command == "recall":
            command_recall(root, args.item_id, args.output)
        elif args.command == "reindex":
            rows = rebuild(root)
            print(f"indexed {len(rows)} item(s)")
        elif args.command == "verify":
            errors = verify(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("FREEZER verification passed")
        else:
            parser.error(f"unknown command: {args.command}")
    except FreezerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
