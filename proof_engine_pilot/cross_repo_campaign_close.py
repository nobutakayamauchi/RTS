from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .cross_repo_review import verify_round_two_review_bundle
from .cross_repo_review_round3 import verify_round_three_review_bundle
from .cross_repo_validation import verify_bundle as verify_cross_repo_bundle
from .learning import preflight_candidate

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
CONTRACT_PATH = PACKAGE_DIR / "cross_repo_reviews" / "round_0004" / "review_contract.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "cross_repo_campaign_close_checkpoint_0012.json"

REVIEW_ROUND_ID = "PROOF-ENGINE-CROSS-REPO-REVIEW-ROUND-0004"
SOURCE_RUN_FINGERPRINT = "413304aa513efe09cae300de23909318e8bfcc6ecfef5be7a35ab79a70def5bb"
SOURCE_ROUND_FINGERPRINT = "d4aa4b703124349227a8eac83923bf12c9a553ea125e9654f6d8f97fd87b43d3"
PREVIOUS_CHECKPOINT_FINGERPRINT = "2302b6ef398ccfbc46a35d400d2a7cb5013419aeddd18abc7e4b9e66f9cc7a12"
APPROVED_IDS = {"VF-001", "VF-002"}
EXPECTED_AUTHOR = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_ROUND_4_CONFIRMATION",
    "role": "PROJECT_OWNER",
    "instruction": "ラウンド4確定次の作業に移る",
}
AUTHORITY_FIELDS = {
    "adjacent_repository_write_authorized",
    "automatic_approval_authorized",
    "automatic_rewrite_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "model_weight_training_authorized",
    "outreach_authorized",
    "provider_execution_authorized",
    "publication_authorized",
    "target_repository_write_authorized",
}
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "source_run_fingerprint",
    "source_round_fingerprint", "previous_round_checkpoint_fingerprint",
    "review_contract_fingerprint", "completed_rounds",
    "round_effective_candidate_count", "cumulative_effective_candidate_count",
    "round_revision_count", "cumulative_revision_count",
    "round_withheld_claim_count", "cumulative_withheld_claim_count", "state",
    "publication_performed", "external_actions_performed",
    "target_repository_writes_performed", "original_source_repositories_modified",
    "private_repository_payload_copied", "next_action", "checkpoint_fingerprint",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _verify_false_authority(value: Any, label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != AUTHORITY_FIELDS:
        raise ProofEngineError(f"{label} authority fields mismatch")
    if any(value[field] is not False for field in AUTHORITY_FIELDS):
        raise ProofEngineError(f"{label} authority widened")
    return value


def _source_round() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    previous = verify_round_three_review_bundle()
    if previous["checkpoint"]["checkpoint_fingerprint"] != PREVIOUS_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("Round 4 previous review checkpoint drift")
    bundle = verify_cross_repo_bundle()
    run = bundle["run"]
    if run.get("run_fingerprint") != SOURCE_RUN_FINGERPRINT:
        raise ProofEngineError("Round 4 source run drift")
    round_value = next((item for item in run["rounds"] if item["round_id"] == "ROUND-4"), None)
    if round_value is None or round_value.get("round_fingerprint") != SOURCE_ROUND_FINGERPRINT:
        raise ProofEngineError("Round 4 source round drift")
    if round_value.get("role") != "NEGATIVE_CONTROL" or round_value.get("source_mode") != "READ_ONLY_SNAPSHOT":
        raise ProofEngineError("Round 4 negative-control boundary drift")
    if len(round_value.get("candidates", [])) != 2 or len(round_value.get("withheld_claims", [])) != 3:
        raise ProofEngineError("Round 4 source counts drift")
    return bundle, round_value, previous


def verify_review_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "Round 4 review contract")
    if value.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-CONTRACT-V1":
        raise ProofEngineError("Round 4 review contract schema mismatch")
    if value.get("contract_id") != "PROOF-ENGINE-CROSS-REPO-ROUND-4-REVIEW-CONTRACT-0001":
        raise ProofEngineError("Round 4 review contract identity mismatch")
    if value.get("review_round_id") != REVIEW_ROUND_ID or value.get("human_authorization") != EXPECTED_AUTHOR:
        raise ProofEngineError("Round 4 review is not bound to the explicit human confirmation")
    _verify_false_authority(value.get("authority"), "Round 4 review contract")
    expected_source = {
        "campaign_fingerprint": "d3dec34bc2686601f08324889510da9a312cc46565fc97d806c651fedbb89c95",
        "run_fingerprint": SOURCE_RUN_FINGERPRINT,
        "round_id": "ROUND-4",
        "round_fingerprint": SOURCE_ROUND_FINGERPRINT,
        "repository": "nobutakayamauchi/rts-video-flow",
        "previous_round_checkpoint_fingerprint": PREVIOUS_CHECKPOINT_FINGERPRINT,
    }
    if value.get("source") != expected_source:
        raise ProofEngineError("Round 4 review source mismatch")
    if value.get("originals_preserved") is not True or value.get("revision_mode") != "APPEND_ONLY":
        raise ProofEngineError("Round 4 review did not preserve originals")
    if [item.get("candidate_id") for item in value.get("decisions", [])] != ["VF-001", "VF-002"]:
        raise ProofEngineError("Round 4 review decision order mismatch")
    if any(item.get("decision") != "APPROVE" for item in value["decisions"]):
        raise ProofEngineError("Round 4 review contains an unexpected decision")
    if value.get("withheld_claim_policy") != {
        "required_count": 3,
        "required_status": "WITHHELD_UNSUPPORTED",
        "must_preserve_topics": ["END_TO_END_OPERATION", "TRANSCRIPTION_ACCURACY", "PRODUCTION_READINESS"],
    }:
        raise ProofEngineError("Round 4 withheld-claim policy mismatch")
    if value.get("campaign_close_request") != {
        "produce_internal_evaluation": True,
        "productization_recommendation": "READY_FOR_INTERNAL_REPORT_TEMPLATE_DESIGN",
        "publication_status": "NOT_PUBLISHED",
    }:
        raise ProofEngineError("Round 4 campaign-close request mismatch")
    return value


def _withheld_topic(claim: str) -> str:
    lowered = claim.lower()
    if "end-to-end" in lowered or "operational" in lowered:
        return "END_TO_END_OPERATION"
    if "transcription" in lowered or "accuracy" in lowered:
        return "TRANSCRIPTION_ACCURACY"
    if "production" in lowered:
        return "PRODUCTION_READINESS"
    raise ProofEngineError("Round 4 withheld claim topic is unknown")


def build_round_four_review(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    source_bundle, round_value, previous = _source_round()
    review_contract = verify_review_contract(contract)
    originals = {item["candidate_id"]: item for item in round_value["candidates"]}
    if set(originals) != APPROVED_IDS:
        raise ProofEngineError("Round 4 candidate set mismatch")

    author_fingerprint = fingerprint(EXPECTED_AUTHOR)
    authority_fingerprint = fingerprint(review_contract["authority"])
    decisions: list[dict[str, Any]] = []
    effective: list[dict[str, Any]] = []
    prior = None
    for sequence, plan in enumerate(review_contract["decisions"], start=1):
        candidate = originals[plan["candidate_id"]]
        if preflight_candidate(candidate).get("result") != "PASS":
            raise ProofEngineError(f"Round 4 candidate failed learning preflight: {candidate['candidate_id']}")
        decision = {
            "decision_id": f"CROSS-REPO-REVIEW-0004-D{sequence:03d}",
            "sequence": sequence,
            "decision_type": "APPROVE",
            "previous_decision_fingerprint": prior,
            "author_fingerprint": author_fingerprint,
            "authority_fingerprint": authority_fingerprint,
            "target": {
                "source": "CROSS_REPO_RUN",
                "candidate_id": candidate["candidate_id"],
                "candidate_version": 1,
                "candidate_fingerprint": candidate["candidate_fingerprint"],
            },
            "reason": plan["reason"],
            "revision_ref": None,
        }
        decision["decision_fingerprint"] = fingerprint(decision)
        prior = decision["decision_fingerprint"]
        decisions.append(decision)
        effective.append({
            "candidate_id": candidate["candidate_id"],
            "candidate_version": 1,
            "source": "CROSS_REPO_RUN",
            "candidate_fingerprint": candidate["candidate_fingerprint"],
            "approval_decision_fingerprint": decision["decision_fingerprint"],
            "status": "APPROVED_FOR_INTERNAL_VALIDATION",
        })

    withheld = [{
        "topic": _withheld_topic(item["claim"]),
        "claim": item["claim"],
        "reason": item["reason"],
        "status": "WITHHELD_UNSUPPORTED",
    } for item in round_value["withheld_claims"]]
    expected_topics = set(review_contract["withheld_claim_policy"]["must_preserve_topics"])
    if {item["topic"] for item in withheld} != expected_topics:
        raise ProofEngineError("Round 4 withheld topics mismatch")

    review = {
        "schema_version": "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-V1",
        "review_round_id": REVIEW_ROUND_ID,
        "source": copy.deepcopy(review_contract["source"]),
        "author": copy.deepcopy(EXPECTED_AUTHOR),
        "author_fingerprint": author_fingerprint,
        "authority": copy.deepcopy(review_contract["authority"]),
        "authority_fingerprint": authority_fingerprint,
        "originals_preserved": True,
        "revision_mode": "APPEND_ONLY",
        "decisions": decisions,
        "effective_candidates": effective,
        "withheld_claims": withheld,
        "counts": {
            "original_candidates": 2, "originals_approved": 2,
            "originals_revised": 0, "revisions_approved": 0,
            "effective_approved": 2, "rejected": 0, "withheld_claims": 3,
        },
        "metrics": {
            "first_pass_approval_rate": 1.0,
            "revision_rate": 0.0,
            "rejection_rate": 0.0,
            "completion_overstatement_incidents": 0,
            "withheld_claim_retention_rate": 1.0,
            "comparison_to_prior_rounds": "DESCRIPTIVE_ONLY_NEGATIVE_CONTROL_TOO_SMALL_FOR_CAUSAL_INFERENCE",
        },
        "review_state": "ROUND_4_COMPLETE",
        "campaign_state": "THREE_REPOSITORY_VALIDATION_COMPLETE",
        "publication_status": "NOT_PUBLISHED",
    }
    review["review_fingerprint"] = fingerprint(review)
    return {"source_bundle": source_bundle, "source_round": round_value, "previous": previous,
            "contract": review_contract, "review": review}


def build_campaign_evaluation(bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    value = build_round_four_review() if bundle is None else bundle
    round2 = verify_round_two_review_bundle()["review"]
    round3 = value["previous"]["review"]
    round4 = value["review"]
    evaluation = {
        "schema_version": "PROOF-ENGINE-CROSS-REPO-CAMPAIGN-EVALUATION-V1",
        "evaluation_id": "PROOF-ENGINE-CROSS-REPO-CAMPAIGN-EVALUATION-0001",
        "source_run_fingerprint": SOURCE_RUN_FINGERPRINT,
        "review_fingerprints": {
            "ROUND-2": round2["review_fingerprint"],
            "ROUND-3": round3["review_fingerprint"],
            "ROUND-4": round4["review_fingerprint"],
        },
        "round_metrics": {
            "ROUND-2": {"candidates": 6, "first_pass_approved": 5, "revised": 1, "rejected": 0, "withheld": 0},
            "ROUND-3": {"candidates": 8, "first_pass_approved": 7, "revised": 1, "rejected": 0, "withheld": 2},
            "ROUND-4": {"candidates": 2, "first_pass_approved": 2, "revised": 0, "rejected": 0, "withheld": 3},
        },
        "cross_repo_totals": {
            "repositories": 3, "candidates": 16, "first_pass_approved": 14,
            "first_pass_approval_rate": 14 / 16, "revised": 2,
            "revision_rate": 2 / 16, "rejected": 0,
            "effective_approved_after_review": 16, "withheld_unsupported_claims": 5,
        },
        "baseline_reference": {
            "round_1_candidates": 12, "round_1_first_pass_approved": 7,
            "round_1_first_pass_approval_rate": 7 / 12,
            "interpretation": "POSITIVE_SIGNAL_NOT_CAUSAL_PROOF",
        },
        "validated_signals": {
            "public_conventional_product_supported": True,
            "private_metadata_only_analysis_supported": True,
            "negative_control_underclaiming_supported": True,
            "unmerged_evidence_exclusion_supported": True,
            "customer_payload_copy_avoided": True,
            "unsupported_commercial_or_runtime_claims_withheld": True,
            "target_repository_writes_performed": False,
        },
        "conclusion": {
            "supported": "BOUNDED_CROSS_REPOSITORY_INTERNAL_ACHIEVEMENT_REPORTING",
            "not_proven": [
                "ARBITRARY_REPOSITORY_GENERALIZATION", "AUTONOMOUS_EXTERNAL_EXECUTION",
                "COMMERCIAL_EFFECTIVENESS", "CUSTOMER_VALUE_OR_REVENUE", "MODEL_WEIGHT_LEARNING",
            ],
            "confidence": "MULTI_REPOSITORY_POSITIVE_EVIDENCE_WITH_LIMITED_SAMPLE",
        },
        "next_stage": {
            "state": "READY_FOR_INTERNAL_REPORT_TEMPLATE_DESIGN",
            "required_work": "Create a reusable customer-facing report schema from the sixteen effective candidates, then stop for human review before pricing, outreach, or publication.",
            "publication_status": "NOT_PUBLISHED",
            "human_review_required": True,
        },
        "authority": copy.deepcopy(value["contract"]["authority"]),
    }
    evaluation["evaluation_fingerprint"] = fingerprint(evaluation)
    return evaluation


def verify_campaign_close(*, contract: dict[str, Any] | None = None,
                          checkpoint: dict[str, Any] | None = None) -> dict[str, Any]:
    bundle = build_round_four_review(contract)
    review = bundle["review"]
    _verify_fingerprint(review, "review_fingerprint", "Round 4 review")
    if review["review_state"] != "ROUND_4_COMPLETE" or review["campaign_state"] != "THREE_REPOSITORY_VALIDATION_COMPLETE":
        raise ProofEngineError("Round 4 terminal state mismatch")
    if review["publication_status"] != "NOT_PUBLISHED" or len(review["withheld_claims"]) != 3:
        raise ProofEngineError("Round 4 publication or withheld boundary mismatch")

    evaluation = build_campaign_evaluation(bundle)
    _verify_fingerprint(evaluation, "evaluation_fingerprint", "cross-repo campaign evaluation")
    expected_totals = {
        "repositories": 3, "candidates": 16, "first_pass_approved": 14,
        "first_pass_approval_rate": 14 / 16, "revised": 2,
        "revision_rate": 2 / 16, "rejected": 0,
        "effective_approved_after_review": 16, "withheld_unsupported_claims": 5,
    }
    if evaluation["cross_repo_totals"] != expected_totals:
        raise ProofEngineError("cross-repo campaign totals mismatch")
    if evaluation["conclusion"]["supported"] != "BOUNDED_CROSS_REPOSITORY_INTERNAL_ACHIEVEMENT_REPORTING":
        raise ProofEngineError("cross-repo campaign conclusion mismatch")
    if evaluation["next_stage"]["state"] != "READY_FOR_INTERNAL_REPORT_TEMPLATE_DESIGN":
        raise ProofEngineError("cross-repo campaign next stage mismatch")
    _verify_false_authority(evaluation["authority"], "cross-repo campaign evaluation")

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("campaign close checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "campaign close checkpoint")
    expected_links = {
        "schema_version": "PROOF-ENGINE-CROSS-REPO-CAMPAIGN-CLOSE-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-CROSS-REPO-CAMPAIGN-CLOSE-CHECKPOINT-0012",
        "source_run_fingerprint": SOURCE_RUN_FINGERPRINT,
        "source_round_fingerprint": SOURCE_ROUND_FINGERPRINT,
        "previous_round_checkpoint_fingerprint": PREVIOUS_CHECKPOINT_FINGERPRINT,
        "review_contract_fingerprint": bundle["contract"]["contract_fingerprint"],
    }
    for field, expected in expected_links.items():
        if cp.get(field) != expected:
            raise ProofEngineError(f"campaign close checkpoint link mismatch: {field}")
    if cp.get("completed_rounds") != ["ROUND-2", "ROUND-3", "ROUND-4"]:
        raise ProofEngineError("campaign close checkpoint completed rounds mismatch")
    if (cp.get("round_effective_candidate_count"), cp.get("cumulative_effective_candidate_count"),
        cp.get("round_revision_count"), cp.get("cumulative_revision_count"),
        cp.get("round_withheld_claim_count"), cp.get("cumulative_withheld_claim_count")) != (2, 16, 0, 2, 3, 5):
        raise ProofEngineError("campaign close checkpoint counts mismatch")
    if cp.get("state") != "THREE_REPOSITORY_VALIDATION_COMPLETE_REPORT_TEMPLATE_DESIGN_READY":
        raise ProofEngineError("campaign close checkpoint state mismatch")
    for field in ("publication_performed", "external_actions_performed",
                  "target_repository_writes_performed", "original_source_repositories_modified",
                  "private_repository_payload_copied"):
        if cp.get(field) is not False:
            raise ProofEngineError(f"campaign close checkpoint exceeded boundary: {field}")
    return {**bundle, "evaluation": evaluation, "checkpoint": cp}
