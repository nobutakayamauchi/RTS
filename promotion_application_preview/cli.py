from __future__ import annotations

import argparse
from pathlib import Path

from .common import PromotionApplicationPreviewError, pretty_json
from .corpus import DEFAULT_ROOT, verify_all
from .generation import generate_preview


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only promotion application preview")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("generate", help="Print a deterministic non-applying preview")
    subparsers.add_parser("verify", help="Verify the committed preview and governed inputs")
    subparsers.add_parser("summary", help="Print the committed preview summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            print(pretty_json(generate_preview(args.root)), end="")
        else:
            print(pretty_json(verify_all(args.root)), end="")
        return 0
    except PromotionApplicationPreviewError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
