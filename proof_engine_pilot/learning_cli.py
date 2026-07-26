from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError, load
from .learning import preflight_candidate, verify_learning_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review-derived learning for future Proof Engine candidate runs")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("replay")
    preflight = sub.add_parser("preflight")
    preflight.add_argument("input", type=Path)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_learning_bundle()
        if args.command == "verify":
            print(f"Review learning verification passed ({bundle['policy']['policy_id']})")
        elif args.command == "summary":
            print(json.dumps({
                "dataset_id": bundle["dataset"]["dataset_id"],
                "positive_examples": bundle["dataset"]["counts"]["positive_examples"],
                "correction_pairs": bundle["dataset"]["counts"]["correction_pairs"],
                "rules": len(bundle["ruleset"]["rules"]),
                "state": bundle["policy"]["state"],
                "mode": bundle["policy"]["mode"],
                "model_weight_update_performed": bundle["policy"]["model_weight_update_performed"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "replay":
            print(json.dumps(bundle["replay"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps(preflight_candidate(load(args.input)), ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"review learning failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
