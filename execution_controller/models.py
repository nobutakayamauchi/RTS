from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "RTS-EXECUTION-CONTROLLER-V1"
PLAN_SCHEMA_VERSION = "RTS-EXECUTION-PLAN-V1"
EVENT_SCHEMA_VERSION = "RTS-EXECUTION-EVENT-V1"
CHECKPOINT_SCHEMA_VERSION = "RTS-EXECUTION-CHECKPOINT-V1"
AUTHORITY = "DRY_RUN_APPROVED"
ALLOWED_CAPABILITIES = {"LOCAL_CHECKPOINT_WRITE"}
ALLOWED_ADAPTERS = {"dry-run"}
BUDGET_FIELDS = {
    "max_attempts",
    "max_elapsed_seconds",
    "max_changed_files",
    "max_changed_bytes",
    "max_events",
}
USAGE_FIELDS = {
    "attempts",
    "elapsed_seconds",
    "changed_files",
    "changed_bytes",
    "events",
}
TERMINAL_STATES = {"SUCCEEDED", "FAILED", "STOPPED", "ESCALATED"}
STATES = {
    "PLANNED",
    "AUTHORIZED",
    "DISPATCHED",
    "RUNNING",
    "VERIFYING",
    *TERMINAL_STATES,
}
TRANSITIONS = {
    "PLANNED": {"AUTHORIZED", "STOPPED"},
    "AUTHORIZED": {"DISPATCHED", "STOPPED"},
    "DISPATCHED": {"RUNNING", "STOPPED"},
    "RUNNING": {"RUNNING", "VERIFYING", "FAILED", "STOPPED", "ESCALATED"},
    "VERIFYING": {"SUCCEEDED", "FAILED", "STOPPED", "ESCALATED"},
    "SUCCEEDED": set(),
    "FAILED": set(),
    "STOPPED": set(),
    "ESCALATED": set(),
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ControllerError(RuntimeError):
    """Raised when an execution request fails closed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise ControllerError(f"missing governed input: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ControllerError(f"missing JSON input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ControllerError(f"invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(value), encoding="utf-8")


def expect_exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControllerError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise ControllerError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise ControllerError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def expect_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ControllerError(f"{label} must be a non-empty string")
    return value


def expect_digest(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ControllerError(f"{label} must be a lowercase SHA-256 digest")
    return value


def expect_safe_id(value: Any, label: str) -> str:
    value = expect_nonempty_string(value, label)
    if not SAFE_ID.fullmatch(value):
        raise ControllerError(f"{label} contains unsafe characters")
    return value


def zero_usage() -> dict[str, int]:
    return {
        "attempts": 0,
        "elapsed_seconds": 0,
        "changed_files": 0,
        "changed_bytes": 0,
        "events": 0,
    }


def validate_budgets(value: Any) -> dict[str, int]:
    value = expect_exact_object(value, BUDGET_FIELDS, "authorization.budgets")
    result: dict[str, int] = {}
    for field in sorted(BUDGET_FIELDS):
        number = value[field]
        minimum = 1 if field in {"max_attempts", "max_events"} else 0
        if isinstance(number, bool) or not isinstance(number, int) or number < minimum:
            raise ControllerError(f"authorization.budgets.{field} must be an integer >= {minimum}")
        result[field] = number
    return result


def validate_usage(value: Any, label: str = "usage") -> dict[str, int]:
    value = expect_exact_object(value, USAGE_FIELDS, label)
    result: dict[str, int] = {}
    for field in sorted(USAGE_FIELDS):
        number = value[field]
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ControllerError(f"{label}.{field} must be a non-negative integer")
        result[field] = number
    return result


def authorization_material(document: dict[str, Any]) -> dict[str, Any]:
    material = dict(document)
    material.pop("authorization_fingerprint", None)
    return material


def validate_authorization(document: Any) -> dict[str, Any]:
    fields = {
        "authorization_id",
        "item_id",
        "item_version",
        "issued_by",
        "issued_at",
        "as_of",
        "adapter_id",
        "skill_id",
        "drive_id",
        "pack_id",
        "trigger",
        "allowed_capabilities",
        "budgets",
        "stop_conditions",
        "authorization_fingerprint",
    }
    document = expect_exact_object(document, fields, "authorization")
    for field in (
        "authorization_id",
        "item_id",
        "issued_by",
        "issued_at",
        "as_of",
        "adapter_id",
        "skill_id",
        "drive_id",
        "pack_id",
        "trigger",
    ):
        expect_nonempty_string(document[field], f"authorization.{field}")
    expect_safe_id(document["authorization_id"], "authorization.authorization_id")
    if not document["item_id"].startswith("RTS-FRZ-"):
        raise ControllerError("authorization.item_id must be an RTS-FRZ item")
    if isinstance(document["item_version"], bool) or not isinstance(document["item_version"], int) or document["item_version"] < 1:
        raise ControllerError("authorization.item_version must be a positive integer")
    if document["adapter_id"] not in ALLOWED_ADAPTERS:
        raise ControllerError(f"unsupported adapter: {document['adapter_id']}")
    capabilities = document["allowed_capabilities"]
    if not isinstance(capabilities, list) or any(not isinstance(entry, str) for entry in capabilities):
        raise ControllerError("authorization.allowed_capabilities must be an array of strings")
    if capabilities != sorted(set(capabilities)):
        raise ControllerError("authorization.allowed_capabilities must be uniquely sorted")
    unknown = sorted(set(capabilities) - ALLOWED_CAPABILITIES)
    if unknown:
        raise ControllerError(f"unknown capability: {', '.join(unknown)}")
    if "LOCAL_CHECKPOINT_WRITE" not in capabilities:
        raise ControllerError("LOCAL_CHECKPOINT_WRITE capability is required")
    validate_budgets(document["budgets"])
    stops = document["stop_conditions"]
    if not isinstance(stops, list) or not stops or any(not isinstance(entry, str) or not entry for entry in stops):
        raise ControllerError("authorization.stop_conditions must be a non-empty string array")
    if stops != sorted(set(stops)):
        raise ControllerError("authorization.stop_conditions must be uniquely sorted")
    supplied = expect_digest(document["authorization_fingerprint"], "authorization.authorization_fingerprint")
    expected = sha256_value(authorization_material(document))
    if supplied != expected:
        raise ControllerError("authorization fingerprint mismatch")
    return document


def validate_transition(before: str, after: str) -> None:
    if before not in STATES or after not in STATES:
        raise ControllerError(f"unknown controller state transition: {before} -> {after}")
    if after not in TRANSITIONS[before]:
        raise ControllerError(f"illegal controller state transition: {before} -> {after}")


def validate_plan(plan: Any) -> dict[str, Any]:
    fields = {
        "schema_version",
        "plan_id",
        "authority",
        "external_execution_authorized",
        "item_id",
        "item_version",
        "authorization_id",
        "authorization_fingerprint",
        "adapter_id",
        "execution_identifiers",
        "allowed_capabilities",
        "budgets",
        "stop_conditions",
        "initial_state",
        "inputs",
        "gate_evidence",
    }
    plan = expect_exact_object(plan, fields, "execution plan")
    if plan["schema_version"] != PLAN_SCHEMA_VERSION:
        raise ControllerError("execution plan schema_version mismatch")
    expect_digest(plan["plan_id"], "execution plan.plan_id")
    if plan["authority"] != AUTHORITY or plan["external_execution_authorized"] is not False:
        raise ControllerError("execution plan authority boundary mismatch")
    if plan["initial_state"] != "PLANNED":
        raise ControllerError("execution plan initial_state must be PLANNED")
    validate_budgets(plan["budgets"])
    if plan["allowed_capabilities"] != sorted(set(plan["allowed_capabilities"])):
        raise ControllerError("execution plan capabilities must be uniquely sorted")
    if set(plan["allowed_capabilities"]) - ALLOWED_CAPABILITIES:
        raise ControllerError("execution plan contains unknown capability")
    inputs = plan["inputs"]
    if not isinstance(inputs, list) or not inputs:
        raise ControllerError("execution plan inputs must be non-empty")
    previous = ""
    for index, row in enumerate(inputs):
        row = expect_exact_object(row, {"path", "sha256"}, f"execution plan.inputs[{index}]")
        path = expect_nonempty_string(row["path"], f"execution plan.inputs[{index}].path")
        expect_digest(row["sha256"], f"execution plan.inputs[{index}].sha256")
        if path <= previous:
            raise ControllerError("execution plan inputs must be uniquely sorted")
        previous = path
    material = dict(plan)
    material.pop("plan_id")
    if plan["plan_id"] != sha256_value(material):
        raise ControllerError("execution plan fingerprint mismatch")
    return plan
