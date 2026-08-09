from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Mapping


REQUIRED_FIELDS = (
    "service_unit",
    "working_directory",
    "executable_or_module",
    "active_route_surface",
    "deployed_revision",
    "source_revision",
    "observed_at",
)

ESTABLISHED = "DEPLOYMENT_IDENTITY_ESTABLISHED"
NOT_ESTABLISHED = "DEPLOYMENT_IDENTITY_NOT_ESTABLISHED"


class DeploymentIdentityError(ValueError):
    """Raised when a deployment observation cannot establish runtime identity."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint_observation(observation: Mapping[str, Any]) -> str:
    """Return a deterministic SHA-256 fingerprint for an observation."""
    return hashlib.sha256(_canonical_json(dict(observation)).encode("utf-8")).hexdigest()


def _require_non_empty_string(observation: Mapping[str, Any], field: str) -> str:
    value = observation.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DeploymentIdentityError(f"missing or invalid required field: {field}")
    return value.strip()


def _validate_timestamp(value: str) -> None:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DeploymentIdentityError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise DeploymentIdentityError("observed_at must include a timezone")


def establish_deployment_identity(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and bind runtime identity to the expected source revision.

    This function is deliberately read-only and fail-closed. It never infers
    deployment identity from repository contents. Runtime identity must be
    explicitly observed.
    """
    if not isinstance(observation, Mapping):
        raise DeploymentIdentityError("observation must be an object")

    values = {field: _require_non_empty_string(observation, field) for field in REQUIRED_FIELDS}
    _validate_timestamp(values["observed_at"])

    if values["deployed_revision"] != values["source_revision"]:
        return {
            "status": NOT_ESTABLISHED,
            "reason": "DEPLOYED_REVISION_MISMATCH",
            "runtime_classification_authorized": False,
            "source_revision": values["source_revision"],
            "deployed_revision": values["deployed_revision"],
            "observation_fingerprint": fingerprint_observation(observation),
        }

    return {
        "status": ESTABLISHED,
        "reason": "EXPLICIT_RUNTIME_IDENTITY_MATCH",
        "runtime_classification_authorized": True,
        "identity": {
            "service_unit": values["service_unit"],
            "working_directory": values["working_directory"],
            "executable_or_module": values["executable_or_module"],
            "active_route_surface": values["active_route_surface"],
            "revision": values["deployed_revision"],
            "observed_at": values["observed_at"],
        },
        "observation_fingerprint": fingerprint_observation(observation),
    }
