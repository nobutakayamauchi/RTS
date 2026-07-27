from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .report_productization_review import verify_productization_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the evidence-report productization decision")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("decision")
    render = sub.add_parser("render-markdown")
    render.add_argument("--output")
    sub.add_parser("next-stage")
    return parser


def _write_or_print(value: str, output: str | None) -> None:
    if output:
        Path(output).write_text(value, encoding="utf-8")
    else:
        print(value)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_productization_review()
        if args.command == "verify":
            print("Evidence report productization review passed")
        elif args.command == "summary":
            print(json.dumps(bundle["summary"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "decision":
            print(json.dumps(bundle["decision"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "render-markdown":
            _write_or_print(bundle["markdown"] + "\n", args.output)
        else:
            print(json.dumps({
                "state": bundle["summary"]["state"],
                "scope": bundle["summary"]["productization_scope"],
                "next_action": bundle["summary"]["next_action"],
                "pricing_authorized": False,
                "outreach_authorized": False,
                "contract_authorized": False,
                "delivery_authorized": False,
                "publication_authorized": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"evidence report productization review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
