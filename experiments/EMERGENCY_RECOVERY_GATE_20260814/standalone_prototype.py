from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


class StandaloneEmergencyError(ValueError):
    pass


def _time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise StandaloneEmergencyError(f"{field} must be exact ISO-8601")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise StandaloneEmergencyError(f"{field} invalid") from exc
    if parsed.tzinfo is None:
        raise StandaloneEmergencyError(f"{field} timezone required")
    return parsed.astimezone(timezone.utc)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value


def _recovery_validation_ok(validation: Any, *, candidate_id: str, applied_at: datetime, at: datetime) -> bool:
    if (
        not isinstance(validation, dict)
        or validation.get("state") not in {"DEPLOYMENT_VALIDATED", "FIX_VALIDATED"}
        or validation.get("stable_eligible") is not True
        or not validation.get("post_deployment_binding")
        or validation.get("validated_candidate_id") != candidate_id
        or not _text(validation.get("validated_at"))
    ):
        return False
    try:
        validated_at = _time(validation["validated_at"], "validation.validated_at")
    except StandaloneEmergencyError:
        return False
    return applied_at < validated_at <= at


def _applied_recovery(
    case: dict[str, Any],
    at: datetime,
    recovery: dict[str, Any],
    recovery_validator: Callable[[dict[str, Any]], dict[str, Any]] | None,
) -> dict[str, Any]:
    candidate = case.get("candidate")
    if not isinstance(candidate, dict) or not _text(candidate.get("candidate_id")):
        return {"state": "RECOVERY_NOT_VALIDATED", "action": "RETURN_TO_ANALYSIS", "temporary_occupant": True, "promotion_authorized": False}
    required_text = (
        "executor_evidence_ref",
        "applied_at",
        "candidate_id",
        "trigger_source_ref",
        "trigger_observed_at",
        "failover_authority_ref",
    )
    if any(not _text(recovery.get(key)) for key in required_text):
        raise StandaloneEmergencyError("applied recovery requires bound trigger/executor/authority evidence")
    if recovery.get("candidate_id") != candidate["candidate_id"]:
        return {"state": "RECOVERY_NOT_VALIDATED", "action": "RETURN_TO_ANALYSIS", "temporary_occupant": True, "promotion_authorized": False}
    if recovery.get("trigger_state") not in {"FAILED", "UNSAFE"}:
        raise StandaloneEmergencyError("applied recovery requires FAILED or UNSAFE trigger snapshot")
    trigger_at = _time(recovery["trigger_observed_at"], "recovery.trigger_observed_at")
    applied_at = _time(recovery["applied_at"], "recovery.applied_at")
    if not (trigger_at < applied_at <= at):
        raise StandaloneEmergencyError("recovery application time must follow its persisted trigger observation and not be future")
    if recovery.get("failback_requested") is True:
        return {"state": "FAILBACK_BLOCKED_PENDING_DARWIN", "action": "NONE", "temporary_occupant": True, "promotion_authorized": False, "automatic_failback_authorized": False}
    if recovery_validator is None:
        return {"state": "RECOVERY_VALIDATION_REQUIRED", "action": "POST_DEPLOY_REALITY_GATE", "temporary_occupant": True, "promotion_authorized": False}
    validation = recovery_validator(recovery)
    if not _recovery_validation_ok(validation, candidate_id=candidate["candidate_id"], applied_at=applied_at, at=at):
        return {"state": "RECOVERY_NOT_VALIDATED", "action": "RETURN_TO_ANALYSIS", "temporary_occupant": True, "promotion_authorized": False}
    return {
        "state": "TEMPORARY_RECOVERY_VALIDATED",
        "action": "CONTINUE_TEMPORARILY",
        "temporary_occupant": True,
        "promotion_authorized": False,
        "automatic_failback_authorized": False,
        "post_deployment_binding": validation["post_deployment_binding"],
        "recovery_debt": ["DISCOVERY_REFRESH", "ROOT_CAUSE_REVIEW", "METEOR_DARWIN", "PERMANENT_OCCUPANT_DECISION"],
    }


def evaluate(
    case: dict[str, Any],
    at: datetime,
    *,
    recovery_validator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Independent reference candidate used only to test whether a new engine is justified."""
    if not isinstance(case, dict) or not isinstance(case.get("emergency"), dict):
        raise StandaloneEmergencyError("emergency case required")
    emergency = case["emergency"]
    policy = emergency.get("policy") or {}
    health = emergency.get("health") or {}
    candidate = case.get("candidate")
    authority = case.get("authority") or {}

    state = health.get("state")
    if state not in {"HEALTHY", "DEGRADED", "FAILED", "UNSAFE", "UNKNOWN"}:
        raise StandaloneEmergencyError("invalid health state")
    if not _text(health.get("source_ref")) or not _text(health.get("observed_at")) or not _text(health.get("stale_after")):
        raise StandaloneEmergencyError("health evidence required")

    recovery = emergency.get("recovery")
    if isinstance(recovery, dict) and recovery.get("applied") is True:
        return _applied_recovery(case, at, recovery, recovery_validator)

    health_at = _time(health["observed_at"], "health.observed_at")
    stale_at = _time(health["stale_after"], "health.stale_after")
    if health_at > at:
        raise StandaloneEmergencyError("health observation cannot be in the future")
    if stale_at <= at or stale_at <= health_at:
        return {"state": "HEALTH_EVIDENCE_STALE", "action": "HUMAN_REVIEW", "promotion_authorized": False}
    if state == "HEALTHY":
        return {"state": "HEALTHY", "action": "NONE", "promotion_authorized": False}
    if state == "UNKNOWN":
        return {"state": "HEALTH_UNKNOWN", "action": "HUMAN_REVIEW", "promotion_authorized": False}
    if policy.get("continuity_required") is not True:
        return {"state": "NO_EMERGENCY_AUTOMATION_REQUIRED", "action": "MANUAL_OR_NORMAL_FAILURE", "promotion_authorized": False}
    if state in {"DEGRADED", "FAILED"} and health.get("hysteresis") != "PASS":
        return {"state": "OBSERVE_CONTINUE", "action": "NONE", "promotion_authorized": False}

    mode = policy.get("operation_mode", "STATELESS")
    if mode not in {"STATELESS", "READ_ONLY", "READ_WRITE_SINGLE_WRITER"}:
        raise StandaloneEmergencyError("unsupported operation_mode")

    blocks: list[str] = []
    if not isinstance(candidate, dict):
        blocks.append("NO_FALLBACK_CANDIDATE")
    else:
        if not _text(candidate.get("candidate_id")):
            blocks.append("FALLBACK_IDENTITY_MISSING")
        if candidate.get("recovery_probe") != "PASS" or not _text(candidate.get("recovery_probe_ref")):
            blocks.append("EMERGENCY_FALLBACK_UNPROVEN")
        stale = candidate.get("recovery_probe_stale_after")
        if not _text(stale) or _time(stale, "recovery_probe_stale_after") <= at:
            blocks.append("EMERGENCY_FALLBACK_PROBE_STALE")
        if candidate.get("guardrail_compatibility") != "PASS" or not _text(candidate.get("guardrail_compatibility_ref")):
            blocks.append("EMERGENCY_GUARDRAIL_COMPATIBILITY_UNPROVEN")
        if policy.get("failure_domain_scope") == "MATERIAL":
            if candidate.get("failure_domain_independence") != "VERIFIED" or not _text(candidate.get("failure_domain_independence_ref")):
                blocks.append("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN")
        if mode == "READ_WRITE_SINGLE_WRITER":
            if emergency.get("primary_write_fence") != "PASS" or not _text(emergency.get("primary_write_fence_ref")):
                blocks.append("PRIMARY_WRITE_FENCE_UNPROVEN")

    blocks = sorted(set(blocks))
    if state == "DEGRADED":
        return {"state": "DEGRADED" if blocks else "STANDBY_PREPARED", "action": "PREPARE_STANDBY" if blocks else "NONE", "blocking_states": blocks, "promotion_authorized": False}
    if blocks:
        return {"state": "NO_VERIFIED_FALLBACK", "action": "FAIL_CLOSED_OR_DECLARED_DEGRADED", "blocking_states": blocks, "promotion_authorized": False}
    if authority.get("failover") != "AUTHORIZED":
        return {"state": "FAILOVER_NOT_AUTHORIZED_OR_ELIGIBLE", "action": "NONE", "promotion_authorized": False}
    return {
        "state": "FAILOVER_ELIGIBLE",
        "action": "EXTERNAL_FAILOVER",
        "candidate": candidate["candidate_id"],
        "temporary_occupant": True,
        "promotion_authorized": False,
        "automatic_failback_authorized": False,
    }
