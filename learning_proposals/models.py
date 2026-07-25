from __future__ import annotations

from typing import Any

from .common import (
    LearningProposalError,
    digest,
    exact,
    optional_text,
    reject_private_keys,
    require_relative_path,
    safe_id,
    sha256_value,
    string_list,
    text,
)

PROPOSAL_SCHEMA = "RTS-SKILL-PROMOTION-PROPOSAL-V1"
REVIEW_SCHEMA = "RTS-SKILL-PROMOTION-REVIEW-V1"
GENERATOR_IDENTITY = "rts-proposal-generator-v1"
PROPOSAL_STATUS = "REVIEW_REQUIRED"
APPROVAL_STATUS = "NOT_APPROVED"
APPLICATION_STATUS = "NOT_APPLIED"
ACTION = "REQUEST_HUMAN_REVIEW"
OUTCOME_IDS = ["RTS-OUTCOME-000001", "RTS-OUTCOME-000002", "RTS-OUTCOME-000003"]
EXPECTED_OUTCOMES = {
    "RTS-OUTCOME-000001": ("SUCCESS", "UNVERIFIED", "SUCCEEDED"),
    "RTS-OUTCOME-000002": ("ESCALATION", "VERIFIED", "ESCALATED"),
    "RTS-OUTCOME-000003": ("RECOVERY", "ASSUMED", "STOPPED"),
}
EXPECTED_EVIDENCE_IDS = {
    "RTS-OUTCOME-000001": "RTS-EVIDENCE-OUTCOME-000001",
    "RTS-OUTCOME-000002": "RTS-EVIDENCE-OUTCOME-000002",
    "RTS-OUTCOME-000003": "RTS-EVIDENCE-OUTCOME-000003",
}

PROPOSAL_FIELDS = {
    "schema_version", "proposal_id", "generator_identity", "proposal_status",
    "generated_from", "evidence_summary", "recommendation", "safeguards",
    "blockers", "proposal_fingerprint",
}
GENERATED_FROM_FIELDS = {"outcome_bundles", "regression", "rollback"}
OUTCOME_FIELDS = {
    "bundle_id", "bundle_fingerprint", "scenario", "outcome_classification",
    "execution_scope", "terminal_state", "evidence_refs", "evidence_integrity",
}
EVIDENCE_REF_FIELDS = {"evidence_id", "source_type", "source_ref", "retrieved_at"}
REGRESSION_FIELDS = {
    "dataset_id", "dataset_fingerprint", "result_id", "result_fingerprint",
    "recommendation", "promotion_eligibility", "baseline_snapshot_fingerprint",
    "candidate_snapshot_id", "candidate_snapshot_fingerprint", "rollback_fingerprint",
}
ROLLBACK_FIELDS = {
    "rollback_id", "rollback_fingerprint", "restore_content_sha256",
    "human_approval_required", "mutation_authorized",
    "adjacent_repository_write_authorized",
}
EVIDENCE_FIELDS = {"confirmed_facts", "assumptions", "unverified_claims", "risks"}
RECOMMENDATION_FIELDS = {
    "action", "target_skill_id", "candidate_snapshot_id",
    "candidate_snapshot_fingerprint", "rationale",
}
SAFEGUARD_FIELDS = {
    "approval_status", "application_status", "external_execution_performed",
    "mutation_authorized", "adjacent_repository_write_authorized",
    "self_approval_authorized", "automatic_rollback_authorized",
}

REVIEW_FIELDS = {
    "schema_version", "decision_id", "proposal_id", "proposal_fingerprint",
    "status", "reviewer", "generator_identity", "separation_of_duties",
    "rationale", "skill_mutation_authorized",
    "adjacent_repository_write_authorized", "application_status",
    "decision_fingerprint",
}
REVIEWER_FIELDS = {"type", "identity"}


def proposal_material(proposal: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in proposal.items() if key != "proposal_fingerprint"}


def review_material(review: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in review.items() if key != "decision_fingerprint"}


def validate_proposal(value: Any) -> dict[str, Any]:
    proposal = exact(value, PROPOSAL_FIELDS, "proposal")
    reject_private_keys(proposal)
    if proposal["schema_version"] != PROPOSAL_SCHEMA:
        raise LearningProposalError("proposal schema_version mismatch")
    safe_id(proposal["proposal_id"], "proposal.proposal_id")
    if proposal["generator_identity"] != GENERATOR_IDENTITY:
        raise LearningProposalError("proposal generator identity mismatch")
    if proposal["proposal_status"] != PROPOSAL_STATUS:
        raise LearningProposalError("proposal must remain REVIEW_REQUIRED")

    generated = exact(proposal["generated_from"], GENERATED_FROM_FIELDS, "proposal.generated_from")
    outcomes = generated["outcome_bundles"]
    if not isinstance(outcomes, list) or len(outcomes) != 3:
        raise LearningProposalError("proposal must reference exactly three outcome bundles")
    observed_ids: list[str] = []
    for index, raw in enumerate(outcomes):
        row = exact(raw, OUTCOME_FIELDS, f"proposal.generated_from.outcome_bundles[{index}]")
        bundle_id = safe_id(row["bundle_id"], "outcome.bundle_id")
        observed_ids.append(bundle_id)
        digest(row["bundle_fingerprint"], "outcome.bundle_fingerprint")
        expected = EXPECTED_OUTCOMES.get(bundle_id)
        if expected is None:
            raise LearningProposalError(f"unexpected outcome bundle: {bundle_id}")
        if (row["scenario"], row["outcome_classification"], row["terminal_state"]) != expected:
            raise LearningProposalError(f"outcome semantics mismatch for {bundle_id}")
        if row["execution_scope"] != "SIMULATED_ONLY":
            raise LearningProposalError("outcome execution_scope must remain SIMULATED_ONLY")

        refs = row["evidence_refs"]
        if not isinstance(refs, list) or len(refs) != 1:
            raise LearningProposalError(f"{bundle_id}: exactly one evidence reference is required")
        ref = exact(refs[0], EVIDENCE_REF_FIELDS, f"{bundle_id}.evidence_refs[0]")
        evidence_id = safe_id(ref["evidence_id"], f"{bundle_id}.evidence_id")
        if evidence_id != EXPECTED_EVIDENCE_IDS[bundle_id]:
            raise LearningProposalError(f"{bundle_id}: unexpected evidence ID")
        if ref["source_type"] != "local_controller_fixture":
            raise LearningProposalError(f"{bundle_id}: evidence source_type mismatch")
        require_relative_path(
            ref["source_ref"],
            f"{bundle_id}.evidence.source_ref",
            "outcome_evidence/evidence/",
        )
        text(ref["retrieved_at"], f"{bundle_id}.evidence.retrieved_at", 64)
        integrity = row["evidence_integrity"]
        if not isinstance(integrity, dict) or set(integrity) != {evidence_id}:
            raise LearningProposalError(f"{bundle_id}: evidence integrity keys mismatch")
        digest(integrity[evidence_id], f"{bundle_id}.evidence_integrity.{evidence_id}")
    if observed_ids != OUTCOME_IDS:
        raise LearningProposalError("outcome bundle references must use the governed order")

    regression = exact(generated["regression"], REGRESSION_FIELDS, "proposal.generated_from.regression")
    for field in (
        "dataset_fingerprint", "result_fingerprint", "baseline_snapshot_fingerprint",
        "candidate_snapshot_fingerprint", "rollback_fingerprint",
    ):
        digest(regression[field], f"regression.{field}")
    for field in ("dataset_id", "result_id", "candidate_snapshot_id"):
        safe_id(regression[field], f"regression.{field}")
    if regression["recommendation"] != "RESEARCH_READY":
        raise LearningProposalError("regression recommendation must be RESEARCH_READY")
    if regression["promotion_eligibility"] != "NOT_ELIGIBLE":
        raise LearningProposalError("regression promotion eligibility must remain NOT_ELIGIBLE")
    if regression["candidate_snapshot_id"] != "RTS-SKILL-SNAPSHOT-000002":
        raise LearningProposalError("unexpected candidate snapshot")

    rollback = exact(generated["rollback"], ROLLBACK_FIELDS, "proposal.generated_from.rollback")
    safe_id(rollback["rollback_id"], "rollback.rollback_id")
    for field in ("rollback_fingerprint", "restore_content_sha256"):
        digest(rollback[field], f"rollback.{field}")
    if rollback["human_approval_required"] is not True:
        raise LearningProposalError("rollback must require human approval")
    for field in ("mutation_authorized", "adjacent_repository_write_authorized"):
        if rollback[field] is not False:
            raise LearningProposalError(f"rollback {field} must be false")

    evidence = exact(proposal["evidence_summary"], EVIDENCE_FIELDS, "proposal.evidence_summary")
    string_list(evidence["confirmed_facts"], "evidence.confirmed_facts", minimum=1)
    string_list(evidence["assumptions"], "evidence.assumptions", minimum=1)
    string_list(evidence["unverified_claims"], "evidence.unverified_claims", minimum=1)
    string_list(evidence["risks"], "evidence.risks", minimum=1)

    recommendation = exact(proposal["recommendation"], RECOMMENDATION_FIELDS, "proposal.recommendation")
    if recommendation["action"] != ACTION:
        raise LearningProposalError("proposal action must be REQUEST_HUMAN_REVIEW")
    if recommendation["target_skill_id"] != "feature-build":
        raise LearningProposalError("proposal target_skill_id mismatch")
    if recommendation["candidate_snapshot_id"] != regression["candidate_snapshot_id"]:
        raise LearningProposalError("proposal candidate snapshot ID mismatch")
    if recommendation["candidate_snapshot_fingerprint"] != regression["candidate_snapshot_fingerprint"]:
        raise LearningProposalError("proposal candidate fingerprint mismatch")
    text(recommendation["rationale"], "proposal.recommendation.rationale")

    safeguards = exact(proposal["safeguards"], SAFEGUARD_FIELDS, "proposal.safeguards")
    if safeguards["approval_status"] != APPROVAL_STATUS:
        raise LearningProposalError("proposal approval_status must remain NOT_APPROVED")
    if safeguards["application_status"] != APPLICATION_STATUS:
        raise LearningProposalError("proposal application_status must remain NOT_APPLIED")
    for field in (
        "external_execution_performed", "mutation_authorized",
        "adjacent_repository_write_authorized", "self_approval_authorized",
        "automatic_rollback_authorized",
    ):
        if safeguards[field] is not False:
            raise LearningProposalError(f"proposal safeguard {field} must be false")

    blockers = string_list(proposal["blockers"], "proposal.blockers", minimum=3)
    required_blockers = {
        "external outcome success remains unverified",
        "human approval has not been recorded",
        "skill mutation and adjacent-repository writes are not authorized",
    }
    if not required_blockers.issubset(blockers):
        raise LearningProposalError("proposal is missing permanent blockers")

    expected_fingerprint = sha256_value(proposal_material(proposal))
    if digest(proposal["proposal_fingerprint"], "proposal.proposal_fingerprint") != expected_fingerprint:
        raise LearningProposalError("proposal fingerprint mismatch")
    return proposal


def validate_review(value: Any, *, committed_pending_only: bool = False) -> dict[str, Any]:
    review = exact(value, REVIEW_FIELDS, "review")
    reject_private_keys(review)
    if review["schema_version"] != REVIEW_SCHEMA:
        raise LearningProposalError("review schema_version mismatch")
    safe_id(review["decision_id"], "review.decision_id")
    safe_id(review["proposal_id"], "review.proposal_id")
    digest(review["proposal_fingerprint"], "review.proposal_fingerprint")
    if review["generator_identity"] != GENERATOR_IDENTITY:
        raise LearningProposalError("review generator identity mismatch")
    if review["status"] not in {"PENDING", "APPROVED", "REJECTED"}:
        raise LearningProposalError("review status is invalid")
    reviewer = exact(review["reviewer"], REVIEWER_FIELDS, "review.reviewer")
    reviewer_type = reviewer["type"]
    reviewer_identity = optional_text(reviewer["identity"], "review.reviewer.identity", 128)
    if review["status"] == "PENDING":
        if reviewer_type != "UNASSIGNED" or reviewer_identity is not None:
            raise LearningProposalError("pending review must remain unassigned")
    else:
        if reviewer_type != "HUMAN" or reviewer_identity is None:
            raise LearningProposalError("final review requires an explicit human identity")
        if reviewer_identity == review["generator_identity"]:
            raise LearningProposalError("proposal generator cannot review its own proposal")
    if committed_pending_only and review["status"] != "PENDING":
        raise LearningProposalError("committed v1 review record must remain PENDING")
    if review["separation_of_duties"] is not True:
        raise LearningProposalError("review must preserve separation of duties")
    text(review["rationale"], "review.rationale")
    if review["skill_mutation_authorized"] is not False:
        raise LearningProposalError("review cannot authorize Skill mutation in v1")
    if review["adjacent_repository_write_authorized"] is not False:
        raise LearningProposalError("review cannot authorize adjacent-repository writes in v1")
    if review["application_status"] != APPLICATION_STATUS:
        raise LearningProposalError("review application_status must remain NOT_APPLIED")
    expected_fingerprint = sha256_value(review_material(review))
    if digest(review["decision_fingerprint"], "review.decision_fingerprint") != expected_fingerprint:
        raise LearningProposalError("review fingerprint mismatch")
    return review
