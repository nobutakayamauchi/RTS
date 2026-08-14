from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROFILE_FIELDS = ("capabilities", "constraints", "current_state")
PROGRESS_AXES = (
    "outcome",
    "capability",
    "knowledge",
    "uncertainty_reduction",
    "risk_reduction",
    "preservation",
)
VALID_CAPACITY = {"NORMAL", "LIMITED", "MINIMAL", "NONE"}
VALID_GOAL_STATUS = {"EXPLORING", "HYPOTHESIS", "CONFIRMED", "INVALIDATED"}
VALID_RESULT = {"SUCCESS", "FAILURE", "UNKNOWN", "NOT_RUN"}
VALID_EVIDENCE_CONFIDENCE = {"UNKNOWN", "HYPOTHESIS", "SUPPORTED", "VERIFIED"}
VALID_METRIC_VALIDITY = {"UNKNOWN", "HYPOTHESIS", "SUPPORTED", "VERIFIED", "INVALID"}


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _evidence_refs(section: dict[str, Any] | None) -> list[str]:
    if not section:
        return []
    refs = section.get("evidence_refs") or []
    return [str(ref).strip() for ref in refs if str(ref).strip()]


def _progress(case: dict[str, Any]) -> dict[str, bool]:
    progress = case.get("progress") or {}
    return {axis: bool(progress.get(axis)) for axis in PROGRESS_AXES}


def _success_maturity(attempt: dict[str, Any], goal: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    measure = attempt.get("measure") or goal.get("success_measure")
    explanation = attempt.get("success_explanation")
    reproduction = attempt.get("personal_reproduction") == "VERIFIED"
    transfer = attempt.get("transfer_reproduction") == "VERIFIED"
    method = attempt.get("reusable_method")
    boundaries = attempt.get("boundary_conditions")
    refs = _evidence_refs(attempt)

    level = "SUCCESS_1"
    if _nonempty(measure) and _nonempty(explanation):
        level = "SUCCESS_2"
    if level == "SUCCESS_2" and reproduction:
        level = "SUCCESS_3"
    if level == "SUCCESS_3" and transfer:
        level = "SUCCESS_4"
    if level == "SUCCESS_4" and _nonempty(method) and _nonempty(boundaries) and refs:
        level = "GOLD_EXPERIENCE_SUCCESS"
    else:
        if level == "SUCCESS_4" and not refs:
            reasons.append("Transferable success remains unverified without evidence references.")
        if level == "SUCCESS_4" and not _nonempty(method):
            reasons.append("Transferable success is not yet retained as a reusable method.")
        if level == "SUCCESS_4" and not _nonempty(boundaries):
            reasons.append("A reusable success method needs explicit boundary conditions.")
    return level, reasons


def _failure_maturity(attempt: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    observed = attempt.get("observed")
    failure_measure = attempt.get("failure_measure")
    cause_confidence = attempt.get("cause_confidence", "UNKNOWN")
    cause = attempt.get("cause")
    prevention = attempt.get("prevention_method")
    prevention_test = attempt.get("prevention_test")
    refs = _evidence_refs(attempt)

    level = "FAILURE_1"
    if _nonempty(observed) and _nonempty(failure_measure):
        level = "FAILURE_2"
    if level == "FAILURE_2" and _nonempty(cause) and cause_confidence in {"HYPOTHESIS", "SUPPORTED", "VERIFIED"}:
        level = "FAILURE_3"
    if level == "FAILURE_3" and _nonempty(prevention):
        level = "FAILURE_4"
    if level == "FAILURE_4" and prevention_test == "PASS":
        level = "FAILURE_5"
    if level == "FAILURE_5" and cause_confidence == "VERIFIED" and refs:
        level = "GOLD_EXPERIENCE_FAILURE"
    else:
        if cause_confidence == "UNKNOWN":
            reasons.append("Failure cause is unknown; collect discriminating evidence instead of inventing a cause.")
        if level == "FAILURE_5" and cause_confidence != "VERIFIED":
            reasons.append("A passing prevention test does not prove the diagnosed cause without verified causal evidence.")
        if level == "FAILURE_5" and not refs:
            reasons.append("Repeat-prevention is not Gold Experience without retained evidence.")
    return level, reasons


def _experience(case: dict[str, Any]) -> tuple[str, list[str]]:
    attempt = case.get("attempt") or {}
    result = attempt.get("result", "NOT_RUN")
    if result not in VALID_RESULT:
        return "RAW_EXPERIENCE", ["Unknown attempt result; retain as Raw Experience until classified."]

    if _nonempty(attempt.get("contradicting_evidence")) or attempt.get("regression") == "FAIL":
        return "EXPERIENCE_REVIEW_REQUIRED", ["Previously retained experience conflicts with new evidence and must be re-evaluated."]

    if result == "SUCCESS":
        return _success_maturity(attempt, case.get("goal") or {})
    if result == "FAILURE":
        return _failure_maturity(attempt)
    if result == "UNKNOWN":
        return "RAW_EXPERIENCE", ["Observed result remains unknown; preserve evidence and reduce uncertainty before attribution."]
    return "NO_EXPERIENCE_YET", []


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    blocks: list[str] = []
    reasons: list[str] = []
    questions: list[str] = []

    case_id = case.get("case_id")
    if not _nonempty(case_id):
        blocks.append("CASE_ID_MISSING")

    profile = case.get("profile") or {}
    missing_profile = [field for field in PROFILE_FIELDS if not _nonempty(profile.get(field))]
    resources = case.get("resources") or []
    brain_dump = case.get("brain_dump") or []

    capacity = case.get("capacity", "NORMAL")
    if capacity not in VALID_CAPACITY:
        blocks.append("INVALID_CAPACITY")
        capacity = "LIMITED"

    if capacity == "NONE" or case.get("do_not_push") is True:
        experience_status, exp_reasons = _experience(case)
        reasons.extend(exp_reasons)
        return {
            "schema": "one-small-step-report/v0",
            "case_id": case_id,
            "classification": "PRESERVE",
            "phase": "PRESERVE_AND_RESTART",
            "next_step_kind": "CHECKPOINT_ONLY",
            "experience_status": experience_status,
            "progress": _progress(case),
            "blocking_states": sorted(set(blocks)),
            "questions": ["What must be preserved so this can resume without starting over?"],
            "reasons": reasons + ["No forward action is required while capacity is unavailable or push is explicitly disabled."],
        }

    if missing_profile:
        questions.extend(f"Profile: provide {field}." for field in missing_profile)
    if not resources:
        questions.append("List resources that are usable now, including time, tools, evidence, people, money, skills, or services.")
    if not brain_dump:
        questions.append("Brain-dump unresolved pains, obligations, ideas, fears, deadlines, and desired outcomes without ordering them yet.")

    if missing_profile or not resources or not brain_dump:
        return {
            "schema": "one-small-step-report/v0",
            "case_id": case_id,
            "classification": "NEEDS_ORIENTATION",
            "phase": "SELF_PROFILE",
            "next_step_kind": "ORIENT",
            "experience_status": "NO_EXPERIENCE_YET",
            "progress": _progress(case),
            "blocking_states": sorted(set(blocks)),
            "questions": questions,
            "reasons": ["A person who does not know what to do starts by making current reality visible, not by inventing a permanent goal."],
        }

    goal = case.get("goal") or {}
    goal_status = goal.get("status", "EXPLORING")
    if goal_status not in VALID_GOAL_STATUS:
        blocks.append("INVALID_GOAL_STATUS")
        goal_status = "EXPLORING"

    if goal_status == "INVALIDATED":
        return {
            "schema": "one-small-step-report/v0",
            "case_id": case_id,
            "classification": "GOAL_REOPENED",
            "phase": "PAIN_AND_GOAL_DISCOVERY",
            "next_step_kind": "REDEFINE_GOAL",
            "experience_status": _experience(case)[0],
            "progress": _progress(case),
            "blocking_states": sorted(set(blocks)),
            "questions": ["What currently hurts or blocks you most, and what better state would reduce that pain?"],
            "reasons": ["An invalidated goal must not be protected merely because effort has already been invested in it."],
        }

    if not _nonempty(goal.get("statement")):
        return {
            "schema": "one-small-step-report/v0",
            "case_id": case_id,
            "classification": "NEEDS_GOAL_HYPOTHESIS",
            "phase": "PAIN_AND_GOAL_DISCOVERY",
            "next_step_kind": "FORM_TEMPORARY_GOAL",
            "experience_status": "NO_EXPERIENCE_YET",
            "progress": _progress(case),
            "blocking_states": sorted(set(blocks)),
            "questions": ["What is the most immediate pain or problem you want to reduce first?", "What temporary better state would count as relief?"],
            "reasons": ["The first goal may be wrong. It is a revisable hypothesis, not an identity or permanent commitment."],
        }

    metric_validity = goal.get("metric_validity", "UNKNOWN")
    if not _nonempty(goal.get("success_measure")) or metric_validity == "INVALID":
        return {
            "schema": "one-small-step-report/v0",
            "case_id": case_id,
            "classification": "NEEDS_MEASUREMENT",
            "phase": "MEASURE",
            "next_step_kind": "DEFINE_OR_REPAIR_METRIC",
            "experience_status": _experience(case)[0],
            "progress": _progress(case),
            "blocking_states": sorted(set(blocks)),
            "questions": ["What observable change would mean you are closer to the goal?", "Could this metric improve while the real goal gets worse?"],
            "reasons": ["Effort cannot be judged as useful or useless until the goal has an observable, challengeable measure."],
        }

    blocker = case.get("external_blocker") or {}
    if blocker.get("active") is True:
        options = blocker.get("options_considered") or []
        return {
            "schema": "one-small-step-report/v0",
            "case_id": case_id,
            "classification": "BLOCKED",
            "phase": "BLOCKER_REVIEW",
            "next_step_kind": "RESOLVE_BYPASS_REFRAME_OR_PRESERVE",
            "experience_status": _experience(case)[0],
            "progress": _progress(case),
            "blocking_states": sorted(set(blocks + ["EXTERNAL_BLOCKER"])),
            "questions": ["Must this blocker actually be removed to reach the goal?", "Is there a substitute evidence source, bypass, delegation path, or goal reframe?"],
            "reasons": (["No bypass options have been recorded yet."] if not options else ["External blockage is not evidence of insufficient effort."]),
        }

    attempt = case.get("attempt") or {}
    result = attempt.get("result", "NOT_RUN")
    if result not in VALID_RESULT:
        blocks.append("INVALID_ATTEMPT_RESULT")
        reasons.append("Unknown attempt result values fail closed and must be classified before a next action is selected.")

    cause_confidence = attempt.get("cause_confidence", "UNKNOWN")
    if cause_confidence not in VALID_EVIDENCE_CONFIDENCE:
        blocks.append("INVALID_CAUSE_CONFIDENCE")
        reasons.append("Unknown cause-confidence values fail closed; causal certainty must not be invented from an unrecognized label.")
        cause_confidence = "UNKNOWN"

    experience_status, exp_reasons = _experience(case)
    reasons.extend(exp_reasons)
    progress = _progress(case)

    metric_validity = goal.get("metric_validity", "UNKNOWN")
    if metric_validity not in VALID_METRIC_VALIDITY:
        blocks.append("INVALID_METRIC_VALIDITY")
        metric_validity = "UNKNOWN"
    if metric_validity in {"UNKNOWN", "HYPOTHESIS"} and progress.get("outcome"):
        blocks.append("METRIC_UNVALIDATED")
        reasons.append("Strong outcome-progress claims require a supported or verified metric; provisional metrics may guide experiments but not certify progress.")

    effort = case.get("effort") or {}
    if _nonempty(effort) and not any(progress.values()):
        reasons.append("Effort is acknowledged, but no claimed progress axis is currently supported; change the method or measurement rather than merely demanding more effort.")
        blocks.append("EFFORT_EFFECT_GAP")

    step_plan = case.get("step_plan") or {}
    if step_plan:
        required_step_fields = ("action", "expected_signal", "review_boundary", "stop_or_change_rule")
        missing_step_fields = [field for field in required_step_fields if not _nonempty(step_plan.get(field))]
        if missing_step_fields:
            blocks.append("STEP_PLAN_INCOMPLETE")
            reasons.append("A meaningful step needs an action, expected signal, review boundary, and stop/change rule so effort cannot run indefinitely without evaluation.")
            questions.extend(f"Step plan: provide {field}." for field in missing_step_fields)

    if result not in VALID_RESULT:
        next_kind = "CLASSIFY_RESULT_BEFORE_NEXT_STEP"
        phase = "TRACE"
    elif result == "UNKNOWN":
        next_kind = "COLLECT_DISCRIMINATING_EVIDENCE"
        phase = "TRACE"
    elif result == "FAILURE":
        if cause_confidence == "UNKNOWN":
            next_kind = "RECONSTRUCT_EVENT_AND_COLLECT_EVIDENCE"
            phase = "TRACE"
        elif experience_status == "GOLD_EXPERIENCE_FAILURE":
            next_kind = "APPLY_VERIFIED_PREVENTION_TO_NEXT_STEP"
            phase = "NEXT_LIGHT"
        else:
            next_kind = "TEST_PREVENTION_HYPOTHESIS"
            phase = "REFINE"
    elif result == "SUCCESS":
        if experience_status == "GOLD_EXPERIENCE_SUCCESS":
            next_kind = "REUSE_OR_TEACH_METHOD"
            phase = "NEXT_LIGHT"
        else:
            next_kind = "EXPLAIN_REPRODUCE_AND_TRANSFER"
            phase = "REFINE"
    else:
        if step_plan and "STEP_PLAN_INCOMPLETE" not in blocks:
            next_kind = "ACT_AND_OBSERVE"
            phase = "ONE_SMALL_STEP"
        else:
            next_kind = "CHOOSE_SMALLEST_MEANINGFUL_STEP"
            phase = "LIGHT"

    if capacity == "MINIMAL" and next_kind in {"CHOOSE_SMALLEST_MEANING_STEP", "ACT_AND_OBSERVE", "TEST_PREVENTION_HYPOTHESIS", "EXPLAIN_REPRODUCE_AND_TRANSFER"}:
        next_kind = "ONE_DECISION_OR_CHECKPOINT"
        reasons.append("Capacity is minimal; reduce the ask to one bounded decision or preservation action.")

    classification = "READY_FOR_NEXT_STEP" if not blocks else "REVIEW_REQUIRED"
    return {
        "schema": "one-small-step-report/v0",
        "case_id": case_id,
        "classification": classification,
        "phase": phase,
        "next_step_kind": next_kind,
        "experience_status": experience_status,
        "progress": progress,
        "blocking_states": sorted(set(blocks)),
        "questions": questions,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a ONE SMALL STEP guidance case")
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    report = evaluate(case)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] not in {"REVIEW_REQUIRED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
