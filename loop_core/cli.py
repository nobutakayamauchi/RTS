from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    future = {
        row["item_id"]: row
        for row in items
        if row["item_id"] in {"RTS-FRZ-000006", "RTS-FRZ-000007"}
    }
    if set(future) != {"RTS-FRZ-000006", "RTS-FRZ-000007"}:
        raise LoopCoreError("future child records are missing")
    for item_id, row in future.items():
        if row["build_authority"] != "NOT_APPROVED" or row["status"] in {
            "SELECTED",
            "IN_PROGRESS",
            "COMPLETED",
        }:
            raise LoopCoreError(
                f"{item_id}: future child crossed the advisory boundary"
            )
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
