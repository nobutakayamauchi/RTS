from __future__ import annotations

from typing import Any

from deployment_identity.attestation import establish_attested_deployment_identity

ESTABLISHED = "DEPLOYMENT_IDENTITY_ESTABLISHED"


class IdentityAdapterError(ValueError):
    pass


_EVIDENCE_FIELDS = {"observation", "attestations", "collector_provenance"}
_VERIFIER_FIELDS = {
    "expected_deployment",
    "trusted_observer_ids",
    "reference_time",
    "trusted_attestation_keys",
    "trusted_collector_keys",
    "trusted_collector_domains",
}


def resolve(evidence: Any, verifier: Any) -> dict[str, Any]:
    """Resolve evidence using verifier-controlled trust anchors.

    Evidence producers may submit observations, attestations and provenance only.
    Expected deployment, observer policy, trusted keys, trust-domain policy and
    reference time are supplied separately by the verifier and cannot be
    self-declared inside the evidence payload.
    """
    if not isinstance(evidence, dict) or set(evidence) != _EVIDENCE_FIELDS:
        raise IdentityAdapterError("exact deployment evidence payload required")
    if not isinstance(verifier, dict) or set(verifier) != _VERIFIER_FIELDS:
        raise IdentityAdapterError("exact verifier-controlled identity policy required")

    proof = establish_attested_deployment_identity(
        evidence["observation"],
        expected_deployment=verifier["expected_deployment"],
        trusted_observer_ids=verifier["trusted_observer_ids"],
        reference_time=verifier["reference_time"],
        attestations=evidence["attestations"],
        trusted_attestation_keys=verifier["trusted_attestation_keys"],
        collector_provenance=evidence["collector_provenance"],
        trusted_collector_keys=verifier["trusted_collector_keys"],
        trusted_collector_domains=verifier["trusted_collector_domains"],
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
    if (
        not isinstance(identity, dict)
        or not isinstance(identity.get("observation_session_id"), str)
        or not identity["observation_session_id"]
        or not isinstance(identity.get("observed_at"), str)
        or not identity["observed_at"]
    ):
        raise IdentityAdapterError("deployment identity session/time missing")
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
