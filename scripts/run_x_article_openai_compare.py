#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from x_article_engine.openai_live_compare import (
    run_openai_live_comparison,
    write_comparison_result,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run X Article Engine tuned-vs-Plain on the same OpenAI model and brief."
    )
    parser.add_argument(
        "--fixture",
        default="x_article_engine/fixtures/plain_reality_neutral.json",
        help="JSON containing brief and trusted_source_refs",
    )
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    parser.add_argument(
        "--output",
        default="artifacts/x_article_openai_plain_comparison.json",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print(
            "OPENAI_API_KEY is not set. Put the key in the environment or a GitHub Actions secret; never put it in the fixture or repository.",
            file=sys.stderr,
        )
        return 2

    fixture_path = Path(args.fixture)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    brief = fixture.get("brief")
    trusted_source_refs = fixture.get("trusted_source_refs")
    if not isinstance(brief, dict) or not isinstance(trusted_source_refs, list):
        print("fixture must contain object brief and list trusted_source_refs", file=sys.stderr)
        return 2

    result = run_openai_live_comparison(
        brief,
        trusted_source_refs=trusted_source_refs,
        api_key=api_key,
        model=args.model,
        max_output_tokens=args.max_output_tokens,
    )
    output = write_comparison_result(result, args.output)

    tuned = result["tuned"]
    plain = result["plain"]
    print(f"wrote: {output}")
    print(f"tuned audit: {tuned['audit']['status']}")
    print(f"plain audit: {plain['audit']['status']}")
    print(f"tuned unexpected author markers: {tuned['unexpected_author_markers']}")
    print(f"plain unexpected author markers: {plain['unexpected_author_markers']}")
    print("publication remains BLOCKED_PENDING_HUMAN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
