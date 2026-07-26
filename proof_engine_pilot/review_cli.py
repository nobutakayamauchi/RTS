from __future__ import annotations

import argparse
import json

from .core import ProofEngineError
from .review import effective_candidate_records, verify_review_round


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the append-only Proof Engine human review round")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("effective")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = verify_review_round()
        if args.command == "verify":
            print(f"Proof Engine review verification passed ({summary['review_round_id']})")
        elif args.command == "summary":
            print(json.dumps({
                "review_round_id": summary["review_round_id"],
                "review_state": summary["review_state"],
                "originals_approved": summary["counts"]["originals_approved"],
                "originals_revised": summary["counts"]["originals_revised"],
                "revisions_approved": summary["counts"]["revisions_approved"],
                "effective_candidates_approved": summary["counts"]["effective_candidates_approved"],
                "output_state": summary["output_asset"]["state"],
                "publication_status": summary["output_asset"]["publication_status"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps(effective_candidate_records(), ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"proof engine review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
