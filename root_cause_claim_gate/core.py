from __future__ import annotations

from typing import Any

from runtime_code_mapping.core import CodeMappingError, validate_code_mapping_result

SCHEMA_VERSION = "RTS-ROOT-CAUSE-CLAIM-GATE-V1"


class RootCauseGateError(RuntimeError):
    """Raised when root-cause claim input or output is invalid."""


def evaluate_root_cause_claims(
    *,
    code_mapping_result: dict[str, Any],
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate hypotheses without allowing unsupported root-cause promotion."""
    try:
        validate_code_mapping_result(code_mapping_result)
    except CodeMappingError as exc:
        raise RootCauseGateError(f"invalid code mapping result: {exc}") from exc

    if code_mapping_result["state"] != "READY_FOR_ROOT_CAUSE_ANALYSIS":
        raise RootCauseGateError("root-cause analysis requires READY_FOR_ROOT_CAUSE_ANALYSIS")
    if not isinstance(claims, list) or not claims:
        raise RootCauseGateError("claims must be a non-empty array")

    mapped_candidate_id = code_mapping_result["candidate_id"]
    rows: list[dict[str, Any]] = []
    eligible_claim_ids: list[str] = []

    required = {
        "claim_id",
        "candidate_id",
        "hypothesis",
        "supporting_evidence_refs",
        "reproduction_refs",
        "falsification_refs",
        "unresolved_counterevidence_refs",
    }

    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or set(claim) != required:
            raise RootCauseGateError(f"claim[{index}] fields mismatch")
        claim_id = claim["claim_id"]
        candidate_id = claim["candidate_id"]
        hypothesis = claim["hypothesis"]
        support = claim["supporting_evidence_refs"]
        reproduction = claim["reproduction_refs"]
        falsification = claim["falsification_refs"]
        counter = claim["unresolved_counterevidence_refs"]

        if not all(isinstance(v, str) and v for v in (claim_id, candidate_id, hypothesis)):
            raise RootCauseGateError(f"claim[{index}] identifiers and hypothesis must be non-empty strings")
        for key, value in (
            ("supporting_evidence_refs", support),
            ("reproduction_refs", reproduction),
            ("falsification_refs", falsification),
            ("unresolved_counterevidence_refs", counter),
        ):
            if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
                raise RootCauseGateError(f"claim[{index}] {key} must be an array of non-empty strings")

        reasons: list[str] = []
        if candidate_id != mapped_candidate_id:
            reasons.append("candidate_mismatch")
        if not support:
            reasons.append("missing_supporting_evidence")
        if not reproduction:
            reasons.append("missing_reproduction")
        if not falsification:
            reasons.append("missing_falsification_attempt")
        if counter:
            reasons.append("unresolved_counterevidence")

        eligible = not reasons
        if eligible:
            disposition = "ELIGIBLE_ROOT_CAUSE_CLAIM"
            eligible_claim_ids.append(claim_id)
        else:
            disposition = "BLOCKED_ROOT_CAUSE_CLAIM"

        rows.append(
            {
                "claim_id": claim_id,
                "candidate_id": candidate_id,
                "hypothesis": hypothesis,
                "supporting_evidence_refs": list(support),
                "reproduction_refs": list(reproduction),
                "falsification_refs": list(falsification),
                "unresolved_counterevidence_refs": list(counter),
                "eligible_root_cause_claim": eligible,
                "disposition": disposition,
                "blocking_reasons": reasons,
            }
        )

    if len(eligible_claim_ids) == 1:
        state = "ROOT_CAUSE_CLAIM_SUPPORTED"
        root_cause_claim_allowed = True
        selected_claim_id = eligible_claim_ids[0]
        next_action = "PROPOSE_PATCH_THEN_RETEST_WITH_DEPLOYMENT_REIDENTITY"
    elif len(eligible_claim_ids) > 1:
        state = "BLOCKED_AMBIGUOUS_ROOT_CAUSE"
        root_cause_claim_allowed = False
        selected_claim_id = None
        next_action = "DISAMBIGUATE_ROOT_CAUSE_HYPOTHESES"
    else:
        state = "BLOCKED_INSUFFICIENT_ROOT_CAUSE_EVIDENCE"
        root_cause_claim_allowed = False
        selected_claim_id = None
        next_action = "COLLECT_REPRODUCTION_OR_FALSIFICATION_EVIDENCE"

    result = {
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "mapped_candidate_id": mapped_candidate_id,
        "eligible_claim_ids": eligible_claim_ids,
        "selected_claim_id": selected_claim_id,
        "root_cause_claim_allowed": root_cause_claim_allowed,
        "fix_validated": False,
        "next_action": next_action,
        "claims": rows,
        "invariant": "Root-cause claims require support, reproduction, falsification, and no unresolved counterevidence.",
    }
    validate_root_cause_result(result)
    return result


def validate_root_cause_result(result: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "state",
        "mapped_candidate_id",
        "eligible_claim_ids",
        "selected_claim_id",
        "root_cause_claim_allowed",
        "fix_validated",
        "next_action",
        "claims",
        "invariant",
    }
    if set(result) != required:
        raise RootCauseGateError("root-cause result fields mismatch")
    if result["schema_version"] != SCHEMA_VERSION:
        raise RootCauseGateError("unsupported root-cause schema_version")
    if result["fix_validated"] is not False:
        raise RootCauseGateError("root-cause gate must not validate a fix")
    if result["invariant"] != "Root-cause claims require support, reproduction, falsification, and no unresolved counterevidence.":
        raise RootCauseGateError("root-cause invariant mismatch")
    if not isinstance(result["claims"], list) or not result["claims"]:
        raise RootCauseGateError("claims must be a non-empty array")

    eligible_rows = [row for row in result["claims"] if row.get("eligible_root_cause_claim") is True]
    if len(eligible_rows) != len(result["eligible_claim_ids"]):
        raise RootCauseGateError("eligible root-cause count mismatch")

    if result["state"] == "ROOT_CAUSE_CLAIM_SUPPORTED":
        if result["root_cause_claim_allowed"] is not True or len(eligible_rows) != 1:
            raise RootCauseGateError("supported state requires exactly one eligible claim")
        if result["selected_claim_id"] != eligible_rows[0]["claim_id"]:
            raise RootCauseGateError("selected root-cause claim mismatch")
    elif result["state"] == "BLOCKED_AMBIGUOUS_ROOT_CAUSE":
        if result["root_cause_claim_allowed"] is not False or len(eligible_rows) <= 1:
            raise RootCauseGateError("ambiguous state requires multiple eligible claims")
        if result["selected_claim_id"] is not None:
            raise RootCauseGateError("ambiguous state cannot select a claim")
    elif result["state"] == "BLOCKED_INSUFFICIENT_ROOT_CAUSE_EVIDENCE":
        if result["root_cause_claim_allowed"] is not False or eligible_rows:
            raise RootCauseGateError("insufficient state requires zero eligible claims")
        if result["selected_claim_id"] is not None:
            raise RootCauseGateError("blocked state cannot select a claim")
    else:
        raise RootCauseGateError(f"unsupported root-cause state: {result['state']}")
