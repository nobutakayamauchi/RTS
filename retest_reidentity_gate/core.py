from __future__ import annotations

from typing import Any

from deployment_identity.core import DeploymentIdentityError, validate_snapshot
from root_cause_claim_gate.core import RootCauseGateError, validate_root_cause_result

SCHEMA_VERSION = "RTS-RETEST-REIDENTITY-GATE-V1"


class RetestGateError(RuntimeError):
    """Raised when retest/re-identity input or output is invalid."""


def evaluate_retest(
    *,
    pre_patch_identity: dict[str, Any],
    post_patch_identity: dict[str, Any],
    root_cause_result: dict[str, Any],
    retest: dict[str, Any],
) -> dict[str, Any]:
    """Validate a post-patch retest only after deployment identity is re-established."""
    try:
        validate_snapshot(pre_patch_identity)
        validate_snapshot(post_patch_identity)
    except DeploymentIdentityError as exc:
        raise RetestGateError(f"invalid deployment identity snapshot: {exc}") from exc
    try:
        validate_root_cause_result(root_cause_result)
    except RootCauseGateError as exc:
        raise RetestGateError(f"invalid root-cause result: {exc}") from exc

    if pre_patch_identity["status"] != "ESTABLISHED":
        raise RetestGateError("pre-patch deployment identity must be ESTABLISHED")
    if post_patch_identity["status"] != "ESTABLISHED":
        raise RetestGateError("post-patch deployment identity must be ESTABLISHED")
    if root_cause_result["state"] != "ROOT_CAUSE_CLAIM_SUPPORTED" or root_cause_result["root_cause_claim_allowed"] is not True:
        raise RetestGateError("retest requires one supported root-cause claim")

    required = {"claim_id", "deployed_revision", "verification_refs", "regression_refs", "outcome"}
    if not isinstance(retest, dict) or set(retest) != required:
        raise RetestGateError("retest fields mismatch")

    claim_id = retest["claim_id"]
    revision = retest["deployed_revision"]
    verification_refs = retest["verification_refs"]
    regression_refs = retest["regression_refs"]
    outcome = retest["outcome"]

    if not isinstance(claim_id, str) or not claim_id:
        raise RetestGateError("claim_id must be a non-empty string")
    if claim_id != root_cause_result["selected_claim_id"]:
        raise RetestGateError("retest claim_id does not match selected root-cause claim")
    if not isinstance(revision, str) or not revision:
        raise RetestGateError("deployed_revision must be a non-empty string")
    post_revision = post_patch_identity["fields"]["deployed_revision"]["value"]
    if revision != post_revision:
        raise RetestGateError("retest revision does not match re-established post-patch deployment revision")
    for key, value in (("verification_refs", verification_refs), ("regression_refs", regression_refs)):
        if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
            raise RetestGateError(f"{key} must be an array of non-empty strings")
    if outcome not in {"PASS", "FAIL"}:
        raise RetestGateError("outcome must be PASS or FAIL")

    identity_changed = _identity_changed(pre_patch_identity, post_patch_identity)

    if outcome == "PASS" and verification_refs and regression_refs:
        state = "FIX_VALIDATED"
        fix_validated = True
        next_action = "CLOSE_OR_CONTINUE_MONITORING_WITH_IDENTITY_BOUND_EVIDENCE"
    elif outcome == "FAIL":
        state = "RETEST_FAILED"
        fix_validated = False
        next_action = "RETURN_TO_ROOT_CAUSE_ANALYSIS_WITH_NEW_RUNTIME_EVIDENCE"
    else:
        state = "BLOCKED_INSUFFICIENT_RETEST_EVIDENCE"
        fix_validated = False
        next_action = "COLLECT_POST_PATCH_VERIFICATION_AND_REGRESSION_EVIDENCE"

    result = {
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "claim_id": claim_id,
        "pre_patch_revision": pre_patch_identity["fields"]["deployed_revision"]["value"],
        "post_patch_revision": post_revision,
        "deployment_identity_reestablished": True,
        "identity_changed": identity_changed,
        "verification_refs": list(verification_refs),
        "regression_refs": list(regression_refs),
        "outcome": outcome,
        "fix_validated": fix_validated,
        "next_action": next_action,
        "invariant": "A fix is not validated until post-patch deployment identity is established and the retest is evidence-bound to it.",
    }
    validate_retest_result(result)
    return result


def _identity_changed(before: dict[str, Any], after: dict[str, Any]) -> bool:
    names = ("service_unit", "working_directory", "executable", "entrypoint", "active_route", "deployed_revision", "artifact_sha256")
    return any(before["fields"][name]["value"] != after["fields"][name]["value"] for name in names)


def validate_retest_result(result: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "state",
        "claim_id",
        "pre_patch_revision",
        "post_patch_revision",
        "deployment_identity_reestablished",
        "identity_changed",
        "verification_refs",
        "regression_refs",
        "outcome",
        "fix_validated",
        "next_action",
        "invariant",
    }
    if set(result) != required:
        raise RetestGateError("retest result fields mismatch")
    if result["schema_version"] != SCHEMA_VERSION:
        raise RetestGateError("unsupported retest schema_version")
    if result["deployment_identity_reestablished"] is not True:
        raise RetestGateError("retest result must prove deployment identity was re-established")
    if result["invariant"] != "A fix is not validated until post-patch deployment identity is established and the retest is evidence-bound to it.":
        raise RetestGateError("retest invariant mismatch")

    if result["state"] == "FIX_VALIDATED":
        if result["fix_validated"] is not True or result["outcome"] != "PASS":
            raise RetestGateError("validated fix requires PASS")
        if not result["verification_refs"] or not result["regression_refs"]:
            raise RetestGateError("validated fix requires verification and regression evidence")
    elif result["state"] == "RETEST_FAILED":
        if result["fix_validated"] is not False or result["outcome"] != "FAIL":
            raise RetestGateError("failed retest must not validate fix")
    elif result["state"] == "BLOCKED_INSUFFICIENT_RETEST_EVIDENCE":
        if result["fix_validated"] is not False or result["outcome"] != "PASS":
            raise RetestGateError("insufficient evidence state must be a non-validating PASS attempt")
    else:
        raise RetestGateError(f"unsupported retest state: {result['state']}")
