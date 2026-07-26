from __future__ import annotations

import argparse
import json

from .core import ProofEngineError
from .publication_review import effective_wording_records, verify_publication_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review audience-facing wording before any release")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("effective")
    sub.add_parser("release-template")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_publication_review()
        if args.command == "verify":
            print(f"Publication wording review passed ({bundle['summary']['review_round_id']})")
        elif args.command == "summary":
            summary = bundle["summary"]
            print(json.dumps({
                "review_round_id": summary["review_round_id"],
                "counts": summary["counts"],
                "review_state": summary["review_state"],
                "publication_status": summary["publication_status"],
                "release_authorization_status": summary["release_authorization_status"],
                "review_origin": summary["review_origin"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "effective":
            print(json.dumps(effective_wording_records(bundle), ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps({
                "review_round_id": bundle["summary"]["review_round_id"],
                "state": "RELEASE_AUTHORIZATION_REQUIRED",
                "effective_wording_ids": [item["wording_id"] for item in bundle["summary"]["effective_wordings"]],
                "required_human_fields": [
                    "release_decision",
                    "exact_release_surface",
                    "exact_document_or_path",
                    "approved_wording_fingerprints",
                    "privacy_confirmation",
                    "release_timing",
                ],
                "allowed_release_decisions": ["AUTHORIZE_RELEASE", "RETURN_FOR_REVISION", "WITHHOLD_RELEASE"],
                "publication_performed": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"publication wording review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
