from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .report_pilot_package import build_pilot_package, verify_pilot_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and verify the first internal evidence-report pilot package")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-summary")
    sub.add_parser("verify")
    sub.add_parser("summary")
    generate = sub.add_parser("generate")
    generate.add_argument("--output")
    render = sub.add_parser("render-markdown")
    render.add_argument("--output")
    sub.add_parser("evidence-inventory")
    sub.add_parser("acceptance-template")
    sub.add_parser("verification-summary")
    sub.add_parser("package-index")
    return parser


def _write_or_print(value: str, output: str | None) -> None:
    if output:
        Path(output).write_text(value, encoding="utf-8")
    else:
        print(value)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build-summary":
            bundle = build_pilot_package()
            print(json.dumps({
                "report_json_fingerprint": bundle["report_json_fingerprint"],
                "report_markdown_fingerprint": bundle["report_markdown_fingerprint"],
                "evidence_inventory_fingerprint": bundle["evidence_inventory"]["inventory_fingerprint"],
                "acceptance_packet_fingerprint": bundle["acceptance_packet"]["packet_fingerprint"],
                "verification_summary_fingerprint": bundle["verification_summary"]["verification_fingerprint"],
                "package_index_fingerprint": bundle["package_index"]["package_index_fingerprint"],
                "summary_fingerprint": bundle["summary"]["summary_fingerprint"],
                "state": bundle["summary"]["state"],
                "next_gate": bundle["summary"]["next_gate"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        bundle = verify_pilot_package()
        if args.command == "verify":
            print("Internal evidence-report pilot package passed")
        elif args.command == "summary":
            print(json.dumps(bundle["summary"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "generate":
            _write_or_print(json.dumps(bundle["report_json"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", args.output)
        elif args.command == "render-markdown":
            _write_or_print(bundle["report_markdown"] + "\n", args.output)
        elif args.command == "evidence-inventory":
            print(json.dumps(bundle["evidence_inventory"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "acceptance-template":
            print(json.dumps(bundle["acceptance_packet"], ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "verification-summary":
            print(json.dumps(bundle["verification_summary"], ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(json.dumps(bundle["package_index"], ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"internal evidence-report pilot package failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
