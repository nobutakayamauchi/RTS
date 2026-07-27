from __future__ import annotations

import argparse
import json

from .core import ProofEngineError
from .cross_repo_campaign_close import verify_campaign_close


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the closed three-repository Proof Engine campaign")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("evaluation")
    sub.add_parser("report-template-design")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_campaign_close()
        if args.command == "verify":
            print("Three-repository campaign close passed")
        elif args.command == "summary":
            print(json.dumps({
                "review_state": bundle["review"]["review_state"],
                "campaign_state": bundle["review"]["campaign_state"],
                "round_4_counts": bundle["review"]["counts"],
                "cross_repo_totals": bundle["evaluation"]["cross_repo_totals"],
                "conclusion": bundle["evaluation"]["conclusion"],
                "next_stage": bundle["evaluation"]["next_stage"],
                "checkpoint_state": bundle["checkpoint"]["state"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "evaluation":
            print(json.dumps(bundle["evaluation"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps({
                "state": "READY_FOR_INTERNAL_REPORT_TEMPLATE_DESIGN",
                "required_sections": [
                    "executive_summary",
                    "repository_scope",
                    "evidence_inventory",
                    "effective_achievement_records",
                    "human_and_ai_contribution_map",
                    "withheld_or_unsupported_claims",
                    "limitations",
                    "human_review_decision",
                ],
                "source_effective_candidate_count": 16,
                "source_withheld_claim_count": 5,
                "authority": {
                    "pricing_authorized": False,
                    "outreach_authorized": False,
                    "publication_authorized": False,
                    "contract_authorized": False,
                },
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"cross-repo campaign close failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
