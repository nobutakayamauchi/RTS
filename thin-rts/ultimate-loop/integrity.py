from __future__ import annotations

from typing import Any

REENTRY_MAP = {
    "DISCOVERY": "DISCOVERY_REFRESH",
    "IMPLEMENTATION": "DA_COUNTER_DA",
    "DEPLOYMENT": "DEPLOYMENT_IDENTITY",
    "POST_DEPLOY_METRIC": "POST_DEPLOY_DEBUG",
}

COERCIVE_PRESSURES = {
    "SUNK_COST_LEVERAGE",
    "HIDDEN_DECLINE_PATH",
    "PRECHECKED_APPROVAL",
    "DECEPTIVE_DEFAULT",
    "SOCIAL_COERCION",
    "PENALTY_FOR_REFUSAL_NOT_INTRINSIC_TO_ACTION",
}


def assess_reentry(failure: dict[str, Any] | None) -> dict[str, Any]:
    if not failure:
        return {"state": "NOT_ASSESSED", "route": "NONE", "blocking_states": [], "reasons": []}

    blocks: list[str] = []
    reasons: list[str] = []
    stage = failure.get("stage")
    causality = failure.get("causality_state", "UNKNOWN")

    if stage not in REENTRY_MAP:
        blocks.append("FAILURE_STAGE_UNKNOWN")
        reasons.append("Unknown failure stage must reopen analysis instead of guessing a local gate.")
        return {"state": "ANALYSIS_REOPEN", "route": "ANALYSIS_REOPEN", "blocking_states": blocks, "reasons": reasons}

    if causality != "PROVEN":
        reasons.append("Correlation or incomplete causality cannot authorize smallest-gate routing.")
        return {"state": "ANALYSIS_REOPEN", "route": "ANALYSIS_REOPEN", "blocking_states": blocks, "reasons": reasons}

    return {"state": "ROUTED", "route": REENTRY_MAP[stage], "blocking_states": blocks, "reasons": reasons}


def assess_evidence(profile: dict[str, Any] | None) -> dict[str, Any]:
    if not profile:
        return {"state": "NOT_ASSESSED", "blocking_states": [], "reasons": []}

    blocks: list[str] = []
    reasons: list[str] = []

    if profile.get("inference_treated_as") == "OBSERVED_FACT":
        blocks.append("INFERENCE_MASQUERADES_AS_OBSERVATION")

    measured = set(profile.get("measured_properties") or [])
    claimed = set(profile.get("claimed_properties") or [])
    if claimed:
        unsupported = sorted(claimed - measured)
        if unsupported and profile.get("construct_mapping_state") != "VALIDATED":
            blocks.extend(f"UNSUPPORTED_PROXY_CLAIM:{item}" for item in unsupported)

    frozen_ref = profile.get("frozen_reference_class_ref")
    current_ref = profile.get("current_reference_class_ref")
    comparison_claim = profile.get("comparison_claim")
    if frozen_ref and current_ref and frozen_ref != current_ref:
        if comparison_claim in {"IMPROVED", "REGRESSED", "BETTER", "WORSE", "DELTA"}:
            if profile.get("paired_old_reference_evidence") != "PASS":
                blocks.append("REFERENCE_CLASS_SHIFT_CONTAMINATES_DELTA")

    evidence_cohort = profile.get("evidence_cohort_ref")
    claim_population = profile.get("claim_population_ref")
    if profile.get("claim_scope") == "POPULATION_GENERALIZATION" and evidence_cohort and claim_population:
        if (evidence_cohort != claim_population or profile.get("selection_history_state") == "BOUND") and profile.get("transportability_state") != "VALIDATED":
            blocks.append("SELECTED_COHORT_NOT_POPULATION_EVIDENCE")

    if profile.get("intervention_history_state") == "BOUND" and profile.get("post_intervention_claim") in {"INTRINSIC_PROPERTY", "CAUSAL_EFFECT"}:
        if profile.get("causal_identification_state") != "VALIDATED_OR_BOUNDED":
            blocks.append("INTERVENTION_CONTAMINATES_INTRINSIC_OR_CAUSAL_CLAIM")

    scope_relation = profile.get("scope_relation")
    if scope_relation in {"EVIDENCE_NARROWER_THAN_CLAIM", "CLAIM_NARROWER_THAN_EVIDENCE", "UNRELATED"}:
        if profile.get("scope_bridge_validation_state") != "PASS":
            blocks.append("ABSTRACTION_LEVEL_DRIFT")

    if (
        profile.get("context_definition_state") == "EVIDENCE_BOUND"
        and profile.get("context_materiality_state") == "MATERIAL"
        and profile.get("context_outcome_state") in {"FAIL", "UNKNOWN"}
        and profile.get("posthoc_only") is not True
    ):
        blocks.append("MATERIAL_CONTEXT_PREVENTS_GLOBAL_PASS")

    if blocks:
        reasons.append("Evidence claims must remain bound to what was observed, measured, compared, selected, intervened on, and scoped.")
        return {"state": "BLOCKED", "blocking_states": sorted(set(blocks)), "reasons": reasons}

    return {"state": "PASS", "blocking_states": [], "reasons": reasons}


def assess_freshness(artifacts: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not artifacts:
        return {"state": "NOT_ASSESSED", "stale_artifacts": [], "blocking_states": [], "reasons": []}

    blocks: list[str] = []
    stale: list[str] = []
    reasons: list[str] = []

    for artifact in artifacts:
        artifact_id = artifact.get("id", "UNKNOWN")
        if artifact.get("dependency_binding_state") != "BOUND":
            blocks.append(f"DERIVATION_DEPENDENCY_UNBOUND:{artifact_id}")
            stale.append(artifact_id)
            continue

        dependencies = set(artifact.get("dependency_fields") or [])
        changed = set(artifact.get("changed_upstream_fields") or [])
        if not dependencies:
            blocks.append(f"DERIVATION_DEPENDENCY_EMPTY:{artifact_id}")
            stale.append(artifact_id)
            continue

        impacted = dependencies & changed
        if not impacted:
            continue

        current = artifact.get("current_upstream_revision")
        derived = artifact.get("derived_from_upstream_revision")
        recomputed = artifact.get("recomputed_from_current") is True and derived == current
        revalidated = artifact.get("bounded_revalidation_state") == "PASS"
        if not recomputed and not revalidated:
            stale.append(artifact_id)
            blocks.extend(f"STALE_DEPENDENCY:{artifact_id}:{field}" for field in sorted(impacted))

    if blocks:
        reasons.append("Only artifacts whose declared consumed upstream fields changed are stale; stale artifacts require recomputation or bounded revalidation before consequential reuse.")
        return {"state": "STALE", "stale_artifacts": sorted(set(stale)), "blocking_states": sorted(set(blocks)), "reasons": reasons}

    return {"state": "PASS", "stale_artifacts": [], "blocking_states": [], "reasons": reasons}


def assess_human_gate(gate: dict[str, Any] | None) -> dict[str, Any]:
    if not gate or gate.get("source") != "HUMAN_GATE":
        return {"state": "NOT_APPLICABLE", "blocking_states": [], "reasons": []}

    blocks: list[str] = []
    reasons: list[str] = []

    if gate.get("decline_path_state") != "VISIBLE_AND_ACTIONABLE":
        blocks.append("MEANINGFUL_DECLINE_PATH_MISSING")
    if gate.get("material_consequence_disclosure_state") != "PASS":
        blocks.append("MATERIAL_CONSEQUENCES_NOT_DISCLOSED")
    if gate.get("current_decision_state") != "EXPLICIT_CURRENT":
        blocks.append("CURRENT_HUMAN_DECISION_MISSING")

    pressure = set(gate.get("system_applied_pressure") or [])
    blocks.extend(f"AGENCY_PRESSURE:{item}" for item in sorted(pressure & COERCIVE_PRESSURES))

    if blocks:
        reasons.append("A consequential Human Gate is not meaningful authorization when refusal is obscured, consequences are undisclosed, the decision is stale, or the system applies coercive choice architecture.")
        return {"state": "BLOCKED", "blocking_states": sorted(set(blocks)), "reasons": reasons}

    return {"state": "PASS", "blocking_states": [], "reasons": reasons}


def assess_decision_succession(profile: dict[str, Any] | None) -> dict[str, Any]:
    if not profile:
        return {"state": "NOT_ASSESSED", "blocking_states": [], "reasons": []}

    blocks: list[str] = []
    reasons: list[str] = []

    if profile.get("canonical_material_state") != "PASS":
        blocks.append("CANONICAL_MATERIAL_UNPROVEN")
    if profile.get("held_out_decision_state") != "PASS":
        blocks.append("HELD_OUT_DECISIONS_UNPROVEN")
    if profile.get("authority_compliance_state") != "PASS":
        blocks.append("SUCCESSOR_AUTHORITY_COMPLIANCE_UNPROVEN")
    if profile.get("escalation_state") != "PASS":
        blocks.append("SUCCESSOR_ESCALATION_UNPROVEN")
    if profile.get("creator_intervention") is not False:
        blocks.append("CREATOR_INDEPENDENCE_UNPROVEN")

    if blocks:
        if profile.get("retrieval_state") == "PASS" and profile.get("held_out_decision_state") != "PASS":
            reasons.append("Retrieval or PHOENIX regeneration evidence is not decision competence.")
        return {"state": "NOT_READY", "blocking_states": sorted(set(blocks)), "reasons": reasons}

    return {"state": "DECISION_SUCCESSION_READY", "blocking_states": [], "reasons": reasons}


def evaluate(profile: dict[str, Any] | None) -> dict[str, Any]:
    profile = profile or {}
    reentry = assess_reentry(profile.get("failure_evidence"))
    evidence = assess_evidence(profile.get("evidence"))
    freshness = assess_freshness(profile.get("derived_artifacts"))
    human_gate = assess_human_gate(profile.get("human_gate"))
    succession = assess_decision_succession(profile.get("decision_succession"))

    blocks = sorted(set(
        reentry["blocking_states"]
        + evidence["blocking_states"]
        + freshness["blocking_states"]
        + human_gate["blocking_states"]
    ))
    reasons = reentry["reasons"] + evidence["reasons"] + freshness["reasons"] + human_gate["reasons"]

    return {
        "schema": "ultimate-loop-integrity-report/v0",
        "classification": "PASS" if not blocks else "UNKNOWN_OR_BLOCKED",
        "reentry_state": reentry["state"],
        "reentry_route": reentry["route"],
        "evidence_state": evidence["state"],
        "freshness_state": freshness["state"],
        "stale_artifacts": freshness["stale_artifacts"],
        "human_gate_state": human_gate["state"],
        "decision_succession_state": succession["state"],
        "decision_succession_blocking_states": succession["blocking_states"],
        "blocking_states": blocks,
        "reasons": reasons,
        "authority_effect": "NONE",
    }
