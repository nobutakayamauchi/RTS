from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import compare_bundles, validate_bundle


def _load(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare immutable old/new model-document evidence bundles.")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="Validate one evidence bundle")
    verify.add_argument("bundle")

    compare = sub.add_parser("compare", help="Compare old/new evidence bundles")
    compare.add_argument("old_bundle")
    compare.add_argument("new_bundle")
    compare.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "verify":
        bundle = _load(args.bundle)
        validate_bundle(bundle)
        print(json.dumps({"valid": True, "generation": bundle["generation"]}, sort_keys=True))
        return 0

    old_bundle = _load(args.old_bundle)
    new_bundle = _load(args.new_bundle)
    report = compare_bundles(old_bundle, new_bundle)
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
