from __future__ import annotations

from typing import Any


class DebugEvidenceError(ValueError):
    pass


def _established(identity: Any) -> bool:
    return (
        isinstance(identity, dict)
        and identity.get("status") == "ESTABLISHED"
        and isinstance(identity.get("evidence_ref"), str)
        and bool(identity["evidence_ref"])
        and isinstance(identity.get("fingerprint"), str)
        and bool(identity["fingerprint"])
    )


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    identity = case.get("deployment_identity") or {}
    if not _established(identity):
        return {"state": "BLOCKED_DEPLOYMENT_IDENTITY", "fix_validated": False}

    probes = case.get("probes")
    if not isinstance(probes, list) or not probes:
        raise DebugEvidenceError("non-empty probes required")

    failed: list[str] = []
    for probe in probes:
        if not isinstance(probe, dict):
            raise DebugEvidenceError("probe must be an object")
        if probe.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
            raise DebugEvidenceError("invalid probe status")
        if not probe.get("probe_id") or not probe.get("evidence_refs"):
            raise DebugEvidenceError("probe identity and evidence required")
        if probe.get("deployment_fingerprint") != identity["fingerprint"]:
            return {
                "state": "BLOCKED_PROBE_IDENTITY_MISMATCH",
                "failed_probe_ids": sorted(failed),
                "blocking_states": [f"PROBE_IDENTITY_MISMATCH:{probe['probe_id']}"],
                "fix_validated": False,
            }
        if probe["status"] == "BLOCKED":
            return {"state": "BLOCKED_PROBE_EXECUTION", "failed_probe_ids": sorted(failed), "fix_validated": False}
        if probe["status"] == "FAIL":
            failed.append(probe["probe_id"])

    if not failed:
        return {"state": "NO_FAILURE_OBSERVED", "failed_probe_ids": [], "fix_validated": False}

    patch = case.get("patch") or {}
    if patch.get("applied") is not True:
        return {"state": "FAILURE_EVIDENCE_READY", "failed_probe_ids": sorted(failed), "fix_validated": False}

    post = patch.get("post_deployment_identity") or {}
    blockers: list[str] = []
    if not _established(post):
        blockers.append("POST_PATCH_IDENTITY_NOT_ESTABLISHED")

    replay_results = patch.get("replay_results", [])
    if not isinstance(replay_results, list):
        raise DebugEvidenceError("replay_results must be a list")
    replay: dict[str, dict[str, Any]] = {}
    for row in replay_results:
        if not isinstance(row, dict):
            raise DebugEvidenceError("replay row must be an object")
        probe_id = row.get("probe_id")
        if not probe_id or probe_id in replay:
            raise DebugEvidenceError("replay probe_id missing or duplicate")
        replay[probe_id] = row

    post_fingerprint = post.get("fingerprint")
    for probe_id in failed:
        row = replay.get(probe_id)
        if not row or row.get("status") != "PASS" or not row.get("evidence_refs"):
            blockers.append(f"FAILED_PROBE_REPLAY_NOT_PROVEN:{probe_id}")
        elif row.get("deployment_fingerprint") != post_fingerprint:
            blockers.append(f"FAILED_PROBE_REPLAY_IDENTITY_MISMATCH:{probe_id}")

    if patch.get("regression_status") != "PASS" or not patch.get("regression_evidence_refs"):
        blockers.append("REGRESSION_NOT_PROVEN")
    elif patch.get("regression_deployment_fingerprint") != post_fingerprint:
        blockers.append("REGRESSION_IDENTITY_MISMATCH")

    return {
        "state": "FIX_VALIDATED" if not blockers else "PATCH_NOT_VALIDATED",
        "failed_probe_ids": sorted(failed),
        "blocking_states": sorted(blockers),
        "fix_validated": not blockers,
        "invariants": [
            "CODE_EXISTENCE != RUNTIME_EVIDENCE",
            "MAPPING != ROOT_CAUSE",
            "PATCH_APPLIED != FIX_VALIDATED",
            "RUNTIME_EVIDENCE_MUST_BIND_TO_DEPLOYMENT_FINGERPRINT",
        ],
    }
