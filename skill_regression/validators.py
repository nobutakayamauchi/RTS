from __future__ import annotations

from pathlib import Path
from typing import Any

from skill_regression.common import (
    DATASET_SCHEMA,
    EXECUTION_SCOPE,
    OUTCOMES,
    PROMOTION,
    RESULT_SCHEMA,
    ROLLBACK_SCHEMA,
    SNAPSHOT_SCHEMA,
    V1_OUTCOMES,
    V1_THRESHOLDS,
    SkillRegressionError,
    digest,
    exact,
    git_sha,
    material,
    reject_private_keys,
    relative,
    safe_id,
    sha256_value,
    strings,
    text,
)

SNAPSHOT_FIELDS = {
    "schema_version", "snapshot_id", "role", "skill_id", "source",
    "content_path", "content_sha256", "contract",
    "external_mutation_performed", "promotion_eligibility",
    "snapshot_fingerprint",
}
SOURCE_FIELDS = {
    "source_type", "repository", "reference_commit_sha", "path",
    "derived_from_snapshot_id", "source_content_sha256",
}
CONTRACT_FIELDS = {"ordered_steps", "expected_outputs", "not_for", "safety_rules"}
ROLLBACK_FIELDS = {
    "schema_version", "rollback_id", "skill_id", "baseline_snapshot_id",
    "baseline_snapshot_fingerprint", "candidate_snapshot_id",
    "restore_content_path", "restore_content_sha256", "trigger_conditions",
    "human_approval_required", "mutation_authorized",
    "adjacent_repository_write_authorized", "rollback_fingerprint",
}
DATASET_FIELDS = {
    "schema_version", "dataset_id", "skill_id", "baseline_snapshot_id",
    "candidate_snapshot_id", "rollback_id", "outcome_bundle_ids",
    "execution_scope", "fixture_set", "thresholds",
    "external_execution_performed", "promotion_eligibility",
    "dataset_fingerprint",
}
FIXTURE_FIELDS = {"fixture_id", "kind", "scenario", "mode", "requirements", "expected"}
REQ_FIELDS = {"steps", "outputs", "safety_rules", "not_for"}
RESULT_FIELDS = {
    "schema_version", "result_id", "dataset_id", "dataset_fingerprint",
    "baseline_snapshot_fingerprint", "candidate_snapshot_fingerprint",
    "rollback_fingerprint", "fixture_results", "summary", "recommendation",
    "promotion_eligibility", "result_fingerprint",
}
ROW_FIELDS = {
    "fixture_id", "baseline", "candidate", "regression", "improvement",
    "safety_failure",
}
SUMMARY_FIELDS = {
    "total_fixtures", "applicable_fixtures", "baseline_passed",
    "candidate_passed", "regressions", "improvements", "safety_failures",
    "candidate_pass_rate",
}


def validate_contract(value: Any, label: str) -> dict[str, Any]:
    value = exact(value, CONTRACT_FIELDS, label)
    strings(value["ordered_steps"], f"{label}.ordered_steps", sorted_unique=False)
    for field in ("expected_outputs", "not_for", "safety_rules"):
        strings(value[field], f"{label}.{field}", sorted_unique=True)
    return value


def validate_snapshot(value: Any) -> dict[str, Any]:
    value = exact(value, SNAPSHOT_FIELDS, "Skill snapshot")
    if value["schema_version"] != SNAPSHOT_SCHEMA:
        raise SkillRegressionError("Skill snapshot schema_version mismatch")
    safe_id(value["snapshot_id"], "Skill snapshot.snapshot_id")
    safe_id(value["skill_id"], "Skill snapshot.skill_id")
    if value["role"] not in {"BASELINE", "CANDIDATE"}:
        raise SkillRegressionError("unsupported Skill snapshot role")

    source = exact(value["source"], SOURCE_FIELDS, "Skill snapshot.source")
    if source["source_type"] not in {"PINNED_PUBLIC_SOURCE", "LOCAL_CANDIDATE_FIXTURE"}:
        raise SkillRegressionError("unsupported Skill source_type")
    repository = text(source["repository"], "Skill snapshot.source.repository")
    if "/" not in repository:
        raise SkillRegressionError("Skill snapshot.source.repository must be owner/name")
    git_sha(source["reference_commit_sha"], "Skill snapshot.source.reference_commit_sha")
    source_path = text(source["path"], "Skill snapshot.source.path")
    if Path(source_path).is_absolute() or ".." in Path(source_path).parts:
        raise SkillRegressionError("Skill snapshot.source.path must be repository-relative")
    digest(source["source_content_sha256"], "Skill snapshot.source.source_content_sha256")

    if value["role"] == "BASELINE":
        if source["source_type"] != "PINNED_PUBLIC_SOURCE" or source["derived_from_snapshot_id"] is not None:
            raise SkillRegressionError("baseline source boundary mismatch")
        if repository != "nobutakayamauchi/RTS-Skills-":
            raise SkillRegressionError("baseline repository mismatch")
    else:
        if source["source_type"] != "LOCAL_CANDIDATE_FIXTURE":
            raise SkillRegressionError("candidate source boundary mismatch")
        safe_id(source["derived_from_snapshot_id"], "Skill snapshot.source.derived_from_snapshot_id")
        if repository != "nobutakayamauchi/RTS":
            raise SkillRegressionError("candidate fixture repository mismatch")

    content_path = relative(
        value["content_path"], "Skill snapshot.content_path",
        "skill_regression/snapshots/",
    )
    digest(value["content_sha256"], "Skill snapshot.content_sha256")
    if source["source_type"] == "LOCAL_CANDIDATE_FIXTURE" and source_path != content_path:
        raise SkillRegressionError("candidate source.path must match content_path")
    if source["source_content_sha256"] != value["content_sha256"]:
        raise SkillRegressionError("source and snapshot content digests must match")
    validate_contract(value["contract"], "Skill snapshot.contract")
    if value["external_mutation_performed"] is not False:
        raise SkillRegressionError("Skill snapshots must not claim external mutation")
    if value["promotion_eligibility"] != PROMOTION:
        raise SkillRegressionError("Skill snapshots are never promotion eligible")
    supplied = digest(value["snapshot_fingerprint"], "Skill snapshot.snapshot_fingerprint")
    if supplied != sha256_value(material(value, "snapshot_fingerprint")):
        raise SkillRegressionError("Skill snapshot fingerprint mismatch")
    reject_private_keys(value, "Skill snapshot")
    return value


def validate_rollback(value: Any) -> dict[str, Any]:
    value = exact(value, ROLLBACK_FIELDS, "rollback snapshot")
    if value["schema_version"] != ROLLBACK_SCHEMA:
        raise SkillRegressionError("rollback snapshot schema_version mismatch")
    for field in ("rollback_id", "skill_id", "baseline_snapshot_id", "candidate_snapshot_id"):
        safe_id(value[field], f"rollback snapshot.{field}")
    digest(value["baseline_snapshot_fingerprint"], "rollback snapshot.baseline_snapshot_fingerprint")
    relative(value["restore_content_path"], "rollback snapshot.restore_content_path", "skill_regression/snapshots/")
    digest(value["restore_content_sha256"], "rollback snapshot.restore_content_sha256")
    strings(value["trigger_conditions"], "rollback snapshot.trigger_conditions", sorted_unique=True)
    if value["human_approval_required"] is not True:
        raise SkillRegressionError("rollback snapshot must require human approval")
    if value["mutation_authorized"] is not False:
        raise SkillRegressionError("rollback snapshot must not authorize mutation")
    if value["adjacent_repository_write_authorized"] is not False:
        raise SkillRegressionError("rollback snapshot must not authorize adjacent-repository writes")
    supplied = digest(value["rollback_fingerprint"], "rollback snapshot.rollback_fingerprint")
    if supplied != sha256_value(material(value, "rollback_fingerprint")):
        raise SkillRegressionError("rollback snapshot fingerprint mismatch")
    reject_private_keys(value, "rollback snapshot")
    return value


def validate_fixture(value: Any, label: str) -> dict[str, Any]:
    value = exact(value, FIXTURE_FIELDS, label)
    safe_id(value["fixture_id"], f"{label}.fixture_id")
    if value["kind"] not in {"FUNCTIONAL", "SAFETY"}:
        raise SkillRegressionError(f"{label}.kind is unsupported")
    safe_id(value["scenario"], f"{label}.scenario")
    if value["mode"] not in {"APPLICABLE", "NOT_APPLICABLE"}:
        raise SkillRegressionError(f"{label}.mode is unsupported")
    req = exact(value["requirements"], REQ_FIELDS, f"{label}.requirements")
    strings(req["steps"], f"{label}.requirements.steps", sorted_unique=False, empty=True)
    for field in ("outputs", "safety_rules", "not_for"):
        strings(req[field], f"{label}.requirements.{field}", sorted_unique=True, empty=True)
    expected = exact(value["expected"], {"baseline", "candidate"}, f"{label}.expected")
    if expected["baseline"] not in OUTCOMES or expected["candidate"] not in OUTCOMES:
        raise SkillRegressionError(f"{label}.expected contains an unsupported outcome")
    if value["mode"] == "NOT_APPLICABLE":
        if not req["not_for"] or req["steps"] or req["outputs"] or req["safety_rules"]:
            raise SkillRegressionError(f"{label} NOT_APPLICABLE requirements mismatch")
        if expected != {"baseline": "NOT_APPLICABLE", "candidate": "NOT_APPLICABLE"}:
            raise SkillRegressionError(f"{label} NOT_APPLICABLE expected outcomes mismatch")
    elif req["not_for"] or not any(req[k] for k in ("steps", "outputs", "safety_rules")):
        raise SkillRegressionError(f"{label} APPLICABLE requirements mismatch")
    return value


def validate_dataset(value: Any) -> dict[str, Any]:
    value = exact(value, DATASET_FIELDS, "regression dataset")
    if value["schema_version"] != DATASET_SCHEMA:
        raise SkillRegressionError("regression dataset schema_version mismatch")
    for field in ("dataset_id", "skill_id", "baseline_snapshot_id", "candidate_snapshot_id", "rollback_id"):
        safe_id(value[field], f"regression dataset.{field}")
    if value["baseline_snapshot_id"] == value["candidate_snapshot_id"]:
        raise SkillRegressionError("baseline and candidate snapshot ids must differ")
    strings(value["outcome_bundle_ids"], "regression dataset.outcome_bundle_ids", sorted_unique=True)
    if value["outcome_bundle_ids"] != V1_OUTCOMES:
        raise SkillRegressionError("regression dataset must reference the immutable v1 outcome corpus")
    if value["execution_scope"] != EXECUTION_SCOPE:
        raise SkillRegressionError("regression dataset execution_scope mismatch")

    fixtures = value["fixture_set"]
    if not isinstance(fixtures, list) or len(fixtures) < 4:
        raise SkillRegressionError("regression dataset requires at least four fixtures")
    previous, kinds, modes = "", set(), set()
    for index, fixture in enumerate(fixtures):
        validate_fixture(fixture, f"fixture_set[{index}]")
        if fixture["fixture_id"] <= previous:
            raise SkillRegressionError("fixture_set must be uniquely sorted by fixture_id")
        previous = fixture["fixture_id"]
        kinds.add(fixture["kind"])
        modes.add(fixture["mode"])
    if kinds != {"FUNCTIONAL", "SAFETY"} or modes != {"APPLICABLE", "NOT_APPLICABLE"}:
        raise SkillRegressionError("fixture_set lacks required variation")

    thresholds = exact(value["thresholds"], set(V1_THRESHOLDS), "dataset.thresholds")
    if thresholds != V1_THRESHOLDS:
        raise SkillRegressionError("dataset thresholds must match the immutable v1 policy")
    if value["external_execution_performed"] is not False:
        raise SkillRegressionError("regression dataset must not claim external execution")
    if value["promotion_eligibility"] != PROMOTION:
        raise SkillRegressionError("regression dataset is never promotion eligible")
    supplied = digest(value["dataset_fingerprint"], "regression dataset.dataset_fingerprint")
    if supplied != sha256_value(material(value, "dataset_fingerprint")):
        raise SkillRegressionError("regression dataset fingerprint mismatch")
    reject_private_keys(value, "regression dataset")
    return value


def validate_result(value: Any) -> dict[str, Any]:
    value = exact(value, RESULT_FIELDS, "regression result")
    if value["schema_version"] != RESULT_SCHEMA:
        raise SkillRegressionError("regression result schema_version mismatch")
    safe_id(value["result_id"], "regression result.result_id")
    safe_id(value["dataset_id"], "regression result.dataset_id")
    for field in (
        "dataset_fingerprint", "baseline_snapshot_fingerprint",
        "candidate_snapshot_fingerprint", "rollback_fingerprint",
    ):
        digest(value[field], f"regression result.{field}")
    rows = value["fixture_results"]
    if not isinstance(rows, list) or not rows:
        raise SkillRegressionError("regression result.fixture_results must be non-empty")
    previous = ""
    for index, row in enumerate(rows):
        exact(row, ROW_FIELDS, f"fixture_results[{index}]")
        safe_id(row["fixture_id"], f"fixture_results[{index}].fixture_id")
        if row["fixture_id"] <= previous:
            raise SkillRegressionError("fixture_results must be uniquely sorted")
        previous = row["fixture_id"]
        if row["baseline"] not in OUTCOMES or row["candidate"] not in OUTCOMES:
            raise SkillRegressionError("fixture result contains unsupported outcome")
        if any(not isinstance(row[f], bool) for f in ("regression", "improvement", "safety_failure")):
            raise SkillRegressionError("fixture result flags must be boolean")
    summary = exact(value["summary"], SUMMARY_FIELDS, "regression result.summary")
    for field in SUMMARY_FIELDS - {"candidate_pass_rate"}:
        if isinstance(summary[field], bool) or not isinstance(summary[field], int) or summary[field] < 0:
            raise SkillRegressionError(f"regression result.summary.{field} is invalid")
    rate = summary["candidate_pass_rate"]
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0 <= float(rate) <= 1:
        raise SkillRegressionError("regression result.summary.candidate_pass_rate is invalid")
    if value["recommendation"] not in {"RESEARCH_READY", "REJECT_CANDIDATE"}:
        raise SkillRegressionError("regression result recommendation mismatch")
    if value["promotion_eligibility"] != PROMOTION:
        raise SkillRegressionError("regression result is never promotion eligible")
    supplied = digest(value["result_fingerprint"], "regression result.result_fingerprint")
    if supplied != sha256_value(material(value, "result_fingerprint")):
        raise SkillRegressionError("regression result fingerprint mismatch")
    reject_private_keys(value, "regression result")
    return value
