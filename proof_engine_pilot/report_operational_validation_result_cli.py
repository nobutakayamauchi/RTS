from __future__ import annotations

import argparse
import json
from typing import Any

from .report_operational_validation_build_v2 import verify_second_case_package
from .report_operational_validation_result import verify_operational_reproduction_result


def _pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the bounded second-case reproduction package and final internal result.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in (
        "verify-build", "build-summary", "report-json", "report-markdown",
        "evidence-inventory", "comparison", "acceptance-packet",
        "verification-summary", "rollback-index", "build-checkpoint",
        "verify", "final-summary", "final-markdown", "acceptance-decision",
        "checkpoint",
    ):
        sub.add_parser(name)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {
        "verify-build", "build-summary", "report-json", "report-markdown",
        "evidence-inventory", "comparison", "acceptance-packet",
        "verification-summary", "rollback-index", "build-checkpoint",
    }:
        bundle = verify_second_case_package()
        values: dict[str, Any] = {
            "verify-build": {"status": "PASS", "state": bundle["summary"]["state"], "next_gate": bundle["summary"]["next_gate"], "dynamic_fingerprints": bundle["dynamic_fingerprints"]},
            "build-summary": bundle["summary"],
            "report-json": bundle["report_json"],
            "report-markdown": bundle["report_markdown"],
            "evidence-inventory": bundle["evidence_inventory"],
            "comparison": bundle["comparison_matrix"],
            "acceptance-packet": bundle["acceptance_packet"],
            "verification-summary": bundle["verification_summary"],
            "rollback-index": bundle["rollback_index"],
            "build-checkpoint": bundle["build_checkpoint"],
        }
        value = values[args.command]
    else:
        result = verify_operational_reproduction_result()
        values = {
            "verify": {"status": "PASS", "state": result["evaluation"]["state"], "next_gate": result["evaluation"]["next_gate"], "reproduction_result": result["evaluation"]["reproduction_result"]},
            "final-summary": result["evaluation"],
            "final-markdown": result["markdown"],
            "acceptance-decision": result["decision"],
            "checkpoint": result["checkpoint"],
        }
        value = values[args.command]
    print(value if isinstance(value, str) else _pretty(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
