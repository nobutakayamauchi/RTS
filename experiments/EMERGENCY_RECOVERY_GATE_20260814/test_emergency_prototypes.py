import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import standalone_prototype
import structural_prototype

spec = importlib.util.spec_from_file_location("ultimate_loop_lifecycle", ROOT / "thin-rts" / "ultimate-loop" / "lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(lifecycle)

AT = datetime(2026, 8, 13, 19, 7, tzinfo=timezone.utc)


def base_case():
    return {
        "frame_id": "frame-critical-api",
        "current_state": "STABLE",
        "material_durable": True,
        "authority": {"promote": "BLOCKED", "failover": "AUTHORIZED"},
        "policy": {"observe_delta_pct": 5, "meteor_delta_pct": 15, "full_replace_delta_pct": 30},
        "recovery": {"backup_present": True, "fresh_restore_test": "PASS", "canonical_material": "PASS", "succession_packet": "PASS", "phoenix_test": "PASS"},
        "candidate": {
            "candidate_id": "fallback-b", "performance_delta_pct": 0, "replacement_value": "UNKNOWN", "resilience_value": "HIGH",
            "stability_state": "SURVIVED", "same_frozen_workload": "PASS", "recovery_probe": "PASS",
            "recovery_probe_ref": "probe:fallback-b", "recovery_probe_stale_after": "2026-08-14T06:00:00+09:00",
            "migration_state": "PASS", "rollback_state": "PASS", "failure_domain_independence": "VERIFIED",
            "failure_domain_independence_ref": "evidence:independent-provider-account", "guardrail_compatibility": "PASS",
            "guardrail_compatibility_ref": "evidence:security-privacy-compatible",
        },
        "emergency": {
            "policy": {"continuity_required": True, "failure_domain_scope": "MATERIAL", "operation_mode": "STATELESS"},
            "health": {"state": "FAILED", "hysteresis": "PASS", "source_ref": "health:primary", "observed_at": "2026-08-14T04:05:00+09:00", "stale_after": "2026-08-14T06:00:00+09:00"},
        },
    }


def valid_recovery():
    return {"applied": True, "applied_at": "2026-08-14T04:06:00+09:00", "executor_evidence_ref": "executor:failover-1", "failback_requested": False}


def recovery_validator(_):
    return {
        "state": "DEPLOYMENT_VALIDATED",
        "stable_eligible": True,
        "post_deployment_binding": ["obs:new", "expect:new", "session:new"],
        "validated_candidate_id": "fallback-b",
        "validated_at": "2026-08-14T04:06:30+09:00",
    }


class ExistingOnlyAttack(unittest.TestCase):
    def test_existing_degradation_meteor_signal_is_overridden_by_standby_disposition(self):
        case = base_case(); case.pop("emergency")
        case["trigger"] = {"type": "PROVIDER_DEGRADATION", "evidence_state": "CURRENT_OBSERVED", "source_ref": "health:degraded", "stale_after": "2026-08-14T06:00:00+09:00", "materiality": "MATERIAL"}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "METEOR")
        self.assertEqual(report["candidate_disposition"], "STANDBY")
        self.assertEqual(report["next_state"], "STANDBY")

    def test_existing_lifecycle_can_already_gate_authorized_emergency_failover(self):
        case = base_case(); case.pop("emergency")
        case["trigger"] = {"type": "PRIMARY_UNAVAILABLE", "evidence_state": "CURRENT_OBSERVED", "source_ref": "health:failed", "stale_after": "2026-08-14T06:00:00+09:00", "materiality": "MATERIAL", "failure_domain_scope": "MATERIAL"}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "EMERGENCY_FAILOVER_ELIGIBLE")
        self.assertEqual(report["next_state"], "RECOVERY")


class StructuralPrototypeTests(unittest.TestCase):
    def run_case(self, case, validator=None):
        return structural_prototype.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate, recovery_validator=validator)

    def test_degraded_prepares_without_failover(self):
        case = base_case(); case["emergency"]["health"]["state"] = "DEGRADED"
        self.assertEqual(self.run_case(case)["state"], "STANDBY_PREPARED")

    def test_hysteresis_blocks_flapping_failure(self):
        case = base_case(); case["emergency"]["health"]["hysteresis"] = "NOT_PASS"
        self.assertEqual(self.run_case(case)["state"], "OBSERVE_CONTINUE")

    def test_unknown_health_does_not_guess_failover(self):
        case = base_case(); case["emergency"]["health"]["state"] = "UNKNOWN"
        self.assertEqual(self.run_case(case)["state"], "HEALTH_UNKNOWN")

    def test_stale_standby_probe_blocks(self):
        case = base_case(); case["candidate"]["recovery_probe_stale_after"] = "2026-08-14T03:00:00+09:00"
        self.assertIn("EMERGENCY_FALLBACK_PROBE_STALE", self.run_case(case)["blocking_states"])

    def test_fallback_identity_is_required(self):
        case = base_case(); case["candidate"]["candidate_id"] = ""
        self.assertIn("FALLBACK_IDENTITY_MISSING", self.run_case(case)["blocking_states"])

    def test_failure_domain_needs_evidence_not_label(self):
        case = base_case(); case["candidate"]["failure_domain_independence_ref"] = ""
        self.assertIn("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN", self.run_case(case)["blocking_states"])

    def test_guardrail_compatibility_is_hard(self):
        case = base_case(); case["candidate"]["guardrail_compatibility"] = "UNKNOWN"
        self.assertIn("EMERGENCY_GUARDRAIL_COMPATIBILITY_UNPROVEN", self.run_case(case)["blocking_states"])

    def test_single_writer_requires_write_fence(self):
        case = base_case(); case["emergency"]["policy"]["operation_mode"] = "READ_WRITE_SINGLE_WRITER"
        self.assertIn("PRIMARY_WRITE_FENCE_UNPROVEN", self.run_case(case)["blocking_states"])

    def test_authority_still_owned_by_existing_lifecycle(self):
        case = base_case(); case["authority"]["failover"] = "BLOCKED"
        self.assertEqual(self.run_case(case)["state"], "FAILOVER_NOT_AUTHORIZED_OR_ELIGIBLE")

    def test_failed_primary_becomes_external_failover_eligible_only(self):
        report = self.run_case(base_case())
        self.assertEqual(report["state"], "FAILOVER_ELIGIBLE")
        self.assertEqual(report["action"], "EXTERNAL_FAILOVER")
        self.assertFalse(report["promotion_authorized"])

    def test_recovery_requires_post_deploy_reality_validation(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        self.assertEqual(self.run_case(case)["state"], "RECOVERY_VALIDATION_REQUIRED")

    def test_malformed_recovery_time_is_rejected(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery(); case["emergency"]["recovery"]["applied_at"] = "not-a-time"
        with self.assertRaises(ValueError): self.run_case(case, recovery_validator)

    def test_future_recovery_time_is_rejected(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery(); case["emergency"]["recovery"]["applied_at"] = "2026-08-14T05:00:00+09:00"
        with self.assertRaises(ValueError): self.run_case(case, recovery_validator)

    def test_validated_recovery_is_temporary_and_opens_debt(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        report = self.run_case(case, recovery_validator)
        self.assertEqual(report["state"], "TEMPORARY_RECOVERY_VALIDATED")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["automatic_failback_authorized"])
        self.assertIn("METEOR_DARWIN", report["recovery_debt"])

    def test_automatic_failback_is_blocked(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery(); case["emergency"]["recovery"]["failback_requested"] = True
        self.assertEqual(self.run_case(case, recovery_validator)["state"], "FAILBACK_BLOCKED_PENDING_DARWIN")


class NewBuildCounterPrototypeTests(unittest.TestCase):
    def test_standalone_matches_structural_on_core_cases(self):
        variants = [base_case()]
        x = base_case(); x["emergency"]["health"]["state"] = "DEGRADED"; variants.append(x)
        x = base_case(); x["emergency"]["health"]["state"] = "UNKNOWN"; variants.append(x)
        x = base_case(); x["candidate"]["failure_domain_independence_ref"] = ""; variants.append(x)
        for case in variants:
            structural = structural_prototype.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate)
            standalone = standalone_prototype.evaluate(case, AT)
            self.assertEqual(standalone["state"], structural["state"])

    def test_standalone_recovery_remains_temporary(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        report = standalone_prototype.evaluate(case, AT, recovery_validator=recovery_validator)
        self.assertEqual(report["state"], "TEMPORARY_RECOVERY_VALIDATED")
        self.assertFalse(report["promotion_authorized"])

    def test_standalone_rejects_malformed_recovery_time_too(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery(); case["emergency"]["recovery"]["applied_at"] = "bad"
        with self.assertRaises(ValueError): standalone_prototype.evaluate(case, AT, recovery_validator=recovery_validator)


if __name__ == "__main__":
    unittest.main()
