from __future__ import annotations

from typing import Any

from .common import (
    PromotionApplicationPreviewError,
    digest,
    exact,
    fingerprint_material,
    integer,
    reject_private_content,
    relative_path,
    sha256_value,
    string_list,
    text,
)

SCHEMA_VERSION = "RTS-PROMOTION-APPLICATION-PREVIEW-V1"
MODE = "READ_ONLY_NON_APPLYING"
STATES = {"BLOCKED", "READY_FOR_SEPARATE_APPLICATION_REVIEW"}
ROOT_FIELDS = {
    "schema_version", "preview_id", "preview_fingerprint", "mode", "state",
    "generated_from", "proposed_change_set", "prerequisites", "blockers",
    "validation_steps", "stop_conditions", "rollback", "authority",
}
SOURCE_FIELDS = {
    "proposal_id", "proposal_fingerprint", "pending_review_fingerprint",
    "ledger_id", "ledger_record_count", "ledger_state",
    "ledger_current_decision_fingerprint", "ledger_approval_status",
    "ledger_summary_fingerprint", "ledger_manifest_fingerprint",
    "regression_result_fingerprint", "rollback_fingerprint",
    "baseline_snapshot_fingerprint", "candidate_snapshot_fingerprint",
}
CHANGE_FIELDS = {
    "operation", "repository", "path", "expected_before_sha256",
    "proposed_after_sha256",
}
ROLLBACK_FIELDS = {
    "rollback_id", "rollback_fingerprint", "restore_content_sha256",
    "human_approval_required", "automatic_rollback_authorized",
}
AUTHORITY_FIELDS = {
    "approval_status", "application_status", "target_write_authorized",
    "adjacent_repository_write_authorized", "skill_mutation_authorized",
    "commit_authorized", "merge_authorized", "external_action_authorized",
}


def validate_preview(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(record, ROOT_FIELDS, "preview")
    reject_private_content(record)
    if record["schema_version"] != SCHEMA_VERSION or record["mode"] != MODE:
        raise PromotionApplicationPreviewError("preview schema or mode boundary widened")
    if record["state"] not in STATES:
        raise PromotionApplicationPreviewError("invalid preview state")

    sources = exact(record["generated_from"], SOURCE_FIELDS, "generated_from")
    text(sources["proposal_id"], "proposal_id")
    for field in (
        "proposal_fingerprint", "pending_review_fingerprint",
        "ledger_summary_fingerprint", "ledger_manifest_fingerprint",
        "regression_result_fingerprint", "rollback_fingerprint",
        "baseline_snapshot_fingerprint", "candidate_snapshot_fingerprint",
    ):
        digest(sources[field], field)
    text(sources["ledger_id"], "ledger_id")
    integer(sources["ledger_record_count"], "ledger_record_count")
    text(sources["ledger_state"], "ledger_state")
    current = sources["ledger_current_decision_fingerprint"]
    if current is not None:
        digest(current, "ledger_current_decision_fingerprint")
    if sources["ledger_approval_status"] not in {"APPROVED", "NOT_APPROVED"}:
        raise PromotionApplicationPreviewError("invalid ledger approval status")

    changes = record["proposed_change_set"]
    if not isinstance(changes, list) or len(changes) != 1:
        raise PromotionApplicationPreviewError("v1 requires exactly one proposed change")
    change = exact(changes[0], CHANGE_FIELDS, "proposed_change_set[0]")
    if change["operation"] != "REPLACE_FILE":
        raise PromotionApplicationPreviewError("v1 operation must be REPLACE_FILE")
    text(change["repository"], "target repository")
    relative_path(change["path"], "target path")
    digest(change["expected_before_sha256"], "expected_before_sha256")
    digest(change["proposed_after_sha256"], "proposed_after_sha256")

    string_list(record["prerequisites"], "prerequisites", minimum=1)
    blockers = string_list(record["blockers"], "blockers")
    string_list(record["validation_steps"], "validation_steps", minimum=1)
    string_list(record["stop_conditions"], "stop_conditions", minimum=1)

    rollback = exact(record["rollback"], ROLLBACK_FIELDS, "rollback")
    text(rollback["rollback_id"], "rollback_id")
    digest(rollback["rollback_fingerprint"], "rollback_fingerprint")
    digest(rollback["restore_content_sha256"], "restore_content_sha256")
    if rollback["human_approval_required"] is not True:
        raise PromotionApplicationPreviewError("rollback must require human approval")
    if rollback["automatic_rollback_authorized"] is not False:
        raise PromotionApplicationPreviewError("automatic rollback authority widened")

    authority = exact(record["authority"], AUTHORITY_FIELDS, "authority")
    expected_authority = {
        "approval_status": "NOT_APPROVED",
        "application_status": "NOT_APPLIED",
        "target_write_authorized": False,
        "adjacent_repository_write_authorized": False,
        "skill_mutation_authorized": False,
        "commit_authorized": False,
        "merge_authorized": False,
        "external_action_authorized": False,
    }
    if authority != expected_authority:
        raise PromotionApplicationPreviewError("preview authority boundary widened")
    if record["state"] == "BLOCKED" and not blockers:
        raise PromotionApplicationPreviewError("blocked preview requires blockers")
    if record["state"] != "BLOCKED":
        raise PromotionApplicationPreviewError("repository-local v1 must remain blocked")

    digest(record["preview_fingerprint"], "preview_fingerprint")
    expected = sha256_value(fingerprint_material(record))
    if record["preview_fingerprint"] != expected:
        raise PromotionApplicationPreviewError("preview fingerprint mismatch")
    expected_id = f"RTS-PROMOTION-PREVIEW-{expected[:16].upper()}"
    if record["preview_id"] != expected_id:
        raise PromotionApplicationPreviewError("preview_id mismatch")
    return record
