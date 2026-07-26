from __future__ import annotations

import argparse
import json

from .core import ProofEngineError
from .cross_repo_review_round3 import verify_round_three_review_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the confirmed RTS-minicompany Round 3 review")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("effective")
    sub.add_parser("round-4-template")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_round_three_review_bundle()
        review = bundle["review"]
        if args.command == "verify":
            print(f"Round 3 review passed ({review['review_round_id']})")
        elif args.command == "summary":
            print(json.dumps({
                "review_round_id": review["review_round_id"],
                "counts": review["counts"],
                "metrics": review["metrics"],
                "withheld_claims": review["withheld_claims_confirmed"],
                "state": bundle["checkpoint"]["state"],
                "publication_status": review["publication_status"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "effective":
            print(json.dumps({
                "effective_candidates": review["effective_candidates"],
                "revision": review["revision"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps({
                "round_id": "ROUND-4",
                "repository": "nobutakayamauchi/rts-video-flow",
                "candidate_ids": ["VF-001", "VF-002"],
                "required_checks": [
                    "scaffold_not_completed_product",
                    "freeze_state_not_runtime_capability",
                    "end_to_end_claim_withheld",
                    "transcription_accuracy_claim_withheld",
                    "production_readiness_claim_withheld",
                ],
                "publication_authorized": False,
                "target_repository_write_authorized": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"Round 3 review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
