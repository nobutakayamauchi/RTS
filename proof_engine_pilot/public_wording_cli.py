from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .public_wording import (
    build_public_wording_draft,
    render_public_wording_markdown,
    verify_public_wording_draft,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audience-facing wording drafts for reviewed Proof Engine assets")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--output", type=Path)
    markdown = sub.add_parser("render-markdown")
    markdown.add_argument("--output", type=Path)
    sub.add_parser("verify")
    sub.add_parser("summary")
    sub.add_parser("review-template")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            value = build_public_wording_draft()
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            if args.output:
                args.output.write_text(text, encoding="utf-8")
            else:
                print(text, end="")
        elif args.command == "render-markdown":
            text = render_public_wording_markdown()
            if args.output:
                args.output.write_text(text, encoding="utf-8")
            else:
                print(text, end="")
        else:
            bundle = verify_public_wording_draft()
            draft = bundle["draft"]
            if args.command == "verify":
                print(f"Public wording draft verification passed ({draft['draft_id']})")
            elif args.command == "summary":
                print(json.dumps({
                    "draft_id": draft["draft_id"],
                    "language": draft["language"],
                    "wording_count": draft["wording_count"],
                    "learning_preflight": draft["learning_preflight"]["required_result"],
                    "review_state": draft["review_gate"]["state"],
                    "publication_status": draft["output"]["publication_status"],
                    "markdown_fingerprint": bundle["markdown_fingerprint"],
                }, ensure_ascii=False, sort_keys=True, indent=2))
            else:
                print(json.dumps({
                    "draft_id": draft["draft_id"],
                    "allowed_decisions": draft["review_gate"]["allowed_decisions"],
                    "wording_ids": [item["wording_id"] for item in draft["wordings"]],
                    "required_fields": ["decision", "rationale", "wording_changes", "redactions", "publication_scope"],
                    "publication_authorized": False,
                }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"public wording draft failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
