from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import integrity

VALID_STATES = {
    "BUILD",
    "STABLE",
    "WATCH",
    "METEOR",
    "SHADOW",
    "STANDBY",
    "PARTIAL",
    "EMERGENCY",
    "RECOVERY",
    "RECONSTRUCTION",
}

TRIGGER_ACTIONS = {
    "SERVICE_EOL": "EMERGENCY",
    "PRIMARY_UNAVAILABLE": "EMERGENCY",
    "CRITICAL_SECURITY": "EMERGENCY",
    "DEPENDENCY_FAILURE": "EMERGENCY",
    "UNKNOWN_EVENT": "INNER_LOOP_REOPEN",
    "NEW_CAPABILITY": "MATERIALITY",
    "PERFORMANCE_JUMP": "MATERIALITY",
    "PRICE_CHANGE": "MATERIALITY",
    "PROVIDER_DEGRADATION": "MATERIALITY",
    "SECURITY_IMPROVEMENT": "MATERIALITY",
    "NEW_REAL_FAILURE": "MATERIALITY",
}

DEFAULT_POLICY = {
    "observe_delta_pct": 5.0,
    "meteor_delta_pct": 15.0,
    "full_replace_delta_pct": 30.0,
}

VALID_INTEGRITY_APPLICABILITY = {"REQUIRED", "NOT_APPLICABLE"}


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _authorized(authority: dict[str, Any], key: str) -> bool:
    return authority.get(key) == "AUTHORIZED"


def _pass_or_na(value: Any) -> bool:
    return value in {"PASS", "NOT_APPLICABLE"}


def _policy(case: dict[str, Any]) -> dict[str, float]:
    supplied = case.get("policy") or {}
    merged = dict(DEFAULT_POLICY)
    for key in merged:
        if key in supplied:
            merged[key] = float(supplied[key])
    if not (0 <= merged["observe_delta_pct"] <= merged["meteor_delta_pct"] <= merged["full_replace_delta_pct"]):
        raise ValueError("policy thresholds must be ordered: observe <= meteor <= full_replace")
    return merged


def _trigger_action(case: dict[str, Any], at: datetime, blocks: list[str], reasons: list[str]) -> str:
    trigger = case.get("trigger")
    if not trigger:
        return "NONE"

    trigger_type = trigger.get("type")
    if trigger_type not in TRIGGER_ACTIONS:
        blocks.append("UNKNOWN_TRIGGER_TYPE")
        reasons.append("Unknown trigger types cannot silently change lifecycle state.")
        return "INNER_LOOP_REOPEN"

    if trigger.get("evidence_state") != "CURRENT_OBSERVED" or not trigger.get("source_ref"):
        blocks.append("TRIGGER_EVIDENCE_NOT_CURRENT")
        reasons.append("A lifecycle trigger requires current observed evidence and a source reference.")
        return "NONE"

    stale_after = trigger.get("stale_after")
    if stale_after and _parse_time(stale_after) <= at:
        blocks.append("TRIGGER_EVIDENCE_STALE")
        reasons.append("Stale discovery evidence cannot open METEOR or authorize emergency migration.")
        return "NONE"

    action = TRIGGER_ACTIONS[trigger_type]
    if action == "MATERIALITY":
        if trigger.get("materiality") == "MATERIAL":
            return "METEOR"
        return "OBSERVE"
    return action


def _recovery_state(case: dict[str, Any], blocks: list[str], reasons: list[str]) -> str:
    recovery = case.get("recovery")
    if not recovery:
        return "NOT_ASSESSED"

    backup = recovery.get("backup_present") is True
    restore = recovery.get("fresh_restore_test") == "PASS"
    canonical = recovery.get("canonical_material") == "PASS"
    succession = recovery.get("succession_packet") == "PASS"
    phoenix = recovery.get("phoenix_test") == "PASS"

    if backup and not restore:
        blocks.append("BACKUP_NOT_RECOVERY")
        reasons.append("Backup existence does not establish recoverability without a fresh restore test.")
        return "UNKNOWN_OR_BLOCKED"

    if restore and not canonical:
        blocks.append("RESTORE_WITHOUT_CANONICAL_MATERIAL")
        reasons.append("A restore that cannot establish canonical protected material is insufficient.")
        return "UNKNOWN_OR_BLOCKED"

    if restore and canonical:
        if succession and phoenix:
            return "PHOENIX_READY"
        if succession and not phoenix:
            blocks.append("SUCCESSION_WITHOUT_PHOENIX_TEST")
            reasons.append("A Succession Packet alone is not creator-independent regeneration proof.")
            return "RECOVERABLE"
        return "RECOVERABLE"

    return "NOT_PROVEN"


def _candidate_disposition(
    case: dict[str, Any],
    watch_action: str,
    recovery_state: str,
    blocks: list[str],
    reasons: list[str],
) -> tuple[str, bool]:
    candidate = case.get("candidate")
    if not candidate:
        return "NONE", False

    if watch_action == "INNER_LOOP_REOPEN":
        reasons.append("Candidate comparison is suspended until the unknown trigger is re-modeled by the inner loop.")
        return "BLOCKED_PENDING_INNER_REVIEW", False
    if case.get("trigger") and watch_action == "NONE" and any(
        block in blocks for block in {"TRIGGER_EVIDENCE_NOT_CURRENT", "TRIGGER_EVIDENCE_STALE"}
    ):
        reasons.append("Candidate comparison is suspended because the trigger evidence is not usable.")
        return "BLOCKED_BY_TRIGGER_EVIDENCE", False

    policy = _policy(case)
    authority = case.get("authority") or {}
    delta = float(candidate.get("performance_delta_pct", 0.0))
    replacement_value = candidate.get("replacement_value", "UNKNOWN")
    resilience_value = candidate.get("resilience_value", "UNKNOWN")
    stability = candidate.get("stability_state")
    same_workload = candidate.get("same_frozen_workload")
    recovery_probe = candidate.get("recovery_probe")
    migration = candidate.get("migration_state", "NOT_APPLICABLE")
    rollback = candidate.get("rollback_state", "NOT_APPLICABLE")
    independence = candidate.get("failure_domain_independence", "NOT_DECLARED")

    if watch_action == "EMERGENCY":
        if recovery_probe != "PASS":
            blocks.append("EMERGENCY_FALLBACK_UNPROVEN")
            reasons.append("Emergency fallback must have a successful bounded recovery/failover probe.")
            return "REJECTED_FOR_EMERGENCY", False
        if case.get("trigger", {}).get("failure_domain_scope") == "MATERIAL" and independence != "VERIFIED":
            blocks.append("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN")
            reasons.append("A fallback cannot claim resilience against the same failure domain without evidence of independence.")
            return "REJECTED_FOR_EMERGENCY", False
        if not _authorized(authority, "failover"):
            blocks.append("FAILOVER_AUTHORITY_BLOCKED")
            reasons.append("A technically suitable emergency fallback does not create failover authority.")
            return "STANDBY", False
        return "EMERGENCY_FAILOVER_ELIGIBLE", True

    full_evidence = (
        stability == "SURVIVED"
        and same_workload == "PASS"
        and _pass_or_na(migration)
        and _pass_or_na(rollback)
    )

    if full_evidence:
        material_replace = replacement_value == "MATERIAL_WIN" or delta >= policy["full_replace_delta_pct"]
        material_partial = replacement_value in {"MATERIAL_WIN", "PARTIAL_WIN"} or delta >= policy["meteor_delta_pct"]

        if material_replace:
            if not _authorized(authority, "promote"):
                blocks.append("PROMOTION_AUTHORITY_BLOCKED")
                reasons.append("A winning challenger does not authorize its own promotion.")
                return "FULL_REPLACEMENT_READY_AUTHORITY_BLOCKED", False
            return "FULL_REPLACEMENT_ELIGIBLE", True

        if material_partial:
            if not _authorized(authority, "promote"):
                blocks.append("PROMOTION_AUTHORITY_BLOCKED")
                reasons.append("Partial replacement still requires explicit promotion authority.")
                return "PARTIAL_REPLACEMENT_READY_AUTHORITY_BLOCKED", False
            return "PARTIAL_REPLACEMENT_ELIGIBLE", True

        if resilience_value == "HIGH" and recovery_probe == "PASS":
            reasons.append("Replacement gain is small, but the candidate has independent resilience value.")
            return "STANDBY", False

        return "INCUMBENT_SURVIVES", False

    if resilience_value == "HIGH" and recovery_probe == "PASS":
        reasons.append("Candidate is not promotion-ready but is useful as a bounded fallback.")
        return "STANDBY", False

    if delta >= policy["observe_delta_pct"] or replacement_value in {"MATERIAL_WIN", "PARTIAL_WIN"}:
        reasons.append("Candidate requires shadow/same-workload evidence before any replacement decision.")
        return "SHADOW", False

    return "CANDIDATE", False


def evaluate(case: dict[str, Any], at: datetime) -> dict[str, Any]:
    blocks: list[str] = []
    reasons: list[str] = []

    frame_id = case.get("frame_id")
    if not frame_id:
        blocks.append("FRAME_ID_MISSING")

    current_state = case.get("current_state")
    if current_state not in VALID_STATES:
        blocks.append("INVALID_CURRENT_STATE")

    applicability = case.get("integrity_applicability", "UNDECLARED")
    integrity_profile = case.get("integrity")
    if applicability not in VALID_INTEGRITY_APPLICABILITY | {"UNDECLARED"}:
        blocks.append("INVALID_INTEGRITY_APPLICABILITY")
        reasons.append("Integrity applicability must be REQUIRED or NOT_APPLICABLE before a consequential transition.")
    if applicability == "REQUIRED" and integrity_profile is None:
        blocks.append("REQUIRED_INTEGRITY_PROFILE_MISSING")
        reasons.append("A workload that declares integrity REQUIRED must bind the applicable integrity evidence instead of omitting the profile.")

    integrity_report = integrity.evaluate(integrity_profile)
    blocks.extend(integrity_report["blocking_states"])
    reasons.extend(integrity_report["reasons"])
    integrity_blocked = integrity_report["classification"] != "PASS" or "REQUIRED_INTEGRITY_PROFILE_MISSING" in blocks or "INVALID_INTEGRITY_APPLICABILITY" in blocks

    watch_action = _trigger_action(case, at, blocks, reasons)
    recovery_state = _recovery_state(case, blocks, reasons)
    disposition, transition_authorized = _candidate_disposition(
        case, watch_action, recovery_state, blocks, reasons
    )

    authority = case.get("authority") or {}
    core_transition_ready = (
        current_state == "BUILD"
        and case.get("core_acceptance") == "PASS"
        and _authorized(authority, "promote")
        and not (case.get("material_durable") is True and recovery_state not in {"RECOVERABLE", "PHOENIX_READY"})
    )
    consequential_transition_ready = transition_authorized or core_transition_ready

    if consequential_transition_ready and applicability == "UNDECLARED":
        blocks.append("INTEGRITY_APPLICABILITY_UNDECLARED")
        reasons.append("A consequential transition cannot treat missing integrity applicability as NOT_APPLICABLE. Declare REQUIRED or NOT_APPLICABLE explicitly.")
        integrity_blocked = True

    if integrity_report["reentry_route"] == "ANALYSIS_REOPEN" and case.get("candidate"):
        disposition = "BLOCKED_PENDING_INTEGRITY_REVIEW"
        transition_authorized = False
    elif integrity_blocked and transition_authorized:
        disposition = "INTEGRITY_BLOCKED"
        transition_authorized = False
        reasons.append("A technically eligible transition cannot proceed while applicable evidence, freshness, Human Gate integrity, or applicability binding is blocked.")

    next_state = current_state if current_state in VALID_STATES else "BUILD"

    if integrity_report["reentry_route"] == "ANALYSIS_REOPEN":
        next_state = "BUILD"
    elif current_state == "BUILD":
        if case.get("core_acceptance") == "PASS":
            if case.get("material_durable") is True and recovery_state not in {"RECOVERABLE", "PHOENIX_READY"}:
                blocks.append("DURABLE_CORE_RECOVERY_NOT_PROVEN")
                reasons.append("A materially durable core cannot freeze while recovery remains unproven.")
            elif integrity_blocked:
                reasons.append("Core acceptance cannot freeze a durable state while applicable integrity or applicability evidence is blocked.")
            elif _authorized(authority, "promote"):
                next_state = "STABLE"
            else:
                blocks.append("CORE_PROMOTION_AUTHORITY_BLOCKED")
                reasons.append("CORE COMPLETE evidence is not promotion authority.")
    elif watch_action == "METEOR":
        next_state = "METEOR"
    elif watch_action == "EMERGENCY":
        next_state = "EMERGENCY"
    elif watch_action == "INNER_LOOP_REOPEN":
        next_state = "BUILD"
    elif watch_action == "OBSERVE":
        next_state = "WATCH"

    if disposition == "SHADOW":
        next_state = "SHADOW"
    elif disposition == "STANDBY":
        next_state = "STANDBY"
    elif disposition == "PARTIAL_REPLACEMENT_ELIGIBLE" and transition_authorized:
        next_state = "PARTIAL"
    elif disposition == "FULL_REPLACEMENT_ELIGIBLE" and transition_authorized:
        next_state = "STABLE"
    elif disposition == "EMERGENCY_FAILOVER_ELIGIBLE" and transition_authorized:
        next_state = "RECOVERY"

    classification = "PASS" if not blocks else "UNKNOWN_OR_BLOCKED"

    return {
        "schema": "ultimate-loop-lifecycle-report/v0",
        "frame_id": frame_id,
        "evaluated_at": at.isoformat().replace("+00:00", "Z"),
        "classification": classification,
        "current_state": current_state,
        "next_state": next_state,
        "watch_action": watch_action,
        "candidate_disposition": disposition,
        "transition_authorized": transition_authorized,
        "recovery_state": recovery_state,
        "integrity_applicability_state": applicability,
        "reentry_route": integrity_report["reentry_route"],
        "evidence_integrity_state": integrity_report["evidence_state"],
        "derived_artifact_freshness_state": integrity_report["freshness_state"],
        "human_gate_integrity_state": integrity_report["human_gate_state"],
        "decision_succession_state": integrity_report["decision_succession_state"],
        "decision_succession_blocking_states": integrity_report["decision_succession_blocking_states"],
        "blocking_states": sorted(set(blocks)),
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate bounded Ultimate Loop lifecycle state")
    parser.add_argument("case", type=Path)
    parser.add_argument("--at", required=True)
    args = parser.parse_args()

    case = json.loads(args.case.read_text(encoding="utf-8"))
    report = evaluate(case, _parse_time(args.at))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["classification"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
