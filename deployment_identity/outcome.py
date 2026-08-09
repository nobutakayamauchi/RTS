from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .core import BOUND, fingerprint_observation


OUTCOME_BOUND = "OUTCOME_EVIDENCE_BOUND"
OUTCOME_NOT_BOUND = "OUTCOME_EVIDENCE_NOT_BOUND"


class OutcomeEvidenceError(ValueError):
    """Raised when outcome evidence cannot be bound to one runtime execution."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def outcome_material(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "signature"}


def compute_outcome_signature(material: Mapping[str, Any], secret: str) -> str:
    if not isinstance(secret, str) or not secret:
        raise OutcomeEvidenceError("outcome source secret must be a non-empty string")
    return hmac.new(secret.encode("utf-8"), _canonical_json(dict(material)).encode("utf-8"), hashlib.sha256).hexdigest()


def fingerprint_outcome(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(dict(value)).encode("utf-8")).hexdigest()


def _require_exact_string(value: Mapping[str, Any], field: str) -> str:
    item = value.get(field)
    if not isinstance(item, str) or not item or item != item.strip():
        raise OutcomeEvidenceError(f"{field} must be an exact non-empty string")
    return item


def _parse_timestamp(value: str, field: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise OutcomeEvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise OutcomeEvidenceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _seen_ids(values: Iterable[str]) -> frozenset[str]:
    result = frozenset(values)
    if any(not isinstance(value, str) or not value or value != value.strip() for value in result):
        raise OutcomeEvidenceError("seen_evidence_ids must contain exact non-empty ids")
    return result


def bind_outcome_evidence(
    bound_runtime_proof: Mapping[str, Any],
    runtime_observation: Mapping[str, Any],
    outcome_evidence: Mapping[str, Any],
    *,
    trusted_outcome_keys: Mapping[str, str],
    seen_evidence_ids: Iterable[str],
    max_outcome_delay_seconds: int = 3600,
) -> dict[str, Any]:
    """Bind signed outcome evidence to exactly one authorized runtime execution.

    The verifier is fail-closed. The exact runtime observation must already be
    bound to an authorized deployment proof. Outcome evidence must then bind the
    same deployment, expectation, session, runtime fingerprint and execution id,
    originate from an externally trusted signing source, remain inside the time
    window, and use an evidence id not already present in the caller's ledger.
    """
    if not isinstance(bound_runtime_proof, Mapping) or not isinstance(runtime_observation, Mapping) or not isinstance(outcome_evidence, Mapping):
        raise OutcomeEvidenceError("bound runtime proof, runtime observation and outcome evidence must be objects")
    if not isinstance(trusted_outcome_keys, Mapping) or not trusted_outcome_keys:
        raise OutcomeEvidenceError("trusted_outcome_keys must be a non-empty mapping")
    if not isinstance(max_outcome_delay_seconds, int) or max_outcome_delay_seconds < 0:
        raise OutcomeEvidenceError("max_outcome_delay_seconds must be a non-negative integer")
    seen = _seen_ids(seen_evidence_ids)
    if bound_runtime_proof.get("status") != BOUND or not bound_runtime_proof.get("runtime_classification_authorized"):
        return {"status": OUTCOME_NOT_BOUND, "reason": "RUNTIME_OBSERVATION_NOT_AUTHORIZED", "outcome_evidence_authorized": False}

    runtime_fp = fingerprint_observation(runtime_observation)
    if runtime_fp != bound_runtime_proof.get("runtime_observation_fingerprint"):
        return {"status": OUTCOME_NOT_BOUND, "reason": "RUNTIME_OBSERVATION_FINGERPRINT_MISMATCH", "outcome_evidence_authorized": False}

    runtime_session = _require_exact_string(runtime_observation, "observation_session_id")
    runtime_execution = _require_exact_string(runtime_observation, "execution_id")
    runtime_at_value = _require_exact_string(runtime_observation, "observed_at")
    deployment_fp = _require_exact_string(runtime_observation, "deployment_identity_fingerprint")
    expectation_fp = _require_exact_string(runtime_observation, "deployment_expectation_fingerprint")

    if runtime_session != bound_runtime_proof.get("observation_session_id"):
        return {"status": OUTCOME_NOT_BOUND, "reason": "BOUND_RUNTIME_SESSION_MISMATCH", "outcome_evidence_authorized": False}
    if deployment_fp != bound_runtime_proof.get("deployment_identity_fingerprint"):
        return {"status": OUTCOME_NOT_BOUND, "reason": "BOUND_DEPLOYMENT_FINGERPRINT_MISMATCH", "outcome_evidence_authorized": False}
    if expectation_fp != bound_runtime_proof.get("deployment_expectation_fingerprint"):
        return {"status": OUTCOME_NOT_BOUND, "reason": "BOUND_EXPECTATION_FINGERPRINT_MISMATCH", "outcome_evidence_authorized": False}

    required = (
        "evidence_id",
        "outcome_source_id",
        "execution_id",
        "observation_session_id",
        "deployment_identity_fingerprint",
        "deployment_expectation_fingerprint",
        "runtime_observation_fingerprint",
        "outcome_at",
        "outcome_type",
        "outcome_status",
        "signature",
    )
    values = {field: _require_exact_string(outcome_evidence, field) for field in required}

    if values["evidence_id"] in seen:
        return {"status": OUTCOME_NOT_BOUND, "reason": "OUTCOME_EVIDENCE_REPLAY", "outcome_evidence_authorized": False, "evidence_id": values["evidence_id"]}

    bindings = (
        ("execution_id", values["execution_id"], runtime_execution, "EXECUTION_ID_MISMATCH"),
        ("observation_session_id", values["observation_session_id"], runtime_session, "OUTCOME_SESSION_MISMATCH"),
        ("deployment_identity_fingerprint", values["deployment_identity_fingerprint"], deployment_fp, "OUTCOME_DEPLOYMENT_FINGERPRINT_MISMATCH"),
        ("deployment_expectation_fingerprint", values["deployment_expectation_fingerprint"], expectation_fp, "OUTCOME_EXPECTATION_FINGERPRINT_MISMATCH"),
        ("runtime_observation_fingerprint", values["runtime_observation_fingerprint"], runtime_fp, "OUTCOME_RUNTIME_FINGERPRINT_MISMATCH"),
    )
    for field, actual, expected, reason in bindings:
        if actual != expected:
            return {"status": OUTCOME_NOT_BOUND, "reason": reason, "field": field, "outcome_evidence_authorized": False}

    source_secret = trusted_outcome_keys.get(values["outcome_source_id"])
    if not isinstance(source_secret, str) or not source_secret:
        return {"status": OUTCOME_NOT_BOUND, "reason": "UNTRUSTED_OUTCOME_SOURCE", "outcome_evidence_authorized": False}
    expected_signature = compute_outcome_signature(outcome_material(outcome_evidence), source_secret)
    if not hmac.compare_digest(values["signature"], expected_signature):
        return {"status": OUTCOME_NOT_BOUND, "reason": "INVALID_OUTCOME_SIGNATURE", "outcome_evidence_authorized": False}

    runtime_at = _parse_timestamp(runtime_at_value, "runtime_observed_at")
    outcome_at = _parse_timestamp(values["outcome_at"], "outcome_at")
    delay = (outcome_at - runtime_at).total_seconds()
    if delay < 0 or delay > max_outcome_delay_seconds:
        return {
            "status": OUTCOME_NOT_BOUND,
            "reason": "OUTCOME_OUTSIDE_EXECUTION_WINDOW",
            "outcome_evidence_authorized": False,
            "delay_seconds": delay,
            "max_outcome_delay_seconds": max_outcome_delay_seconds,
        }

    return {
        "status": OUTCOME_BOUND,
        "reason": "SIGNED_OUTCOME_BOUND_TO_AUTHORIZED_RUNTIME_EXECUTION",
        "outcome_evidence_authorized": True,
        "evidence_id": values["evidence_id"],
        "outcome_source_id": values["outcome_source_id"],
        "execution_id": runtime_execution,
        "observation_session_id": runtime_session,
        "deployment_identity_fingerprint": deployment_fp,
        "deployment_expectation_fingerprint": expectation_fp,
        "runtime_observation_fingerprint": runtime_fp,
        "outcome_evidence_fingerprint": fingerprint_outcome(outcome_evidence),
        "outcome_type": values["outcome_type"],
        "outcome_status": values["outcome_status"],
    }
