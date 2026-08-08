from __future__ import annotations

from typing import Any

from runtime_evidence_correlation.core import CorrelationError, validate_correlation_result

SCHEMA_VERSION = "RTS-RUNTIME-CODE-MAPPING-V1"


class CodeMappingError(RuntimeError):
    """Raised when runtime-to-code mapping input or output is invalid."""


def establish_code_mapping(
    *,
    correlation_result: dict[str, Any],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    """Establish one evidence-bound runtime-to-code mapping without claiming root cause."""
    try:
        validate_correlation_result(correlation_result)
    except CorrelationError as exc:
        raise CodeMappingError(f"invalid correlation result: {exc}") from exc

    if correlation_result["state"] != "READY_FOR_CODE_MAPPING":
        raise CodeMappingError("code mapping requires READY_FOR_CODE_MAPPING correlation state")
    if correlation_result["code_mapping_allowed"] is not True:
        raise CodeMappingError("correlation result does not authorize code mapping")

    required = {"candidate_id", "source_ref", "symbols", "mapping_evidence_refs"}
    if not isinstance(mapping, dict) or set(mapping) != required:
        raise CodeMappingError("mapping fields mismatch")

    candidate_id = mapping["candidate_id"]
    source_ref = mapping["source_ref"]
    symbols = mapping["symbols"]
    evidence_refs = mapping["mapping_evidence_refs"]
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CodeMappingError("candidate_id must be a non-empty string")
    if not isinstance(source_ref, str) or not source_ref:
        raise CodeMappingError("source_ref must be a non-empty string")
    if not isinstance(symbols, list) or not symbols or not all(isinstance(v, str) and v for v in symbols):
        raise CodeMappingError("symbols must be a non-empty array of non-empty strings")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(isinstance(v, str) and v for v in evidence_refs):
        raise CodeMappingError("mapping_evidence_refs must be a non-empty array of non-empty strings")

    eligible_ids = correlation_result["eligible_candidate_ids"]
    if eligible_ids != [candidate_id]:
        raise CodeMappingError("mapping candidate must equal the single correlated candidate")

    correlated_rows = [row for row in correlation_result["candidates"] if row["candidate_id"] == candidate_id]
    if len(correlated_rows) != 1:
        raise CodeMappingError("correlated candidate row is missing or duplicated")
    if correlated_rows[0]["source_ref"] != source_ref:
        raise CodeMappingError("mapping source_ref does not match correlated source_ref")

    result = {
        "schema_version": SCHEMA_VERSION,
        "state": "READY_FOR_ROOT_CAUSE_ANALYSIS",
        "candidate_id": candidate_id,
        "source_ref": source_ref,
        "symbols": list(symbols),
        "mapping_evidence_refs": list(evidence_refs),
        "mapping_established": True,
        "root_cause_claim_allowed": False,
        "next_action": "TEST_ROOT_CAUSE_HYPOTHESES_WITH_REPRODUCTION_AND_FALSIFICATION",
        "invariant": "Runtime-to-code mapping is not a root-cause claim.",
    }
    validate_code_mapping_result(result)
    return result


def validate_code_mapping_result(result: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "state",
        "candidate_id",
        "source_ref",
        "symbols",
        "mapping_evidence_refs",
        "mapping_established",
        "root_cause_claim_allowed",
        "next_action",
        "invariant",
    }
    if set(result) != required:
        raise CodeMappingError("code mapping result fields mismatch")
    if result["schema_version"] != SCHEMA_VERSION:
        raise CodeMappingError("unsupported code mapping schema_version")
    if result["state"] != "READY_FOR_ROOT_CAUSE_ANALYSIS":
        raise CodeMappingError("unsupported code mapping state")
    if result["mapping_established"] is not True:
        raise CodeMappingError("ready mapping state requires mapping_established=true")
    if result["root_cause_claim_allowed"] is not False:
        raise CodeMappingError("code mapping must not grant root-cause claim authority")
    if result["invariant"] != "Runtime-to-code mapping is not a root-cause claim.":
        raise CodeMappingError("code mapping invariant mismatch")
    if not isinstance(result["candidate_id"], str) or not result["candidate_id"]:
        raise CodeMappingError("invalid candidate_id")
    if not isinstance(result["source_ref"], str) or not result["source_ref"]:
        raise CodeMappingError("invalid source_ref")
    for key in ("symbols", "mapping_evidence_refs"):
        value = result[key]
        if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
            raise CodeMappingError(f"invalid {key}")
