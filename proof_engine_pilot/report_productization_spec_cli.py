from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .report_productization_spec_v2 import verify_internal_productization_spec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the corrected internal evidence-report product specification"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("spec")
    sub.add_parser("pre-build")
    sub.add_parser("acceptance")
    sub.add_parser("review-template")
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
        bundle = verify_internal_productization_spec()
        if args.command == "verify":
            print("Corrected evidence report internal product specification passed")
        elif args.command == "summary":
            print(json.dumps(bundle["summary"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "spec":
            print(json.dumps(bundle["spec"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "pre-build":
            print(json.dumps(bundle["pre_build"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "acceptance":
            print(json.dumps(bundle["acceptance"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "review-template":
            print(json.dumps(bundle["review_template"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            _write_or_print(bundle["markdown"] + "\n", args.output)
    except ProofEngineError as exc:
        print(f"corrected evidence report internal product specification failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
