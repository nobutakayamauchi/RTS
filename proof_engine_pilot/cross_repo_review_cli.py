from __future__ import annotations

import argparse
import json

from .core import ProofEngineError
from .cross_repo_review import verify_round_two_review_bundle
from .cross_repo_validation import verify_bundle as verify_cross_repo_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify sequential cross-repository human reviews")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-round-2")
    sub.add_parser("summary-round-2")
    sub.add_parser("effective-round-2")
    sub.add_parser("round-3-template")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_round_two_review_bundle()
        if args.command == "verify-round-2":
            print(f"Cross-repository Round 2 review passed ({bundle['review']['review_round_id']})")
        elif args.command == "summary-round-2":
            print(json.dumps({
                "review_round_id": bundle["review"]["review_round_id"],
                "counts": bundle["review"]["counts"],
                "metrics": bundle["review"]["metrics"],
                "review_state": bundle["review"]["review_state"],
                "next_round": bundle["review"]["next_round"],
                "checkpoint_state": bundle["checkpoint"]["state"],
                "publication_status": bundle["review"]["publication_status"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "effective-round-2":
            print(json.dumps(bundle["review"]["effective_candidates"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            campaign = verify_cross_repo_bundle()["run"]
            round_three = next(item for item in campaign["rounds"] if item["round_id"] == "ROUND-3")
            print(json.dumps({
                "round_id": "ROUND-3",
                "repository": round_three["repository"],
                "candidate_ids": [item["candidate_id"] for item in round_three["candidates"]],
                "withheld_claims": round_three["withheld_claims"],
                "learning_observation_fingerprint": bundle["learning_observation"]["observation_fingerprint"],
                "allowed_decisions": ["APPROVE", "REVISE", "REJECT", "REDACT", "EXPIRE"],
                "automatic_approval_authorized": False,
                "publication_authorized": False,
                "target_repository_write_authorized": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"cross-repository review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
