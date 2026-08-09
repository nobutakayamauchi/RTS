"""Deployment identity proof boundary for RTS."""

from .attestation import (
    AttestationError,
    compute_hmac_signature,
    establish_attested_deployment_identity,
    verify_attestation_quorum,
)
from .core import (
    DeploymentIdentityError,
    bind_runtime_observation,
    establish_deployment_identity,
    fingerprint_expectation,
    fingerprint_observation,
)
from .outcome import (
    OUTCOME_BOUND,
    OUTCOME_NOT_BOUND,
    OutcomeEvidenceError,
    bind_outcome_evidence,
    compute_outcome_signature,
    fingerprint_outcome,
)

__all__ = [
    "AttestationError",
    "DeploymentIdentityError",
    "OUTCOME_BOUND",
    "OUTCOME_NOT_BOUND",
    "OutcomeEvidenceError",
    "bind_outcome_evidence",
    "bind_runtime_observation",
    "compute_hmac_signature",
    "compute_outcome_signature",
    "establish_attested_deployment_identity",
    "establish_deployment_identity",
    "fingerprint_expectation",
    "fingerprint_observation",
    "fingerprint_outcome",
    "verify_attestation_quorum",
]
