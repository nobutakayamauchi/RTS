from __future__ import annotations

from typing import Any, Callable

REQUIRED_FEAR_FIELDS = (
    "feared_loss",
    "reversibility",
    "cost_of_inaction",
    "bounded_experiment",
)


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def apply_fear_gate(case: dict[str, Any], core_evaluate: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    """Add fail-closed pre-action fear/risk bounding without overriding earlier core gates."""
    report = core_evaluate(case)
    fear = case.get("fear") or {}
    attempt = case.get("attempt") or {}

    # Orientation, preservation, invalid goal, measurement, blockers, and post-attempt
    # learning all dominate fear review. This gate only runs before an unstarted action.
    if fear.get("active") is not True or attempt.get("result", "NOT_RUN") != "NOT_RUN":
        return report
    if report.get("classification") != "READY_FOR_NEXT_STEP":
        return report
    if report.get("phase") not in {"LIGHT", "ONE_SMALL_STEP"}:
        return report

    missing = [field for field in REQUIRED_FEAR_FIELDS if not _nonempty(fear.get(field))]
    if missing:
        return {
            **report,
            "classification": "NEEDS_RISK_BOUNDING",
            "phase": "RISK_BOUNDING",
            "next_step_kind": "DECOMPOSE_FEAR_AND_BOUND_RISK",
            "blocking_states": sorted(set((report.get("blocking_states") or []) + ["FEAR_NOT_BOUNDED"])),
            "questions": [
                "What exact loss are you afraid of?",
                "If it happens, how reversible is it?",
                "What is the cost of not trying?",
                "What is the smallest bounded experiment that can learn something without taking the full risk?",
            ],
            "reasons": (report.get("reasons") or []) + [
                "Fear is treated as risk information to decompose, not as a character flaw or a command to be brave."
            ],
        }

    return {
        **report,
        "reasons": (report.get("reasons") or []) + [
            "Fear has been bounded into explicit loss, reversibility, inaction cost, and a smaller experiment; proceed only within those bounds."
        ],
    }
