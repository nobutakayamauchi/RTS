from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .common import HumanReviewLedgerError, load_json, pretty_json
from .corpus import DEFAULT_ROOT, summarize, verify_all

TEMPLATE_PATH = "human_review_ledger/templates/decision.blank.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify and inspect the non-authorizing Human Review Ledger")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify", help="Verify the committed append-only ledger")
    summary_parser = subparsers.add_parser("summary", help="Print a derived non-authorizing summary")
    summary_parser.add_argument("--as-of", default=None, help="Optional ISO-8601 time for expiry evaluation")
    subparsers.add_parser("blank-template", help="Print the blank human-authored decision template")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "verify":
            print(pretty_json(verify_all(args.root.resolve())), end="")
        elif args.command == "summary":
            print(pretty_json(summarize(args.root.resolve(), as_of=args.as_of)), end="")
        elif args.command == "blank-template":
            value = load_json(args.root.resolve() / TEMPLATE_PATH)
            print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            raise HumanReviewLedgerError(f"unsupported command: {args.command}")
    except HumanReviewLedgerError as exc:
        raise SystemExit(f"human review ledger verification failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
