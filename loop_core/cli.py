from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from freezer.assessment_core import BuildAssessmentError, load_current_item
from freezer.assessment_store import require_build_now_assessment
from freezer.preflight import PreflightError, require_passing_preflight

from .core import DEFAULT_INPUTS, evaluate
from .models import (
    AUTHORITY,
    LoopCoreError,
    load_json,
    pretty_json,
    sha256_file,
    validate_evaluation,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
LEARNING_GOVERNED_STATUSES = {"SELECTED", "IN_PROGRESS", "VERIFIED", "COMPLETED"}


def validate_learning_index_boundary(learning: dict[str, Any]) -> bool:
    """Validate the index-level authority boundary for RTS-FRZ-000007.

    Returns True when current Assessment and Preflight gates must also be
    revalidated from their immutable records.
    """

    status = learning.get("status")
    authority = learning.get("build_authority")
    preflight = learning.get("preflight_state")

    if status == "FROZEN":
        if authority != "NOT_APPROVED":
            raise LoopCoreError(
                "RTS-FRZ-000007 FROZEN state requires build_authority=NOT_APPROVED"
            )
        return False

    if status not in LEARNING_GOVERNED_STATUSES:
        raise LoopCoreError(
            f"RTS-FRZ-000007 has unsupported governed status={status!r}"
        )
    if authority != "APPROVED":
        raise LoopCoreError(
            f"RTS-FRZ-000007 {status} state requires build_authority=APPROVED"
        )
    if preflight != "PASS":
        raise LoopCoreError(
            f"RTS-FRZ-000007 {status} state requires preflight_state=PASS"
        )
    return True


def validate_learning_current_gates(root: Path, learning: dict[str, Any]) -> None:
    """Fail closed unless an active/terminal learning item has current gates."""

    if not validate_learning_index_boundary(learning):
        return
    try:
        item = load_current_item(root, "RTS-FRZ-000007")
        require_build_now_assessment(root, item)
        require_passing_preflight(root, item)
    except (BuildAssessmentError, PreflightError) as exc:
        raise LoopCoreError(
            f"RTS-FRZ-000007 governed lifecycle gate failed: {exc}"
        ) from exc

    for field in ("status", "build_authority"):
        if item.get(field) != learning.get(field):
            raise LoopCoreError(
                f"RTS-FRZ-000007 item/index {field} mismatch"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Read-Only Loop Core v1")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("--execution-records", type=Path)
    evaluate_parser.add_argument("--evidence-refs", type=Path)
    evaluate_parser.add_argument("--as-of")
    sub.add_parser("verify")
    return parser


def command_evaluate(root: Path, args: argparse.Namespace) -> None:
    payload = evaluate(
        root,
        execution_records_path=args.execution_records,
        evidence_refs_path=args.evidence_refs,
        as_of=args.as_of,
    )
    sys.stdout.write(pretty_json(payload))


def command_verify(root: Path) -> None:
    governed = [root / relative for relative in DEFAULT_INPUTS]
    before = {path: sha256_file(path) for path in governed}
    first = evaluate(root)
    second = evaluate(root)
    if pretty_json(first) != pretty_json(second):
        raise LoopCoreError("determinism verification failed")
    after = {path: sha256_file(path) for path in governed}
    if before != after:
        raise LoopCoreError("read-only verification failed: governed input changed")
    validate_evaluation(first)
    example = load_json(root / "loop_core" / "examples" / "evaluation.json")
    validate_evaluation(example)
    if (
        first["authority"] != AUTHORITY
        or first["implementation_authority_granted"] is not False
    ):
        raise LoopCoreError("authority boundary verification failed")
    items = load_json(root / "freezer" / "index" / "items.json")["items"]
    children = {
        row["item_id"]: row
        for row in items
        if row["item_id"] in {"RTS-FRZ-000006", "RTS-FRZ-000007"}
    }
    if set(children) != {"RTS-FRZ-000006", "RTS-FRZ-000007"}:
        raise LoopCoreError("controller/learning child records are missing")
    controller = children["RTS-FRZ-000006"]
    if (
        controller["build_authority"] != "APPROVED"
        or controller["status"] != "COMPLETED"
    ):
        raise LoopCoreError("RTS-FRZ-000006 controller lifecycle is not completed")
    validate_learning_current_gates(root, children["RTS-FRZ-000007"])
    print("Read-Only Loop Core verification passed")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "evaluate":
            command_evaluate(root, args)
        elif args.command == "verify":
            command_verify(root)
        else:
            raise LoopCoreError(f"unknown command: {args.command}")
    except LoopCoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
