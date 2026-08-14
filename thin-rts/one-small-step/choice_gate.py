from __future__ import annotations

from typing import Any, Callable

VALID_MATERIALITY = {"LOW", "MATERIAL", "HIGH_STAKES"}
VALID_REVERSIBILITY = {"REVERSIBLE", "PARTIAL", "IRREVERSIBLE", "UNKNOWN"}
VALID_SEVERE_RISK = {"NONE", "POSSIBLE", "MATERIAL", "UNKNOWN"}

REQUIRED_MATERIAL_FIELDS = (
    "values_or_priorities",
    "expected_gains",
    "accepted_costs_or_losses",
    "alternatives_considered",
    "reversibility",
    "severe_or_irreversible_harm_risk",
    "counterevidence_or_reasons_to_stop",
)


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _field_recorded(mapping: dict[str, Any], key: str) -> bool:
    """Some fields may legitimately record an empty set, but must be explicit."""
    if key not in mapping:
        return False
    if key == "accepted_costs_or_losses":
        return mapping.get(key) is not None
    return _nonempty(mapping.get(key))


def apply_choice_gate(
    case: dict[str, Any],
    core_evaluate: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Bound material choices without turning the system into a life-decision authority."""
    report = core_evaluate(case)
    choice = case.get("choice") or {}
    attempt = case.get("attempt") or {}

    # Earlier core gates and post-attempt learning remain authoritative.
    if choice.get("active") is not True or attempt.get("result", "NOT_RUN") != "NOT_RUN":
        return report
    if report.get("classification") != "READY_FOR_NEXT_STEP":
        return report
    if report.get("phase") not in {"LIGHT", "ONE_SMALL_STEP"}:
        return report

    materiality = choice.get("materiality", "MATERIAL")
    if materiality not in VALID_MATERIALITY:
        return {
            **report,
            "classification": "NEEDS_CHOICE_REVIEW",
            "phase": "CHOICE_REVIEW",
            "next_step_kind": "CLASSIFY_CHOICE_MATERIALITY",
            "blocking_states": sorted(set((report.get("blocking_states") or []) + ["INVALID_CHOICE_MATERIALITY"])),
            "decision_owner": "USER",
            "reasons": (report.get("reasons") or []) + [
                "The system cannot infer how consequential a choice is from an unknown materiality label."
            ],
        }

    # Low-consequence choices should not be buried in life-review overhead.
    if materiality == "LOW":
        return {
            **report,
            "decision_owner": "USER",
            "reasons": (report.get("reasons") or []) + [
                "This is a low-consequence choice; the system does not require a full values/trade-off review."
            ],
        }

    missing = [field for field in REQUIRED_MATERIAL_FIELDS if not _field_recorded(choice, field)]
    reversibility = choice.get("reversibility", "UNKNOWN")
    severe_risk = choice.get("severe_or_irreversible_harm_risk", "UNKNOWN")

    if reversibility not in VALID_REVERSIBILITY:
        missing.append("valid reversibility classification")
    if severe_risk not in VALID_SEVERE_RISK:
        missing.append("valid severe-risk classification")

    if missing:
        return {
            **report,
            "classification": "NEEDS_CHOICE_REVIEW",
            "phase": "CHOICE_REVIEW",
            "next_step_kind": "MAP_GAINS_LOSSES_ALTERNATIVES_AND_REVERSIBILITY",
            "blocking_states": sorted(set((report.get("blocking_states") or []) + ["CHOICE_NOT_INFORMED_ENOUGH"])),
            "decision_owner": "USER",
            "questions": [
                "What matters most to you in this choice?",
                "What might you gain, and what cost or loss are you knowingly accepting?",
                "What credible alternatives exist?",
                "How reversible is this choice?",
                "What evidence or outcome would make you stop, change course, or choose differently?",
            ],
            "reasons": (report.get("reasons") or []) + [
                "ONE SMALL STEP does not supply a universal life answer; material choices need enough information for the user to own the trade-off."
            ],
        }

    # Autonomy does not require the system to normalize unresolved severe/irreversible harm.
    if severe_risk == "MATERIAL" or (
        severe_risk in {"POSSIBLE", "UNKNOWN"}
        and (materiality == "HIGH_STAKES" or reversibility in {"IRREVERSIBLE", "UNKNOWN"})
    ):
        return {
            **report,
            "classification": "SAFETY_REVIEW_REQUIRED",
            "phase": "SAFETY_BOUNDARY",
            "next_step_kind": "REDUCE_IRREVERSIBILITY_OR_SEEK_QUALIFIED_REVIEW",
            "blocking_states": sorted(set((report.get("blocking_states") or []) + ["SEVERE_OR_IRREVERSIBLE_RISK_UNRESOLVED"])),
            "decision_owner": "USER",
            "questions": [
                "Can the same objective be tested with a smaller, more reversible step?",
                "What evidence would reduce uncertainty about the severe downside?",
                "Does this domain require qualified professional, legal, medical, financial, safety, or other external review before acting?",
            ],
            "reasons": (report.get("reasons") or []) + [
                "The system does not choose the user's life path, but it must not convert unresolved severe or irreversible harm into a normal next-step recommendation."
            ],
        }

    return {
        **report,
        "decision_owner": "USER",
        "choice_status": "INFORMED_CHOICE_READY",
        "reasons": (report.get("reasons") or []) + [
            "Trade-offs, alternatives, reversibility, and counterevidence are recorded. This does not certify the choice as universally correct; the choice remains the user's and may be revised as evidence or values change."
        ],
    }
