from __future__ import annotations

from typing import Any

from deployment_identity.core import DeploymentIdentityError, validate_snapshot

SCHEMA_VERSION = "RTS-RUNTIME-EVIDENCE-CORRELATION-V1"


class CorrelationError(RuntimeError):
    """Raised when runtime evidence correlation input or output is invalid."""


def correlate_candidates(
    *,
    deployment_identity: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Correlate source candidates to an ESTABLISHED deployed revision.

    This gate only determines candidate eligibility for code mapping. It never
    determines root cause and never treats source existence as runtime evidence.
    """
    try:
        validate_snapshot(deployment_identity)
    except DeploymentIdentityError as exc:
        raise CorrelationError(f"invalid deployment identity snapshot: {exc}") from exc

    if deployment_identity["status"] != "ESTABLISHED":
        raise CorrelationError("evidence correlation requires ESTABLISHED deployment identity")
    if not isinstance(candidates, list) or not candidates:
        raise CorrelationError("candidates must be a non-empty array")

    deployed_revision = deployment_identity["fields"]["deployed_revision"]["value"]
    if not isinstance(deployed_revision, str) or not deployed_revision:
        raise CorrelationError("ESTABLISHED identity is missing deployed revision")

    rows: list[dict[str, Any]] = []
    eligible_ids: list[str] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise CorrelationError(f"candidate[{index}] must be an object")
        required = {"candidate_id", "source_ref", "revision", "runtime_evidence_refs"}
        if set(candidate) != required:
            raise CorrelationError(f"candidate[{index}] fields mismatch")
        candidate_id = candidate["candidate_id"]
        source_ref = candidate["source_ref"]
        revision = candidate["revision"]
        evidence_refs = candidate["runtime_evidence_refs"]
        if not all(isinstance(value, str) and value for value in (candidate_id, source_ref, revision)):
            raise CorrelationError(f"candidate[{index}] identifiers must be non-empty strings")
        if not isinstance(evidence_refs, list) or not all(isinstance(value, str) and value for value in evidence_refs):
            raise CorrelationError(f"candidate[{index}] runtime_evidence_refs must be an array of non-empty strings")

        if revision != deployed_revision:
            disposition = "REJECTED_REVISION_MISMATCH"
            eligible = False
            reason = "Candidate revision does not equal the established deployed revision."
        elif not evidence_refs:
            disposition = "BLOCKED_MISSING_RUNTIME_EVIDENCE"
            eligible = False
            reason = "Candidate revision matches, but no runtime evidence reference binds the candidate to the observation."
        else:
            disposition = "ELIGIBLE_FOR_CODE_MAPPING"
            eligible = True
            reason = "Candidate revision matches the established deployment and has runtime evidence references."
            eligible_ids.append(candidate_id)

        rows.append(
            {
                "candidate_id": candidate_id,
                "source_ref": source_ref,
                "revision": revision,
                "runtime_evidence_refs": list(evidence_refs),
                "disposition": disposition,
                "eligible_for_code_mapping": eligible,
                "root_cause_claim_allowed": False,
                "reason": reason,
            }
        )

    if len(eligible_ids) == 1:
        state = "READY_FOR_CODE_MAPPING"
        code_mapping_allowed = True
        next_action = "MAP_SINGLE_ELIGIBLE_CANDIDATE_WITHOUT_ROOT_CAUSE_CLAIM"
    elif len(eligible_ids) > 1:
        state = "BLOCKED_AMBIGUOUS_CANDIDATES"
        code_mapping_allowed = False
        next_action = "DISAMBIGUATE_RUNTIME_EVIDENCE"
    else:
        state = "BLOCKED_NO_CORRELATED_CANDIDATE"
        code_mapping_allowed = False
        next_action = "COLLECT_OR_CORRECT_RUNTIME_EVIDENCE"

    result = {
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "deployed_revision": deployed_revision,
        "eligible_candidate_ids": eligible_ids,
        "code_mapping_allowed": code_mapping_allowed,
        "root_cause_claim_allowed": False,
        "next_action": next_action,
        "candidates": rows,
        "invariant": "Code existence != runtime evidence.",
    }
    validate_correlation_result(result)
    return result


def validate_correlation_result(result: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "state",
        "deployed_revision",
        "eligible_candidate_ids",
        "code_mapping_allowed",
        "root_cause_claim_allowed",
        "next_action",
        "candidates",
        "invariant",
    }
    if set(result) != required:
        raise CorrelationError("correlation result fields mismatch")
    if result["schema_version"] != SCHEMA_VERSION:
        raise CorrelationError("unsupported correlation schema_version")
    if result["root_cause_claim_allowed"] is not False:
        raise CorrelationError("evidence correlation must never grant root-cause claim authority")
    if result["invariant"] != "Code existence != runtime evidence.":
        raise CorrelationError("correlation invariant mismatch")
    if not isinstance(result["eligible_candidate_ids"], list):
        raise CorrelationError("eligible_candidate_ids must be an array")
    if not isinstance(result["candidates"], list) or not result["candidates"]:
        raise CorrelationError("candidates must be a non-empty array")

    eligible_rows = [row for row in result["candidates"] if row.get("eligible_for_code_mapping") is True]
    if len(eligible_rows) != len(result["eligible_candidate_ids"]):
        raise CorrelationError("eligible candidate count mismatch")
    if any(row.get("root_cause_claim_allowed") is not False for row in result["candidates"]):
        raise CorrelationError("candidate row granted root-cause claim authority")

    if result["state"] == "READY_FOR_CODE_MAPPING":
        if result["code_mapping_allowed"] is not True or len(eligible_rows) != 1:
            raise CorrelationError("ready state requires exactly one eligible candidate")
    elif result["state"] == "BLOCKED_AMBIGUOUS_CANDIDATES":
        if result["code_mapping_allowed"] is not False or len(eligible_rows) <= 1:
            raise CorrelationError("ambiguous state requires multiple eligible candidates")
    elif result["state"] == "BLOCKED_NO_CORRELATED_CANDIDATE":
        if result["code_mapping_allowed"] is not False or eligible_rows:
            raise CorrelationError("blocked state requires zero eligible candidates")
    else:
        raise CorrelationError(f"unsupported correlation state: {result['state']}")
