from __future__ import annotations

import argparse
import json
from typing import Sequence

from .report_operator_runbook import verify_operator_runbook_stage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the bounded evidence-report operator runbook stage.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify", help="Verify every HARD-002 artifact and binding.")
    subparsers.add_parser("summary", help="Print the bounded completion summary.")
    subparsers.add_parser("runbook", help="Print the operator runbook.")
    subparsers.add_parser("intake", help="Print the intake contract.")
    subparsers.add_parser("instruction-policy", help="Print instruction provenance policy.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = verify_operator_runbook_stage()
    if args.command == "verify":
        value = {"verified": True, **bundle["summary"]}
    elif args.command == "summary":
        value = bundle["summary"]
    elif args.command == "runbook":
        value = bundle["operator_runbook"]
    elif args.command == "intake":
        value = bundle["intake_contract"]
    else:
        value = bundle["policy"]
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
