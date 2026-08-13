from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def _time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(timezone.utc)


def evaluate(case: dict[str, Any], at: datetime, *, lifecycle_evaluator: Callable[[dict[str, Any], datetime], dict[str, Any]]) -> dict[str, Any]:
    """Reference for existing RTS plus bounded human runbook composition."""
    manual = case.get("manual") or {}
    emergency = case.get("emergency") or {}
    health = emergency.get("health") or {}
    if manual.get("operator_available") is not True:
        return {"state": "MANUAL_UNAVAILABLE", "survives": False}
    if manual.get("runbook_current") is not True:
        return {"state": "MANUAL_RUNBOOK_STALE", "survives": False}
    if manual.get("rto_satisfied") is not True:
        return {"state": "MANUAL_RTO_FAIL", "survives": False}
    if not health.get("source_ref") or not health.get("observed_at") or not health.get("stale_after"):
        return {"state": "MANUAL_EVIDENCE_INCOMPLETE", "survives": False}
    if _time(health["observed_at"]) > at or _time(health["stale_after"]) <= at:
        return {"state": "MANUAL_HEALTH_EVIDENCE_STALE", "survives": False}
    candidate = case.get("candidate") or {}
    if not candidate.get("candidate_id"):
        return {"state": "MANUAL_FALLBACK_IDENTITY_MISSING", "survives": False}
    if candidate.get("recovery_probe") != "PASS" or not candidate.get("recovery_probe_ref"):
        return {"state": "MANUAL_FALLBACK_UNPROVEN", "survives": False}
    if candidate.get("guardrail_compatibility") != "PASS" or not candidate.get("guardrail_compatibility_ref"):
        return {"state": "MANUAL_GUARDRAIL_UNPROVEN", "survives": False}
    policy = emergency.get("policy") or {}
    if policy.get("failure_domain_scope") == "MATERIAL" and (
        candidate.get("failure_domain_independence") != "VERIFIED" or not candidate.get("failure_domain_independence_ref")
    ):
        return {"state": "MANUAL_INDEPENDENCE_UNPROVEN", "survives": False}
    if policy.get("operation_mode") == "READ_WRITE_SINGLE_WRITER" and (
        emergency.get("primary_write_fence") != "PASS" or not emergency.get("primary_write_fence_ref")
    ):
        return {"state": "MANUAL_WRITE_FENCE_UNPROVEN", "survives": False}

    bound = dict(case)
    bound["trigger"] = {
        "type": "CRITICAL_SECURITY" if health.get("state") == "UNSAFE" else "PRIMARY_UNAVAILABLE",
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
        "promotion_authorized": False,
        "automatic_failback_authorized": False,
    }
