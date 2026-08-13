from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Callable


class EmergencyPrototypeError(ValueError):
    pass


def _time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise EmergencyPrototypeError(f"{field} must be an exact ISO-8601 timestamp")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise EmergencyPrototypeError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise EmergencyPrototypeError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value


def _candidate_preflight(case: dict[str, Any], at: datetime) -> list[str]:
    candidate = case.get("candidate")
    emergency = case["emergency"]
    policy = emergency["policy"]
    blocks: list[str] = []
    if not isinstance(candidate, dict):
        return ["NO_FALLBACK_CANDIDATE"]
    if candidate.get("recovery_probe") != "PASS" or not _text(candidate.get("recovery_probe_ref")):
        blocks.append("EMERGENCY_FALLBACK_UNPROVEN")
    stale_after = candidate.get("recovery_probe_stale_after")
    if not _text(stale_after) or _time(stale_after, "recovery_probe_stale_after") <= at:
        blocks.append("EMERGENCY_FALLBACK_PROBE_STALE")
    if candidate.get("guardrail_compatibility") != "PASS" or not _text(candidate.get("guardrail_compatibility_ref")):
        blocks.append("EMERGENCY_GUARDRAIL_COMPATIBILITY_UNPROVEN")
    if policy.get("failure_domain_scope") == "MATERIAL":
        if candidate.get("failure_domain_independence") != "VERIFIED" or not _text(candidate.get("failure_domain_independence_ref")):
            blocks.append("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN")
    mode = policy.get("operation_mode", "STATELESS")
    if mode not in {"STATELESS", "READ_ONLY", "READ_WRITE_SINGLE_WRITER"}:
        raise EmergencyPrototypeError("unsupported operation_mode")
    if mode == "READ_WRITE_SINGLE_WRITER":
        if emergency.get("primary_write_fence") != "PASS" or not _text(emergency.get("primary_write_fence_ref")):
            blocks.append("PRIMARY_WRITE_FENCE_UNPROVEN")
    return sorted(set(blocks))


def evaluate(
    case: dict[str, Any],
    at: datetime,
    *,
    lifecycle_evaluator: Callable[[dict[str, Any], datetime], dict[str, Any]],
    recovery_validator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Prototype emergency layer extracted around the existing lifecycle binder.

    Monitoring, traffic switching, restart, secret handling and provider APIs remain external.
    The prototype only adds emergency-prep and temporary-recovery semantics that the existing
    lifecycle binder does not currently express.
    """
    if not isinstance(case, dict) or not isinstance(case.get("emergency"), dict):
        raise EmergencyPrototypeError("emergency case required")
    emergency = case["emergency"]
    policy = emergency.get("policy")
    health = emergency.get("health")
    if not isinstance(policy, dict) or not isinstance(health, dict):
        raise EmergencyPrototypeError("emergency policy/health required")
    state = health.get("state")
    if state not in {"HEALTHY", "DEGRADED", "FAILED", "UNSAFE", "UNKNOWN"}:
        raise EmergencyPrototypeError("invalid health state")
    if not _text(health.get("source_ref")) or not _text(health.get("stale_after")):
        raise EmergencyPrototypeError("current health evidence required")
    if _time(health["stale_after"], "health.stale_after") <= at:
        return {"state": "HEALTH_EVIDENCE_STALE", "action": "HUMAN_REVIEW", "promotion_authorized": False}

    if state == "HEALTHY":
        return {"state": "HEALTHY", "action": "NONE", "promotion_authorized": False}
    if state == "UNKNOWN":
        return {"state": "HEALTH_UNKNOWN", "action": "HUMAN_REVIEW", "promotion_authorized": False}
    if policy.get("continuity_required") is not True:
        return {"state": "NO_EMERGENCY_AUTOMATION_REQUIRED", "action": "MANUAL_OR_NORMAL_FAILURE", "promotion_authorized": False}
    if state in {"DEGRADED", "FAILED"} and health.get("hysteresis") != "PASS":
        return {"state": "OBSERVE_CONTINUE", "action": "NONE", "promotion_authorized": False}

    blocks = _candidate_preflight(case, at)
    if state == "DEGRADED":
        if blocks:
            return {"state": "DEGRADED", "action": "PREPARE_STANDBY", "blocking_states": blocks, "promotion_authorized": False}
        return {"state": "STANDBY_PREPARED", "action": "NONE", "promotion_authorized": False}

    if blocks:
        return {"state": "NO_VERIFIED_FALLBACK", "action": "FAIL_CLOSED_OR_DECLARED_DEGRADED", "blocking_states": blocks, "promotion_authorized": False}

    bound = copy.deepcopy(case)
    bound["trigger"] = {
        "type": "CRITICAL_SECURITY" if state == "UNSAFE" else "PRIMARY_UNAVAILABLE",
        "evidence_state": "CURRENT_OBSERVED",
        "source_ref": health["source_ref"],
        "stale_after": health["stale_after"],
        "materiality": "MATERIAL",
        "failure_domain_scope": policy.get("failure_domain_scope", "NOT_DECLARED"),
    }
    base = lifecycle_evaluator(bound, at)
    if base.get("candidate_disposition") != "EMERGENCY_FAILOVER_ELIGIBLE":
        return {
            "state": "FAILOVER_NOT_AUTHORIZED_OR_ELIGIBLE",
            "action": "NONE",
            "base_lifecycle": base,
            "promotion_authorized": False,
        }

    recovery = emergency.get("recovery")
    if not isinstance(recovery, dict) or recovery.get("applied") is not True:
        return {
            "state": "FAILOVER_ELIGIBLE",
            "action": "EXTERNAL_FAILOVER",
            "candidate": case["candidate"].get("candidate_id"),
            "temporary_occupant": True,
            "promotion_authorized": False,
            "automatic_failback_authorized": False,
        }
    if recovery.get("failback_requested") is True:
        return {
            "state": "FAILBACK_BLOCKED_PENDING_DARWIN",
            "action": "NONE",
            "temporary_occupant": True,
            "promotion_authorized": False,
            "automatic_failback_authorized": False,
        }
    if not _text(recovery.get("executor_evidence_ref")) or not _text(recovery.get("applied_at")):
        raise EmergencyPrototypeError("failover execution evidence required")
    if recovery_validator is None:
        return {
            "state": "RECOVERY_VALIDATION_REQUIRED",
            "action": "POST_DEPLOY_REALITY_GATE",
            "temporary_occupant": True,
            "promotion_authorized": False,
        }
    validation = recovery_validator(recovery)
    if (
        not isinstance(validation, dict)
        or validation.get("state") not in {"DEPLOYMENT_VALIDATED", "FIX_VALIDATED"}
        or validation.get("stable_eligible") is not True
        or not validation.get("post_deployment_binding")
    ):
        return {
            "state": "RECOVERY_NOT_VALIDATED",
            "action": "RETURN_TO_ANALYSIS",
            "temporary_occupant": True,
            "promotion_authorized": False,
        }
    return {
        "state": "TEMPORARY_RECOVERY_VALIDATED",
        "action": "CONTINUE_TEMPORARILY",
        "temporary_occupant": True,
        "promotion_authorized": False,
        "automatic_failback_authorized": False,
        "post_deployment_binding": validation["post_deployment_binding"],
        "recovery_debt": [
            "DISCOVERY_REFRESH",
            "ROOT_CAUSE_REVIEW",
            "METEOR_DARWIN",
            "PERMANENT_OCCUPANT_DECISION",
        ],
    }
