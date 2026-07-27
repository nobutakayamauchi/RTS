from __future__ import annotations

import argparse
import json
from typing import Sequence

from .report_product_readiness import render_product_readiness_markdown, verify_product_readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the bounded evidence-report product-readiness assessment.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("assessment")
    sub.add_parser("plan")
    sub.add_parser("render-markdown")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = verify_product_readiness()
    if args.command == "verify":
        value = {
            "state": bundle["summary"]["state"],
            "decision": bundle["summary"]["decision"],
            "score": bundle["summary"]["completion"]["product_readiness_score"],
            "next_gate": bundle["summary"]["next_gate"],
        }
    elif args.command == "summary":
        value = bundle["summary"]
    elif args.command == "assessment":
        value = bundle["assessment"]
    elif args.command == "plan":
        value = bundle["plan"]
    else:
        print(render_product_readiness_markdown(bundle))
        return 0
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
