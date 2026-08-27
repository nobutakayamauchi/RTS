#!/usr/bin/env python3
"""Read-only CLI for RTS Selective Recall + Memory Lifecycle v1."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (
    RecallValidationError,
    lifecycle_states,
    parse_request,
    route_recall,
    validate_transition,
    verify_registry,
)


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RecallValidationError(f"missing JSON input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RecallValidationError(f"invalid JSON input {path}: {exc}") from exc


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--registry", default="memory/recall_registry.json")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="validate registry structure and exact source freshness")

    recall = sub.add_parser("recall", help="route one bounded recall request")
    recall.add_argument("--request", type=Path, required=True)

    transition = sub.add_parser("transition", help="validate one lifecycle transition without applying it")
    transition.add_argument("from_state")
    transition.add_argument("to_state")

    sub.add_parser("states", help="list exact lifecycle states")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "verify":
            payload = verify_registry(root, args.registry, require_current=True)
        elif args.command == "recall":
            request = parse_request(_load_json(args.request.resolve()))
            payload = route_recall(root, request, args.registry)
        elif args.command == "transition":
            payload = validate_transition(args.from_state, args.to_state)
        elif args.command == "states":
            payload = {
                "states": list(lifecycle_states()),
                "execution_authority": "NONE",
                "promotion_authority": "NONE",
            }
        else:
            raise RecallValidationError(f"unknown command: {args.command}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except RecallValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
