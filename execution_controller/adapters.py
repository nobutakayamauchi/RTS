from __future__ import annotations

import copy
import re
from typing import Any

from .models import ControllerError, expect_exact_object, expect_nonempty_string

SCRIPT_FIELDS = {"kind", "summary", "retryable", "usage", "result", "timestamp"}
USAGE_DELTA_FIELDS = {"elapsed_seconds", "changed_files", "changed_bytes"}
FORBIDDEN_PRIVATE_KEYS = {
    "prompt",
    "prompts",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "password",
    "passwords",
    "api_key",
    "api_keys",
    "token",
    "tokens",
    "customer_data",
    "private_payload",
    "provider_raw_payload",
    "tool_argument",
    "tool_arguments",
    "tool_args",
}
FORBIDDEN_PRIVATE_SEGMENTS = {
    "prompt",
    "prompts",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "password",
    "passwords",
    "token",
    "tokens",
}
FORBIDDEN_SUMMARY_PATTERN = re.compile(
    r"(?:prompt|secret|credential|password|api\s*key|token|customer\s+data|"
    r"private\s+payload|provider\s+raw\s+payload|tool\s+arguments?)\s*[:=]",
    re.IGNORECASE,
)
MAX_SUMMARY_LENGTH = 512


def _normalized_key(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _reject_private_fields(value: Any, *, path: str = "result") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalized_key(key)
            collapsed = normalized.replace("_", "")
            segments = set(normalized.split("_"))
            forbidden_collapsed = {entry.replace("_", "") for entry in FORBIDDEN_PRIVATE_KEYS}
            if (
                normalized in FORBIDDEN_PRIVATE_KEYS
                or collapsed in forbidden_collapsed
                or segments & FORBIDDEN_PRIVATE_SEGMENTS
            ):
                raise ControllerError(
                    f"dry-run script.result contains a forbidden private field: {path}.{key}"
                )
            _reject_private_fields(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_private_fields(child, path=f"{path}[{index}]")


def _validate_safe_summary(value: Any) -> str:
    summary = expect_nonempty_string(value, "dry-run script.summary")
    if len(summary) > MAX_SUMMARY_LENGTH:
        raise ControllerError(
            f"dry-run script.summary must be at most {MAX_SUMMARY_LENGTH} characters"
        )
    if any(character in summary for character in ("\n", "\r", "\x00")):
        raise ControllerError("dry-run script.summary must be a single safe line")
    if FORBIDDEN_SUMMARY_PATTERN.search(summary):
        raise ControllerError("dry-run script.summary contains a forbidden private marker")
    return summary


def validate_script_response(value: Any) -> dict[str, Any]:
    value = expect_exact_object(value, SCRIPT_FIELDS, "dry-run script")
    if value["kind"] not in {"success", "failure", "stop"}:
        raise ControllerError("dry-run script.kind must be success, failure, or stop")
    _validate_safe_summary(value["summary"])
    if not isinstance(value["retryable"], bool):
        raise ControllerError("dry-run script.retryable must be boolean")
    usage = expect_exact_object(value["usage"], USAGE_DELTA_FIELDS, "dry-run script.usage")
    for field, number in usage.items():
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ControllerError(f"dry-run script.usage.{field} must be a non-negative integer")
    if not isinstance(value["result"], dict):
        raise ControllerError("dry-run script.result must be an object")
    _reject_private_fields(value["result"])
    expect_nonempty_string(value["timestamp"], "dry-run script.timestamp")
    if value["kind"] != "failure" and value["retryable"]:
        raise ControllerError("retryable=true is valid only for failure")
    return value


class DryRunAdapter:
    adapter_id = "dry-run"

    def execute(self, script: dict[str, Any]) -> dict[str, Any]:
        script = validate_script_response(script)
        return {
            "kind": script["kind"],
            "summary": script["summary"],
            "retryable": script["retryable"],
            "usage": dict(script["usage"]),
            "result": copy.deepcopy(script["result"]),
            "timestamp": script["timestamp"],
            "verification": "SIMULATED_ONLY",
        }


def get_adapter(adapter_id: str) -> DryRunAdapter:
    if adapter_id != DryRunAdapter.adapter_id:
        raise ControllerError(f"unsupported adapter: {adapter_id}")
    return DryRunAdapter()
