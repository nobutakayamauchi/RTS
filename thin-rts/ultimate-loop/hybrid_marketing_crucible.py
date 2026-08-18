from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXTENSIONS = {
    "HM_EXT01_FILTER_AWARE_STAGE_TELEMETRY",
    "HM_EXT02_EVIDENCE_CONSTRUCT_VALIDITY",
    "HM_EXT03_EVIDENCE_SATISFIED_SHORT_CIRCUIT",
    "HM_EXT04_COMMITMENT_CONTAMINATION_GUARD",
    "HM_EXT05_HUMAN_GATE_AGENCY_PRESERVATION",
    "HM_EXT06_REFERENCE_CLASS_FREEZE",
    "HM_EXT07_SELECTION_LINEAGE_GUARD",
    "HM_EXT08_INTERVENTION_HISTORY_BINDING",
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
        reasons.append("A challenger cannot grant itself canonical authority.")
    return blocks, reasons


def _filter_aware(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    objective = case.get("stage_objective")
    throughput = case.get("throughput_state")
    downstream_quality = case.get("downstream_quality_state")
    rejection_semantics = case.get("rejection_semantics")
    causality = case.get("causality_state")
    if objective not in {"FILTER", "TRANSFORM", "PASS_THROUGH"}:
        blocks.append("STAGE_OBJECTIVE_UNKNOWN")
        return "ANALYSIS_REOPEN"
    if throughput == "LOW" and objective == "FILTER":
        if rejection_semantics != "DECLARED":
            blocks.append("FILTER_REJECTION_SEMANTICS_MISSING")
            return "ANALYSIS_REOPEN"
        if downstream_quality == "IMPROVED" and causality == "PROVEN_OR_BOUNDED":
            reasons.append("Intentional attrition can be correct when the stage exists to reject low-fit cases and downstream quality improves.")
            return "NO_BOTTLENECK_FILTER_WORKING"
        if causality != "PROVEN_OR_BOUNDED":
            reasons.append("Low throughput alone does not prove either a healthy filter or a bottleneck.")
            return "ANALYSIS_REOPEN"
    if throughput == "LOW" and objective in {"TRANSFORM", "PASS_THROUGH"}:
        if causality != "PROVEN_OR_BOUNDED":
            return "ANALYSIS_REOPEN"
        return "BOTTLENECK_CANDIDATE"
    return "OBSERVE"


def _construct_validity(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    measured = set(case.get("measured_properties") or [])
    claimed = set(case.get("claimed_properties") or [])
    mapping = case.get("construct_mapping_state")
    if not measured or not claimed:
        blocks.append("MEASURED_OR_CLAIMED_PROPERTY_MISSING")
        return "BLOCK_CLAIM"
    unsupported = sorted(claimed - measured)
    if unsupported and mapping != "VALIDATED":
        blocks.extend(f"UNSUPPORTED_PROXY_CLAIM:{x}" for x in unsupported)
        reasons.append("A gate may not claim properties it did not directly measure unless the proxy relationship is separately validated.")
        return "BLOCK_CLAIM"
    if mapping == "VALIDATED" or claimed.issubset(measured):
        return "BOUND_CLAIM_TO_EVIDENCE_SCOPE"
    return "ANALYSIS_REOPEN"


def _short_circuit(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    remaining = case.get("remaining_stages") or []
    missing = [s for s in remaining if s.get("unique_obligation_state") == "UNSATISFIED"]
    if missing:
        blocks.extend(f"UNSATISFIED_UNIQUE_OBLIGATION:{s.get('id','UNKNOWN')}" for s in missing)
        return "NO_SHORT_CIRCUIT"
    if case.get("downstream_preconditions_state") != "PASS":
        blocks.append("DOWNSTREAM_PRECONDITIONS_NOT_PROVEN")
        return "NO_SHORT_CIRCUIT"
    if case.get("authority_state") != "AUTHORIZED":
        blocks.append("TRANSITION_AUTHORITY_MISSING")
        return "NO_SHORT_CIRCUIT"
    if case.get("skip_reason") in {"SUNK_COST", "CANDIDATE_ATTRACTIVENESS", "TIME_PRESSURE_ONLY", "PARETO_HEURISTIC_ONLY"}:
        blocks.append("INVALID_SKIP_REASON")
        reasons.append("Efficiency or leverage heuristics cannot erase a unique safety, evidence, or authority obligation.")
        return "NO_SHORT_CIRCUIT"
    reasons.append("Optional stages may be bypassed only when every unique evidence/safety obligation is already satisfied or not applicable.")
    return "SHORT_CIRCUIT_ELIGIBLE"


def _commitment_guard(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    current = case.get("current_explicit_state")
    historical = case.get("historical_commitment") or {}
    inference = case.get("proposed_inference")
    if inference in {"CONSENT", "VALIDITY", "AUTHORITY", "FIT"} and historical.get("present") is True:
        if current != "EXPLICIT_CURRENT":
            blocks.append(f"HISTORICAL_COMMITMENT_NOT_{inference}")
            reasons.append("Past time, effort, money, clicks, prior approvals, or other sunk costs cannot establish current consent, validity, authority, or fit.")
            return "BLOCK_INFERENCE"
    if current == "EXPLICIT_CURRENT":
        return "CURRENT_STATE_GOVERNS"
    return "UNKNOWN_OR_RECONFIRM"


def _agency_preservation(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    if case.get("gate_requires_human_choice") is not True:
        return "NOT_APPLICABLE_NON_HUMAN_GATE"
    decline = case.get("decline_path_state")
    disclosure = case.get("material_consequence_disclosure_state")
    current = case.get("current_decision_state")
    system_pressure = set(case.get("system_applied_pressure") or [])
    coercive = {"SUNK_COST_LEVERAGE", "HIDDEN_DECLINE_PATH", "PRECHECKED_APPROVAL", "DECEPTIVE_DEFAULT", "SOCIAL_COERCION", "PENALTY_FOR_REFUSAL_NOT_INTRINSIC_TO_ACTION"}
    if decline != "VISIBLE_AND_ACTIONABLE":
        blocks.append("MEANINGFUL_DECLINE_PATH_MISSING")
    if disclosure != "PASS":
        blocks.append("MATERIAL_CONSEQUENCES_NOT_DISCLOSED")
    contaminated = sorted(system_pressure & coercive)
    blocks.extend(f"AGENCY_PRESSURE:{x}" for x in contaminated)
    if any(b == "MEANINGFUL_DECLINE_PATH_MISSING" or b == "MATERIAL_CONSEQUENCES_NOT_DISCLOSED" or b.startswith("AGENCY_PRESSURE:") for b in blocks):
        reasons.append("A Human Gate is not evidence of meaningful authorization if the system makes refusal obscure, punitive, preselected, deceptive, or dependent on sunk-cost/social pressure.")
        return "BLOCK_HUMAN_GATE_VALIDITY"
    if current != "EXPLICIT_CURRENT":
        blocks.append("CURRENT_HUMAN_DECISION_MISSING")
        return "RECONFIRM_HUMAN_GATE"
    reasons.append("Choice architecture may reduce friction, but a valid Human Gate must preserve an explicit, visible, non-deceptive refusal path and current decision authority.")
    return "HUMAN_GATE_AGENCY_BOUND"


def _reference_class_freeze(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    claim = case.get("comparison_claim")
    frozen_ref = case.get("frozen_reference_class_ref")
    current_ref = case.get("current_reference_class_ref")
    protocol = case.get("measurement_protocol_state")
    change_authority = case.get("reference_change_authority")
    paired_old_frame = case.get("paired_old_reference_evidence") == "PASS"
    if not frozen_ref or not current_ref:
        blocks.append("REFERENCE_CLASS_MISSING")
        return "BLOCK_COMPARISON_CLAIM"
    if protocol != "PASS":
        blocks.append("MEASUREMENT_PROTOCOL_NOT_BOUND")
        return "BLOCK_COMPARISON_CLAIM"
    if frozen_ref != current_ref:
        if claim in {"IMPROVED", "REGRESSED", "BETTER", "WORSE", "DELTA"} and not paired_old_frame:
            blocks.append("REFERENCE_CLASS_SHIFT_CONTAMINATES_DELTA")
            reasons.append("Changing the comparator can change the apparent result without changing the underlying system. A before/after claim remains bound to the frozen reference class unless paired evidence preserves comparability.")
            return "BLOCK_COMPARISON_CLAIM"
        if change_authority == "AUTHORIZED_NEW_FRAME" and claim in {"ABSOLUTE_ONLY", "NEW_FRAME_BASELINE"}:
            reasons.append("An authorized new reference class may start a new baseline, but it cannot inherit improvement claims from the old frame.")
            return "NEW_REFERENCE_BASELINE_ONLY"
        if change_authority != "AUTHORIZED_NEW_FRAME":
            blocks.append("UNAUTHORIZED_REFERENCE_CLASS_SHIFT")
            return "BLOCK_COMPARISON_CLAIM"
    reasons.append("Evaluation claims remain revision-bound to the frozen reference class and measurement protocol.")
    return "REFERENCE_CLASS_BOUND"


def _selection_lineage(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    evidence_cohort = case.get("evidence_cohort_ref")
    claim_population = case.get("claim_population_ref")
    lineage = case.get("selection_history_state")
    claim_scope = case.get("claim_scope")
    transportability = case.get("transportability_state")
    if not evidence_cohort or not claim_population or lineage not in {"NONE", "BOUND"}:
        blocks.append("SELECTION_LINEAGE_UNKNOWN")
        return "ANALYSIS_REOPEN"
    if claim_scope == "COHORT_ONLY":
        reasons.append("Evidence from a selected cohort may support claims about that cohort when its selection lineage remains bound.")
        return "BOUND_TO_SELECTED_COHORT"
    if claim_scope == "POPULATION_GENERALIZATION":
        if evidence_cohort != claim_population or lineage == "BOUND":
            if transportability != "VALIDATED":
                blocks.append("SELECTED_COHORT_NOT_POPULATION_EVIDENCE")
                reasons.append("Downstream success after screening cannot be generalized to the upstream population without separately validated transportability evidence.")
                return "BLOCK_POPULATION_GENERALIZATION"
            return "GENERALIZATION_BOUND_TO_VALIDATED_TRANSPORT"
        return "POPULATION_SCOPE_BOUND"
    blocks.append("CLAIM_SCOPE_UNKNOWN")
    return "ANALYSIS_REOPEN"


def _intervention_history(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    history = case.get("intervention_history_state")
    claim = case.get("claim_type")
    causal = case.get("causal_identification_state")
    history_match = case.get("history_match_state")
    if history not in {"NONE", "BOUND"}:
        blocks.append("INTERVENTION_HISTORY_UNKNOWN")
        return "ANALYSIS_REOPEN"
    if history == "NONE":
        return "NO_INTERVENTION_CONTAMINATION_DETECTED"
    if claim == "STATE_AFTER_INTERVENTION":
        reasons.append("Observed state after education, screening, repeated exposure, payment, or other intervention is valid only as a state conditional on that intervention history.")
        return "BOUND_TO_INTERVENTION_HISTORY"
    if claim in {"INTRINSIC_PROPERTY", "CAUSAL_EFFECT"}:
        if causal != "VALIDATED_OR_BOUNDED":
            blocks.append("INTERVENTION_CONTAMINATES_INTRINSIC_OR_CAUSAL_CLAIM")
            reasons.append("A post-intervention outcome cannot be re-labeled as an intrinsic property or causal effect unless the intervention history and causal identification are separately controlled.")
            return "BLOCK_CAUSAL_OR_INTRINSIC_CLAIM"
        return "CAUSAL_CLAIM_BOUND_TO_IDENTIFICATION"
    if claim == "PATH_COMPARISON":
        if history_match != "PASS":
            blocks.append("INTERVENTION_HISTORY_NOT_COMPARABLE")
            reasons.append("Comparing outcomes across paths with different intervention histories can manufacture an apparent effect.")
            return "BLOCK_PATH_COMPARISON"
        return "PATH_COMPARISON_HISTORY_BOUND"
    blocks.append("CLAIM_TYPE_UNKNOWN")
    return "ANALYSIS_REOPEN"


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    blocks, reasons = _base(case)
    ext = case.get("extension_id")
    if ext == "HM_EXT01_FILTER_AWARE_STAGE_TELEMETRY":
        disposition = _filter_aware(case, blocks, reasons)
    elif ext == "HM_EXT02_EVIDENCE_CONSTRUCT_VALIDITY":
        disposition = _construct_validity(case, blocks, reasons)
    elif ext == "HM_EXT03_EVIDENCE_SATISFIED_SHORT_CIRCUIT":
        disposition = _short_circuit(case, blocks, reasons)
    elif ext == "HM_EXT04_COMMITMENT_CONTAMINATION_GUARD":
        disposition = _commitment_guard(case, blocks, reasons)
    elif ext == "HM_EXT05_HUMAN_GATE_AGENCY_PRESERVATION":
        disposition = _agency_preservation(case, blocks, reasons)
    elif ext == "HM_EXT06_REFERENCE_CLASS_FREEZE":
        disposition = _reference_class_freeze(case, blocks, reasons)
    elif ext == "HM_EXT07_SELECTION_LINEAGE_GUARD":
        disposition = _selection_lineage(case, blocks, reasons)
    elif ext == "HM_EXT08_INTERVENTION_HISTORY_BINDING":
        disposition = _intervention_history(case, blocks, reasons)
    else:
        disposition = "REJECT_UNKNOWN_EXTENSION"
    hard = {"UNKNOWN_EXTENSION", "FROZEN_WORKLOAD_MISSING", "AUTHORITY_EFFECT_NOT_NONE"}
    classification = "UNKNOWN_OR_BLOCKED" if any(x in hard for x in blocks) else "PASS_WITH_FINDINGS"
    return {"schema": "ultimate-loop-hybrid-marketing-crucible-report/v0", "extension_id": ext, "classification": classification, "disposition": disposition, "canonical_promotion_authorized": False, "blocking_states": sorted(set(blocks)), "reasons": reasons, "evidence_scope": "CONTRACT_METEOR_ONLY_NOT_REAL_WORLD_UTILITY_PROOF"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    report = evaluate(json.loads(args.case.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] != "UNKNOWN_OR_BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
