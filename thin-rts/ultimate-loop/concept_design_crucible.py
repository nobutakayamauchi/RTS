from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXTENSIONS = {
    "CD_EXT01_SEMANTIC_INVARIANT_ADAPTER_GUARD",
    "CD_EXT02_OBSERVATION_INFERENCE_LAYERING",
    "CD_EXT03_END_TO_END_OBJECTIVE_BINDING",
    "CD_EXT04_CONTEXT_CONDITIONED_TELEMETRY",
    "CD_EXT05_DERIVED_ARTIFACT_STALENESS_PROPAGATION",
    "CD_EXT06_CONTEXT_BOUND_POLICY_SELECTION",
    "CD_EXT07_ABSTRACTION_LEVEL_BINDING",
}


def _base(case: dict[str, Any]) -> tuple[list[str], list[str]]:
    blocks: list[str] = []
    reasons: list[str] = []
    if case.get("extension_id") not in EXTENSIONS:
        blocks.append("UNKNOWN_EXTENSION")
    if not case.get("frozen_workload_ref"):
        blocks.append("FROZEN_WORKLOAD_MISSING")
    if case.get("authority_effect", "NONE") != "NONE":
        blocks.append("AUTHORITY_EFFECT_NOT_NONE")
        reasons.append("A challenger cannot create its own promotion authority.")
    return blocks, reasons


def _ext01(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    protected = case.get("protected_semantic_fingerprint")
    adapters = case.get("adapters") or []
    if not protected:
        blocks.append("PROTECTED_SEMANTICS_MISSING")
    if len(adapters) < 2:
        blocks.append("MULTI_ADAPTER_EVIDENCE_MISSING")
    if case.get("presentation_identity_required") is True:
        blocks.append("PRESENTATION_STYLE_OVERCONSTRAINED")
        reasons.append("Adapter form may differ; only declared protected semantics and provenance are invariant.")
        return "REJECT_STYLE_LOCK"

    for adapter in adapters:
        adapter_id = adapter.get("id", "UNKNOWN")
        if adapter.get("semantic_fingerprint") != protected:
            blocks.append(f"SEMANTIC_DRIFT:{adapter_id}")
        if adapter.get("provenance_state") != "PASS":
            blocks.append(f"PROVENANCE_LOSS:{adapter_id}")

    if blocks:
        return "STANDBY_RESEARCH"
    reasons.append("One semantic core may have multiple presentation forms when protected claims and provenance remain invariant.")
    return "COMPOSE_SEMANTIC_ADAPTER_GUARD"


def _ext02(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    if case.get("raw_observation_state") != "BOUND":
        blocks.append("RAW_OBSERVATION_UNBOUND")

    treatment = case.get("inference_treated_as")
    validation = case.get("independent_validation_state", "UNKNOWN")

    if treatment == "OBSERVED_FACT":
        blocks.append("INFERENCE_MASQUERADES_AS_OBSERVATION")
        reasons.append("A latent need, motive, cause, or interpretation is not first-party observation merely because it is plausible or repeated.")
        return "REJECT_EVIDENCE_COLLAPSE"

    if treatment == "VALIDATED_INFERENCE":
        if validation != "PASS":
            blocks.append("INFERENCE_VALIDATION_UNPROVEN")
            return "STANDBY_RESEARCH"
        reasons.append("Validated interpretation may be promoted only as a separately typed derived fact with its validation evidence attached.")
        return "COMPOSE_TYPED_INFERENCE_LAYER"

    if treatment == "HYPOTHESIS":
        reasons.append("Unvalidated interpretation may guide a falsifiable probe but must remain distinct from observed evidence.")
        return "COMPOSE_TYPED_INFERENCE_LAYER"

    blocks.append("INFERENCE_TREATMENT_UNKNOWN")
    return "ANALYSIS_REOPEN"


def _ext03(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    downstream_surface = case.get("downstream_surface") is True
    mandatory = case.get("mandatory_for_all_workloads") is True
    if not downstream_surface:
        if mandatory:
            blocks.append("DOWNSTREAM_OBJECTIVE_FORCED_ON_INAPPLICABLE_WORKLOAD")
            return "REJECT_UNIVERSAL_GATE"
        return "NOT_APPLICABLE_PROFILE"

    protected = case.get("protected_downstream_outcome_state", "UNKNOWN")
    local = case.get("local_metric_state", "UNKNOWN")
    promotion = case.get("local_change_promotion_requested") is True

    if protected == "FAIL" and promotion:
        blocks.append("LOCAL_WIN_MASKS_END_TO_END_REGRESSION")
        reasons.append("A local metric improvement cannot authorize promotion while the frozen protected downstream outcome materially regresses.")
        return "BLOCK_LOCAL_PROMOTION"
    if protected == "UNKNOWN" and promotion:
        blocks.append("DOWNSTREAM_OUTCOME_UNKNOWN")
        reasons.append("UNKNOWN downstream outcome cannot be converted into a pass by a local metric win.")
        return "BLOCK_LOCAL_PROMOTION"
    if protected == "PASS":
        reasons.append("Local optimization is admissible only because the protected end-to-end outcome remains satisfied under the frozen workload.")
        return "COMPOSE_END_TO_END_OBJECTIVE_GUARD"
    if local == "FAIL":
        return "ANALYSIS_REOPEN"
    return "ANALYSIS_REOPEN"


def _ext04(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    aggregate = case.get("aggregate_state", "UNKNOWN")
    context_state = case.get("context_definition_state", "UNKNOWN")
    material = case.get("context_materiality_state", "UNKNOWN")
    context_outcome = case.get("context_outcome_state", "UNKNOWN")
    posthoc = case.get("posthoc_only") is True

    if posthoc or context_state != "EVIDENCE_BOUND" or material != "MATERIAL":
        reasons.append("Arbitrary or immaterial post-hoc segmentation cannot veto the aggregate result.")
        return "IGNORE_NONMATERIAL_CONTEXT"

    if context_outcome == "FAIL" and aggregate in {"PASS", "NEUTRAL"}:
        blocks.append("AGGREGATE_MASKS_MATERIAL_CONTEXT_FAILURE")
        reasons.append("A material evidence-bound cohort/context failure blocks global diagnosis and requires targeted analysis.")
        return "TARGETED_ANALYSIS_REOPEN"
    if context_outcome == "UNKNOWN":
        reasons.append("Material context exists but its outcome is UNKNOWN; do not infer uniform effect from the aggregate.")
        return "TARGETED_ANALYSIS_REOPEN"
    if context_outcome == "PASS":
        return "COMPOSE_CONTEXT_CONDITIONED_TELEMETRY_GUARD"
    return "ANALYSIS_REOPEN"


def _ext05(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    dependency_state = case.get("dependency_binding_state", "UNKNOWN")
    dependency_fields = set(case.get("dependency_fields") or [])
    changed_fields = set(case.get("changed_upstream_fields") or [])
    derived_from = case.get("derived_from_upstream_revision")
    current = case.get("current_upstream_revision")
    recomputed = case.get("recomputed_from_current") is True
    bounded_revalidation = case.get("bounded_revalidation_state", "UNKNOWN")

    if dependency_state != "BOUND" or not dependency_fields:
        blocks.append("DERIVATION_DEPENDENCY_UNBOUND")
        reasons.append("A derived artifact cannot prove freshness when the upstream fields it depends on are unknown.")
        return "BLOCK_DERIVED_FRESHNESS_CLAIM"

    impacted = sorted(dependency_fields & changed_fields)
    if not impacted:
        reasons.append("The upstream revision changed, but no declared dependency field used by this artifact changed.")
        return "CURRENT_UNAFFECTED_BY_DECLARED_CHANGE"

    if derived_from == current and recomputed:
        return "CURRENT_DERIVATION_BOUND"

    if bounded_revalidation == "PASS":
        reasons.append("A stale derivation may remain usable only when the affected dependency slice is explicitly revalidated against the current upstream revision.")
        return "CURRENT_BY_BOUNDED_REVALIDATION"

    blocks.extend(f"STALE_DEPENDENCY:{field}" for field in impacted)
    reasons.append("Changing an upstream decision invalidates downstream artifacts that consumed that field until they are recomputed or explicitly revalidated.")
    return "STALE_RECOMPUTE_REQUIRED"


def _ext06(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    policy = case.get("policy_ref")
    applicability = case.get("applicability_state", "UNKNOWN")
    frozen_context = case.get("frozen_context_ref")
    current_context = case.get("current_context_ref")
    reevaluated = case.get("policy_reevaluation_state", "UNKNOWN")

    if not policy or not frozen_context or not current_context:
        blocks.append("POLICY_OR_CONTEXT_BINDING_MISSING")
        return "ANALYSIS_REOPEN"

    if applicability == "UNIVERSAL_ASSERTION":
        blocks.append("CONTEXTUAL_POLICY_OVERGENERALIZED")
        reasons.append("A policy selected for one maturity/risk/operating context cannot silently become universal doctrine.")
        return "REJECT_POLICY_OVERGENERALIZATION"

    if frozen_context != current_context and reevaluated != "PASS":
        blocks.append("POLICY_CONTEXT_CHANGED_WITHOUT_REEVALUATION")
        reasons.append("When the material context that selected a control policy changes, the policy must be re-evaluated before reuse.")
        return "POLICY_RESELECTION_REQUIRED"

    if applicability == "EVIDENCE_BOUND" and (frozen_context == current_context or reevaluated == "PASS"):
        return "CONTEXT_BOUND_POLICY_VALID"

    return "ANALYSIS_REOPEN"


def _ext07(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    evidence_scope = case.get("evidence_scope")
    claim_scope = case.get("claim_scope")
    scope_relation = case.get("scope_relation", "UNKNOWN")
    bridge = case.get("scope_bridge_validation_state", "UNKNOWN")
    use = case.get("proposed_use", "SUPPORT")

    if not evidence_scope or not claim_scope:
        blocks.append("SCOPE_BINDING_MISSING")
        return "BLOCK_SCOPE_CLAIM"

    if scope_relation == "MATCH":
        return "SCOPE_BOUND_CLAIM"

    if scope_relation in {"EVIDENCE_NARROWER_THAN_CLAIM", "CLAIM_NARROWER_THAN_EVIDENCE"}:
        if bridge == "PASS":
            reasons.append("Cross-level use is allowed only because an explicit validated bridge binds the concrete and abstract scopes.")
            return "SCOPE_BOUND_BY_VALIDATED_BRIDGE"
        blocks.append("ABSTRACTION_LEVEL_DRIFT")
        if use in {"REFUTE_SPECIFIC_FAILURE", "GENERALIZE_SUCCESS", "PROMOTE"}:
            reasons.append("A broad success statement cannot erase a concrete failure, and a narrow success cannot establish a broader system property without coverage evidence.")
            return "BLOCK_ABSTRACTION_ESCAPE"
        return "ANALYSIS_REOPEN"

    if scope_relation == "UNRELATED":
        blocks.append("UNRELATED_SCOPE_EVIDENCE")
        return "BLOCK_SCOPE_CLAIM"

    return "ANALYSIS_REOPEN"


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    blocks, reasons = _base(case)
    extension_id = case.get("extension_id")
    if extension_id == "CD_EXT01_SEMANTIC_INVARIANT_ADAPTER_GUARD":
        disposition = _ext01(case, blocks, reasons)
    elif extension_id == "CD_EXT02_OBSERVATION_INFERENCE_LAYERING":
        disposition = _ext02(case, blocks, reasons)
    elif extension_id == "CD_EXT03_END_TO_END_OBJECTIVE_BINDING":
        disposition = _ext03(case, blocks, reasons)
    elif extension_id == "CD_EXT04_CONTEXT_CONDITIONED_TELEMETRY":
        disposition = _ext04(case, blocks, reasons)
    elif extension_id == "CD_EXT05_DERIVED_ARTIFACT_STALENESS_PROPAGATION":
        disposition = _ext05(case, blocks, reasons)
    elif extension_id == "CD_EXT06_CONTEXT_BOUND_POLICY_SELECTION":
        disposition = _ext06(case, blocks, reasons)
    elif extension_id == "CD_EXT07_ABSTRACTION_LEVEL_BINDING":
        disposition = _ext07(case, blocks, reasons)
    else:
        disposition = "REJECT_UNKNOWN_EXTENSION"

    hard = [
        state for state in blocks
        if state in {"UNKNOWN_EXTENSION", "FROZEN_WORKLOAD_MISSING", "AUTHORITY_EFFECT_NOT_NONE"}
    ]
    return {
        "schema": "ultimate-loop-concept-design-crucible-report/v0",
        "extension_id": extension_id,
        "classification": "UNKNOWN_OR_BLOCKED" if hard else "PASS_WITH_FINDINGS",
        "disposition": disposition,
        "canonical_promotion_authorized": False,
        "blocking_states": sorted(set(blocks)),
        "reasons": reasons,
        "evidence_scope": "CONTRACT_METEOR_ONLY_NOT_REAL_WORLD_SAME_WORKLOAD_PROOF",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Attack an OSARU concept-design derived Ultimate Loop challenger")
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    report = evaluate(case)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if report["classification"] == "UNKNOWN_OR_BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
