from __future__ import annotations

from typing import Any


class DebugEvidenceError(ValueError):
    pass


def evaluate(case: dict[str, Any]) -> dict[str, Any]:
    identity = case.get("deployment_identity") or {}
    if identity.get("status") != "ESTABLISHED" or not identity.get("evidence_ref"):
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
        if probe["status"] == "BLOCKED":
            return {"state": "BLOCKED_PROBE_EXECUTION", "failed_probe_ids": failed, "fix_validated": False}
        if probe["status"] == "FAIL":
            failed.append(probe["probe_id"])

    if not failed:
        return {"state": "NO_FAILURE_OBSERVED", "failed_probe_ids": [], "fix_validated": False}

    patch = case.get("patch") or {}
    if patch.get("applied") is not True:
        return {"state": "FAILURE_EVIDENCE_READY", "failed_probe_ids": failed, "fix_validated": False}

    post = patch.get("post_deployment_identity") or {}
    blockers: list[str] = []
    if post.get("status") != "ESTABLISHED" or not post.get("evidence_ref"):
        blockers.append("POST_PATCH_IDENTITY_NOT_ESTABLISHED")

    replay = {row.get("probe_id"): row for row in patch.get("replay_results", []) if isinstance(row, dict)}
    for probe_id in failed:
        row = replay.get(probe_id)
        if not row or row.get("status") != "PASS" or not row.get("evidence_refs"):
            blockers.append(f"FAILED_PROBE_REPLAY_NOT_PROVEN:{probe_id}")

    if patch.get("regression_status") != "PASS" or not patch.get("regression_evidence_refs"):
        blockers.append("REGRESSION_NOT_PROVEN")

    return {
        "state": "FIX_VALIDATED" if not blockers else "PATCH_NOT_VALIDATED",
        "failed_probe_ids": sorted(failed),
        "blocking_states": sorted(blockers),
        "fix_validated": not blockers,
        "invariants": [
            "CODE_EXISTENCE != RUNTIME_EVIDENCE",
            "MAPPING != ROOT_CAUSE",
            "PATCH_APPLIED != FIX_VALIDATED",
        ],
    }
