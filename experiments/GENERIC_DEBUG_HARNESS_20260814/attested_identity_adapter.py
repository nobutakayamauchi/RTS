from __future__ import annotations

from typing import Any

from deployment_identity.attestation import establish_attested_deployment_identity

ESTABLISHED = "DEPLOYMENT_IDENTITY_ESTABLISHED"


class IdentityAdapterError(ValueError):
    pass


_REQUIRED = {
    "observation", "expected_deployment", "trusted_observer_ids", "reference_time",
    "attestations", "trusted_attestation_keys", "collector_provenance",
    "trusted_collector_keys", "trusted_collector_domains",
}


def resolve(bundle: Any) -> dict[str, Any]:
    if not isinstance(bundle, dict) or set(bundle) != _REQUIRED:
        raise IdentityAdapterError("exact attested deployment bundle required")
    proof = establish_attested_deployment_identity(
        bundle["observation"],
        expected_deployment=bundle["expected_deployment"],
        trusted_observer_ids=bundle["trusted_observer_ids"],
        reference_time=bundle["reference_time"],
        attestations=bundle["attestations"],
        trusted_attestation_keys=bundle["trusted_attestation_keys"],
        collector_provenance=bundle["collector_provenance"],
        trusted_collector_keys=bundle["trusted_collector_keys"],
        trusted_collector_domains=bundle["trusted_collector_domains"],
    )
    if (
        not isinstance(proof, dict)
        or proof.get("status") != ESTABLISHED
        or proof.get("runtime_classification_authorized") is not True
        or proof.get("attestation_quorum", {}).get("status") != "ATTESTATION_QUORUM_VERIFIED"
        or proof.get("collector_provenance", {}).get("status") != "COLLECTOR_PROVENANCE_VERIFIED"
    ):
        raise IdentityAdapterError("authorized attested deployment identity required")
    identity = proof.get("identity")
    if not isinstance(identity, dict) or not identity.get("observation_session_id"):
        raise IdentityAdapterError("deployment identity session missing")
    for key in ("observation_fingerprint", "expectation_fingerprint"):
        if not isinstance(proof.get(key), str) or not proof[key]:
            raise IdentityAdapterError(f"{key} missing")
    return proof


def binding(proof: dict[str, Any]) -> tuple[str, str, str]:
    return (
        proof["observation_fingerprint"],
        proof["expectation_fingerprint"],
        proof["identity"]["observation_session_id"],
    )
