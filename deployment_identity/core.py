from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


REQUIRED_FIELDS = (
    "service_unit",
    "working_directory",
    "executable_or_module",
    "active_route_surface",
    "deployed_revision",
    "source_revision",
    "observer_id",
    "observation_session_id",
    "observed_at",
)

ESTABLISHED = "DEPLOYMENT_IDENTITY_ESTABLISHED"
NOT_ESTABLISHED = "DEPLOYMENT_IDENTITY_NOT_ESTABLISHED"
BOUND = "RUNTIME_OBSERVATION_BOUND"
NOT_BOUND = "RUNTIME_OBSERVATION_NOT_BOUND"


class DeploymentIdentityError(ValueError):
    """Raised when deployment evidence cannot establish runtime identity."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint_observation(observation: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(dict(observation)).encode("utf-8")).hexdigest()


def _require_non_empty_string(observation: Mapping[str, Any], field: str) -> str:
    value = observation.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DeploymentIdentityError(f"missing or invalid required field: {field}")
    if value != value.strip():
        raise DeploymentIdentityError(f"surrounding whitespace is not allowed: {field}")
    return value


def _parse_timestamp(value: str, field: str = "observed_at") -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DeploymentIdentityError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise DeploymentIdentityError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _trusted_observers(values: Iterable[str]) -> frozenset[str]:
    trusted = frozenset(values)
    if not trusted or any(not isinstance(v, str) or not v or v != v.strip() for v in trusted):
        raise DeploymentIdentityError("trusted_observer_ids must contain exact non-empty ids")
    return trusted


def establish_deployment_identity(
    observation: Mapping[str, Any],
    *,
    trusted_observer_ids: Iterable[str],
    reference_time: str,
    max_age_seconds: int = 300,
) -> dict[str, Any]:
    """Fail-closed deployment identity establishment.

    v2 deliberately requires an external trust anchor (trusted_observer_ids) and
    freshness reference. The observation cannot make itself trusted merely by
    naming an observer. This is still an attestation boundary, not cryptographic
    proof of host truth; privileged collection remains separately governed.
    """
    if not isinstance(observation, Mapping):
        raise DeploymentIdentityError("observation must be an object")
    if not isinstance(max_age_seconds, int) or max_age_seconds < 0:
        raise DeploymentIdentityError("max_age_seconds must be a non-negative integer")

    values = {field: _require_non_empty_string(observation, field) for field in REQUIRED_FIELDS}
    observed_at = _parse_timestamp(values["observed_at"])
    reference = _parse_timestamp(reference_time, "reference_time")
    trusted = _trusted_observers(trusted_observer_ids)

    if values["observer_id"] not in trusted:
        return {
            "status": NOT_ESTABLISHED,
            "reason": "UNTRUSTED_OBSERVER",
            "runtime_classification_authorized": False,
            "observer_id": values["observer_id"],
            "observation_fingerprint": fingerprint_observation(observation),
        }

    age = (reference - observed_at).total_seconds()
    if age < 0 or age > max_age_seconds:
        return {
            "status": NOT_ESTABLISHED,
            "reason": "STALE_OR_FUTURE_OBSERVATION",
            "runtime_classification_authorized": False,
            "age_seconds": age,
            "max_age_seconds": max_age_seconds,
            "observation_fingerprint": fingerprint_observation(observation),
        }

    if values["deployed_revision"] != values["source_revision"]:
        return {
            "status": NOT_ESTABLISHED,
            "reason": "DEPLOYED_REVISION_MISMATCH",
            "runtime_classification_authorized": False,
            "source_revision": values["source_revision"],
            "deployed_revision": values["deployed_revision"],
            "observation_fingerprint": fingerprint_observation(observation),
        }

    fingerprint = fingerprint_observation(observation)
    return {
        "status": ESTABLISHED,
        "reason": "TRUSTED_FRESH_RUNTIME_IDENTITY_MATCH",
        "runtime_classification_authorized": True,
        "identity": {
            "service_unit": values["service_unit"],
            "working_directory": values["working_directory"],
            "executable_or_module": values["executable_or_module"],
            "active_route_surface": values["active_route_surface"],
            "revision": values["deployed_revision"],
            "observer_id": values["observer_id"],
            "observation_session_id": values["observation_session_id"],
            "observed_at": values["observed_at"],
        },
        "observation_fingerprint": fingerprint,
    }


def bind_runtime_observation(
    deployment_proof: Mapping[str, Any],
    runtime_observation: Mapping[str, Any],
    *,
    max_skew_seconds: int = 30,
) -> dict[str, Any]:
    """Bind a runtime observation to an established Deployment Identity proof."""
    if not isinstance(deployment_proof, Mapping) or not isinstance(runtime_observation, Mapping):
        raise DeploymentIdentityError("deployment proof and runtime observation must be objects")
    if deployment_proof.get("status") != ESTABLISHED or not deployment_proof.get("runtime_classification_authorized"):
        return {"status": NOT_BOUND, "reason": "DEPLOYMENT_IDENTITY_NOT_ESTABLISHED", "runtime_classification_authorized": False}
    if not isinstance(max_skew_seconds, int) or max_skew_seconds < 0:
        raise DeploymentIdentityError("max_skew_seconds must be a non-negative integer")

    expected_fp = deployment_proof.get("observation_fingerprint")
    supplied_fp = _require_non_empty_string(runtime_observation, "deployment_identity_fingerprint")
    supplied_session = _require_non_empty_string(runtime_observation, "observation_session_id")
    runtime_at_value = _require_non_empty_string(runtime_observation, "observed_at")
    if supplied_fp != expected_fp:
        return {"status": NOT_BOUND, "reason": "DEPLOYMENT_FINGERPRINT_MISMATCH", "runtime_classification_authorized": False}

    identity = deployment_proof.get("identity")
    if not isinstance(identity, Mapping) or supplied_session != identity.get("observation_session_id"):
        return {"status": NOT_BOUND, "reason": "OBSERVATION_SESSION_MISMATCH", "runtime_classification_authorized": False}

    deployment_at = _parse_timestamp(str(identity.get("observed_at")), "deployment_observed_at")
    runtime_at = _parse_timestamp(runtime_at_value, "runtime_observed_at")
    skew = (runtime_at - deployment_at).total_seconds()
    if skew < 0 or skew > max_skew_seconds:
        return {
            "status": NOT_BOUND,
            "reason": "RUNTIME_OBSERVATION_OUTSIDE_BINDING_WINDOW",
            "runtime_classification_authorized": False,
            "skew_seconds": skew,
            "max_skew_seconds": max_skew_seconds,
        }

    return {
        "status": BOUND,
        "reason": "DEPLOYMENT_PROOF_BOUND_TO_RUNTIME_OBSERVATION",
        "runtime_classification_authorized": True,
        "deployment_identity_fingerprint": expected_fp,
        "runtime_observation_fingerprint": fingerprint_observation(runtime_observation),
        "observation_session_id": supplied_session,
    }
