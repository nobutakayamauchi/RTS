from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any

CONTEXT_SCHEMA = "RTS-ADAPTIVE-GOVERNANCE-CONTEXT-V1"
PLAN_SCHEMA = "RTS-ADAPTIVE-GOVERNANCE-PLAN-V1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
LEVELS = ("G0", "G1", "G2", "G3", "G4")
REPOSITORY_SCOPES = {"LOCAL", "ADJACENT", "EXTERNAL"}
UNCERTAINTY_LEVELS = {"LOW", "MEDIUM", "HIGH"}
CHANGE_KINDS = {"CODE", "CONFIG", "DATA", "DOCUMENTATION", "SCHEMA", "TEST", "WORKFLOW"}
REQUESTED_ACTIONS = {
    "READ",
    "WRITE_LOCAL",
    "WRITE_ADJACENT",
    "NETWORK",
    "EXECUTE",
    "PUBLISH",
    "DEPLOY",
    "MESSAGE",
    "MERGE",
}


class AdaptiveGovernanceError(RuntimeError):
    """Raised when adaptive governance input or output fails closed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def fingerprint_material(record: dict[str, Any], field: str) -> dict[str, Any]:
    material = copy.deepcopy(record)
    material.pop(field, None)
    return material


def exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdaptiveGovernanceError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise AdaptiveGovernanceError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise AdaptiveGovernanceError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def text(value: Any, label: str, limit: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdaptiveGovernanceError(f"{label} must be a non-empty string")
    if len(value) > limit or any(char in value for char in ("\x00", "\r")):
        raise AdaptiveGovernanceError(f"{label} contains unsafe or excessive text")
    return value


def safe_id(value: Any, label: str) -> str:
    value = text(value, label, 128)
    if not SAFE_ID.fullmatch(value):
        raise AdaptiveGovernanceError(f"{label} contains unsafe characters")
    return value


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise AdaptiveGovernanceError(f"{label} must be a boolean")
    return value


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AdaptiveGovernanceError(f"{label} must be an integer >= {minimum}")
    return value


def sorted_unique_strings(value: Any, label: str, allowed: set[str] | None = None) -> list[str]:
    if not isinstance(value, list):
        raise AdaptiveGovernanceError(f"{label} must be an array")
    result = [text(item, f"{label}[]", 256) for item in value]
    if result != sorted(set(result)):
        raise AdaptiveGovernanceError(f"{label} must be sorted and unique")
    if allowed is not None and set(result) - allowed:
        raise AdaptiveGovernanceError(f"{label} contains unsupported values")
    return result


def safe_paths(value: Any, label: str) -> list[str]:
    paths = sorted_unique_strings(value, label)
    for raw in paths:
        path = PurePosixPath(raw)
        if path.is_absolute() or ".." in path.parts or raw.startswith(".git/"):
            raise AdaptiveGovernanceError(f"{label} contains an unsafe path")
    return paths


def validate_context(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "change_id",
            "summary",
            "change_kinds",
            "affected_paths",
            "requested_actions",
            "impact",
            "estimated_implementation_steps",
        },
        "context",
    )
    if record["schema_version"] != CONTEXT_SCHEMA:
        raise AdaptiveGovernanceError("context schema mismatch")
    safe_id(record["change_id"], "change_id")
    text(record["summary"], "summary", 2048)
    sorted_unique_strings(record["change_kinds"], "change_kinds", CHANGE_KINDS)
    safe_paths(record["affected_paths"], "affected_paths")
    sorted_unique_strings(record["requested_actions"], "requested_actions", REQUESTED_ACTIONS)
    impact = exact(
        record["impact"],
        {
            "read_only",
            "repository_scope",
            "reversible",
            "touches_approval_flow",
            "handles_personal_data",
            "handles_sensitive_material",
            "financial_or_contractual",
            "production_effect",
            "external_action",
            "historical_failure",
            "emergency",
            "uncertainty",
        },
        "impact",
    )
    for field in (
        "read_only",
        "reversible",
        "touches_approval_flow",
        "handles_personal_data",
        "handles_sensitive_material",
        "financial_or_contractual",
        "production_effect",
        "external_action",
        "historical_failure",
        "emergency",
    ):
        boolean(impact[field], f"impact.{field}")
    if impact["repository_scope"] not in REPOSITORY_SCOPES:
        raise AdaptiveGovernanceError("impact.repository_scope is unsupported")
    if impact["uncertainty"] not in UNCERTAINTY_LEVELS:
        raise AdaptiveGovernanceError("impact.uncertainty is unsupported")
    integer(record["estimated_implementation_steps"], "estimated_implementation_steps", 1)
    return record


def validate_plan(record: dict[str, Any]) -> dict[str, Any]:
    record = exact(
        record,
        {
            "schema_version",
            "change_id",
            "context_fingerprint",
            "level",
            "classification_reasons",
            "requirements",
            "workflow",
            "prohibitions",
            "governance_cost",
            "authority",
            "plan_fingerprint",
        },
        "plan",
    )
    if record["schema_version"] != PLAN_SCHEMA:
        raise AdaptiveGovernanceError("plan schema mismatch")
    safe_id(record["change_id"], "change_id")
    if not isinstance(record["context_fingerprint"], str) or len(record["context_fingerprint"]) != 64:
        raise AdaptiveGovernanceError("context_fingerprint must be SHA-256")
    if record["level"] not in LEVELS:
        raise AdaptiveGovernanceError("plan level is unsupported")
    sorted_unique_strings(record["classification_reasons"], "classification_reasons")
    requirements = exact(
        record["requirements"],
        {
            "human_approvals",
            "independent_review",
            "preflight",
            "rollback",
            "test_scope",
            "execution_mode",
            "max_pull_requests",
            "max_governance_steps",
        },
        "requirements",
    )
    integer(requirements["human_approvals"], "requirements.human_approvals")
    boolean(requirements["independent_review"], "requirements.independent_review")
    boolean(requirements["preflight"], "requirements.preflight")
    if requirements["rollback"] not in {"NOT_REQUIRED", "REQUIRED", "REQUIRED_AND_TESTED"}:
        raise AdaptiveGovernanceError("requirements.rollback is unsupported")
    if requirements["test_scope"] not in {"DIFF_ONLY", "FOCUSED", "FULL"}:
        raise AdaptiveGovernanceError("requirements.test_scope is unsupported")
    if requirements["execution_mode"] not in {"AUTOMATED", "HUMAN_TRIGGERED", "MANUAL"}:
        raise AdaptiveGovernanceError("requirements.execution_mode is unsupported")
    integer(requirements["max_pull_requests"], "requirements.max_pull_requests", 1)
    integer(requirements["max_governance_steps"], "requirements.max_governance_steps", 1)
    workflow = record["workflow"]
    if not isinstance(workflow, list) or not workflow:
        raise AdaptiveGovernanceError("workflow must be a non-empty array")
    for index, step in enumerate(workflow):
        step = exact(step, {"order", "step_id", "description", "human_gate"}, f"workflow[{index}]")
        if step["order"] != index + 1:
            raise AdaptiveGovernanceError("workflow order must be contiguous")
        safe_id(step["step_id"], f"workflow[{index}].step_id")
        text(step["description"], f"workflow[{index}].description", 512)
        boolean(step["human_gate"], f"workflow[{index}].human_gate")
    sorted_unique_strings(record["prohibitions"], "prohibitions")
    cost = exact(
        record["governance_cost"],
        {"implementation_steps", "governance_steps", "ratio", "status", "warnings"},
        "governance_cost",
    )
    integer(cost["implementation_steps"], "governance_cost.implementation_steps", 1)
    integer(cost["governance_steps"], "governance_cost.governance_steps", 1)
    if not isinstance(cost["ratio"], (int, float)) or isinstance(cost["ratio"], bool) or cost["ratio"] < 0:
        raise AdaptiveGovernanceError("governance_cost.ratio must be non-negative")
    if cost["status"] not in {"BALANCED", "HEAVY", "OVER_GOVERNED"}:
        raise AdaptiveGovernanceError("governance_cost.status is unsupported")
    sorted_unique_strings(cost["warnings"], "governance_cost.warnings")
    authority = exact(
        record["authority"],
        {
            "approval_status",
            "application_status",
            "self_approval_authorized",
            "mutation_authorized",
            "merge_authorized",
            "external_action_authorized",
        },
        "authority",
    )
    expected_authority = {
        "approval_status": "REVIEW_REQUIRED",
        "application_status": "NOT_APPLIED",
        "self_approval_authorized": False,
        "mutation_authorized": False,
        "merge_authorized": False,
        "external_action_authorized": False,
    }
    if authority != expected_authority:
        raise AdaptiveGovernanceError("plan authority boundary widened")
    expected = fingerprint(fingerprint_material(record, "plan_fingerprint"))
    if record["plan_fingerprint"] != expected:
        raise AdaptiveGovernanceError("plan fingerprint mismatch")
    return record
