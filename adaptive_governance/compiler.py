from __future__ import annotations

from typing import Any

from .models import PLAN_SCHEMA, AdaptiveGovernanceError, fingerprint, fingerprint_material, validate_context, validate_plan

PROFILES: dict[str, dict[str, Any]] = {
    "G0": {
        "human_approvals": 0,
        "independent_review": False,
        "preflight": False,
        "rollback": "NOT_REQUIRED",
        "test_scope": "DIFF_ONLY",
        "execution_mode": "AUTOMATED",
        "max_pull_requests": 1,
        "max_governance_steps": 3,
    },
    "G1": {
        "human_approvals": 0,
        "independent_review": False,
        "preflight": False,
        "rollback": "REQUIRED",
        "test_scope": "FOCUSED",
        "execution_mode": "AUTOMATED",
        "max_pull_requests": 1,
        "max_governance_steps": 4,
    },
    "G2": {
        "human_approvals": 1,
        "independent_review": False,
        "preflight": True,
        "rollback": "REQUIRED",
        "test_scope": "FOCUSED",
        "execution_mode": "HUMAN_TRIGGERED",
        "max_pull_requests": 1,
        "max_governance_steps": 6,
    },
    "G3": {
        "human_approvals": 1,
        "independent_review": True,
        "preflight": True,
        "rollback": "REQUIRED_AND_TESTED",
        "test_scope": "FULL",
        "execution_mode": "HUMAN_TRIGGERED",
        "max_pull_requests": 2,
        "max_governance_steps": 9,
    },
    "G4": {
        "human_approvals": 2,
        "independent_review": True,
        "preflight": True,
        "rollback": "REQUIRED_AND_TESTED",
        "test_scope": "FULL",
        "execution_mode": "MANUAL",
        "max_pull_requests": 2,
        "max_governance_steps": 12,
    },
}


def _raise_level(current: str, candidate: str) -> str:
    order = tuple(PROFILES)
    return order[max(order.index(current), order.index(candidate))]


def classify_context(context: dict[str, Any]) -> tuple[str, list[str]]:
    impact = context["impact"]
    kinds = set(context["change_kinds"])
    actions = set(context["requested_actions"])
    level = "G0"
    reasons: list[str] = []

    if (
        not impact["read_only"]
        or impact["repository_scope"] != "LOCAL"
        or kinds - {"DOCUMENTATION", "TEST"}
        or actions - {"READ"}
    ):
        level = _raise_level(level, "G1")
        reasons.append("LOCAL_CHANGE")
    if (
        impact["touches_approval_flow"]
        or impact["historical_failure"]
        or impact["uncertainty"] == "HIGH"
        or bool(kinds & {"SCHEMA", "WORKFLOW"})
    ):
        level = _raise_level(level, "G2")
        reasons.append("GOVERNED_OR_HIGH_UNCERTAINTY_CHANGE")
    if (
        impact["handles_personal_data"]
        or impact["handles_sensitive_material"]
        or impact["repository_scope"] in {"ADJACENT", "EXTERNAL"}
        or impact["external_action"]
        or bool(actions & {"WRITE_ADJACENT", "NETWORK", "PUBLISH", "DEPLOY", "MESSAGE", "MERGE"})
    ):
        level = _raise_level(level, "G3")
        reasons.append("EXTERNAL_OR_SENSITIVE_BOUNDARY")
    if impact["financial_or_contractual"] or (impact["production_effect"] and not impact["reversible"]):
        level = _raise_level(level, "G4")
        reasons.append("CRITICAL_OR_IRREVERSIBLE_EFFECT")
    elif impact["production_effect"]:
        level = _raise_level(level, "G3")
        reasons.append("PRODUCTION_EFFECT")
    if impact["emergency"]:
        reasons.append("EMERGENCY_DOES_NOT_LOWER_GOVERNANCE")
    if impact["read_only"]:
        reasons.append("READ_ONLY_BOUNDARY")
    if impact["reversible"]:
        reasons.append("REVERSIBLE_CHANGE")
    if not reasons:
        reasons.append("MINIMAL_INTERNAL_CHANGE")
    return level, sorted(set(reasons))


def _workflow(level: str, context: dict[str, Any], requirements: dict[str, Any]) -> list[dict[str, Any]]:
    if level == "G0":
        steps: list[tuple[str, str, bool]] = [
            ("CLASSIFY", "Validate context and confirm the minimal G0 boundary.", False),
            ("CHANGE_AND_VERIFY", "Make the bounded change and verify the exact diff.", False),
            ("COMPLETE", "Record completion and leave application authority disabled.", False),
        ]
    else:
        steps = [
            ("CLASSIFY_AND_PREFLIGHT", "Validate context and compile the minimum governance plan.", requirements["preflight"]),
        ]
        if requirements["human_approvals"]:
            steps.append(("HUMAN_APPROVAL", "Obtain the required explicit human approval for this exact plan.", True))
        if requirements["independent_review"]:
            steps.append(("INDEPENDENT_REVIEW", "Perform an independent review separated from proposer and implementer.", True))
        steps.append(("IMPLEMENT", "Implement only the approved scope without widening authority.", False))
        validation = f"Run {requirements['test_scope']} validation, verify rollback when required, and preserve deterministic evidence."
        steps.append(("VALIDATE_AND_EVIDENCE", validation, False))
        if level in {"G3", "G4"}:
            steps.append(("STAGED_CHECKPOINT", "Stop for a final checkpoint before any separately authorized external effect.", True))
        steps.append(("COMPLETE", "Record completion and leave application authority disabled.", False))
    return [
        {"order": index, "step_id": step_id, "description": description, "human_gate": human_gate}
        for index, (step_id, description, human_gate) in enumerate(steps, start=1)
    ]


def _prohibitions(context: dict[str, Any]) -> list[str]:
    prohibitions = {"AUTHORITY_ESCALATION", "SELF_APPROVAL", "UNRECORDED_POLICY_RELAXATION"}
    impact = context["impact"]
    if impact["read_only"]:
        prohibitions.update({"MUTATION", "TARGET_WRITE"})
    if impact["repository_scope"] == "LOCAL":
        prohibitions.add("ADJACENT_REPOSITORY_WRITE")
    if not impact["external_action"]:
        prohibitions.add("EXTERNAL_ACTION")
    return sorted(prohibitions)


def _governance_cost(implementation_steps: int, governance_steps: int) -> dict[str, Any]:
    ratio = round(governance_steps / implementation_steps, 2)
    warnings: list[str] = []
    if governance_steps >= 5 and ratio > 2.5:
        status = "OVER_GOVERNED"
        warnings.append("GOVERNANCE_EXCEEDS_2_5X_IMPLEMENTATION")
    elif ratio > 1.5:
        status = "HEAVY"
        warnings.append("GOVERNANCE_EXCEEDS_1_5X_IMPLEMENTATION")
    else:
        status = "BALANCED"
    return {
        "implementation_steps": implementation_steps,
        "governance_steps": governance_steps,
        "ratio": ratio,
        "status": status,
        "warnings": sorted(warnings),
    }


def compile_plan(raw_context: dict[str, Any]) -> dict[str, Any]:
    context = validate_context(raw_context)
    level, reasons = classify_context(context)
    requirements = dict(PROFILES[level])
    workflow = _workflow(level, context, requirements)
    if len(workflow) > requirements["max_governance_steps"]:
        raise RuntimeError("internal governance profile exceeded its own step budget")
    plan = {
        "schema_version": PLAN_SCHEMA,
        "change_id": context["change_id"],
        "context_fingerprint": fingerprint(context),
        "level": level,
        "classification_reasons": reasons,
        "requirements": requirements,
        "workflow": workflow,
        "prohibitions": _prohibitions(context),
        "governance_cost": _governance_cost(context["estimated_implementation_steps"], len(workflow)),
        "authority": {
            "approval_status": "REVIEW_REQUIRED",
            "application_status": "NOT_APPLIED",
            "self_approval_authorized": False,
            "mutation_authorized": False,
            "merge_authorized": False,
            "external_action_authorized": False,
        },
        "plan_fingerprint": "",
    }
    plan["plan_fingerprint"] = fingerprint(fingerprint_material(plan, "plan_fingerprint"))
    return validate_plan(plan)


def verify_plan(raw_plan: dict[str, Any], raw_context: dict[str, Any]) -> dict[str, Any]:
    plan = validate_plan(raw_plan)
    context = validate_context(raw_context)
    if plan["context_fingerprint"] != fingerprint(context):
        raise AdaptiveGovernanceError("plan does not match the supplied context")
    expected = compile_plan(context)
    if plan != expected:
        raise AdaptiveGovernanceError("plan is not the deterministic compiled result")
    return plan
