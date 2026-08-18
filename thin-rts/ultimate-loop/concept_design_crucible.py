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
