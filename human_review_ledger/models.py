from __future__ import annotations

from typing import Any

from .common import (
    HumanReviewLedgerError,
    boolean,
    digest,
    exact,
    fingerprint_material,
    integer,
    optional_time,
    reject_private_content,
    require_relative_path,
    safe_id,
    sha256_value,
    string_list,
    text,
)

POLICY_SCHEMA = "RTS-HUMAN-REVIEW-POLICY-V1"
SCOPE_SCHEMA = "RTS-HUMAN-REVIEW-SCOPE-V1"
DECISION_SCHEMA = "RTS-HUMAN-REVIEW-DECISION-V1"
MANIFEST_SCHEMA = "RTS-HUMAN-REVIEW-LEDGER-MANIFEST-V1"
SUMMARY_SCHEMA = "RTS-HUMAN-REVIEW-LEDGER-SUMMARY-V1"
LEDGER_ID = "RTS-HUMAN-REVIEW-LEDGER-000001"
DECISION_TYPES = {
    "APPROVE",
    "REJECT",
    "RETURN_FOR_REVISION",
    "EXPIRE",
    "SUPERSEDE",
}
SOURCE_FIELDS = {
    "proposal",
    "pending_review",
    "outcome_evidence",
    "regression_result",
    "rollback",
    "policy",
    "reviewer_scope",
}
NON_AUTHORITY_FIELDS = {
    "approval_status",
    "application_status",
    "skill_mutation_authorized",
    "adjacent_repository_write_authorized",
    "merge_authorized",
    "external_action_authorized",
}


def validate_policy(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "policy_id",
            "ledger_id",
            "allowed_decisions",
            "reviewer_roles",
            "required_source_kinds",
            "separation_of_duties",
            "expiry_rules",
            "authority",
            "policy_fingerprint",
        },
        "policy",
    )
    reject_private_content(record)
    if record["schema_version"] != POLICY_SCHEMA or record["ledger_id"] != LEDGER_ID:
        raise HumanReviewLedgerError("policy schema or ledger identifier mismatch")
    safe_id(record["policy_id"], "policy_id")
    if set(string_list(record["allowed_decisions"], "allowed_decisions", minimum=5)) != DECISION_TYPES:
        raise HumanReviewLedgerError("policy decision vocabulary mismatch")
    roles = string_list(record["reviewer_roles"], "reviewer_roles", minimum=1)
    if "INDEPENDENT_REVIEWER" not in roles:
        raise HumanReviewLedgerError("policy requires INDEPENDENT_REVIEWER role")
    if set(string_list(record["required_source_kinds"], "required_source_kinds", minimum=7)) != SOURCE_FIELDS:
        raise HumanReviewLedgerError("policy source requirements mismatch")
    duties = exact(
        record["separation_of_duties"],
        {"reviewer_must_differ_from_proposer", "reviewer_must_differ_from_implementer"},
        "policy.separation_of_duties",
    )
    if duties["reviewer_must_differ_from_proposer"] is not True or duties["reviewer_must_differ_from_implementer"] is not True:
        raise HumanReviewLedgerError("policy separation-of-duties boundary widened")
    expiry = exact(
        record["expiry_rules"],
        {"approve_requires_expiry", "explicit_expire_record_supported", "stale_source_invalidates_current_approval"},
        "policy.expiry_rules",
    )
    if any(value is not True for value in expiry.values()):
        raise HumanReviewLedgerError("policy expiry boundary widened")
    authority = exact(record["authority"], NON_AUTHORITY_FIELDS, "policy.authority")
    if authority != {
        "approval_status": "EVIDENCE_ONLY",
        "application_status": "NOT_APPLIED",
        "skill_mutation_authorized": False,
        "adjacent_repository_write_authorized": False,
        "merge_authorized": False,
        "external_action_authorized": False,
    }:
        raise HumanReviewLedgerError("policy authority boundary widened")
    digest(record["policy_fingerprint"], "policy_fingerprint")
    if record["policy_fingerprint"] != sha256_value(fingerprint_material(record, "policy_fingerprint")):
        raise HumanReviewLedgerError("policy fingerprint mismatch")
    return record


def validate_scope(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "scope_id",
            "ledger_id",
            "allowed_roles",
            "identity_source_required",
            "cryptographic_identity_proof",
            "scope_fingerprint",
        },
        "reviewer scope",
    )
    reject_private_content(record)
    if record["schema_version"] != SCOPE_SCHEMA or record["ledger_id"] != LEDGER_ID:
        raise HumanReviewLedgerError("reviewer scope schema or ledger identifier mismatch")
    safe_id(record["scope_id"], "scope_id")
    roles = string_list(record["allowed_roles"], "allowed_roles", minimum=1)
    if "INDEPENDENT_REVIEWER" not in roles:
        raise HumanReviewLedgerError("reviewer scope excludes independent review")
    if record["identity_source_required"] is not True:
        raise HumanReviewLedgerError("reviewer identity source must be required")
    if record["cryptographic_identity_proof"] is not False:
        raise HumanReviewLedgerError("repository-local v1 cannot claim cryptographic identity proof")
    digest(record["scope_fingerprint"], "scope_fingerprint")
    if record["scope_fingerprint"] != sha256_value(fingerprint_material(record, "scope_fingerprint")):
        raise HumanReviewLedgerError("reviewer scope fingerprint mismatch")
    return record


def validate_decision(
    record: dict[str, Any],
    *,
    policy: dict[str, Any],
    scope: dict[str, Any],
    allow_test_only: bool = False,
) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "decision_id",
            "ledger_id",
            "sequence",
            "previous_decision_fingerprint",
            "decision_type",
            "authored_by",
            "separation_of_duties",
            "reviewed_at",
            "expires_at",
            "rationale",
            "conditions",
            "source_fingerprints",
            "supersedes_decision_fingerprint",
            "authority",
            "test_only",
            "decision_fingerprint",
        },
        "decision",
    )
    reject_private_content(record)
    if record["schema_version"] != DECISION_SCHEMA or record["ledger_id"] != LEDGER_ID:
        raise HumanReviewLedgerError("decision schema or ledger identifier mismatch")
    safe_id(record["decision_id"], "decision_id")
    sequence = integer(record["sequence"], "sequence", minimum=1)
    previous = record["previous_decision_fingerprint"]
    if sequence == 1:
        if previous is not None:
            raise HumanReviewLedgerError("first decision must not reference a previous decision")
    else:
        digest(previous, "previous_decision_fingerprint")
    decision_type = record["decision_type"]
    if decision_type not in DECISION_TYPES or decision_type not in policy["allowed_decisions"]:
        raise HumanReviewLedgerError("invalid decision_type")

    author = exact(record["authored_by"], {"type", "identity", "identity_source", "role"}, "authored_by")
    if author["type"] != "HUMAN":
        raise HumanReviewLedgerError("decision must be explicitly human-authored")
    identity = safe_id(author["identity"], "authored_by.identity")
    text(author["identity_source"], "authored_by.identity_source", 256)
    if author["role"] not in scope["allowed_roles"] or author["role"] not in policy["reviewer_roles"]:
        raise HumanReviewLedgerError("reviewer role is outside the governed scope")

    duties = exact(
        record["separation_of_duties"],
        {
            "proposer_identity",
            "implementer_identity",
            "reviewer_differs_from_proposer",
            "reviewer_differs_from_implementer",
        },
        "separation_of_duties",
    )
    proposer = safe_id(duties["proposer_identity"], "proposer_identity")
    implementer = safe_id(duties["implementer_identity"], "implementer_identity")
    if duties["reviewer_differs_from_proposer"] is not True or identity == proposer:
        raise HumanReviewLedgerError("reviewer must differ from proposer")
    if duties["reviewer_differs_from_implementer"] is not True or identity == implementer:
        raise HumanReviewLedgerError("reviewer must differ from implementer")

    reviewed_at = optional_time(record["reviewed_at"], "reviewed_at")
    if reviewed_at is None:
        raise HumanReviewLedgerError("reviewed_at is required")
    expires_at = optional_time(record["expires_at"], "expires_at")
    if decision_type == "APPROVE":
        if expires_at is None or expires_at <= reviewed_at:
            raise HumanReviewLedgerError("APPROVE requires a later expires_at")
    text(record["rationale"], "rationale", 1024)
    string_list(record["conditions"], "conditions")

    sources = exact(record["source_fingerprints"], SOURCE_FIELDS, "source_fingerprints")
    for key, value in sources.items():
        digest(value, f"source_fingerprints.{key}")
    if sources["policy"] != policy["policy_fingerprint"]:
        raise HumanReviewLedgerError("decision policy fingerprint mismatch")
    if sources["reviewer_scope"] != scope["scope_fingerprint"]:
        raise HumanReviewLedgerError("decision reviewer-scope fingerprint mismatch")

    supersedes = record["supersedes_decision_fingerprint"]
    if decision_type in {"EXPIRE", "SUPERSEDE"}:
        digest(supersedes, "supersedes_decision_fingerprint")
        if sequence == 1 or supersedes != previous:
            raise HumanReviewLedgerError(f"{decision_type} must target the immediately prior decision")
    elif supersedes is not None:
        raise HumanReviewLedgerError("only EXPIRE or SUPERSEDE may set supersedes_decision_fingerprint")

    authority = exact(record["authority"], NON_AUTHORITY_FIELDS, "decision.authority")
    expected_approval = "APPROVED" if decision_type == "APPROVE" else "NOT_APPROVED"
    if authority != {
        "approval_status": expected_approval,
        "application_status": "NOT_APPLIED",
        "skill_mutation_authorized": False,
        "adjacent_repository_write_authorized": False,
        "merge_authorized": False,
        "external_action_authorized": False,
    }:
        raise HumanReviewLedgerError("decision authority boundary widened")
    test_only = boolean(record["test_only"], "test_only")
    if test_only and not allow_test_only:
        raise HumanReviewLedgerError("TEST_ONLY decision is forbidden in committed ledger state")
    digest(record["decision_fingerprint"], "decision_fingerprint")
    if record["decision_fingerprint"] != sha256_value(fingerprint_material(record, "decision_fingerprint")):
        raise HumanReviewLedgerError("decision fingerprint mismatch")
    return record


def validate_manifest(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "ledger_id",
            "record_count",
            "records",
            "head_fingerprint",
            "manifest_fingerprint",
        },
        "ledger manifest",
    )
    reject_private_content(record)
    if record["schema_version"] != MANIFEST_SCHEMA or record["ledger_id"] != LEDGER_ID:
        raise HumanReviewLedgerError("manifest schema or ledger identifier mismatch")
    count = integer(record["record_count"], "record_count")
    rows = record["records"]
    if not isinstance(rows, list) or len(rows) != count:
        raise HumanReviewLedgerError("manifest record_count mismatch")
    sequences: list[int] = []
    paths: list[str] = []
    fingerprints: list[str] = []
    for index, row in enumerate(rows):
        row = exact(
            row,
            {"sequence", "path", "file_sha256", "decision_id", "decision_fingerprint"},
            f"manifest.records[{index}]",
        )
        sequences.append(integer(row["sequence"], f"manifest.records[{index}].sequence", minimum=1))
        paths.append(require_relative_path(row["path"], f"manifest.records[{index}].path", "human_review_ledger/ledger/decisions/"))
        digest(row["file_sha256"], f"manifest.records[{index}].file_sha256")
        safe_id(row["decision_id"], f"manifest.records[{index}].decision_id")
        fingerprints.append(digest(row["decision_fingerprint"], f"manifest.records[{index}].decision_fingerprint"))
    if sequences != list(range(1, count + 1)):
        raise HumanReviewLedgerError("manifest sequence is not contiguous")
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise HumanReviewLedgerError("manifest decision paths must be sorted and unique")
    if len(fingerprints) != len(set(fingerprints)):
        raise HumanReviewLedgerError("manifest contains duplicate decision fingerprints")
    expected_head = fingerprints[-1] if fingerprints else None
    if record["head_fingerprint"] != expected_head:
        raise HumanReviewLedgerError("manifest head fingerprint mismatch")
    digest(record["manifest_fingerprint"], "manifest_fingerprint")
    if record["manifest_fingerprint"] != sha256_value(fingerprint_material(record, "manifest_fingerprint")):
        raise HumanReviewLedgerError("manifest fingerprint mismatch")
    return record


def validate_summary(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "ledger_id",
            "state",
            "record_count",
            "current_decision_id",
            "current_decision_type",
            "current_decision_fingerprint",
            "current_sequence",
            "approval_status",
            "application_status",
            "stale",
            "expired",
            "policy_fingerprint",
            "reviewer_scope_fingerprint",
            "summary_fingerprint",
        },
        "ledger summary",
    )
    reject_private_content(record)
    if record["schema_version"] != SUMMARY_SCHEMA or record["ledger_id"] != LEDGER_ID:
        raise HumanReviewLedgerError("summary schema or ledger identifier mismatch")
    count = integer(record["record_count"], "summary.record_count")
    sequence = integer(record["current_sequence"], "summary.current_sequence")
    for field in ("stale", "expired"):
        boolean(record[field], f"summary.{field}")
    digest(record["policy_fingerprint"], "summary.policy_fingerprint")
    digest(record["reviewer_scope_fingerprint"], "summary.reviewer_scope_fingerprint")
    if record["application_status"] != "NOT_APPLIED":
        raise HumanReviewLedgerError("summary application authority widened")
    if count == 0:
        if record["state"] != "NO_DECISIONS" or sequence != 0:
            raise HumanReviewLedgerError("empty ledger summary mismatch")
        if any(record[field] is not None for field in ("current_decision_id", "current_decision_type", "current_decision_fingerprint")):
            raise HumanReviewLedgerError("empty ledger must not claim a current decision")
        if record["approval_status"] != "NOT_APPROVED" or record["stale"] or record["expired"]:
            raise HumanReviewLedgerError("empty ledger authority mismatch")
    else:
        safe_id(record["current_decision_id"], "summary.current_decision_id")
        if record["current_decision_type"] not in DECISION_TYPES:
            raise HumanReviewLedgerError("summary current_decision_type mismatch")
        digest(record["current_decision_fingerprint"], "summary.current_decision_fingerprint")
        if sequence != count:
            raise HumanReviewLedgerError("summary sequence does not match record_count")
        expected_state = "STALE_DECISION" if record["stale"] else "EXPIRED_DECISION" if record["expired"] else "CURRENT_DECISION"
        if record["state"] != expected_state:
            raise HumanReviewLedgerError("summary state mismatch")
        if record["approval_status"] not in {"APPROVED", "NOT_APPROVED"}:
            raise HumanReviewLedgerError("summary approval status mismatch")
        if (record["stale"] or record["expired"]) and record["approval_status"] != "NOT_APPROVED":
            raise HumanReviewLedgerError("stale or expired decision cannot remain approved")
    digest(record["summary_fingerprint"], "summary_fingerprint")
    if record["summary_fingerprint"] != sha256_value(fingerprint_material(record, "summary_fingerprint")):
        raise HumanReviewLedgerError("summary fingerprint mismatch")
    return record
