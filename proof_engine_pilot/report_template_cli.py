from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError
from .report_template import render_demonstration_markdown, verify_report_template


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and verify internal evidence-backed achievement reports")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    sub.add_parser("summary")
    generate = sub.add_parser("generate")
    generate.add_argument("--output")
    render = sub.add_parser("render-markdown")
    render.add_argument("--output")
    sub.add_parser("review-template")
    return parser


def _write_or_print(value: str, output: str | None) -> None:
    if output:
        Path(output).write_text(value, encoding="utf-8")
    else:
        print(value)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = verify_report_template()
        if args.command == "verify":
            print("Evidence-backed achievement report template passed")
        elif args.command == "summary":
            print(json.dumps({
                "template_id": bundle["template"]["template_id"],
                "template_fingerprint": bundle["template"]["template_fingerprint"],
                "pack_id": bundle["pack"]["pack_id"],
                "pack_fingerprint": bundle["pack"]["pack_fingerprint"],
                "counts": bundle["pack"]["counts"],
                "state": bundle["pack"]["state"],
                "publication_status": bundle["pack"]["publication_status"],
                "delivery_status": bundle["pack"]["delivery_status"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "generate":
            _write_or_print(json.dumps(bundle["pack"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", args.output)
        elif args.command == "render-markdown":
            _write_or_print(render_demonstration_markdown(bundle) + "\n", args.output)
        else:
            print(json.dumps({
                "template_id": bundle["template"]["template_id"],
                "report_ids": [item["report_id"] for item in bundle["pack"]["reports"]],
                "required_sections": list(bundle["pack"]["reports"][0]["sections"]),
                "allowed_decisions": bundle["template"]["allowed_human_decisions"],
                "state": "HUMAN_REPORT_TEMPLATE_REVIEW_REQUIRED",
                "pricing_authorized": False,
                "outreach_authorized": False,
                "delivery_authorized": False,
                "publication_authorized": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"evidence report template failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
