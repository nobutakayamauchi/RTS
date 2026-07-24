from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

BUNDLE_SCHEMA_VERSION = "RTS-OUTCOME-BUNDLE-V1"
EVIDENCE_SCHEMA_VERSION = "RTS-OUTCOME-EVIDENCE-SOURCE-V1"
EXECUTION_SCOPE = "SIMULATED_ONLY"
PROMOTION_ELIGIBILITY = "NOT_ELIGIBLE"
SCENARIOS = {"SUCCESS", "ESCALATION", "RECOVERY"}
CLASSIFICATIONS = {"VERIFIED", "UNVERIFIED", "ASSUMED"}
TERMINAL_STATES = {"SUCCEEDED", "FAILED", "STOPPED", "ESCALATED"}
USAGE_FIELDS = {"attempts", "elapsed_seconds", "changed_files", "changed_bytes", "events"}
EXECUTION_RECORD_FIELDS = {"skill_id", "drive_id", "pack_id", "trigger", "result", "timestamp"}
EVIDENCE_REF_FIELDS = {"evidence_id", "source_type", "source_ref", "retrieved_at"}
CONTROLLER_FIELDS = {
    "plan_fingerprint",
    "authorization_fingerprint",
    "terminal_state",
    "budget_usage",
    "external_execution_performed",
}
CRITERIA_FIELDS = {"success", "failure", "observed"}
BUNDLE_FIELDS = {
    "schema_version",
    "bundle_id",
    "scenario",
    "execution_scope",
    "outcome_classification",
    "classification_rationale",
    "execution_record",
    "evidence_refs",
    "evidence_integrity",
    "controller",
    "criteria",
    "promotion_eligibility",
    "promotion_blockers",
    "bundle_fingerprint",
}
EVIDENCE_FIELDS = {
    "schema_version",
    "evidence_id",
    "scenario",
    "plan_id",
    "authorization_id",
    "plan_fingerprint",
    "authorization_fingerprint",
    "terminal_state",
    "usage",
    "verification",
    "external_execution_performed",
    "timestamp",
    "summary",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FORBIDDEN_PRIVATE_SEGMENTS = {
    "prompt",
    "prompts",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "password",
    "passwords",
    "api",
    "token",
    "tokens",
    "customer",
    "private",
    "payload",
    "provider",
    "tool",
}


class OutcomeEvidenceError(RuntimeError):
    """Raised when an outcome bundle or corpus fails closed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise OutcomeEvidenceError(f"missing evidence file: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OutcomeEvidenceError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise OutcomeEvidenceError(f"invalid JSON: {path}: {exc}") from exc


def expect_exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OutcomeEvidenceError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise OutcomeEvidenceError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise OutcomeEvidenceError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def expect_nonempty_string(value: Any, label: str, *, max_length: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OutcomeEvidenceError(f"{label} must be a non-empty string")
    if len(value) > max_length:
        raise OutcomeEvidenceError(f"{label} exceeds {max_length} characters")
    if any(char in value for char in ("\x00", "\r")):
        raise OutcomeEvidenceError(f"{label} contains unsafe control characters")
    return value


def expect_safe_id(value: Any, label: str) -> str:
    value = expect_nonempty_string(value, label, max_length=128)
    if not SAFE_ID.fullmatch(value):
        raise OutcomeEvidenceError(f"{label} contains unsafe characters")
    return value


def expect_digest(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise OutcomeEvidenceError(f"{label} must be a lowercase SHA-256 digest")
    return value


def expect_timestamp(value: Any, label: str) -> str:
    value = expect_nonempty_string(value, label)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OutcomeEvidenceError(f"{label} must be an ISO-8601 timestamp") from exc
    return value


def expect_sorted_unique_strings(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise OutcomeEvidenceError(f"{label} must be an array of non-empty strings")
    if not allow_empty and not value:
        raise OutcomeEvidenceError(f"{label} must not be empty")
    if value != sorted(set(value)):
        raise OutcomeEvidenceError(f"{label} must be uniquely sorted")
    for index, entry in enumerate(value):
        expect_nonempty_string(entry, f"{label}[{index}]")
    return value


def reject_private_keys(value: Any, *, path: str = "document") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
            segments = set(normalized.split("_"))
            if segments & FORBIDDEN_PRIVATE_SEGMENTS:
                raise OutcomeEvidenceError(f"{path} contains a forbidden private field: {key}")
            reject_private_keys(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_keys(child, path=f"{path}[{index}]")


def validate_usage(value: Any, label: str) -> dict[str, int]:
    value = expect_exact_object(value, USAGE_FIELDS, label)
    result: dict[str, int] = {}
    for field in sorted(USAGE_FIELDS):
        number = value[field]
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise OutcomeEvidenceError(f"{label}.{field} must be a non-negative integer")
        result[field] = number
    return result


def validate_execution_record(value: Any, scenario: str) -> dict[str, Any]:
    value = expect_exact_object(value, EXECUTION_RECORD_FIELDS, "execution_record")
    for field in ("skill_id", "drive_id", "pack_id", "trigger"):
        expect_nonempty_string(value[field], f"execution_record.{field}")
    expect_timestamp(value["timestamp"], "execution_record.timestamp")
    result = expect_exact_object(
        value["result"],
        {"scenario", "summary", "verification"},
        "execution_record.result",
    )
    if result["scenario"] != scenario:
        raise OutcomeEvidenceError("execution_record.result scenario mismatch")
    if result["verification"] != EXECUTION_SCOPE:
        raise OutcomeEvidenceError("execution_record.result must remain SIMULATED_ONLY")
    expect_nonempty_string(result["summary"], "execution_record.result.summary")
    reject_private_keys(value, path="execution_record")
    return value


def validate_evidence_ref(value: Any, label: str) -> dict[str, Any]:
    value = expect_exact_object(value, EVIDENCE_REF_FIELDS, label)
    expect_safe_id(value["evidence_id"], f"{label}.evidence_id")
    expect_nonempty_string(value["source_type"], f"{label}.source_type")
    source_ref = expect_nonempty_string(value["source_ref"], f"{label}.source_ref")
    path = Path(source_ref)
    if path.is_absolute() or ".." in path.parts:
        raise OutcomeEvidenceError(f"{label}.source_ref must be repository-relative")
    if not source_ref.startswith("outcome_evidence/evidence/"):
        raise OutcomeEvidenceError(f"{label}.source_ref must stay inside outcome_evidence/evidence")
    expect_timestamp(value["retrieved_at"], f"{label}.retrieved_at")
    return value


def validate_criteria(value: Any) -> dict[str, list[str]]:
    value = expect_exact_object(value, CRITERIA_FIELDS, "criteria")
    for field in sorted(CRITERIA_FIELDS):
        expect_sorted_unique_strings(value[field], f"criteria.{field}")
    return value


def bundle_material(bundle: dict[str, Any]) -> dict[str, Any]:
    material = dict(bundle)
    material.pop("bundle_fingerprint", None)
    return material


def validate_bundle(value: Any) -> dict[str, Any]:
    value = expect_exact_object(value, BUNDLE_FIELDS, "outcome bundle")
    if value["schema_version"] != BUNDLE_SCHEMA_VERSION:
        raise OutcomeEvidenceError("outcome bundle schema_version mismatch")
    expect_safe_id(value["bundle_id"], "outcome bundle.bundle_id")
    scenario = value["scenario"]
    if scenario not in SCENARIOS:
        raise OutcomeEvidenceError(f"unsupported outcome scenario: {scenario!r}")
    if value["execution_scope"] != EXECUTION_SCOPE:
        raise OutcomeEvidenceError("outcome bundle execution_scope must be SIMULATED_ONLY")
    classification = value["outcome_classification"]
    if classification not in CLASSIFICATIONS:
        raise OutcomeEvidenceError(f"unsupported outcome classification: {classification!r}")
    expect_nonempty_string(value["classification_rationale"], "classification_rationale")

    validate_execution_record(value["execution_record"], scenario)

    refs = value["evidence_refs"]
    if not isinstance(refs, list) or not refs:
        raise OutcomeEvidenceError("evidence_refs must be a non-empty array")
    evidence_ids: list[str] = []
    previous = ""
    for index, ref in enumerate(refs):
        validate_evidence_ref(ref, f"evidence_refs[{index}]")
        evidence_id = ref["evidence_id"]
        if evidence_id <= previous:
            raise OutcomeEvidenceError("evidence_refs must be uniquely sorted by evidence_id")
        previous = evidence_id
        evidence_ids.append(evidence_id)

    integrity = value["evidence_integrity"]
    if not isinstance(integrity, dict) or sorted(integrity) != evidence_ids:
        raise OutcomeEvidenceError("evidence_integrity keys must exactly match evidence_refs")
    for evidence_id, digest in integrity.items():
        expect_digest(digest, f"evidence_integrity.{evidence_id}")

    controller = expect_exact_object(value["controller"], CONTROLLER_FIELDS, "controller")
    expect_digest(controller["plan_fingerprint"], "controller.plan_fingerprint")
    expect_digest(controller["authorization_fingerprint"], "controller.authorization_fingerprint")
    if controller["terminal_state"] not in TERMINAL_STATES:
        raise OutcomeEvidenceError("controller.terminal_state must be terminal")
    validate_usage(controller["budget_usage"], "controller.budget_usage")
    if controller["external_execution_performed"] is not False:
        raise OutcomeEvidenceError("external execution claims are forbidden")

    validate_criteria(value["criteria"])
    if value["promotion_eligibility"] != PROMOTION_ELIGIBILITY:
        raise OutcomeEvidenceError("simulated bundles are never promotion eligible")
    expect_sorted_unique_strings(value["promotion_blockers"], "promotion_blockers")

    expected = {
        "SUCCESS": ("SUCCEEDED", "UNVERIFIED"),
        "ESCALATION": ("ESCALATED", "VERIFIED"),
        "RECOVERY": ("STOPPED", "ASSUMED"),
    }[scenario]
    if controller["terminal_state"] != expected[0]:
        raise OutcomeEvidenceError(f"{scenario} terminal state must be {expected[0]}")
    if classification != expected[1]:
        raise OutcomeEvidenceError(f"{scenario} classification must be {expected[1]}")
    if scenario == "SUCCESS" and classification == "VERIFIED":
        raise OutcomeEvidenceError("SIMULATED_ONLY success cannot be VERIFIED")

    supplied = expect_digest(value["bundle_fingerprint"], "bundle_fingerprint")
    if supplied != sha256_value(bundle_material(value)):
        raise OutcomeEvidenceError("outcome bundle fingerprint mismatch")
    reject_private_keys(value, path="outcome bundle")
    return value


def validate_evidence_source(value: Any) -> dict[str, Any]:
    value = expect_exact_object(value, EVIDENCE_FIELDS, "evidence source")
    if value["schema_version"] != EVIDENCE_SCHEMA_VERSION:
        raise OutcomeEvidenceError("evidence source schema_version mismatch")
    expect_safe_id(value["evidence_id"], "evidence source.evidence_id")
    if value["scenario"] not in SCENARIOS:
        raise OutcomeEvidenceError("evidence source scenario mismatch")
    expect_digest(value["plan_id"], "evidence source.plan_id")
    expect_safe_id(value["authorization_id"], "evidence source.authorization_id")
    expect_digest(value["plan_fingerprint"], "evidence source.plan_fingerprint")
    expect_digest(value["authorization_fingerprint"], "evidence source.authorization_fingerprint")
    if value["terminal_state"] not in TERMINAL_STATES:
        raise OutcomeEvidenceError("evidence source terminal_state must be terminal")
    validate_usage(value["usage"], "evidence source.usage")
    if value["verification"] != EXECUTION_SCOPE:
        raise OutcomeEvidenceError("evidence source must remain SIMULATED_ONLY")
    if value["external_execution_performed"] is not False:
        raise OutcomeEvidenceError("evidence source external execution claim is forbidden")
    expect_timestamp(value["timestamp"], "evidence source.timestamp")
    expect_nonempty_string(value["summary"], "evidence source.summary")
    reject_private_keys(value, path="evidence source")
    return value
