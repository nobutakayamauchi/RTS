from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .common import GovernedLoopError, pretty_json
from .corpus import DEFAULT_ROOT, verify_all
from .generation import generate_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RTS Read-Only Governed Loop Orchestrator v1"
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    sub.add_parser("verify")
    sub.add_parser("summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "generate":
            sys.stdout.write(pretty_json(generate_run(root)))
        elif args.command == "verify":
            summary = verify_all(root)
            print(
                "Read-Only Governed Loop verification passed "
                f"({summary['run_id']})"
            )
        elif args.command == "summary":
            run = generate_run(root)
            sys.stdout.write(
                pretty_json(
                    {
                        "run_id": run["run_id"],
                        "run_fingerprint": run["run_fingerprint"],
                        "mode": run["mode"],
                        "status": run["status"],
                        "as_of": run["as_of"],
                        "active_item_ids": run["components"]["read_only_loop"][
                            "active_item_ids"
                        ],
                        "recommendation": run["components"]["read_only_loop"][
                            "recommendation_action"
                        ],
                        "proposal_status": run["components"]["learning_proposal"][
                            "proposal_status"
                        ],
                        "approval_status": run["authority"]["approval_status"],
                        "application_status": run["authority"]["application_status"],
                    }
                )
            )
        else:
            raise GovernedLoopError(f"unknown command: {args.command}")
    except (GovernedLoopError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
