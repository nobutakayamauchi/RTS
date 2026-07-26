from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .compiler import PROFILES, compile_plan, verify_plan
from .models import AdaptiveGovernanceError, pretty_json


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AdaptiveGovernanceError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AdaptiveGovernanceError(f"invalid JSON file: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdaptiveGovernanceError(f"JSON root must be an object: {path}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile minimum non-authorizing governance for an exact change context")
    subparsers = parser.add_subparsers(dest="command", required=True)
    compile_parser = subparsers.add_parser("compile", help="Compile a deterministic governance plan")
    compile_parser.add_argument("--context", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path)
    verify_parser = subparsers.add_parser("verify", help="Verify a compiled governance plan against its exact context")
    verify_parser.add_argument("--plan", type=Path, required=True)
    verify_parser.add_argument("--context", type=Path, required=True)
    subparsers.add_parser("profiles", help="Print the fixed G0-G4 profiles")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "compile":
            plan = compile_plan(_load(args.context))
            rendered = pretty_json(plan)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
        elif args.command == "verify":
            plan = verify_plan(_load(args.plan), _load(args.context))
            print(pretty_json(plan), end="")
        elif args.command == "profiles":
            print(pretty_json(PROFILES), end="")
        else:
            raise AdaptiveGovernanceError(f"unsupported command: {args.command}")
    except AdaptiveGovernanceError as exc:
        raise SystemExit(f"adaptive governance failed closed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
