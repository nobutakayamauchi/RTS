from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .report_operational_validation_plan import verify_operational_validation_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the second-case internal operational validation plan"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command in (
        "verify",
        "summary",
        "selection",
        "plan",
        "review-contract",
        "review-template",
    ):
        sub.add_parser(command)
    render = sub.add_parser("render-markdown")
    render.add_argument("--output")
    return parser


def _write_or_print(value: str, output: str | None) -> None:
    if output:
        Path(output).write_text(value, encoding="utf-8")
    else:
        print(value)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_operational_validation_plan()
        if args.command == "verify":
            print("Evidence report operational validation plan passed")
        elif args.command == "summary":
            print(json.dumps(bundle["summary"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "selection":
            print(json.dumps(bundle["selection"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "plan":
            print(json.dumps(bundle["plan"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "review-contract":
            print(json.dumps(bundle["review_contract"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "review-template":
            print(json.dumps(bundle["review_template"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            _write_or_print(bundle["markdown"] + "\n", args.output)
    except ProofEngineError as exc:
        print(f"evidence report operational validation plan failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
