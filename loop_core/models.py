from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "RTS-LOOP-EVALUATION-V1"
AUTHORITY = "ADVISORY_ONLY"
STATES = {"NORMAL", "FOCUS", "OVERLOAD", "STALL", "BLOCKED"}
AUDIT_LEVELS = {"NORMAL", "WARNING", "RISK", "CRITICAL"}
ACTIVE_STATUSES = {"SELECTED", "IN_PROGRESS"}


class LoopCoreError(RuntimeError):
    """Raised when governed inputs or evaluation output are invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise LoopCoreError(f"missing input: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LoopCoreError(f"missing input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LoopCoreError(f"invalid JSON: {path}: {exc}") from exc


def _expect_exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LoopCoreError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise LoopCoreError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise LoopCoreError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
        raise LoopCoreError(f"{label} must be an array of strings")
    return value


def validate_optional_records(
    value: Any,
    required_fields: set[str],
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise LoopCoreError(f"{label} must be a JSON array")
    records: list[dict[str, Any]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise LoopCoreError(f"{label}[{index}] must be an object")
        missing = sorted(required_fields - record.keys())
        if missing:
            raise LoopCoreError(f"{label}[{index}] missing fields: {', '.join(missing)}")
        records.append(record)
    return records


def validate_evaluation(payload: Any) -> dict[str, Any]:
    top_fields = {
        "schema_version",
        "evaluation_id",
        "as_of",
        "authority",
        "implementation_authority_granted",
        "inputs",
        "wip",
        "state",
        "audit_level",
        "evidence",
        "recommendation",
    }
    payload = _expect_exact_object(payload, top_fields, "evaluation")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise LoopCoreError("evaluation schema_version mismatch")
    evaluation_id = payload["evaluation_id"]
    if (
        not isinstance(evaluation_id, str)
        or len(evaluation_id) != 64
        or any(char not in "0123456789abcdef" for char in evaluation_id)
    ):
        raise LoopCoreError("evaluation_id must be a lowercase SHA-256 digest")
    if not isinstance(payload["as_of"], str) or not payload["as_of"]:
        raise LoopCoreError("as_of must be a non-empty string")
    if payload["authority"] != AUTHORITY:
        raise LoopCoreError("authority must be ADVISORY_ONLY")
    if payload["implementation_authority_granted"] is not False:
        raise LoopCoreError("implementation_authority_granted must be false")

    if not isinstance(payload["inputs"], list) or not payload["inputs"]:
        raise LoopCoreError("inputs must be a non-empty array")
    input_paths: list[str] = []
    for index, row in enumerate(payload["inputs"]):
        row = _expect_exact_object(row, {"path", "sha256"}, f"inputs[{index}]")
        if not isinstance(row["path"], str) or not row["path"]:
            raise LoopCoreError(f"inputs[{index}].path must be a non-empty string")
        digest = row["sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise LoopCoreError(
                f"inputs[{index}].sha256 must be a lowercase SHA-256 digest"
            )
        input_paths.append(row["path"])
    if input_paths != sorted(input_paths) or len(input_paths) != len(set(input_paths)):
        raise LoopCoreError("inputs must be uniquely sorted by path")

    wip = _expect_exact_object(payload["wip"], {"count", "active_item_ids"}, "wip")
    if not isinstance(wip["count"], int) or wip["count"] < 0:
        raise LoopCoreError("wip.count must be a non-negative integer")
    active_ids = _string_list(wip["active_item_ids"], "wip.active_item_ids")
    if active_ids != sorted(active_ids) or wip["count"] != len(active_ids):
        raise LoopCoreError("wip count/list mismatch")

    if payload["state"] not in STATES:
        raise LoopCoreError("invalid state")
    if payload["audit_level"] not in AUDIT_LEVELS:
        raise LoopCoreError("invalid audit_level")

    evidence = _expect_exact_object(
        payload["evidence"],
        {"verified", "unverified", "assumed"},
        "evidence",
    )
    for key in ("verified", "unverified", "assumed"):
        _string_list(evidence[key], f"evidence.{key}")

    recommendation = _expect_exact_object(
        payload["recommendation"],
        {
            "action",
            "item_id",
            "why",
            "success_condition",
            "fallback",
            "stop_conditions",
        },
        "recommendation",
    )
    for key in ("action", "why", "success_condition", "fallback"):
        if not isinstance(recommendation[key], str) or not recommendation[key]:
            raise LoopCoreError(f"recommendation.{key} must be a non-empty string")
    if recommendation["item_id"] is not None and not isinstance(
        recommendation["item_id"], str
    ):
        raise LoopCoreError("recommendation.item_id must be string or null")
    _string_list(recommendation["stop_conditions"], "recommendation.stop_conditions")
    return payload
