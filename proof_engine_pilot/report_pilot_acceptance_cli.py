from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .report_pilot_acceptance import verify_pilot_acceptance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the first internal evidence-report pilot package acceptance"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("decision")
    sub.add_parser("summary")
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
        bundle = verify_pilot_acceptance()
        if args.command == "verify":
            print("Internal evidence-report pilot package acceptance passed")
        elif args.command == "decision":
            print(json.dumps(bundle["decision"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "summary":
            print(json.dumps(bundle["summary"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            _write_or_print(bundle["markdown"] + "\n", args.output)
    except ProofEngineError as exc:
        print(f"internal evidence-report pilot package acceptance failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
