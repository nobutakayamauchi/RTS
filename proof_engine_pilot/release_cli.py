from __future__ import annotations

import argparse
import json

from .core import ProofEngineError
from .release import verify_publication_release


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the bounded RTS repository publication release")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_publication_release()
        if args.command == "verify":
            print(f"Publication release verified ({bundle['checkpoint']['checkpoint_id']})")
        else:
            print(json.dumps({
                "state": bundle["checkpoint"]["state"],
                "document_path": bundle["checkpoint"]["document_path"],
                "document_fingerprint": bundle["document_fingerprint"],
                "published_wording_count": bundle["checkpoint"]["published_wording_count"],
                "publication_performed": bundle["checkpoint"]["publication_performed"],
                "repository_visibility": bundle["checkpoint"]["repository_visibility"],
                "social_posting_performed": bundle["checkpoint"]["social_posting_performed"],
                "direct_outreach_performed": bundle["checkpoint"]["direct_outreach_performed"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"publication release failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
