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
    if case.get("skip_reason") in {"SUNK_COST", "CANDIDATE_ATTRACTIVENESS", "TIME_PRESSURE_ONLY"}:
        blocks.append("INVALID_SKIP_REASON")
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
    else:
        disposition = "REJECT_UNKNOWN_EXTENSION"

    hard = {"UNKNOWN_EXTENSION", "FROZEN_WORKLOAD_MISSING", "AUTHORITY_EFFECT_NOT_NONE"}
    classification = "UNKNOWN_OR_BLOCKED" if any(x in hard for x in blocks) else "PASS_WITH_FINDINGS"
    return {
        "schema": "ultimate-loop-hybrid-marketing-crucible-report/v0",
        "extension_id": ext,
        "classification": classification,
        "disposition": disposition,
        "canonical_promotion_authorized": False,
        "blocking_states": sorted(set(blocks)),
        "reasons": reasons,
        "evidence_scope": "CONTRACT_METEOR_ONLY_NOT_REAL_WORLD_UTILITY_PROOF",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    report = evaluate(json.loads(args.case.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] != "UNKNOWN_OR_BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
