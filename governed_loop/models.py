from __future__ import annotations

import copy
import string
from pathlib import PurePosixPath
from typing import Any

from .common import (
    GovernedLoopError,
    exact_object,
    reject_private_content,
    sha256_value,
)

SCHEMA_VERSION = "RTS-GOVERNED-LOOP-RUN-V1"
MODE = "ONE_SHOT_READ_ONLY"
STATUS = "RECONSTRUCTED"
VERIFICATION_ORDER = [
    "asset_manifest",
    "read_only_loop",
    "execution_controller",
    "outcome_evidence",
    "skill_regression",
    "learning_proposals",
    "human_review_ledger",
]
ROOT_FIELDS = {
    "schema_version",
    "run_id",
    "run_fingerprint",
    "mode",
    "status",
    "as_of",
    "verification_order",
    "source_fingerprints",
    "components",
    "evidence_summary",
    "authority",
}
AUTHORITY_FIELDS = {
    "read_only",
    "external_execution_performed",
    "scheduler_authorized",
    "provider_authorized",
    "adjacent_repository_write_authorized",
    "skill_mutation_authorized",
    "approval_status",
    "application_status",
    "automatic_rollback_authorized",
}
EVIDENCE_FIELDS = {
    "confirmed_facts",
    "assumptions",
    "unverified_claims",
    "risks",
}
COMPONENT_FIELDS = {
    "asset_manifest",
    "read_only_loop",
    "execution_controller",
    "outcome_evidence",
    "skill_regression",
    "learning_proposal",
    "human_review_ledger",
}
SOURCE_ROW_FIELDS = {"path", "sha256"}
OUTCOME_LINK_FIELDS = {
    "bundle_id",
    "bundle_fingerprint",
    "plan_fingerprint",
    "authorization_fingerprint",
    "terminal_state",
    "execution_scope",
    "outcome_classification",
}
CLASSIFICATIONS = {"VERIFIED", "UNVERIFIED", "ASSUMED"}


def run_material(record: dict[str, Any]) -> dict[str, Any]:
    material = copy.deepcopy(record)
    material.pop("run_id", None)
    material.pop("run_fingerprint", None)
    return material


def _sha256(value: Any, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in string.hexdigits.lower() for character in value)
        or value != value.lower()
    ):
        raise GovernedLoopError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _integer(value: Any, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise GovernedLoopError(f"{field} must be an integer >= {minimum}")
    return value


def _safe_relative_path(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise GovernedLoopError(f"{field} is required")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        raise GovernedLoopError(f"unsafe {field}: {value}")
    return value


def _string_list(value: Any, *, field: str, non_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (non_empty and not value):
        raise GovernedLoopError(f"{field} must be a string list")
    if any(not isinstance(entry, str) or not entry for entry in value):
        raise GovernedLoopError(f"{field} must contain non-empty strings")
    return value


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    record = exact_object(record, ROOT_FIELDS, field="loop run")
    reject_private_content(record)
    if record["schema_version"] != SCHEMA_VERSION:
        raise GovernedLoopError("loop run schema_version mismatch")
    if record["mode"] != MODE or record["status"] != STATUS:
        raise GovernedLoopError("loop run mode/status boundary widened")
    if not isinstance(record["as_of"], str) or not record["as_of"]:
        raise GovernedLoopError("loop run as_of is required")
    if record["verification_order"] != VERIFICATION_ORDER:
        raise GovernedLoopError("component verification order mismatch")

    rows = record["source_fingerprints"]
    if not isinstance(rows, list) or not rows:
        raise GovernedLoopError("source_fingerprints must be a non-empty list")
    paths: list[str] = []
    for index, row in enumerate(rows):
        row = exact_object(row, SOURCE_ROW_FIELDS, field=f"source_fingerprints[{index}]")
        path = _safe_relative_path(
            row["path"], field=f"source_fingerprints[{index}].path"
        )
        _sha256(row["sha256"], field=f"source_fingerprints[{index}].sha256")
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise GovernedLoopError("source_fingerprints must be sorted and unique")

    components = exact_object(record["components"], COMPONENT_FIELDS, field="components")
    asset = exact_object(
        components["asset_manifest"],
        {
            "verification",
            "snapshot_version",
            "snapshot_path",
            "snapshot_sha256",
            "asset_count",
            "repository_count",
        },
        field="components.asset_manifest",
    )
    if asset["verification"] != "PASSED":
        raise GovernedLoopError("asset manifest verification did not pass")
    _integer(asset["snapshot_version"], field="asset snapshot_version", minimum=1)
    _safe_relative_path(asset["snapshot_path"], field="asset snapshot_path")
    _sha256(asset["snapshot_sha256"], field="asset snapshot_sha256")
    _integer(asset["asset_count"], field="asset_count", minimum=1)
    _integer(asset["repository_count"], field="repository_count", minimum=1)

    loop = exact_object(
        components["read_only_loop"],
        {
            "verification",
            "evaluation_id",
            "authority",
            "state",
            "audit_level",
            "wip_count",
            "active_item_ids",
            "recommendation_action",
            "recommendation_item_id",
        },
        field="components.read_only_loop",
    )
    if loop["verification"] != "PASSED" or loop["authority"] != "ADVISORY_ONLY":
        raise GovernedLoopError("read-only loop authority boundary widened")
    _sha256(loop["evaluation_id"], field="read-only evaluation_id")
    active_ids = _string_list(
        loop["active_item_ids"], field="read-only active_item_ids", non_empty=False
    )
    if active_ids != sorted(active_ids) or len(active_ids) != len(set(active_ids)):
        raise GovernedLoopError("active_item_ids must be sorted and unique")
    wip_count = _integer(loop["wip_count"], field="read-only wip_count")
    if wip_count != len(active_ids):
        raise GovernedLoopError("read-only wip_count does not match active_item_ids")
    if not isinstance(loop["state"], str) or not loop["state"]:
        raise GovernedLoopError("read-only state is required")
    if not isinstance(loop["audit_level"], str) or not loop["audit_level"]:
        raise GovernedLoopError("read-only audit_level is required")
    if not isinstance(loop["recommendation_action"], str) or not loop["recommendation_action"]:
        raise GovernedLoopError("read-only recommendation_action is required")
    recommendation_item = loop["recommendation_item_id"]
    if recommendation_item is not None and (
        not isinstance(recommendation_item, str) or not recommendation_item
    ):
        raise GovernedLoopError("invalid read-only recommendation_item_id")
    if wip_count == 1 and recommendation_item not in active_ids:
        raise GovernedLoopError("active recommendation item must match the sole WIP item")

    controller = exact_object(
        components["execution_controller"],
        {"verification", "execution_scope", "external_execution_performed", "outcome_links"},
        field="components.execution_controller",
    )
    if (
        controller["verification"] != "PASSED"
        or controller["execution_scope"] != "LOCAL_DRY_RUN_ONLY"
        or controller["external_execution_performed"] is not False
    ):
        raise GovernedLoopError("execution controller boundary widened")
    links = controller["outcome_links"]
    if not isinstance(links, list) or not links:
        raise GovernedLoopError("execution controller outcome_links are required")
    link_ids: list[str] = []
    link_fingerprints: list[str] = []
    for index, link in enumerate(links):
        link = exact_object(
            link, OUTCOME_LINK_FIELDS, field=f"execution_controller.outcome_links[{index}]"
        )
        for field in ("bundle_id", "terminal_state"):
            if not isinstance(link[field], str) or not link[field]:
                raise GovernedLoopError(f"outcome link {field} is required")
        for field in (
            "bundle_fingerprint",
            "plan_fingerprint",
            "authorization_fingerprint",
        ):
            _sha256(link[field], field=f"outcome link {field}")
        if link["execution_scope"] != "SIMULATED_ONLY":
            raise GovernedLoopError("controller outcome execution scope widened")
        if link["outcome_classification"] not in CLASSIFICATIONS:
            raise GovernedLoopError("invalid controller outcome classification")
        link_ids.append(link["bundle_id"])
        link_fingerprints.append(link["bundle_fingerprint"])
    if link_ids != sorted(link_ids) or len(link_ids) != len(set(link_ids)):
        raise GovernedLoopError("controller outcome links must be sorted and unique")

    outcome = exact_object(
        components["outcome_evidence"],
        {
            "verification",
            "bundle_count",
            "bundle_ids",
            "bundle_fingerprints",
            "classifications",
            "execution_scope",
            "promotion_eligibility",
        },
        field="components.outcome_evidence",
    )
    if (
        outcome["verification"] != "PASSED"
        or outcome["execution_scope"] != "SIMULATED_ONLY"
        or outcome["promotion_eligibility"] != "NOT_ELIGIBLE"
    ):
        raise GovernedLoopError("outcome evidence boundary widened")
    bundle_count = _integer(outcome["bundle_count"], field="outcome bundle_count", minimum=3)
    bundle_ids = _string_list(outcome["bundle_ids"], field="outcome bundle_ids")
    bundle_fingerprints = _string_list(
        outcome["bundle_fingerprints"], field="outcome bundle_fingerprints"
    )
    for digest in bundle_fingerprints:
        _sha256(digest, field="outcome bundle fingerprint")
    classifications = _string_list(
        outcome["classifications"], field="outcome classifications"
    )
    if any(value not in CLASSIFICATIONS for value in classifications):
        raise GovernedLoopError("invalid outcome classification")
    if bundle_count != len(bundle_ids) or bundle_count != len(bundle_fingerprints):
        raise GovernedLoopError("outcome bundle_count does not match bundle arrays")
    if bundle_ids != link_ids or bundle_fingerprints != link_fingerprints:
        raise GovernedLoopError("controller and outcome bundle linkage mismatch")

    regression = exact_object(
        components["skill_regression"],
        {
            "verification",
            "dataset_id",
            "result_fingerprint",
            "recommendation",
            "promotion_eligibility",
            "regressions",
            "improvements",
            "safety_failures",
            "candidate_pass_rate",
        },
        field="components.skill_regression",
    )
    if (
        regression["verification"] != "PASSED"
        or regression["recommendation"] != "RESEARCH_READY"
        or regression["promotion_eligibility"] != "NOT_ELIGIBLE"
    ):
        raise GovernedLoopError("skill regression boundary widened")
    if not isinstance(regression["dataset_id"], str) or not regression["dataset_id"]:
        raise GovernedLoopError("regression dataset_id is required")
    _sha256(regression["result_fingerprint"], field="regression result_fingerprint")
    if _integer(regression["regressions"], field="regressions") != 0:
        raise GovernedLoopError("regression count widened")
    _integer(regression["improvements"], field="improvements")
    if _integer(regression["safety_failures"], field="safety_failures") != 0:
        raise GovernedLoopError("safety failure count widened")
    pass_rate = regression["candidate_pass_rate"]
    if isinstance(pass_rate, bool) or not isinstance(pass_rate, (int, float)) or not 0 <= pass_rate <= 1:
        raise GovernedLoopError("candidate_pass_rate must be between 0 and 1")

    proposal = exact_object(
        components["learning_proposal"],
        {
            "verification",
            "proposal_id",
            "proposal_fingerprint",
            "proposal_status",
            "review_status",
            "recommendation",
            "approval_status",
            "application_status",
        },
        field="components.learning_proposal",
    )
    if (
        proposal["verification"] != "PASSED"
        or proposal["proposal_status"] != "REVIEW_REQUIRED"
        or proposal["review_status"] != "PENDING"
        or proposal["recommendation"] != "REQUEST_HUMAN_REVIEW"
        or proposal["approval_status"] != "NOT_APPROVED"
        or proposal["application_status"] != "NOT_APPLIED"
    ):
        raise GovernedLoopError("learning proposal boundary widened")
    if not isinstance(proposal["proposal_id"], str) or not proposal["proposal_id"]:
        raise GovernedLoopError("proposal_id is required")
    _sha256(proposal["proposal_fingerprint"], field="proposal_fingerprint")

    ledger = exact_object(
        components["human_review_ledger"],
        {
            "verification",
            "ledger_id",
            "record_count",
            "state",
            "current_decision_id",
            "current_decision_type",
            "current_decision_fingerprint",
            "approval_status",
            "application_status",
            "stale",
            "expired",
            "policy_fingerprint",
            "reviewer_scope_fingerprint",
            "manifest_fingerprint",
            "summary_fingerprint",
        },
        field="components.human_review_ledger",
    )
    if ledger["verification"] != "PASSED":
        raise GovernedLoopError("human review ledger verification did not pass")
    if ledger["ledger_id"] != "RTS-HUMAN-REVIEW-LEDGER-000001":
        raise GovernedLoopError("human review ledger identifier mismatch")
    record_count = _integer(ledger["record_count"], field="human review record_count")
    if ledger["application_status"] != "NOT_APPLIED":
        raise GovernedLoopError("human review ledger application authority widened")
    for field in ("stale", "expired"):
        if not isinstance(ledger[field], bool):
            raise GovernedLoopError(f"human review ledger {field} must be boolean")
    for field in (
        "policy_fingerprint",
        "reviewer_scope_fingerprint",
        "manifest_fingerprint",
        "summary_fingerprint",
    ):
        _sha256(ledger[field], field=f"human review ledger {field}")
    if record_count == 0:
        if (
            ledger["state"] != "NO_DECISIONS"
            or ledger["current_decision_id"] is not None
            or ledger["current_decision_type"] is not None
            or ledger["current_decision_fingerprint"] is not None
            or ledger["approval_status"] != "NOT_APPROVED"
            or ledger["stale"] is not False
            or ledger["expired"] is not False
        ):
            raise GovernedLoopError("empty human review ledger boundary widened")
    else:
        if not isinstance(ledger["current_decision_id"], str) or not ledger["current_decision_id"]:
            raise GovernedLoopError("human review current_decision_id is required")
        if ledger["current_decision_type"] not in {
            "APPROVE", "REJECT", "RETURN_FOR_REVISION", "EXPIRE", "SUPERSEDE"
        }:
            raise GovernedLoopError("human review current_decision_type mismatch")
        _sha256(
            ledger["current_decision_fingerprint"],
            field="human review current_decision_fingerprint",
        )
        if ledger["approval_status"] not in {"APPROVED", "NOT_APPROVED"}:
            raise GovernedLoopError("human review approval status mismatch")
        if (ledger["stale"] or ledger["expired"]) and ledger["approval_status"] != "NOT_APPROVED":
            raise GovernedLoopError("stale or expired human review evidence remained approved")

    evidence = exact_object(record["evidence_summary"], EVIDENCE_FIELDS, field="evidence_summary")
    for field in sorted(EVIDENCE_FIELDS):
        _string_list(evidence[field], field=f"evidence_summary.{field}")

    authority = exact_object(record["authority"], AUTHORITY_FIELDS, field="authority")
    expected_authority = {
        "read_only": True,
        "external_execution_performed": False,
        "scheduler_authorized": False,
        "provider_authorized": False,
        "adjacent_repository_write_authorized": False,
        "skill_mutation_authorized": False,
        "approval_status": "NOT_APPROVED",
        "application_status": "NOT_APPLIED",
        "automatic_rollback_authorized": False,
    }
    if authority != expected_authority:
        raise GovernedLoopError("loop run authority boundary widened")

    expected = sha256_value(run_material(record))
    if record["run_fingerprint"] != expected:
        raise GovernedLoopError("loop run fingerprint mismatch")
    expected_id = f"RTS-LOOP-RUN-{expected[:16].upper()}"
    if record["run_id"] != expected_id:
        raise GovernedLoopError("loop run identifier mismatch")
    return record
