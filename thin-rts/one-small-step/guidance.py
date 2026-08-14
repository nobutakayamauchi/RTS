from __future__ import annotations

import argparse
import json
from pathlib import Path

from fear_gate import apply_fear_gate
from one_small_step import evaluate as core_evaluate


def evaluate(case: dict) -> dict:
    """Canonical ONE SMALL STEP v0.1 evaluator entrypoint."""
    return apply_fear_gate(case, core_evaluate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a ONE SMALL STEP guidance case")
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    report = evaluate(case)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] not in {"REVIEW_REQUIRED", "NEEDS_RISK_BOUNDING"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
