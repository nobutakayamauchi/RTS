from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from .core import DeploymentIdentityError, ESTABLISHED, establish_deployment_identity
from .provenance import verify_collector_provenance


class AttestationError(ValueError):
    """Raised when collector attestations cannot establish a trusted quorum."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_timestamp(value: str, field: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AttestationError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise AttestationError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def attestation_material(attestation: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in attestation.items() if key != "signature"}


def compute_hmac_signature(material: Mapping[str, Any], secret: str) -> str:
    if not isinstance(secret, str) or not secret:
        raise AttestationError("attestation secret must be a non-empty string")
    return hmac.new(secret.encode("utf-8"), _canonical_json(dict(material)).encode("utf-8"), hashlib.sha256).hexdigest()


def verify_attestation_quorum(attestations: Sequence[Mapping[str, Any]], *, trusted_keys: Mapping[str, str], observation_fingerprint: str, expectation_fingerprint: str, observation_session_id: str, reference_time: str, max_age_seconds: int = 300, min_attestors: int = 2) -> dict[str, Any]:
    if not isinstance(attestations, Sequence) or isinstance(attestations, (str, bytes)):
        raise AttestationError("attestations must be an array")
    if not isinstance(trusted_keys, Mapping) or not trusted_keys:
        raise AttestationError("trusted_keys must be a non-empty mapping")
    if not isinstance(min_attestors, int) or min_attestors < 2:
        raise AttestationError("min_attestors must be at least 2")
    if not isinstance(max_age_seconds, int) or max_age_seconds < 0:
        raise AttestationError("max_age_seconds must be a non-negative integer")
    reference = _parse_timestamp(reference_time, "reference_time")
    verified: list[str] = []
    seen: set[str] = set()
    for index, attestation in enumerate(attestations):
        if not isinstance(attestation, Mapping):
            raise AttestationError(f"attestations[{index}] must be an object")
        required = ("attestor_id", "observation_fingerprint", "expectation_fingerprint", "observation_session_id", "issued_at", "signature")
        values: dict[str, str] = {}
        for field in required:
            value = attestation.get(field)
            if not isinstance(value, str) or not value or value != value.strip():
                raise AttestationError(f"attestations[{index}].{field} must be an exact non-empty string")
            values[field] = value
        attestor_id = values["attestor_id"]
        if attestor_id in seen:
            raise AttestationError(f"duplicate attestor_id: {attestor_id}")
        seen.add(attestor_id)
        secret = trusted_keys.get(attestor_id)
        if not isinstance(secret, str) or not secret:
            raise AttestationError(f"untrusted attestor_id: {attestor_id}")
        if values["observation_fingerprint"] != observation_fingerprint:
            raise AttestationError(f"attestor {attestor_id} signed a different observation")
        if values["expectation_fingerprint"] != expectation_fingerprint:
            raise AttestationError(f"attestor {attestor_id} signed a different expectation")
        if values["observation_session_id"] != observation_session_id:
            raise AttestationError(f"attestor {attestor_id} signed a different session")
        issued = _parse_timestamp(values["issued_at"], f"attestations[{index}].issued_at")
        age = (reference - issued).total_seconds()
        if age < 0 or age > max_age_seconds:
            raise AttestationError(f"attestor {attestor_id} attestation is stale or future-dated")
        expected_signature = compute_hmac_signature(attestation_material(attestation), secret)
        if not hmac.compare_digest(values["signature"], expected_signature):
            raise AttestationError(f"invalid signature for attestor_id: {attestor_id}")
        verified.append(attestor_id)
    if len(verified) < min_attestors:
        raise AttestationError(f"attestation quorum not met: {len(verified)} < {min_attestors}")
    return {"status": "ATTESTATION_QUORUM_VERIFIED", "verified_attestors": sorted(verified), "attestor_count": len(verified), "min_attestors": min_attestors}


def establish_attested_deployment_identity(observation: Mapping[str, Any], *, expected_deployment: Mapping[str, Any], trusted_observer_ids: Sequence[str], reference_time: str, attestations: Sequence[Mapping[str, Any]], trusted_attestation_keys: Mapping[str, str], collector_provenance: Sequence[Mapping[str, Any]], trusted_collector_keys: Mapping[str, str], max_age_seconds: int = 300, min_attestors: int = 2, min_independent_domains: int = 2) -> dict[str, Any]:
    proof = establish_deployment_identity(observation, expected_deployment=expected_deployment, trusted_observer_ids=trusted_observer_ids, reference_time=reference_time, max_age_seconds=max_age_seconds)
    if proof.get("status") != ESTABLISHED or not proof.get("material_match_verified"):
        return proof
    identity = proof.get("identity")
    if not isinstance(identity, Mapping):
        raise DeploymentIdentityError("established material proof is missing identity")
    quorum = verify_attestation_quorum(attestations, trusted_keys=trusted_attestation_keys, observation_fingerprint=str(proof["observation_fingerprint"]), expectation_fingerprint=str(proof["expectation_fingerprint"]), observation_session_id=str(identity["observation_session_id"]), reference_time=reference_time, max_age_seconds=max_age_seconds, min_attestors=min_attestors)
    provenance = verify_collector_provenance(
        collector_provenance,
        trusted_collector_keys=trusted_collector_keys,
        observation_fingerprint=str(proof["observation_fingerprint"]),
        expectation_fingerprint=str(proof["expectation_fingerprint"]),
        observation_session_id=str(identity["observation_session_id"]),
        active_route_surface=str(identity["active_route_surface"]),
        executable_or_module=str(identity["executable_or_module"]),
        active_route_instance_ids=identity["active_route_instance_ids"],
        expected_artifact_digest=str(identity["artifact_digest"]),
        reference_time=reference_time,
        max_age_seconds=max_age_seconds,
        min_independent_domains=min_independent_domains,
    )
    result = dict(proof)
    result["reason"] = "SIGNED_ATTESTATION_AND_INDEPENDENT_PROVENANCE_VERIFIED"
    result["runtime_classification_authorized"] = True
    result["attestation_quorum"] = quorum
    result["collector_provenance"] = provenance
    return result
