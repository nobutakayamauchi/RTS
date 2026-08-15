from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import PostAdapterError, build_bundle


def _write_bundle(bundle: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(
        json.dumps(bundle["manifest"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_summary.md").write_text(bundle["source_summary"], encoding="utf-8")
    for channel, content in bundle["outputs"].items():
        (out_dir / f"{channel}.md").write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate human-reviewed cross-channel publication drafts without posting them."
    )
    parser.add_argument("source", type=Path, help="JSON source update")
    parser.add_argument("--out-dir", type=Path, required=True, help="Bundle output directory")
    parser.add_argument(
        "--review-state",
        choices=("DRAFT", "REVIEW_REQUIRED", "APPROVED_FOR_COPY", "REJECTED"),
        default=None,
        help="Optional human review state. APPROVED_FOR_COPY fails when evidence warnings remain.",
    )
    args = parser.parse_args(argv)

    try:
        source = json.loads(args.source.read_text(encoding="utf-8"))
        bundle = build_bundle(source, review_state=args.review_state)
        _write_bundle(bundle, args.out_dir)
    except (OSError, json.JSONDecodeError, PostAdapterError) as exc:
        print(f"post-adapter: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "bundle_id": bundle["manifest"]["bundle_id"],
                "human_review_state": bundle["manifest"]["human_review_state"],
                "channels": bundle["manifest"]["channels"],
                "verification_warnings": len(bundle["manifest"]["verification_warnings"]),
                "external_publication_performed": False,
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
