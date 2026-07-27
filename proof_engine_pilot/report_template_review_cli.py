from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import ProofEngineError, fingerprint
from .report_template_review import (
    build_report_template_review,
    render_revised_markdown,
    verify_report_template_review,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review and revise the evidence-backed report template")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-summary")
    sub.add_parser("verify")
    sub.add_parser("summary")
    generate = sub.add_parser("generate")
    generate.add_argument("--output")
    render = sub.add_parser("render-markdown")
    render.add_argument("--output")
    sub.add_parser("productization-template")
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
            bundle = build_report_template_review()
            markdown = render_revised_markdown(bundle)
            print(json.dumps({
                "review_contract_fingerprint": bundle["contract"]["contract_fingerprint"],
                "revised_template_fingerprint": bundle["template"]["template_fingerprint"],
                "revised_pack_fingerprint": bundle["pack"]["pack_fingerprint"],
                "review_fingerprint": bundle["summary"]["review_fingerprint"],
                "revised_markdown_fingerprint": fingerprint(markdown),
                "counts": bundle["pack"]["counts"],
                "state": bundle["pack"]["state"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
            return 0

        bundle = verify_report_template_review()
        if args.command == "verify":
            print("Evidence report template review passed")
        elif args.command == "summary":
            print(json.dumps({
                "review_id": bundle["summary"]["review_id"],
                "review_fingerprint": bundle["summary"]["review_fingerprint"],
                "findings": bundle["summary"]["findings"],
                "counts": bundle["summary"]["counts"],
                "state": bundle["summary"]["state"],
                "publication_status": bundle["summary"]["publication_status"],
                "delivery_status": bundle["summary"]["delivery_status"],
                "pricing_status": bundle["summary"]["pricing_status"],
            }, ensure_ascii=False, sort_keys=True, indent=2))
        elif args.command == "generate":
            _write_or_print(json.dumps(bundle["pack"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", args.output)
        elif args.command == "render-markdown":
            _write_or_print(bundle["markdown"] + "\n", args.output)
        else:
            print(json.dumps({
                "state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
                "revised_template_fingerprint": bundle["template"]["template_fingerprint"],
                "revised_report_fingerprints": [item["report_fingerprint"] for item in bundle["pack"]["reports"]],
                "review_criteria": bundle["pack"]["reports"][0]["sections"]["human_review_decision"]["review_criteria"],
                "required_decision_fields": bundle["pack"]["reports"][0]["sections"]["human_review_decision"]["required_decision_fields"],
                "allowed_decisions": bundle["pack"]["reports"][0]["sections"]["human_review_decision"]["allowed_decisions"],
                "pricing_authorized": False,
                "delivery_authorized": False,
                "publication_authorized": False,
            }, ensure_ascii=False, sort_keys=True, indent=2))
    except ProofEngineError as exc:
        print(f"evidence report template review failed closed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
