from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skill_regression.corpus import DEFAULT_ROOT, load_artifacts, verify_all
from skill_regression.models import SkillRegressionError, evaluate_dataset, pretty_json


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Verify the governed Skill regression dataset.")
    value.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = value.add_subparsers(dest="command", required=True)
    sub.add_parser("verify", help="verify snapshots, rollback, fixtures, and committed result")
    sub.add_parser("evaluate", help="print the deterministic regression result")
    sub.add_parser("summary", help="print a compact dataset summary")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "verify":
            summary = verify_all(root)
            print(
                "Skill regression verification passed: "
                f"{summary['dataset_id']} recommendation={summary['recommendation']} "
                f"promotion={summary['promotion_eligibility']}"
            )
        elif args.command == "evaluate":
            artifacts = load_artifacts(root)
            result = evaluate_dataset(
                artifacts["baseline"],
                artifacts["candidate"],
                artifacts["rollback"],
                artifacts["dataset"],
            )
            print(pretty_json(result), end="")
        elif args.command == "summary":
            print(json.dumps(verify_all(root), ensure_ascii=False, sort_keys=True, indent=2))
        else:
            raise SkillRegressionError(f"unknown command: {args.command}")
    except SkillRegressionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
