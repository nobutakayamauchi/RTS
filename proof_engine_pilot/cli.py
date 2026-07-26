from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError, generate_run, verify_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Proof Engine pilot: deterministic evidence-backed candidate generation")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--output", type=Path)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("review-template")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            run = verify_run(generate_run())
            rendered = json.dumps(run, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
        elif args.command == "verify":
            run = verify_run()
            print(f"Proof Engine verification passed ({run['run_id']})")
        elif args.command == "summary":
            run = verify_run()
            print(json.dumps({
                "run_id": run["run_id"],
                "result": run["result"],
                "candidate_count": run["candidate_count"],
                "review_state": run["review_queue"]["state"],
                "output_state": run["output_asset"]["state"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            run = verify_run()
            print(json.dumps({
                "run_id": run["run_id"],
                "allowed_decisions": run["review_queue"]["allowed_decisions"],
                "candidate_ids": [candidate["candidate_id"] for candidate in run["candidates"]],
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"proof engine failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
