from __future__ import annotations

import argparse
import json
from pathlib import Path

from .asset_draft import build_internal_asset_draft, verify_internal_asset_draft
from .core import ProofEngineError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Six-part internal asset draft for Proof Engine")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--output", type=Path)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("review-template")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            value = build_internal_asset_draft()
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            if args.output:
                args.output.write_text(text, encoding="utf-8")
            else:
                print(text, end="")
        else:
            value = verify_internal_asset_draft()
            if args.command == "verify":
                print(f"Internal asset draft verification passed ({value['draft_id']})")
            elif args.command == "summary":
                print(json.dumps({
                    "draft_id": value["draft_id"],
                    "asset_count": value["asset_count"],
                    "covered_candidate_count": value["coverage"]["effective_candidate_count"],
                    "learning_preflight": value["learning_preflight"]["required_result"],
                    "review_state": value["review_gate"]["state"],
                    "publication_status": value["output"]["publication_status"],
                }, ensure_ascii=False, sort_keys=True, indent=2))
            else:
                print(json.dumps({
                    "draft_id": value["draft_id"],
                    "allowed_decisions": value["review_gate"]["allowed_decisions"],
                    "asset_ids": [item["asset_id"] for item in value["assets"]],
                    "required_fields": ["decision", "rationale", "wording_changes", "public_disclosure"],
                    "publication_authorized": False,
                }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"internal asset draft failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
