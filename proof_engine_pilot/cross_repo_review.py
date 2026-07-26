from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .cross_repo_validation import verify_bundle as verify_cross_repo_bundle
from .learning import preflight_candidate

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "cross_repo_reviews" / "round_0002"
REVIEW_PATH = ROUND_DIR / "review.json"
LEARNING_PATH = ROUND_DIR / "learning_observation.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "cross_repo_round_2_review_checkpoint_0010.json"

REVIEW_ROUND_ID = "PROOF-ENGINE-CROSS-REPO-REVIEW-ROUND-0002"
SOURCE_RUN_FINGERPRINT = "413304aa513efe09cae300de23909318e8bfcc6ecfef5be7a35ab79a70def5bb"
SOURCE_ROUND_FINGERPRINT = "d9d2f1b9dc73ddcb7fbd062431d08c311eb9ef26a9fdb8d38f1d653eccc42ea8"
APPROVED_ORIGINAL_IDS = {"SC-001", "SC-002", "SC-003", "SC-004", "SC-005"}
REVISED_ID = "SC-006"
EXPECTED_AUTHOR = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_ROUND_2_CONFIRMATION",
    "role": "PROJECT_OWNER",
    "instruction": "ラウンド2確定で、ラウンド3に行く。",
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
    "review_fingerprint",
    "learning_observation_fingerprint",
    "completed_rounds",
    "effective_candidate_count",
    "revision_count",
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


def _round_two_source() -> tuple[dict[str, Any], dict[str, Any]]:
    bundle = verify_cross_repo_bundle()
    run = bundle["run"]
    if run.get("run_fingerprint") != SOURCE_RUN_FINGERPRINT:
        raise ProofEngineError("Round 2 review source run drift")
    round_value = next((item for item in run["rounds"] if item["round_id"] == "ROUND-2"), None)
    if round_value is None or round_value.get("round_fingerprint") != SOURCE_ROUND_FINGERPRINT:
        raise ProofEngineError("Round 2 review source round drift")
    if round_value.get("excluded_unmerged_prs") != [17, 18]:
        raise ProofEngineError("Round 2 review unmerged exclusion drift")
    return bundle, round_value


def verify_round_two_review(review: dict[str, Any] | None = None) -> dict[str, Any]:
    source_bundle, round_value = _round_two_source()
    value = load(REVIEW_PATH) if review is None else copy.deepcopy(review)
    _verify_fingerprint(value, "review_fingerprint", "Round 2 review")
    if value.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-V1":
        raise ProofEngineError("Round 2 review schema mismatch")
    if value.get("review_round_id") != REVIEW_ROUND_ID:
        raise ProofEngineError("Round 2 review identity mismatch")
    source = value.get("source", {})
    if source != {
        "campaign_fingerprint": source_bundle["campaign"]["campaign_fingerprint"],
        "run_fingerprint": SOURCE_RUN_FINGERPRINT,
        "round_id": "ROUND-2",
        "round_fingerprint": SOURCE_ROUND_FINGERPRINT,
        "repository": "nobutakayamauchi/seminar-compass",
    }:
        raise ProofEngineError("Round 2 review source mismatch")
    if value.get("author") != EXPECTED_AUTHOR or value.get("author_fingerprint") != fingerprint(EXPECTED_AUTHOR):
        raise ProofEngineError("Round 2 review is not bound to the explicit human confirmation")
    authority = _verify_false_authority(value.get("authority"), "Round 2 review")
    if value.get("authority_fingerprint") != fingerprint(authority):
        raise ProofEngineError("Round 2 review authority fingerprint mismatch")
    if value.get("originals_preserved") is not True or value.get("revision_mode") != "APPEND_ONLY":
        raise ProofEngineError("Round 2 review did not preserve originals")

    originals = {item["candidate_id"]: item for item in round_value["candidates"]}
    if set(originals) != APPROVED_ORIGINAL_IDS | {REVISED_ID}:
        raise ProofEngineError("Round 2 candidate set mismatch")
    revision = value.get("revision")
    if not isinstance(revision, dict):
        raise ProofEngineError("Round 2 revision missing")
    _verify_fingerprint(revision, "candidate_fingerprint", "SC-006-R1")
    original = originals[REVISED_ID]
    if revision.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-CANDIDATE-REVISION-V1":
        raise ProofEngineError("Round 2 revision schema mismatch")
    if revision.get("revision_id") != "SC-006-R1" or revision.get("version") != 2:
        raise ProofEngineError("Round 2 revision identity mismatch")
    if revision.get("supersedes_candidate_fingerprint") != original["candidate_fingerprint"]:
        raise ProofEngineError("Round 2 revision lineage mismatch")
    if revision.get("record_kind") != "PROCESS_BYPRODUCT":
        raise ProofEngineError("Round 2 revision classification mismatch")
    if revision.get("evidence_prs") != original["evidence_prs"] or set(revision["evidence_prs"]) & {17, 18}:
        raise ProofEngineError("Round 2 revision evidence boundary mismatch")
    if revision.get("status") != "REVIEW_REQUIRED" or revision.get("public_disclosure") != "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL":
        raise ProofEngineError("Round 2 revision authority widened")
    if preflight_candidate(revision).get("result") != "PASS":
        raise ProofEngineError("Round 2 revision failed active learning preflight")

    decisions = value.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 7:
        raise ProofEngineError("Round 2 decision count mismatch")
    previous = None
    approved_originals: set[str] = set()
    revised_originals: set[str] = set()
    approved_revisions: set[str] = set()
    approvals: dict[tuple[str, int], str] = {}
    for sequence, decision in enumerate(decisions, start=1):
        _verify_fingerprint(decision, "decision_fingerprint", f"Round 2 decision {sequence}")
        if decision.get("decision_id") != f"CROSS-REPO-REVIEW-0002-D{sequence:03d}" or decision.get("sequence") != sequence:
            raise ProofEngineError("Round 2 decision identity mismatch")
        if decision.get("previous_decision_fingerprint") != previous:
            raise ProofEngineError("Round 2 decision chain mismatch")
        previous = decision["decision_fingerprint"]
        if decision.get("author_fingerprint") != value["author_fingerprint"] or decision.get("authority_fingerprint") != value["authority_fingerprint"]:
            raise ProofEngineError("Round 2 decision attribution mismatch")
        target = decision.get("target", {})
        candidate_id = target.get("candidate_id")
        candidate_version = target.get("candidate_version")
        if target.get("source") == "CROSS_REPO_RUN" and candidate_version == 1:
            if candidate_id not in originals or target.get("candidate_fingerprint") != originals[candidate_id]["candidate_fingerprint"]:
                raise ProofEngineError("Round 2 decision original target mismatch")
            if decision.get("decision_type") == "APPROVE" and candidate_id in APPROVED_ORIGINAL_IDS:
                if decision.get("revision_ref") is not None:
                    raise ProofEngineError("Round 2 original approval references a revision")
                approved_originals.add(candidate_id)
                approvals[(candidate_id, 1)] = decision["decision_fingerprint"]
            elif decision.get("decision_type") == "REVISE" and candidate_id == REVISED_ID:
                expected_ref = {"revision_id": "SC-006-R1", "candidate_fingerprint": revision["candidate_fingerprint"]}
                if decision.get("revision_ref") != expected_ref:
                    raise ProofEngineError("Round 2 revision decision link mismatch")
                revised_originals.add(candidate_id)
            else:
                raise ProofEngineError("Round 2 unexpected original decision")
        elif target.get("source") == "REVISION_LEDGER" and candidate_version == 2:
            if candidate_id != REVISED_ID or decision.get("decision_type") != "APPROVE":
                raise ProofEngineError("Round 2 unexpected revision decision")
            if target.get("candidate_fingerprint") != revision["candidate_fingerprint"] or decision.get("revision_ref") is not None:
                raise ProofEngineError("Round 2 revision approval mismatch")
            approved_revisions.add(candidate_id)
            approvals[(candidate_id, 2)] = decision["decision_fingerprint"]
        else:
            raise ProofEngineError("Round 2 decision target source mismatch")
    if approved_originals != APPROVED_ORIGINAL_IDS or revised_originals != {REVISED_ID} or approved_revisions != {REVISED_ID}:
        raise ProofEngineError("Round 2 decision coverage incomplete")

    expected_effective = []
    for candidate_id in sorted(APPROVED_ORIGINAL_IDS):
        expected_effective.append({
            "candidate_id": candidate_id,
            "candidate_version": 1,
            "source": "CROSS_REPO_RUN",
            "candidate_fingerprint": originals[candidate_id]["candidate_fingerprint"],
            "approval_decision_fingerprint": approvals[(candidate_id, 1)],
            "status": "APPROVED_FOR_INTERNAL_VALIDATION",
        })
    expected_effective.append({
        "candidate_id": REVISED_ID,
        "candidate_version": 2,
        "source": "REVISION_LEDGER",
        "candidate_fingerprint": revision["candidate_fingerprint"],
        "approval_decision_fingerprint": approvals[(REVISED_ID, 2)],
        "status": "APPROVED_FOR_INTERNAL_VALIDATION",
    })
    if value.get("effective_candidates") != expected_effective:
        raise ProofEngineError("Round 2 effective candidate set mismatch")
    if value.get("counts") != {
        "original_candidates": 6,
        "originals_approved": 5,
        "originals_revised": 1,
        "revisions_approved": 1,
        "effective_approved": 6,
        "rejected": 0,
        "redacted": 0,
        "expired": 0,
    }:
        raise ProofEngineError("Round 2 review counts mismatch")
    metrics = value.get("metrics", {})
    if metrics.get("first_pass_approval_rate") != 5 / 6 or metrics.get("revision_rate") != 1 / 6:
        raise ProofEngineError("Round 2 review metrics mismatch")
    if metrics.get("classification_corrections") != 1 or metrics.get("overclaim_corrections") != 0 or metrics.get("unmerged_evidence_incidents") != 0:
        raise ProofEngineError("Round 2 review metric details mismatch")
    if metrics.get("comparison_to_round_1", {}).get("direction") != "POSITIVE_SIGNAL_NOT_PROOF":
        raise ProofEngineError("Round 2 review overclaims learning effectiveness")
    if value.get("review_state") != "ROUND_2_COMPLETE" or value.get("next_round") != "ROUND-3" or value.get("publication_status") != "NOT_PUBLISHED":
        raise ProofEngineError("Round 2 review terminal state mismatch")
    return value


def verify_learning_observation(review: dict[str, Any], observation: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(LEARNING_PATH) if observation is None else copy.deepcopy(observation)
    _verify_fingerprint(value, "observation_fingerprint", "Round 2 learning observation")
    if value.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-LEARNING-OBSERVATION-V1":
        raise ProofEngineError("Round 2 learning observation schema mismatch")
    if value.get("observation_id") != "PROOF-ENGINE-CROSS-REPO-LEARNING-OBSERVATION-0002":
        raise ProofEngineError("Round 2 learning observation identity mismatch")
    if value.get("source_review_round_id") != REVIEW_ROUND_ID or value.get("source_review_fingerprint") != review["review_fingerprint"]:
        raise ProofEngineError("Round 2 learning observation source mismatch")
    positives = value.get("positive_examples")
    if not isinstance(positives, list) or {item.get("candidate_id") for item in positives} != APPROVED_ORIGINAL_IDS:
        raise ProofEngineError("Round 2 learning positive set mismatch")
    review_effective = {item["candidate_id"]: item for item in review["effective_candidates"]}
    for item in positives:
        candidate_id = item["candidate_id"]
        if item.get("candidate_fingerprint") != review_effective[candidate_id]["candidate_fingerprint"] or item.get("expected_action") != "APPROVE":
            raise ProofEngineError("Round 2 learning positive link mismatch")
    pairs = value.get("correction_pairs")
    if not isinstance(pairs, list) or len(pairs) != 1:
        raise ProofEngineError("Round 2 learning correction count mismatch")
    pair = pairs[0]
    if pair.get("candidate_id") != REVISED_ID or pair.get("original_fingerprint") != review["revision"]["supersedes_candidate_fingerprint"]:
        raise ProofEngineError("Round 2 learning correction source mismatch")
    if pair.get("revision_id") != "SC-006-R1" or pair.get("revision_fingerprint") != review["revision"]["candidate_fingerprint"]:
        raise ProofEngineError("Round 2 learning correction revision mismatch")
    if pair.get("error_labels") != ["ARTIFACT_KIND_MISCLASSIFIED", "AUDIT_IMPLICATION_UNSUPPORTED"]:
        raise ProofEngineError("Round 2 learning error labels mismatch")
    if value.get("rule_change") != {
        "new_rule_activated": False,
        "existing_rules_reinforced": ["REVIEW-RULE-002"],
        "mode": "SUGGEST_ONLY",
    }:
        raise ProofEngineError("Round 2 learning rule authority mismatch")
    if value.get("authority") != {
        "automatic_approval_authorized": False,
        "automatic_rewrite_authorized": False,
        "model_weight_training_authorized": False,
        "publication_authorized": False,
    }:
        raise ProofEngineError("Round 2 learning authority widened")
    return value


def verify_round_two_review_bundle(
    *,
    review: dict[str, Any] | None = None,
    observation: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reviewed = verify_round_two_review(review)
    learned = verify_learning_observation(reviewed, observation)
    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("Round 2 review checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "Round 2 review checkpoint")
    if cp.get("schema_version") != "PROOF-ENGINE-CROSS-REPO-ROUND-REVIEW-CHECKPOINT-V1":
        raise ProofEngineError("Round 2 review checkpoint schema mismatch")
    if cp.get("checkpoint_id") != "PROOF-ENGINE-CROSS-REPO-ROUND-2-REVIEW-CHECKPOINT-0010":
        raise ProofEngineError("Round 2 review checkpoint identity mismatch")
    if cp.get("source_run_fingerprint") != SOURCE_RUN_FINGERPRINT or cp.get("source_round_fingerprint") != SOURCE_ROUND_FINGERPRINT:
        raise ProofEngineError("Round 2 review checkpoint source mismatch")
    if cp.get("review_fingerprint") != reviewed["review_fingerprint"] or cp.get("learning_observation_fingerprint") != learned["observation_fingerprint"]:
        raise ProofEngineError("Round 2 review checkpoint link mismatch")
    if cp.get("completed_rounds") != ["ROUND-2"] or cp.get("effective_candidate_count") != 6 or cp.get("revision_count") != 1:
        raise ProofEngineError("Round 2 review checkpoint counts mismatch")
    if cp.get("state") != "ROUND_2_COMPLETE_ROUND_3_REVIEW_REQUIRED":
        raise ProofEngineError("Round 2 review checkpoint state mismatch")
    for field in (
        "publication_performed",
        "external_actions_performed",
        "target_repository_writes_performed",
        "original_source_repository_modified",
        "private_repository_payload_copied",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"Round 2 review checkpoint exceeded boundary: {field}")
    return {"review": reviewed, "learning_observation": learned, "checkpoint": cp}
