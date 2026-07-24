#!/usr/bin/env python3
"""CLI for GitHub reuse surveys and FREEZER build-value assessments."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from freezer.assessment_core import (
    BuildAssessmentError, DEFAULT_ROOT, derive, load_current_item, load_json, validate_record,
)
from freezer.assessment_rank import build_index_rows, gate_payload, rebuild_index, verify_assessments
from freezer.assessment_store import (
    assessment_root, assessment_state, create_assessment, load_current_assessment,
)

__all__ = [
    "BuildAssessmentError", "assessment_state", "build_index_rows", "create_assessment",
    "derive", "gate_payload", "load_current_assessment", "rebuild_index",
    "validate_record", "verify_assessments",
]


def command_show(root: Path, item_id: str) -> None:
    print(json.dumps(load_current_assessment(root, item_id), ensure_ascii=False, indent=2))


def command_history(root: Path, item_id: str) -> None:
    directory = assessment_root(root, item_id)
    if not directory.exists():
        raise BuildAssessmentError(f"{item_id}: no assessment history")
    for path in sorted(directory.glob("ba*.json")):
        record = load_json(path)
        validate_record(record)
        d = record["derived"]
        print(
            f"{path.stem}\t{record['created_at']}\t{d['recommendation']}\t"
            f"score={d['decision_score']:.2f}\tnet={d['net_hours']:.2f}h"
        )


def command_status(root: Path, item_id: str) -> None:
    item = load_current_item(root, item_id)
    state = assessment_state(root, item)
    record = state["assessment"]
    payload = {
        "item_id": item_id,
        "item_version": item["version"],
        "state": state["state"],
        "assessment_id": record["assessment_id"] if record else None,
        "recommendation": record["derived"]["recommendation"] if record else None,
        "decision_score": record["derived"]["decision_score"] if record else None,
        "build_now_ready": bool(
            record and state["state"] == "CURRENT" and record["derived"]["recommendation"] == "BUILD_NOW"
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_list(root: Path, limit: int) -> None:
    rows = load_json(root / "freezer" / "index" / "build_priority.json")["items"][:limit]
    print("RANK\tRANKING\tBUILD\tPRIORITY\tASSESSMENT\tRECOMMENDATION\tITEM_ID\tTITLE\tNET_HOURS")
    for rank, row in enumerate(rows, 1):
        build = "-" if row["build_score"] is None else f"{row['build_score']:.2f}"
        net = "-" if row["net_hours"] is None else f"{row['net_hours']:.2f}"
        print(
            f"{rank}\t{row['ranking_score']:.2f}\t{build}\t{row['priority_score']:.2f}\t"
            f"{row['assessment_state']}\t{row['recommendation']}\t{row['item_id']}\t"
            f"{row['title']}\t{net}"
        )


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = p.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="append an immutable GitHub reuse/value assessment")
    create.add_argument("item_id")
    create.add_argument("--input", type=Path, required=True)
    for name, help_text in (
        ("show", "show the latest build assessment"),
        ("history", "show assessment history"),
        ("status", "show whether the current assessment recommends build now"),
        ("gate", "show assessment, preflight, approval, and selection readiness"),
    ):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("item_id")
    listing = sub.add_parser("list", help="list candidates by combined build ranking")
    listing.add_argument("--limit", type=int, default=100)
    sub.add_parser("reindex", help="recalculate the combined build ranking")
    sub.add_parser("verify", help="validate assessment histories, active-item gates, and build index")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "create":
            record = create_assessment(root, args.item_id, args.input.resolve())
            rebuild_index(root)
            print(record["assessment_id"])
        elif args.command == "show":
            command_show(root, args.item_id)
        elif args.command == "history":
            command_history(root, args.item_id)
        elif args.command == "status":
            command_status(root, args.item_id)
        elif args.command == "gate":
            print(json.dumps(gate_payload(root, args.item_id), ensure_ascii=False, indent=2))
        elif args.command == "list":
            command_list(root, args.limit)
        elif args.command == "reindex":
            print(f"indexed {len(rebuild_index(root))} build candidate(s)")
        elif args.command == "verify":
            errors = verify_assessments(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("FREEZER build assessment verification passed")
        else:
            raise BuildAssessmentError(f"unknown command: {args.command}")
    except BuildAssessmentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
