from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .cross_repo_review import verify_round_two_review_bundle
from .cross_repo_validation import verify_bundle as verify_cross_repo_bundle
from .learning import preflight_candidate

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "cross_repo_reviews" / "round_0003"
CONTRACT_PATH = ROUND_DIR / "review_contract.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "cross_repo_round_3_review_checkpoint_0011.json"

REVIEW_ROUND_ID = "PROOF-ENGINE-CROSS-REPO-REVIEW-ROUND-0003"
SOURCE_RUN_FINGERPRINT = "413304aa513efe09cae300de23909318e8bfcc6ecfef5be7a35ab79a70def5bb"
SOURCE_ROUND_FINGERPRINT = "93b30a087662bc62a6e5060fff9221c41f83d1596b181117ae70dee78769685f"
PREVIOUS_CHECKPOINT_FINGERPRINT = "70fddeb389c615fdaed8769cefb940333de262bf47711c1d937c8d32cb1bb74d"
APPROVED_ORIGINAL_IDS = {f"MC-{index:03d}" for index in range(1, 8)}
REVISED_ID = "MC-008"
EXPECTED_AUTHOR = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_ROUND_3_CONFIRMATION",
    "role": "PROJECT_OWNER",
    "instruction": "ラウンド三からラウンド四へ。",
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
    "schema_version",
    "checkpoint_id",
    "source_run_fingerprint",
    "source_round_fingerprint",
    "previous_round_checkpoint_fingerprint",
    "review_fingerprint",
    "learning_observation_fingerprint",
    "completed_rounds",
    "round_effective_candidate_count",
    "cumulative_effective_candidate_count",
    "round_revision_count",
    "cumulative_revision_count",
    "withheld_claim_count",
    "state",
    "publication_performed",
    "external_actions_performed",
    "target_repository_writes_performed",
    "original_source_repository_modified",
    "private_repository_payload_copied",
    "next_action",
    "checkpoint_fingerprint",
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


def _source_round() -> tuple[dict[str, Any], dict[str, Any]]:
    previous = verify_round_two_review_bundle()
    if previous["checkpoint"]["checkpoint_fingerprint"] != PREVIOUS_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("Round 3 previous review checkpoint drift")
    bundle = verify_cross_repo_bundle()
    run = bundle["run"]
    if run.get("run_fingerprint") != SOURCE_RUN_FINGERPRINT:
        raise ProofEngineError("Round 3 source run drift")
    round_value = next((item for item in run["rounds"] if item["round_id"] == "ROUND-3"), None)
    if round_value is None or round_value.get("round_fingerprint") != SOURCE_ROUND_FINGERPRINT:
        raise ProofEngineError("Round 3 source round drift")
    if round_value.get("source_mode") != "READ_ONLY_METADATA_SNAPSHOT":
        raise ProofEngineError("Round 3 private source boundary widened")
    if len(round_value.get("withheld_claims", [])) != 2:
        raise ProofEngineError("Round 3 withheld claims drift")
    return bundle, round_value


def verify_review_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "Round 3 review contract")
    if value.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-CONTRACT-V1":
        raise ProofEngineError("Round 3 review contract schema mismatch")
    if value.get("contract_id") != "PROOF-ENGINE-CROSS-REPO-ROUND-3-REVIEW-CONTRACT-0001":
        raise ProofEngineError("Round 3 review contract identity mismatch")
    if value.get("human_authorization") != EXPECTED_AUTHOR:
        raise ProofEngineError("Round 3 review contract is not bound to the explicit human confirmation")
    _verify_false_authority(value.get("authority"), "Round 3 review contract")
    source = value.get("source")
    if source != {
        "campaign_fingerprint": "d3dec34bc2686601f08324889510da9a312cc46565fc97d806c651fedbb89c95",
        "run_fingerprint": SOURCE_RUN_FINGERPRINT,
        "round_id": "ROUND-3",
        "round_fingerprint": SOURCE_ROUND_FINGERPRINT,
        "repository": "nobutakayamauchi/RTS-minicompany",
        "previous_round_checkpoint_fingerprint": PREVIOUS_CHECKPOINT_FINGERPRINT,
    }:
        raise ProofEngineError("Round 3 review contract source mismatch")
    decisions = value.get("original_decisions")
    if not isinstance(decisions, list) or [item.get("candidate_id") for item in decisions] != [f"MC-{index:03d}" for index in range(1, 9)]:
        raise ProofEngineError("Round 3 original decision order mismatch")
    if any(item.get("decision") != "APPROVE" for item in decisions[:7]) or decisions[7].get("decision") != "REVISE":
        raise ProofEngineError("Round 3 original decisions mismatch")
    if any(not isinstance(item.get("reason"), str) or not item["reason"].strip() for item in decisions):
        raise ProofEngineError("Round 3 decision reason missing")
    revision = value.get("revision")
    if not isinstance(revision, dict) or revision.get("candidate_id") != REVISED_ID or revision.get("revision_id") != "MC-008-R1":
        raise ProofEngineError("Round 3 revision contract mismatch")
    if revision.get("record_kind") != "PROCESS_BYPRODUCT":
        raise ProofEngineError("Round 3 revision classification mismatch")
    if not revision.get("claim", "").startswith("In this validation run,"):
        raise ProofEngineError("Round 3 revision is not bounded to the observed run")
    if value.get("revision_decision", {}).get("decision") != "APPROVE":
        raise ProofEngineError("Round 3 revision approval missing")
    if value.get("withheld_claims") != [
        {"claim": "The selected publication cycles generated revenue.", "status": "WITHHELD_UNSUPPORTED"},
        {"claim": "Media Engine performs automatic social publishing.", "status": "WITHHELD_CONTRADICTED_BY_BOUNDARY"},
    ]:
        raise ProofEngineError("Round 3 withheld decisions mismatch")
    if value.get("terminal") != {
        "review_state": "ROUND_3_COMPLETE",
        "next_round": "ROUND-4",
        "publication_status": "NOT_PUBLISHED",
    }:
        raise ProofEngineError("Round 3 review terminal mismatch")
    return value


def _build_revision(original: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    patch = contract["revision"]
    revision = {
        "schema_version": "PROOF-ENGINE-CROSS-REPO-CANDIDATE-REVISION-V1",
        "candidate_id": REVISED_ID,
        "revision_id": "MC-008-R1",
        "version": 2,
        "supersedes_candidate_fingerprint": original["candidate_fingerprint"],
        "round_id": "ROUND-3",
        "repository": "nobutakayamauchi/RTS-minicompany",
        "claim": patch["claim"],
        "record_kind": patch["record_kind"],
        "factuality_note": patch["factuality_note"],
        "contribution_map": copy.deepcopy(original["contribution_map"]),
        "evidence_label": original["evidence_label"],
        "evidence_prs": copy.deepcopy(original["evidence_prs"]),
        "public_disclosure": "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL",
        "status": "REVIEW_REQUIRED",
        "revision_reason": patch["revision_reason"],
    }
    revision["candidate_fingerprint"] = fingerprint(revision)
    if preflight_candidate(revision).get("result") != "PASS":
        raise ProofEngineError("MC-008-R1 failed active learning preflight")
    return revision


def build_round_three_review(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    source_bundle, round_value = _source_round()
    review_contract = verify_review_contract(contract)
    originals = {item["candidate_id"]: item for item in round_value["candidates"]}
    if set(originals) != APPROVED_ORIGINAL_IDS | {REVISED_ID}:
        raise ProofEngineError("Round 3 candidate set mismatch")
    revision = _build_revision(originals[REVISED_ID], review_contract)
    author_fingerprint = fingerprint(EXPECTED_AUTHOR)
    authority = review_contract["authority"]
    authority_fingerprint = fingerprint(authority)

    decisions: list[dict[str, Any]] = []
    approval_fingerprints: dict[tuple[str, int], str] = {}
    previous = None
    sequence = 1
    for contract_decision in review_contract["original_decisions"]:
        candidate_id = contract_decision["candidate_id"]
        decision_type = contract_decision["decision"]
        decision = {
            "decision_id": f"CROSS-REPO-REVIEW-0003-D{sequence:03d}",
            "sequence": sequence,
            "previous_decision_fingerprint": previous,
            "author_fingerprint": author_fingerprint,
            "authority_fingerprint": authority_fingerprint,
            "decision_type": decision_type,
            "reason": contract_decision["reason"],
            "target": {
                "candidate_id": candidate_id,
                "candidate_version": 1,
                "source": "CROSS_REPO_RUN",
                "candidate_fingerprint": originals[candidate_id]["candidate_fingerprint"],
            },
            "revision_ref": None,
        }
        if decision_type == "REVISE":
            decision["revision_ref"] = {
                "revision_id": revision["revision_id"],
                "candidate_fingerprint": revision["candidate_fingerprint"],
            }
        decision["decision_fingerprint"] = fingerprint(decision)
        decisions.append(decision)
        previous = decision["decision_fingerprint"]
        if decision_type == "APPROVE":
            approval_fingerprints[(candidate_id, 1)] = previous
        sequence += 1

    revision_decision = {
        "decision_id": f"CROSS-REPO-REVIEW-0003-D{sequence:03d}",
        "sequence": sequence,
        "previous_decision_fingerprint": previous,
        "author_fingerprint": author_fingerprint,
        "authority_fingerprint": authority_fingerprint,
        "decision_type": "APPROVE",
        "reason": review_contract["revision_decision"]["reason"],
        "target": {
            "candidate_id": REVISED_ID,
            "candidate_version": 2,
            "source": "REVISION_LEDGER",
            "candidate_fingerprint": revision["candidate_fingerprint"],
        },
        "revision_ref": None,
    }
    revision_decision["decision_fingerprint"] = fingerprint(revision_decision)
    decisions.append(revision_decision)
    approval_fingerprints[(REVISED_ID, 2)] = revision_decision["decision_fingerprint"]

    effective = [
        {
            "candidate_id": candidate_id,
            "candidate_version": 1,
            "source": "CROSS_REPO_RUN",
            "candidate_fingerprint": originals[candidate_id]["candidate_fingerprint"],
            "approval_decision_fingerprint": approval_fingerprints[(candidate_id, 1)],
            "status": "APPROVED_FOR_INTERNAL_VALIDATION",
        }
        for candidate_id in sorted(APPROVED_ORIGINAL_IDS)
    ]
    effective.append({
        "candidate_id": REVISED_ID,
        "candidate_version": 2,
        "source": "REVISION_LEDGER",
        "candidate_fingerprint": revision["candidate_fingerprint"],
        "approval_decision_fingerprint": approval_fingerprints[(REVISED_ID, 2)],
        "status": "APPROVED_FOR_INTERNAL_VALIDATION",
    })

    review = {
        "schema_version": "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-V1",
        "review_round_id": REVIEW_ROUND_ID,
        "source": {
            "campaign_fingerprint": source_bundle["campaign"]["campaign_fingerprint"],
            "run_fingerprint": SOURCE_RUN_FINGERPRINT,
            "round_id": "ROUND-3",
            "round_fingerprint": SOURCE_ROUND_FINGERPRINT,
            "repository": "nobutakayamauchi/RTS-minicompany",
        },
        "previous_round_checkpoint_fingerprint": PREVIOUS_CHECKPOINT_FINGERPRINT,
        "author": copy.deepcopy(EXPECTED_AUTHOR),
        "author_fingerprint": author_fingerprint,
        "authority": copy.deepcopy(authority),
        "authority_fingerprint": authority_fingerprint,
        "originals_preserved": True,
        "revision_mode": "APPEND_ONLY",
        "revision": revision,
        "decisions": decisions,
        "effective_candidates": effective,
        "withheld_claims_confirmed": copy.deepcopy(review_contract["withheld_claims"]),
        "counts": {
            "original_candidates": 8,
            "originals_approved": 7,
            "originals_revised": 1,
            "revisions_approved": 1,
            "effective_approved": 8,
            "rejected": 0,
            "redacted": 0,
            "expired": 0,
            "withheld_claims_retained": 2,
        },
        "metrics": {
            "first_pass_approval_rate": 7 / 8,
            "revision_rate": 1 / 8,
            "rejection_rate": 0.0,
            "scope_corrections": 1,
            "commercial_overclaim_corrections": 0,
            "withheld_claims_retained": 2,
            "private_payload_exposure_incidents": 0,
            "comparison_to_round_2": {
                "round_2_first_pass_approval_rate": 5 / 6,
                "direction": "POSITIVE_SIGNAL_NOT_PROOF",
                "reason": "Repository type, privacy boundary, evidence density, and candidate count differ, so the comparison is descriptive rather than causal.",
            },
        },
        "review_state": "ROUND_3_COMPLETE",
        "next_round": "ROUND-4",
        "publication_status": "NOT_PUBLISHED",
    }
    review["review_fingerprint"] = fingerprint(review)
    return review


def build_learning_observation(review: dict[str, Any]) -> dict[str, Any]:
    effective = {item["candidate_id"]: item for item in review["effective_candidates"]}
    revision = review["revision"]
    observation = {
        "schema_version": "PROOF-ENGINE-CROSS-REPO-LEARNING-OBSERVATION-V1",
        "observation_id": "PROOF-ENGINE-CROSS-REPO-LEARNING-OBSERVATION-0003",
        "source_review_round_id": REVIEW_ROUND_ID,
        "source_review_fingerprint": review["review_fingerprint"],
        "positive_examples": [
            {
                "candidate_id": candidate_id,
                "candidate_fingerprint": effective[candidate_id]["candidate_fingerprint"],
                "expected_action": "APPROVE",
            }
            for candidate_id in sorted(APPROVED_ORIGINAL_IDS)
        ],
        "correction_pairs": [{
            "candidate_id": REVISED_ID,
            "original_fingerprint": revision["supersedes_candidate_fingerprint"],
            "original_claim": "The private repository evidence can be analyzed without exposing customer records or treating publication-cycle evidence as proof of revenue.",
            "revision_id": revision["revision_id"],
            "revision_fingerprint": revision["candidate_fingerprint"],
            "revised_claim": revision["claim"],
            "record_kind": revision["record_kind"],
            "error_labels": ["GENERALIZATION_EXCEEDS_SINGLE_RUN", "PRIVATE_REPOSITORY_SAFETY_SCOPE_OVERSTATED"],
            "expected_action": "REVISE_THEN_APPROVE",
        }],
        "withheld_claims": [
            {
                "claim": "The selected publication cycles generated revenue.",
                "learning_label": "COMMERCIAL_OUTCOME_UNSUPPORTED",
                "expected_action": "WITHHOLD",
            },
            {
                "claim": "Media Engine performs automatic social publishing.",
                "learning_label": "AUTOMATION_CLAIM_CONTRADICTS_MANUAL_BOUNDARY",
                "expected_action": "WITHHOLD",
            },
        ],
        "rule_change": {
            "new_rule_activated": False,
            "existing_rules_reinforced": ["REVIEW-RULE-004", "REVIEW-RULE-006"],
            "mode": "SUGGEST_ONLY",
        },
        "metrics": {
            "positive_examples": 7,
            "correction_pairs": 1,
            "withheld_claims": 2,
            "first_pass_approval_rate": 7 / 8,
            "comparison_state": "POSITIVE_SIGNAL_NOT_PROOF",
        },
        "authority": {
            "automatic_approval_authorized": False,
            "automatic_rewrite_authorized": False,
            "model_weight_training_authorized": False,
            "publication_authorized": False,
        },
    }
    observation["observation_fingerprint"] = fingerprint(observation)
    return observation


def verify_round_three_review_bundle(
    *,
    contract: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = build_round_three_review(contract)
    _verify_fingerprint(review, "review_fingerprint", "Round 3 review")
    if review.get("review_fingerprint") != "9466b9832eddce9e9458d07197ca68054bd26b0a12e1171dc165b1c56a27be43":
        raise ProofEngineError("Round 3 review deterministic fingerprint mismatch")
    observation = build_learning_observation(review)
    _verify_fingerprint(observation, "observation_fingerprint", "Round 3 learning observation")
    if observation.get("observation_fingerprint") != "ee16d8cebd9563c6b13374a990885595c7a29fceff88af95b62155f46190e684":
        raise ProofEngineError("Round 3 learning observation deterministic fingerprint mismatch")
    if observation["rule_change"]["new_rule_activated"] is not False:
        raise ProofEngineError("Round 3 learning observation manufactured a new rule")

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("Round 3 review checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "Round 3 review checkpoint")
    if cp.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-CHECKPOINT-V1":
        raise ProofEngineError("Round 3 review checkpoint schema mismatch")
    if cp.get("checkpoint_id") != "PROOF-ENGINE-CROSS-REPO-ROUND-3-REVIEW-CHECKPOINT-0011":
        raise ProofEngineError("Round 3 review checkpoint identity mismatch")
    links = {
        "source_run_fingerprint": SOURCE_RUN_FINGERPRINT,
        "source_round_fingerprint": SOURCE_ROUND_FINGERPRINT,
        "previous_round_checkpoint_fingerprint": PREVIOUS_CHECKPOINT_FINGERPRINT,
        "review_fingerprint": review["review_fingerprint"],
        "learning_observation_fingerprint": observation["observation_fingerprint"],
    }
    for field, expected in links.items():
        if cp.get(field) != expected:
            raise ProofEngineError(f"Round 3 review checkpoint link mismatch: {field}")
    if cp.get("completed_rounds") != ["ROUND-2", "ROUND-3"]:
        raise ProofEngineError("Round 3 review checkpoint order mismatch")
    if cp.get("round_effective_candidate_count") != 8 or cp.get("cumulative_effective_candidate_count") != 14:
        raise ProofEngineError("Round 3 review checkpoint candidate counts mismatch")
    if cp.get("round_revision_count") != 1 or cp.get("cumulative_revision_count") != 2 or cp.get("withheld_claim_count") != 2:
        raise ProofEngineError("Round 3 review checkpoint review counts mismatch")
    if cp.get("state") != "ROUND_3_COMPLETE_ROUND_4_REVIEW_REQUIRED":
        raise ProofEngineError("Round 3 review checkpoint state mismatch")
    for field in (
        "publication_performed",
        "external_actions_performed",
        "target_repository_writes_performed",
        "original_source_repository_modified",
        "private_repository_payload_copied",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"Round 3 review checkpoint exceeded boundary: {field}")
    return {"contract": verify_review_contract(contract), "review": review, "learning_observation": observation, "checkpoint": cp}
