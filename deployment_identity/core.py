from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_FIELDS = (
    "service_unit",
    "working_directory",
    "executable_or_module",
    "active_route_surface",
    "deployed_revision",
    "deployed_artifact_digest",
    "runtime_config_fingerprint",
    "runtime_environment_fingerprint",
    "source_tree_state",
    "observer_id",
    "observation_session_id",
    "observed_at",
)

EXPECTED_FIELDS = (
    "source_revision",
    "artifact_digest",
    "config_fingerprint",
    "environment_fingerprint",
)

INSTANCE_FIELDS = (
    "instance_id",
    "revision",
    "artifact_digest",
    "config_fingerprint",
    "environment_fingerprint",
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


def fingerprint_expectation(expectation: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(dict(expectation)).encode("utf-8")).hexdigest()


def _require_non_empty_string(value: Mapping[str, Any], field: str) -> str:
    field_value = value.get(field)
    if not isinstance(field_value, str) or not field_value.strip():
        raise DeploymentIdentityError(f"missing or invalid required field: {field}")
    if field_value != field_value.strip():
        raise DeploymentIdentityError(f"surrounding whitespace is not allowed: {field}")
    return field_value


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


def _validate_instances(observation: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    raw = observation.get("runtime_instances")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or not raw:
        raise DeploymentIdentityError("runtime_instances must be a non-empty array")

    seen: set[str] = set()
    instances: list[dict[str, str]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise DeploymentIdentityError(f"runtime_instances[{index}] must be an object")
        normalized = {field: _require_non_empty_string(item, field) for field in INSTANCE_FIELDS}
        instance_id = normalized["instance_id"]
        if instance_id in seen:
            raise DeploymentIdentityError(f"duplicate runtime instance id: {instance_id}")
        seen.add(instance_id)
        instances.append(normalized)
    return tuple(instances)


def _validate_route_instance_ids(observation: Mapping[str, Any], known_ids: set[str]) -> tuple[str, ...]:
    raw = observation.get("active_route_instance_ids")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or not raw:
        raise DeploymentIdentityError("active_route_instance_ids must be a non-empty array")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, str) or not item or item != item.strip():
            raise DeploymentIdentityError(f"active_route_instance_ids[{index}] must be an exact non-empty string")
        if item in seen:
            raise DeploymentIdentityError(f"duplicate active route instance id: {item}")
        if item not in known_ids:
            raise DeploymentIdentityError(f"active route references unknown runtime instance: {item}")
        seen.add(item)
        result.append(item)
    return tuple(result)


def _not_established(reason: str, observation: Mapping[str, Any], **details: Any) -> dict[str, Any]:
    return {
        "status": NOT_ESTABLISHED,
        "reason": reason,
        "runtime_classification_authorized": False,
        "material_match_verified": False,
        "observation_fingerprint": fingerprint_observation(observation),
        **details,
    }


def establish_deployment_identity(
    observation: Mapping[str, Any],
    *,
    expected_deployment: Mapping[str, Any],
    trusted_observer_ids: Iterable[str],
    reference_time: str,
    max_age_seconds: int = 300,
) -> dict[str, Any]:
    """Validate runtime material against an external expectation.

    This lower-level v4 material proof is deliberately non-authorizing. Matching
    revision, artifact, config, environment and routed instances are necessary
    but not sufficient for runtime classification. A separate signed attestation
    quorum must elevate the proof to authorization.
    """
    if not isinstance(observation, Mapping):
        raise DeploymentIdentityError("observation must be an object")
    if not isinstance(expected_deployment, Mapping):
        raise DeploymentIdentityError("expected_deployment must be an object")
    if not isinstance(max_age_seconds, int) or max_age_seconds < 0:
        raise DeploymentIdentityError("max_age_seconds must be a non-negative integer")

    values = {field: _require_non_empty_string(observation, field) for field in REQUIRED_FIELDS}
    expected = {field: _require_non_empty_string(expected_deployment, field) for field in EXPECTED_FIELDS}
    observed_at = _parse_timestamp(values["observed_at"])
    reference = _parse_timestamp(reference_time, "reference_time")
    trusted = _trusted_observers(trusted_observer_ids)

    instances = _validate_instances(observation)
    instance_by_id = {item["instance_id"]: item for item in instances}
    route_ids = _validate_route_instance_ids(observation, set(instance_by_id))

    if values["observer_id"] not in trusted:
        return _not_established("UNTRUSTED_OBSERVER", observation, observer_id=values["observer_id"])

    age = (reference - observed_at).total_seconds()
    if age < 0 or age > max_age_seconds:
        return _not_established(
            "STALE_OR_FUTURE_OBSERVATION",
            observation,
            age_seconds=age,
            max_age_seconds=max_age_seconds,
        )

    if values["source_tree_state"] != "CLEAN":
        return _not_established("SOURCE_TREE_NOT_CLEAN", observation, source_tree_state=values["source_tree_state"])

    material_pairs = (
        ("deployed_revision", values["deployed_revision"], expected["source_revision"], "DEPLOYED_REVISION_MISMATCH"),
        ("deployed_artifact_digest", values["deployed_artifact_digest"], expected["artifact_digest"], "ARTIFACT_DIGEST_MISMATCH"),
        ("runtime_config_fingerprint", values["runtime_config_fingerprint"], expected["config_fingerprint"], "CONFIG_FINGERPRINT_MISMATCH"),
        ("runtime_environment_fingerprint", values["runtime_environment_fingerprint"], expected["environment_fingerprint"], "ENVIRONMENT_FINGERPRINT_MISMATCH"),
    )
    for field, actual, wanted, reason in material_pairs:
        if actual != wanted:
            return _not_established(reason, observation, field=field, expected=wanted, observed=actual)

    for instance_id in route_ids:
        instance = instance_by_id[instance_id]
        checks = (
            ("revision", expected["source_revision"], "ROUTE_INSTANCE_REVISION_MISMATCH"),
            ("artifact_digest", expected["artifact_digest"], "ROUTE_INSTANCE_ARTIFACT_MISMATCH"),
            ("config_fingerprint", expected["config_fingerprint"], "ROUTE_INSTANCE_CONFIG_MISMATCH"),
            ("environment_fingerprint", expected["environment_fingerprint"], "ROUTE_INSTANCE_ENVIRONMENT_MISMATCH"),
        )
        for field, wanted, reason in checks:
            if instance[field] != wanted:
                return _not_established(
                    reason,
                    observation,
                    instance_id=instance_id,
                    field=field,
                    expected=wanted,
                    observed=instance[field],
                )

    fingerprint = fingerprint_observation(observation)
    expectation_fp = fingerprint_expectation(expected_deployment)
    return {
        "status": ESTABLISHED,
        "reason": "RUNTIME_MATERIAL_MATCH_ATTESTATION_REQUIRED",
        "runtime_classification_authorized": False,
        "material_match_verified": True,
        "identity": {
            "service_unit": values["service_unit"],
            "working_directory": values["working_directory"],
            "executable_or_module": values["executable_or_module"],
            "active_route_surface": values["active_route_surface"],
            "revision": values["deployed_revision"],
            "artifact_digest": values["deployed_artifact_digest"],
            "config_fingerprint": values["runtime_config_fingerprint"],
            "environment_fingerprint": values["runtime_environment_fingerprint"],
            "source_tree_state": values["source_tree_state"],
            "active_route_instance_ids": list(route_ids),
            "observer_id": values["observer_id"],
            "observation_session_id": values["observation_session_id"],
            "observed_at": values["observed_at"],
        },
        "observation_fingerprint": fingerprint,
        "expectation_fingerprint": expectation_fp,
    }


def bind_runtime_observation(
    deployment_proof: Mapping[str, Any],
    runtime_observation: Mapping[str, Any],
    *,
    max_skew_seconds: int = 30,
) -> dict[str, Any]:
    """Bind a runtime observation only to a fully authorized deployment proof."""
    if not isinstance(deployment_proof, Mapping) or not isinstance(runtime_observation, Mapping):
        raise DeploymentIdentityError("deployment proof and runtime observation must be objects")
    if deployment_proof.get("status") != ESTABLISHED or not deployment_proof.get("runtime_classification_authorized"):
        return {"status": NOT_BOUND, "reason": "DEPLOYMENT_IDENTITY_NOT_FULLY_AUTHORIZED", "runtime_classification_authorized": False}
    if not isinstance(max_skew_seconds, int) or max_skew_seconds < 0:
        raise DeploymentIdentityError("max_skew_seconds must be a non-negative integer")

    expected_fp = deployment_proof.get("observation_fingerprint")
    expected_expectation_fp = deployment_proof.get("expectation_fingerprint")
    supplied_fp = _require_non_empty_string(runtime_observation, "deployment_identity_fingerprint")
    supplied_expectation_fp = _require_non_empty_string(runtime_observation, "deployment_expectation_fingerprint")
    supplied_session = _require_non_empty_string(runtime_observation, "observation_session_id")
    runtime_at_value = _require_non_empty_string(runtime_observation, "observed_at")
    if supplied_fp != expected_fp:
        return {"status": NOT_BOUND, "reason": "DEPLOYMENT_FINGERPRINT_MISMATCH", "runtime_classification_authorized": False}
    if supplied_expectation_fp != expected_expectation_fp:
        return {"status": NOT_BOUND, "reason": "DEPLOYMENT_EXPECTATION_FINGERPRINT_MISMATCH", "runtime_classification_authorized": False}

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
        "deployment_expectation_fingerprint": expected_expectation_fp,
        "runtime_observation_fingerprint": fingerprint_observation(runtime_observation),
        "observation_session_id": supplied_session,
    }
