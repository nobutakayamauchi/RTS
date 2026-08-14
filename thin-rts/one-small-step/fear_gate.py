from __future__ import annotations

from typing import Any, Callable

REQUIRED_FEAR_FIELDS = (
    "feared_loss",
    "reversibility",
    "cost_of_inaction",
    "bounded_experiment",
)

VALID_FEAR_REVERSIBILITY = {"REVERSIBLE"}


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _risk_review(report: dict[str, Any], reason: str, block: str) -> dict[str, Any]:
    return {
        **report,
        "classification": "NEEDS_RISK_BOUNDING",
        "phase": "RISK_BOUNDING",
        "next_step_kind": "DECOMPOSE_FEAR_AND_BOUND_RISK",
        "blocking_states": sorted(set((report.get("blocking_states") or []) + [block])),
        "questions": [
            "What exact loss are you afraid of?",
            "Can the experiment be made genuinely reversible?",
            "What is the cost of not trying?",
            "Does the planned action exactly match the bounded experiment you intend to test?",
        ],
        "reasons": (report.get("reasons") or []) + [reason],
    }


def apply_fear_gate(case: dict[str, Any], core_evaluate: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    """Add fail-closed pre-action fear/risk bounding without overriding earlier core gates."""
    report = core_evaluate(case)
    fear = case.get("fear") or {}
    attempt = case.get("attempt") or {}

    # Orientation, preservation, invalid goal, measurement, blockers, material-choice
    # safety, and post-attempt learning all dominate fear review. This gate only runs
    # before an unstarted action.
    if fear.get("active") is not True or attempt.get("result", "NOT_RUN") != "NOT_RUN":
        return report
    if report.get("classification") != "READY_FOR_NEXT_STEP":
        return report
    if report.get("phase") not in {"LIGHT", "ONE_SMALL_STEP"}:
        return report

    missing = [field for field in REQUIRED_FEAR_FIELDS if not _nonempty(fear.get(field))]
    if missing:
        return _risk_review(
            report,
            "Fear is treated as risk information to decompose, not as a character flaw or a command to be brave.",
            "FEAR_NOT_BOUNDED",
        )

    if fear.get("reversibility") not in VALID_FEAR_REVERSIBILITY:
        return _risk_review(
            report,
            "A bounded experiment must be explicitly reversible before fear/risk review may return the normal action path.",
            "FEAR_EXPERIMENT_NOT_REVERSIBLE",
        )

    step_plan = case.get("step_plan") or {}
    planned_action = step_plan.get("action")
    bounded_experiment = fear.get("bounded_experiment")
    if _nonempty(planned_action) and planned_action != bounded_experiment:
        return _risk_review(
            report,
            "The planned action does not match the bounded experiment. A small reversible experiment cannot authorize a larger unrelated action.",
            "FEAR_EXPERIMENT_ACTION_MISMATCH",
        )

    return {
        **report,
        "reasons": (report.get("reasons") or []) + [
            "Fear has been bounded into explicit loss, a reversible experiment, inaction cost, and an action that matches the experiment; proceed only within those bounds."
        ],
    }
