from __future__ import annotations

import argparse
import json

from .asset_review import verify_asset_review
from .core import ProofEngineError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify append-only review of six internal Proof Engine assets")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("effective")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_asset_review()
        if args.command == "verify":
            print(f"Asset review verification passed ({bundle['summary']['review_round_id']})")
        elif args.command == "summary":
            print(json.dumps({
                "review_round_id": bundle["summary"]["review_round_id"],
                "review_state": bundle["summary"]["review_state"],
                "approved": bundle["summary"]["counts"]["approved"],
                "publication_status": bundle["summary"]["publication_status"],
                "next_action": bundle["summary"]["next_action"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps(bundle["summary"]["effective_assets"], ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"asset review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
