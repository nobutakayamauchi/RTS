from __future__ import annotations

import argparse
import json
from pathlib import Path

from choice_gate import apply_choice_gate
from fear_gate import apply_fear_gate
from one_small_step import evaluate as core_evaluate


def _core_with_choice(case: dict) -> dict:
    return apply_choice_gate(case, core_evaluate)


def evaluate(case: dict) -> dict:
    """Canonical ONE SMALL STEP v0.1 evaluator entrypoint."""
    # Core orientation/capacity/goal gates run first, then material-choice
    # autonomy/safety review, then fear/risk decomposition for an otherwise
    # actionable step. A blocked choice cannot be bypassed by the fear gate.
    return apply_fear_gate(case, _core_with_choice)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a ONE SMALL STEP guidance case")
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    report = evaluate(case)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    blocked = {
        "REVIEW_REQUIRED",
        "NEEDS_RISK_BOUNDING",
        "NEEDS_CHOICE_REVIEW",
        "SAFETY_REVIEW_REQUIRED",
    }
    return 0 if report["classification"] not in blocked else 2


if __name__ == "__main__":
    raise SystemExit(main())
