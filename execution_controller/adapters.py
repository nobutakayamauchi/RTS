from __future__ import annotations

from typing import Any

from .models import ControllerError, expect_exact_object, expect_nonempty_string

SCRIPT_FIELDS = {"kind", "summary", "retryable", "usage", "result", "timestamp"}
USAGE_DELTA_FIELDS = {"elapsed_seconds", "changed_files", "changed_bytes"}


def validate_script_response(value: Any) -> dict[str, Any]:
    value = expect_exact_object(value, SCRIPT_FIELDS, "dry-run script")
    if value["kind"] not in {"success", "failure", "stop"}:
        raise ControllerError("dry-run script.kind must be success, failure, or stop")
    expect_nonempty_string(value["summary"], "dry-run script.summary")
    if not isinstance(value["retryable"], bool):
        raise ControllerError("dry-run script.retryable must be boolean")
    usage = expect_exact_object(value["usage"], USAGE_DELTA_FIELDS, "dry-run script.usage")
    for field, number in usage.items():
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise ControllerError(f"dry-run script.usage.{field} must be a non-negative integer")
    if not isinstance(value["result"], dict):
        raise ControllerError("dry-run script.result must be an object")
    if any(key.lower() in {"prompt", "secret", "credential", "customer_data", "private_payload"} for key in value["result"]):
        raise ControllerError("dry-run script.result contains a forbidden private field")
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
            "result": dict(script["result"]),
            "timestamp": script["timestamp"],
            "verification": "SIMULATED_ONLY",
        }


def get_adapter(adapter_id: str) -> DryRunAdapter:
    if adapter_id != DryRunAdapter.adapter_id:
        raise ControllerError(f"unsupported adapter: {adapter_id}")
    return DryRunAdapter()
