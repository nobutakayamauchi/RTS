import copy
import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


emergency = load("ultimate_loop_emergency", HERE / "emergency.py")
lifecycle = load("ultimate_loop_lifecycle", HERE / "lifecycle.py")
AT = datetime(2026, 8, 13, 19, 7, tzinfo=timezone.utc)


def case():
    return {
        "frame_id": "frame-critical-api",
        "current_state": "STABLE",
        "authority": {"promote": "BLOCKED", "failover": "AUTHORIZED"},
        "candidate": {
            "candidate_id": "fallback-b",
            "performance_delta_pct": 0,
            "replacement_value": "UNKNOWN",
            "resilience_value": "HIGH",
            "stability_state": "SURVIVED",
            "same_frozen_workload": "PASS",
            "recovery_probe": "PASS",
            "recovery_probe_ref": "probe:fallback-b",
            "recovery_probe_stale_after": "2026-08-14T06:00:00+09:00",
            "migration_state": "PASS",
            "rollback_state": "PASS",
            "failure_domain_independence": "VERIFIED",
            "failure_domain_independence_ref": "evidence:independent-provider-account",
            "guardrail_compatibility": "PASS",
            "guardrail_compatibility_ref": "evidence:security-privacy-compatible",
        },
        "emergency": {
            "policy": {"continuity_required": True, "failure_domain_scope": "MATERIAL", "operation_mode": "STATELESS"},
            "health": {
                "state": "FAILED",
                "hysteresis": "PASS",
                "source_ref": "health:primary",
                "observed_at": "2026-08-14T04:05:00+09:00",
                "stale_after": "2026-08-14T06:00:00+09:00",
            },
        },
    }


def recovery():
    return {
        "applied": True,
        "applied_at": "2026-08-14T04:06:00+09:00",
        "executor_evidence_ref": "executor:failover-1",
        "candidate_id": "fallback-b",
        "trigger_state": "FAILED",
        "trigger_source_ref": "health:primary",
        "trigger_observed_at": "2026-08-14T04:05:00+09:00",
        "failover_authority_ref": "authority:failover-approved",
        "failback_requested": False,
    }


def validator(candidate="fallback-b", when="2026-08-14T04:06:30+09:00"):
    def run(_):
        return {
            "state": "DEPLOYMENT_VALIDATED",
            "stable_eligible": True,
            "post_deployment_binding": ["obs:new", "expect:new", "session:new"],
            "validated_candidate_id": candidate,
            "validated_at": when,
        }
    return run


def evaluate(value, recovery_validator=None):
    return emergency.evaluate(value, AT, lifecycle_evaluator=lifecycle.evaluate, recovery_validator=recovery_validator)


class EmergencyGateTests(unittest.TestCase):
    def test_failed_primary_is_external_failover_eligible_only(self):
        result = evaluate(case())
        self.assertEqual(result["state"], "FAILOVER_ELIGIBLE")
        self.assertEqual(result["action"], "EXTERNAL_FAILOVER")
        self.assertFalse(result["promotion_authorized"])

    def test_degraded_prepares_standby(self):
        value = case(); value["emergency"]["health"]["state"] = "DEGRADED"
        self.assertEqual(evaluate(value)["state"], "STANDBY_PREPARED")

    def test_flapping_failure_does_not_failover(self):
        value = case(); value["emergency"]["health"]["hysteresis"] = "NOT_PASS"
        self.assertEqual(evaluate(value)["state"], "OBSERVE_CONTINUE")

    def test_unknown_health_does_not_guess(self):
        value = case(); value["emergency"]["health"]["state"] = "UNKNOWN"
        self.assertEqual(evaluate(value)["state"], "HEALTH_UNKNOWN")

    def test_stale_fallback_probe_blocks(self):
        value = case(); value["candidate"]["recovery_probe_stale_after"] = "2026-08-14T03:00:00+09:00"
        self.assertIn("EMERGENCY_FALLBACK_PROBE_STALE", evaluate(value)["blocking_states"])

    def test_missing_guardrail_blocks(self):
        value = case(); value["candidate"]["guardrail_compatibility_ref"] = ""
        self.assertIn("EMERGENCY_GUARDRAIL_COMPATIBILITY_UNPROVEN", evaluate(value)["blocking_states"])

    def test_independence_label_without_evidence_blocks(self):
        value = case(); value["candidate"]["failure_domain_independence_ref"] = ""
        self.assertIn("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN", evaluate(value)["blocking_states"])

    def test_single_writer_without_fence_blocks(self):
        value = case(); value["emergency"]["policy"]["operation_mode"] = "READ_WRITE_SINGLE_WRITER"
        self.assertIn("PRIMARY_WRITE_FENCE_UNPROVEN", evaluate(value)["blocking_states"])

    def test_unknown_operation_mode_fails_closed(self):
        value = case(); value["emergency"]["policy"]["operation_mode"] = "READ_WRITE_SINGLE_WRTER"
        with self.assertRaises(ValueError): evaluate(value)

    def test_failover_authority_is_not_created(self):
        value = case(); value["authority"]["failover"] = "BLOCKED"
        self.assertEqual(evaluate(value)["state"], "FAILOVER_NOT_AUTHORIZED_OR_ELIGIBLE")

    def test_applied_failover_requires_reality_validation(self):
        value = case(); value["emergency"]["recovery"] = recovery()
        self.assertEqual(evaluate(value)["state"], "RECOVERY_VALIDATION_REQUIRED")

    def test_wrong_fallback_reality_validation_is_rejected(self):
        value = case(); value["emergency"]["recovery"] = recovery()
        self.assertEqual(evaluate(value, validator("other"))["state"], "RECOVERY_NOT_VALIDATED")

    def test_validation_before_failover_is_rejected(self):
        value = case(); value["emergency"]["recovery"] = recovery()
        self.assertEqual(evaluate(value, validator(when="2026-08-14T04:05:30+09:00"))["state"], "RECOVERY_NOT_VALIDATED")

    def test_new_primary_sample_does_not_invalidate_applied_recovery(self):
        value = case(); value["emergency"]["recovery"] = recovery()
        value["emergency"]["health"]["observed_at"] = "2026-08-14T04:07:00+09:00"
        self.assertEqual(evaluate(value, validator())["state"], "TEMPORARY_RECOVERY_VALIDATED")

    def test_healthy_primary_does_not_auto_failback(self):
        value = case(); value["emergency"]["recovery"] = recovery()
        value["emergency"]["health"]["state"] = "HEALTHY"
        value["emergency"]["health"]["observed_at"] = "2026-08-14T04:07:00+09:00"
        result = evaluate(value, validator())
        self.assertEqual(result["state"], "TEMPORARY_RECOVERY_VALIDATED")
        self.assertFalse(result["automatic_failback_authorized"])

    def test_explicit_failback_still_waits_for_darwin(self):
        value = case(); value["emergency"]["recovery"] = recovery(); value["emergency"]["recovery"]["failback_requested"] = True
        self.assertEqual(evaluate(value, validator())["state"], "FAILBACK_BLOCKED_PENDING_DARWIN")

    def test_valid_recovery_keeps_debt(self):
        value = case(); value["emergency"]["recovery"] = recovery()
        result = evaluate(value, validator())
        self.assertEqual(result["state"], "TEMPORARY_RECOVERY_VALIDATED")
        self.assertEqual(set(result["recovery_debt"]), {"DISCOVERY_REFRESH", "ROOT_CAUSE_REVIEW", "METEOR_DARWIN", "PERMANENT_OCCUPANT_DECISION"})


if __name__ == "__main__":
    unittest.main()
