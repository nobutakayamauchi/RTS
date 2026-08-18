from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXTENSIONS = {
    "EXT01_FIRST_PARTY_SIGNAL_BINDING",
    "EXT02_CANONICAL_SOURCE_COMPILER",
    "EXT03_BOTTLENECK_REENTRY_ROUTING",
    "EXT04_SCALE_PROOF_GATE",
    "EXT05_DECISION_CAPABILITY_SUCCESSION",
}

REENTRY_MAP = {
    "DISCOVERY": "DISCOVERY_REFRESH",
    "IMPLEMENTATION": "DA_COUNTER_DA",
    "DEPLOYMENT": "DEPLOYMENT_IDENTITY",
    "POST_DEPLOY_METRIC": "POST_DEPLOY_DEBUG",
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
        reasons.append("An extension under attack cannot authorize its own canonical promotion.")
    return blocks, reasons


def _ext01(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    human_surface = case.get("human_or_user_surface") is True
    mandatory = case.get("mandatory_for_all_workloads") is True
    if not human_surface:
        if mandatory:
            blocks.append("FIRST_PARTY_FORCED_ON_INAPPLICABLE_WORKLOAD")
            reasons.append("Offline/library/non-user workloads cannot be forced through customer-contact evidence.")
            return "REJECT_UNIVERSAL_GATE"
        return "NOT_APPLICABLE_PROFILE"

    state = case.get("first_party_evidence_state")
    consent = case.get("consent_privacy_state")
    if state != "CURRENT_BOUND" or consent not in {"PASS", "NOT_APPLICABLE"}:
        blocks.append("FIRST_PARTY_EVIDENCE_UNPROVEN")
        return "STANDBY_RESEARCH"
    reasons.append("Direct human/user evidence survives only as a conditional evidence profile, not a universal stage.")
    return "COMPOSE_CONDITIONAL_PROFILE"


def _ext02(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    adapters = case.get("adapters") or []
    if not case.get("canonical_source_ref"):
        blocks.append("CANONICAL_SOURCE_MISSING")
    if len(adapters) < 2:
        blocks.append("MULTI_ADAPTER_EVIDENCE_MISSING")
    source_fp = case.get("canonical_fact_fingerprint")
    if not source_fp:
        blocks.append("CANONICAL_FINGERPRINT_MISSING")
    for adapter in adapters:
        if adapter.get("fact_fingerprint") != source_fp:
            blocks.append(f"FACT_DRIFT:{adapter.get('id', 'UNKNOWN')}")
        if adapter.get("provenance_state") != "PASS":
            blocks.append(f"PROVENANCE_LOSS:{adapter.get('id', 'UNKNOWN')}")
        if adapter.get("private_field_leakage") is not False:
            blocks.append(f"PRIVATE_FIELD_LEAKAGE:{adapter.get('id', 'UNKNOWN')}")
    if any(
        b.startswith(("FACT_DRIFT:", "PROVENANCE_LOSS:", "PRIVATE_FIELD_LEAKAGE:"))
        for b in blocks
    ) or "CANONICAL_SOURCE_MISSING" in blocks or "MULTI_ADAPTER_EVIDENCE_MISSING" in blocks or "CANONICAL_FINGERPRINT_MISSING" in blocks:
        return "STANDBY_RESEARCH"
    reasons.append("The surviving responsibility is a bounded source-to-adapter contract, not a publishing platform.")
    return "COMPOSE_BOUNDED_ADAPTER_CONTRACT"


def _ext03(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    stage = case.get("observed_failure_stage")
    causality = case.get("causality_state")
    route = case.get("proposed_reentry")
    if stage not in REENTRY_MAP:
        blocks.append("UNKNOWN_FAILURE_STAGE")
        return "ANALYSIS_REOPEN"
    if causality != "PROVEN":
        reasons.append("Correlation is not root cause; uncertain causality must reopen analysis rather than guess a local gate.")
        return "ANALYSIS_REOPEN"
    expected = REENTRY_MAP[stage]
    if route != expected:
        blocks.append("WRONG_REENTRY_ROUTE")
        reasons.append(f"Proven {stage} failure must route to {expected}, not {route!r}.")
        return "REJECT_ROUTE"
    reasons.append("A typed fail-closed re-entry binder can reduce global rewrites without inventing root cause.")
    return "COMPOSE_TYPED_REENTRY_ROUTER"


def _ext04(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    if case.get("safety_state") != "PASS" or case.get("correctness_state") != "PASS":
        blocks.append("SAFETY_OR_CORRECTNESS_NOT_PROVEN")
        reasons.append("Scale/business evidence cannot outrank safety or correctness.")
        return "BLOCK_SCALE"

    local = case.get("local_loop_proof") == "PASS"
    scale_dependent = case.get("behavior_scale_dependent") is True
    guardrails = case.get("scale_guardrails") == "PASS"
    bounded_probe = case.get("bounded_scale_probe") == "AUTHORIZED"

    if local and guardrails:
        reasons.append("Scale may proceed only as a bounded profile with continued observation; it is not a promotion shortcut.")
        return "COMPOSE_BOUNDED_SCALE_PROFILE"
    if scale_dependent and guardrails and bounded_probe:
        reasons.append("Scale-dependent behavior requires a bounded scale probe; a universal local-proof prerequisite would destroy learnability.")
        return "BOUNDED_SCALE_PROBE_ONLY"

    blocks.append("SCALE_PROOF_OR_BOUNDED_PROBE_MISSING")
    return "BLOCK_SCALE"


def _ext05(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    if case.get("canonical_material_state") != "PASS":
        blocks.append("CANONICAL_MATERIAL_UNPROVEN")
    retrieval = case.get("retrieval_state")
    held_out = case.get("held_out_decision_state")
    authority = case.get("authority_compliance_state")
    escalation = case.get("escalation_state")
    creator_absent = case.get("creator_intervention") is False

    if retrieval == "PASS" and held_out != "PASS":
        blocks.append("RETRIEVAL_NOT_COMPETENCE")
        reasons.append("Knowledge retrieval quality cannot substitute for decision competence.")
    if held_out != "PASS":
        blocks.append("HELD_OUT_DECISIONS_UNPROVEN")
    if authority != "PASS":
        blocks.append("SUCCESSOR_AUTHORITY_COMPLIANCE_UNPROVEN")
    if escalation != "PASS":
        blocks.append("SUCCESSOR_ESCALATION_UNPROVEN")
    if not creator_absent:
        blocks.append("CREATOR_INDEPENDENCE_UNPROVEN")

    if blocks:
        return "STANDBY_RESEARCH"
    reasons.append("Decision-capability succession is stricter than material recovery: it requires held-out decisions, authority compliance, escalation and creator absence.")
    return "COMPOSE_PHOENIX_SUCCESSION_EXTENSION"


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    blocks, reasons = _base(case)
    extension_id = case.get("extension_id")
    if extension_id == "EXT01_FIRST_PARTY_SIGNAL_BINDING":
        disposition = _ext01(case, blocks, reasons)
    elif extension_id == "EXT02_CANONICAL_SOURCE_COMPILER":
        disposition = _ext02(case, blocks, reasons)
    elif extension_id == "EXT03_BOTTLENECK_REENTRY_ROUTING":
        disposition = _ext03(case, blocks, reasons)
    elif extension_id == "EXT04_SCALE_PROOF_GATE":
        disposition = _ext04(case, blocks, reasons)
    elif extension_id == "EXT05_DECISION_CAPABILITY_SUCCESSION":
        disposition = _ext05(case, blocks, reasons)
    else:
        disposition = "REJECT_UNKNOWN_EXTENSION"

    hard_blocks = [
        b for b in blocks
        if b in {"UNKNOWN_EXTENSION", "FROZEN_WORKLOAD_MISSING", "AUTHORITY_EFFECT_NOT_NONE"}
    ]
    classification = "UNKNOWN_OR_BLOCKED" if hard_blocks else "PASS_WITH_FINDINGS"
    return {
        "schema": "ultimate-loop-extension-crucible-report/v0",
        "extension_id": extension_id,
        "classification": classification,
        "disposition": disposition,
        "canonical_promotion_authorized": False,
        "blocking_states": sorted(set(blocks)),
        "reasons": reasons,
        "evidence_scope": "CONTRACT_METEOR_ONLY_NOT_REAL_WORLD_UTILITY_PROOF",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Attack an OSARU-derived Ultimate Loop extension contract")
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    report = evaluate(case)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] != "UNKNOWN_OR_BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
