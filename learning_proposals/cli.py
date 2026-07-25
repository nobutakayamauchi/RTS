from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .common import LearningProposalError, pretty_json
from .corpus import DEFAULT_ROOT, verify_all
from .generation import generate_pending_review, generate_proposal


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Verify proposal-only outcome learning records.")
    value.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = value.add_subparsers(dest="command", required=True)
    sub.add_parser("verify", help="verify deterministic proposal and pending review records")
    sub.add_parser("generate", help="print the deterministic proposal without writing files")
    sub.add_parser("review-template", help="print a non-authorizing PENDING review template")
    sub.add_parser("summary", help="print a compact verification summary")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "verify":
            summary = verify_all(root)
            print(
                "Learning proposal verification passed: "
                f"{summary['proposal_id']} status={summary['proposal_status']} "
                f"review={summary['review_status']} application={summary['application_status']}"
            )
        elif args.command == "generate":
            print(pretty_json(generate_proposal(root)), end="")
        elif args.command == "review-template":
            print(pretty_json(generate_pending_review(generate_proposal(root))), end="")
        elif args.command == "summary":
            print(json.dumps(verify_all(root), ensure_ascii=False, sort_keys=True, indent=2))
        else:
            raise LearningProposalError(f"unknown command: {args.command}")
    except LearningProposalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
