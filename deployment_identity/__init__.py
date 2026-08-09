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

__all__ = [
    "AttestationError",
    "DeploymentIdentityError",
    "bind_runtime_observation",
    "compute_hmac_signature",
    "establish_attested_deployment_identity",
    "establish_deployment_identity",
    "fingerprint_expectation",
    "fingerprint_observation",
    "verify_attestation_quorum",
]
