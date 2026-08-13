from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError("exact timestamp required")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(timezone.utc)


def evaluate(case: dict[str, Any], at: datetime, *, lifecycle_evaluator: Callable[[dict[str, Any], datetime], dict[str, Any]]) -> dict[str, Any]:
    """Reference for existing RTS plus bounded human runbook composition.

    This models the governance evidence a qualified operator must check. It does
    not implement monitoring or failover actuation.
    """
    manual = case.get("manual") or {}
    emergency = case.get("emergency") or {}
    health = emergency.get("health") or {}
    policy = emergency.get("policy") or {}

    if manual.get("operator_available") is not True:
        return {"state": "MANUAL_UNAVAILABLE", "survives": False}
    if manual.get("runbook_current") is not True:
        return {"state": "MANUAL_RUNBOOK_STALE", "survives": False}
    if manual.get("rto_satisfied") is not True:
        return {"state": "MANUAL_RTO_FAIL", "survives": False}

    state = health.get("state")
    if state not in {"HEALTHY", "DEGRADED", "FAILED", "UNSAFE", "UNKNOWN"}:
        raise ValueError("invalid health state")
    if not health.get("source_ref") or not health.get("observed_at") or not health.get("stale_after"):
        return {"state": "MANUAL_EVIDENCE_INCOMPLETE", "survives": False}
    observed_at = _time(health["observed_at"])
    stale_at = _time(health["stale_after"])
    if observed_at > at or stale_at <= at or stale_at <= observed_at:
        return {"state": "MANUAL_HEALTH_EVIDENCE_STALE", "survives": False}

    # Manual composition is still subject to the same health-state semantics.
    if state == "HEALTHY":
        return {"state": "MANUAL_NO_FAILOVER_REQUIRED", "survives": True, "failover_eligible": False}
    if state == "UNKNOWN":
        return {"state": "MANUAL_HEALTH_UNKNOWN", "survives": True, "failover_eligible": False}
    if state in {"DEGRADED", "FAILED"} and health.get("hysteresis") != "PASS":
        return {"state": "MANUAL_OBSERVE_CONTINUE", "survives": True, "failover_eligible": False}
    if state == "DEGRADED":
        return {"state": "MANUAL_PREPARE_STANDBY", "survives": True, "failover_eligible": False}

    candidate = case.get("candidate") or {}
    if not candidate.get("candidate_id"):
        return {"state": "MANUAL_FALLBACK_IDENTITY_MISSING", "survives": False}
    if candidate.get("recovery_probe") != "PASS" or not candidate.get("recovery_probe_ref"):
        return {"state": "MANUAL_FALLBACK_UNPROVEN", "survives": False}
    probe_stale_after = candidate.get("recovery_probe_stale_after")
    if not probe_stale_after or _time(probe_stale_after) <= at:
        return {"state": "MANUAL_FALLBACK_PROBE_STALE", "survives": False}
    if candidate.get("guardrail_compatibility") != "PASS" or not candidate.get("guardrail_compatibility_ref"):
        return {"state": "MANUAL_GUARDRAIL_UNPROVEN", "survives": False}
    if policy.get("failure_domain_scope") == "MATERIAL" and (
        candidate.get("failure_domain_independence") != "VERIFIED" or not candidate.get("failure_domain_independence_ref")
    ):
        return {"state": "MANUAL_INDEPENDENCE_UNPROVEN", "survives": False}

    mode = policy.get("operation_mode", "STATELESS")
    if mode not in {"STATELESS", "READ_ONLY", "READ_WRITE_SINGLE_WRITER"}:
        raise ValueError("unsupported operation_mode")
    if mode == "READ_WRITE_SINGLE_WRITER" and (
        emergency.get("primary_write_fence") != "PASS" or not emergency.get("primary_write_fence_ref")
    ):
        return {"state": "MANUAL_WRITE_FENCE_UNPROVEN", "survives": False}

    bound = dict(case)
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
        return {"state": "MANUAL_NOT_AUTHORIZED_OR_ELIGIBLE", "survives": False, "base": base}
    return {
        "state": "MANUAL_FAILOVER_ELIGIBLE",
        "survives": True,
        "failover_eligible": True,
        "promotion_authorized": False,
        "automatic_failback_authorized": False,
    }
