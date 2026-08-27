from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    PROVIDER_POLICIES,
    build_intake_report,
    discover_document_urls,
    report_fingerprint,
    verify_intake_report,
)


def _dump(value: object, output: str | None = None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="official-docs-intake")
    sub = parser.add_subparsers(dest="command", required=True)

    policy = sub.add_parser("policy", help="show built-in provider policies")
    policy.add_argument("provider", nargs="?")

    discover = sub.add_parser("discover", help="bounded discovery from official provider indexes/seeds")
    discover.add_argument("--provider", required=True)
    discover.add_argument("--term", action="append", default=[])
    discover.add_argument("--url", action="append", default=[])
    discover.add_argument("--max-documents", type=int, default=8)
    discover.add_argument("--output")

    build = sub.add_parser("build", help="build an H-compatible intake report from a JSON request")
    build.add_argument("--request", required=True)
    build.add_argument("--output")

    verify = sub.add_parser("verify", help="verify a previously generated intake report")
    verify.add_argument("--report", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "policy":
        if args.provider:
            key = args.provider.strip().lower()
            if key not in PROVIDER_POLICIES:
                raise SystemExit(f"unsupported provider: {args.provider}")
            _dump({key: PROVIDER_POLICIES[key]})
        else:
            _dump(PROVIDER_POLICIES)
        return 0

    if args.command == "discover":
        result = discover_document_urls(
            args.provider,
            args.term,
            explicit_urls=args.url,
            max_documents=args.max_documents,
        )
        _dump(result, args.output)
        return 0

    if args.command == "build":
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        report = build_intake_report(request)
        verify_intake_report(report)
        report["report_fingerprint"] = report_fingerprint(report)
        _dump(report, args.output)
        return 0

    if args.command == "verify":
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        fingerprint = report.pop("report_fingerprint", None)
        verify_intake_report(report)
        calculated = report_fingerprint(report)
        if fingerprint is not None and fingerprint != calculated:
            raise SystemExit("report fingerprint mismatch")
        print(calculated)
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
