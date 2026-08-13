from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .attested_identity_adapter import binding, resolve


class DebugEvidenceError(ValueError):
    pass


def _refs(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and bool(item.strip()) and item == item.strip()
        for item in value
    )


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DebugEvidenceError(f"{field} must be an exact timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DebugEvidenceError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise DebugEvidenceError(f"{field} timezone required")
    return parsed.astimezone(timezone.utc)


def _manifest(rows: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise DebugEvidenceError("probe_manifest required")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"probe_id", "definition_fingerprint", "required"}:
            raise DebugEvidenceError("probe manifest shape")
        pid, definition, required = row["probe_id"], row["definition_fingerprint"], row["required"]
        if not isinstance(pid, str) or not pid or not isinstance(definition, str) or not definition or not isinstance(required, bool):
            raise DebugEvidenceError("probe manifest values")
        if pid in out:
            raise DebugEvidenceError("duplicate probe_id")
        out[pid] = row
    return out


def _results(rows: Any, manifest: dict[str, dict[str, Any]], proof: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise DebugEvidenceError(f"{label} must be a list")
    fields = {
        "probe_id", "definition_fingerprint", "status", "evidence_refs",
        "deployment_observation_fingerprint", "deployment_expectation_fingerprint",
        "observation_session_id",
    }
    expected = binding(proof)
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != fields:
            raise DebugEvidenceError(f"{label} shape")
        pid = row["probe_id"]
        if pid not in manifest or pid in out:
            raise DebugEvidenceError(f"{label} unknown or duplicate probe")
        if row["definition_fingerprint"] != manifest[pid]["definition_fingerprint"]:
            raise DebugEvidenceError(f"{label} probe definition mismatch")
        if row["status"] not in {"PASS", "FAIL", "BLOCKED"} or not _refs(row["evidence_refs"]):
            raise DebugEvidenceError(f"{label} evidence invalid")
        actual = (
            row["deployment_observation_fingerprint"],
            row["deployment_expectation_fingerprint"],
            row["observation_session_id"],
        )
        if actual != expected:
            raise DebugEvidenceError(f"{label} deployment binding mismatch")
        out[pid] = row
    return out


def _verifier(verifiers: Any, key: str) -> dict[str, Any]:
    if not isinstance(verifiers, dict) or key not in verifiers or not isinstance(verifiers[key], dict):
        raise DebugEvidenceError(f"verifier-controlled policy missing: {key}")
    return verifiers[key]


def evaluate(case: Any, *, identity_verifiers: Any) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise DebugEvidenceError("case object required")

    manifest = _manifest(case.get("probe_manifest"))
    initial = resolve(
        case.get("deployment_identity_evidence"),
        _verifier(identity_verifiers, "initial"),
    )
    results = _results(case.get("probe_results"), manifest, initial, "probe_results")
    required = {pid for pid, row in manifest.items() if row["required"]}

    missing = sorted(required - set(results))
    if missing:
        return {"state": "BLOCKED_REQUIRED_PROBE_MISSING", "stable_eligible": False, "fix_validated": False}
    if any(results[pid]["status"] == "BLOCKED" for pid in required):
        return {"state": "BLOCKED_PROBE_EXECUTION", "stable_eligible": False, "fix_validated": False}

    failed = sorted(pid for pid in required if results[pid]["status"] == "FAIL")
    if not failed:
        return {"state": "DEPLOYMENT_VALIDATED", "stable_eligible": True, "fix_validated": False}

    patch = case.get("patch")
    if not isinstance(patch, dict) or patch.get("applied") is not True:
        return {"state": "FAILURE_EVIDENCE_READY", "stable_eligible": False, "fix_validated": False}
    if not isinstance(patch.get("applied_at"), str):
        raise DebugEvidenceError("patch applied_at required")

    post = resolve(
        patch.get("post_deployment_identity_evidence"),
        _verifier(identity_verifiers, "post_patch"),
    )

    blockers: list[str] = []
    initial_binding = binding(initial)
    post_binding = binding(post)
    if post["observation_fingerprint"] == initial["observation_fingerprint"]:
        blockers.append("POST_PATCH_OBSERVATION_FINGERPRINT_NOT_NEW")
    if post["identity"]["observation_session_id"] == initial["identity"]["observation_session_id"]:
        blockers.append("POST_PATCH_SESSION_NOT_NEW")

    initial_at = _timestamp(initial["identity"]["observed_at"], "initial observed_at")
    applied_at = _timestamp(patch["applied_at"], "patch applied_at")
    post_at = _timestamp(post["identity"]["observed_at"], "post observed_at")
    if not (initial_at < applied_at < post_at):
        blockers.append("POST_PATCH_TEMPORAL_ORDER_NOT_PROVEN")

    replay = _results(patch.get("replay_results"), manifest, post, "replay_results")
    blockers.extend(
        f"FAILED_PROBE_REPLAY_NOT_PASS:{pid}"
        for pid in failed
        if pid not in replay or replay[pid]["status"] != "PASS"
    )

    reg_manifest = case.get("regression_manifest")
    regression = patch.get("regression_result")
    if not isinstance(reg_manifest, dict) or set(reg_manifest) != {"suite_fingerprint"} or not reg_manifest["suite_fingerprint"]:
        raise DebugEvidenceError("regression manifest invalid")
    fields = {
        "suite_fingerprint", "status", "evidence_refs",
        "deployment_observation_fingerprint", "deployment_expectation_fingerprint",
        "observation_session_id",
    }
    if not isinstance(regression, dict) or set(regression) != fields:
        raise DebugEvidenceError("regression result invalid")
    if regression["suite_fingerprint"] != reg_manifest["suite_fingerprint"]:
        blockers.append("REGRESSION_SUITE_FINGERPRINT_MISMATCH")
    if regression["status"] != "PASS" or not _refs(regression["evidence_refs"]):
        blockers.append("REGRESSION_NOT_PROVEN")
    if (
        regression["deployment_observation_fingerprint"],
        regression["deployment_expectation_fingerprint"],
        regression["observation_session_id"],
    ) != post_binding:
        blockers.append("REGRESSION_DEPLOYMENT_BINDING_MISMATCH")

    ok = not blockers
    return {
        "state": "FIX_VALIDATED" if ok else "PATCH_NOT_VALIDATED",
        "stable_eligible": ok,
        "fix_validated": ok,
        "initial_deployment_binding": initial_binding,
        "post_deployment_binding": post_binding,
        "blocking_states": sorted(blockers),
    }
