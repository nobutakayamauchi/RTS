from __future__ import annotations

import copy
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
}
SOURCE_ROW_FIELDS = {"path", "sha256"}


def run_material(record: dict[str, Any]) -> dict[str, Any]:
    material = copy.deepcopy(record)
    material.pop("run_id", None)
    material.pop("run_fingerprint", None)
    return material


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
        path = row["path"]
        digest = row["sha256"]
        if not isinstance(path, str) or not path:
            raise GovernedLoopError("source fingerprint path is required")
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts:
            raise GovernedLoopError(f"unsafe source fingerprint path: {path}")
        if not isinstance(digest, str) or len(digest) != 64:
            raise GovernedLoopError(f"invalid source fingerprint digest: {path}")
        paths.append(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise GovernedLoopError("source_fingerprints must be sorted and unique")

    components = exact_object(record["components"], COMPONENT_FIELDS, field="components")
    asset = exact_object(
        components["asset_manifest"],
        {"verification", "snapshot_version", "snapshot_path", "snapshot_sha256", "asset_count", "repository_count"},
        field="components.asset_manifest",
    )
    if asset["verification"] != "PASSED":
        raise GovernedLoopError("asset manifest verification did not pass")

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
    if not isinstance(controller["outcome_links"], list) or not controller["outcome_links"]:
        raise GovernedLoopError("execution controller outcome_links are required")

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

    evidence = exact_object(record["evidence_summary"], EVIDENCE_FIELDS, field="evidence_summary")
    for field in sorted(EVIDENCE_FIELDS):
        values = evidence[field]
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v for v in values):
            raise GovernedLoopError(f"evidence_summary.{field} must be a non-empty string list")

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
