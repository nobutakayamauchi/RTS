from __future__ import annotations

from typing import Any

from deployment_identity.core import DeploymentIdentityError, validate_snapshot

SCHEMA_VERSION = "RTS-RUNTIME-DEBUG-GATE-V1"


class DebugGateError(RuntimeError):
    """Raised when a runtime debug gate result is invalid."""


def evaluate_debug_gate(
    *,
    observation: dict[str, Any],
    deployment_identity: dict[str, Any] | None,
) -> dict[str, Any]:
    """Gate runtime-to-source classification on established deployment identity.

    Observation shape is intentionally small in v1. The gate does not decide root
    cause; it only decides whether runtime implementation classification may begin.
    """
    if not isinstance(observation, dict):
        raise DebugGateError("observation must be an object")
    if not observation:
        raise DebugGateError("observation must not be empty")

    if deployment_identity is None:
        result = {
            "schema_version": SCHEMA_VERSION,
            "state": "BLOCKED_IDENTITY_MISSING",
            "runtime_classification_allowed": False,
            "runtime_implementation": "UNKNOWN",
            "next_action": "ESTABLISH_DEPLOYMENT_IDENTITY",
            "reason": "No Deployment Identity snapshot was supplied.",
            "observation": observation,
            "deployment_identity_status": "MISSING",
            "invariant": "Deployment Identity MUST be established before runtime implementation classification.",
            "code_existence_is_runtime_evidence": False,
        }
        validate_gate_result(result)
        return result

    try:
        validate_snapshot(deployment_identity)
    except DeploymentIdentityError as exc:
        raise DebugGateError(f"invalid deployment identity snapshot: {exc}") from exc

    identity_status = deployment_identity["status"]
    allowed = deployment_identity["runtime_classification_allowed"] is True

    if not allowed:
        result = {
            "schema_version": SCHEMA_VERSION,
            "state": "BLOCKED_IDENTITY_NOT_ESTABLISHED",
            "runtime_classification_allowed": False,
            "runtime_implementation": "UNKNOWN",
            "next_action": "RESOLVE_DEPLOYMENT_IDENTITY",
            "reason": f"Deployment Identity status is {identity_status}; runtime implementation classification is forbidden.",
            "observation": observation,
            "deployment_identity_status": identity_status,
            "invariant": deployment_identity["invariant"],
            "code_existence_is_runtime_evidence": False,
        }
        validate_gate_result(result)
        return result

    result = {
        "schema_version": SCHEMA_VERSION,
        "state": "READY_FOR_EVIDENCE_CORRELATION",
        "runtime_classification_allowed": True,
        "runtime_implementation": "UNCLASSIFIED",
        "next_action": "CORRELATE_RUNTIME_EVIDENCE_BEFORE_CODE_MAPPING",
        "reason": "Deployment Identity is ESTABLISHED. Runtime evidence may now be correlated to source candidates.",
        "observation": observation,
        "deployment_identity_status": identity_status,
        "invariant": deployment_identity["invariant"],
        "code_existence_is_runtime_evidence": False,
    }
    validate_gate_result(result)
    return result


def validate_gate_result(result: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "state",
        "runtime_classification_allowed",
        "runtime_implementation",
        "next_action",
        "reason",
        "observation",
        "deployment_identity_status",
        "invariant",
        "code_existence_is_runtime_evidence",
    }
    if set(result) != required:
        raise DebugGateError("debug gate fields mismatch")
    if result["schema_version"] != SCHEMA_VERSION:
        raise DebugGateError("unsupported debug gate schema_version")
    if result["code_existence_is_runtime_evidence"] is not False:
        raise DebugGateError("code existence must never be runtime evidence")
    if not isinstance(result["observation"], dict) or not result["observation"]:
        raise DebugGateError("observation must be a non-empty object")

    state = result["state"]
    allowed = result["runtime_classification_allowed"]
    implementation = result["runtime_implementation"]

    if state in {"BLOCKED_IDENTITY_MISSING", "BLOCKED_IDENTITY_NOT_ESTABLISHED"}:
        if allowed is not False or implementation != "UNKNOWN":
            raise DebugGateError("fail-closed identity gate violated")
    elif state == "READY_FOR_EVIDENCE_CORRELATION":
        if allowed is not True or implementation != "UNCLASSIFIED":
            raise DebugGateError("ready-state classification boundary violated")
        if result["deployment_identity_status"] != "ESTABLISHED":
            raise DebugGateError("ready state requires ESTABLISHED deployment identity")
    else:
        raise DebugGateError(f"unsupported debug gate state: {state}")
