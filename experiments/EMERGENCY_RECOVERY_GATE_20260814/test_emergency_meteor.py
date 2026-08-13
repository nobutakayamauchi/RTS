import copy
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import manual_composition_reference
import standalone_prototype
import structural_prototype
from test_emergency_prototypes import base_case, valid_recovery

spec = importlib.util.spec_from_file_location("ultimate_loop_lifecycle", ROOT / "thin-rts" / "ultimate-loop" / "lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(lifecycle)

AT = datetime(2026, 8, 13, 19, 7, tzinfo=timezone.utc)


def bound_validator(candidate_id="fallback-b"):
    def _validate(_):
        return {
            "state": "DEPLOYMENT_VALIDATED",
            "stable_eligible": True,
            "post_deployment_binding": ["obs:new", "expect:new", "session:new"],
            "validated_candidate_id": candidate_id,
            "validated_at": "2026-08-14T04:06:30+09:00",
        }
    return _validate


def structural(case, validator=None):
    return structural_prototype.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate, recovery_validator=validator)


def standalone(case, validator=None):
    return standalone_prototype.evaluate(case, AT, recovery_validator=validator)


class ManualCompositionMeteor(unittest.TestCase):
    def manual_case(self):
        case = base_case()
        case["manual"] = {"operator_available": True, "runbook_current": True, "rto_satisfied": True}
        return case

    def test_manual_survives_when_workload_allows_it(self):
        report = manual_composition_reference.evaluate(self.manual_case(), AT, lifecycle_evaluator=lifecycle.evaluate)
        self.assertTrue(report["survives"])
        self.assertEqual(report["state"], "MANUAL_FAILOVER_ELIGIBLE")

    def test_manual_dies_when_operator_absent(self):
        case = self.manual_case(); case["manual"]["operator_available"] = False
        self.assertEqual(manual_composition_reference.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate)["state"], "MANUAL_UNAVAILABLE")

    def test_manual_dies_when_rto_cannot_be_met(self):
        case = self.manual_case(); case["manual"]["rto_satisfied"] = False
        self.assertEqual(manual_composition_reference.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate)["state"], "MANUAL_RTO_FAIL")

    def test_manual_dies_on_missing_guardrail_evidence(self):
        case = self.manual_case(); case["candidate"]["guardrail_compatibility_ref"] = ""
        self.assertEqual(manual_composition_reference.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate)["state"], "MANUAL_GUARDRAIL_UNPROVEN")


class SharedDeathCases(unittest.TestCase):
    def test_flapping_failed_state_does_not_failover(self):
        case = base_case(); case["emergency"]["health"]["hysteresis"] = "NOT_PASS"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "OBSERVE_CONTINUE")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "OBSERVE_CONTINUE")

    def test_unknown_health_never_guesses_failover(self):
        case = base_case(); case["emergency"]["health"]["state"] = "UNKNOWN"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "HEALTH_UNKNOWN")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "HEALTH_UNKNOWN")

    def test_degraded_only_prepares_standby(self):
        case = base_case(); case["emergency"]["health"]["state"] = "DEGRADED"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "STANDBY_PREPARED")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "STANDBY_PREPARED")

    def test_unsafe_bypasses_ordinary_hysteresis_but_not_authority(self):
        case = base_case(); case["emergency"]["health"]["state"] = "UNSAFE"; case["emergency"]["health"]["hysteresis"] = "NOT_PASS"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "FAILOVER_ELIGIBLE")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "FAILOVER_ELIGIBLE")

    def test_future_health_observation_rejected(self):
        case = base_case(); case["emergency"]["health"]["observed_at"] = "2026-08-14T05:00:00+09:00"
        with self.assertRaises(ValueError): structural(copy.deepcopy(case))
        with self.assertRaises(ValueError): standalone(copy.deepcopy(case))

    def test_stale_health_evidence_blocks(self):
        case = base_case(); case["emergency"]["health"]["stale_after"] = "2026-08-14T03:00:00+09:00"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "HEALTH_EVIDENCE_STALE")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "HEALTH_EVIDENCE_STALE")

    def test_missing_fallback_identity_blocks(self):
        case = base_case(); case["candidate"]["candidate_id"] = ""
        self.assertIn("FALLBACK_IDENTITY_MISSING", structural(copy.deepcopy(case))["blocking_states"])
        self.assertIn("FALLBACK_IDENTITY_MISSING", standalone(copy.deepcopy(case))["blocking_states"])

    def test_stale_fallback_probe_blocks(self):
        case = base_case(); case["candidate"]["recovery_probe_stale_after"] = "2026-08-14T03:00:00+09:00"
        self.assertIn("EMERGENCY_FALLBACK_PROBE_STALE", structural(copy.deepcopy(case))["blocking_states"])
        self.assertIn("EMERGENCY_FALLBACK_PROBE_STALE", standalone(copy.deepcopy(case))["blocking_states"])

    def test_independence_label_without_evidence_blocks(self):
        case = base_case(); case["candidate"]["failure_domain_independence_ref"] = ""
        self.assertIn("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN", structural(copy.deepcopy(case))["blocking_states"])
        self.assertIn("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN", standalone(copy.deepcopy(case))["blocking_states"])

    def test_guardrail_unknown_blocks(self):
        case = base_case(); case["candidate"]["guardrail_compatibility"] = "UNKNOWN"
        self.assertIn("EMERGENCY_GUARDRAIL_COMPATIBILITY_UNPROVEN", structural(copy.deepcopy(case))["blocking_states"])
        self.assertIn("EMERGENCY_GUARDRAIL_COMPATIBILITY_UNPROVEN", standalone(copy.deepcopy(case))["blocking_states"])

    def test_single_writer_without_fence_blocks(self):
        case = base_case(); case["emergency"]["policy"]["operation_mode"] = "READ_WRITE_SINGLE_WRITER"
        self.assertIn("PRIMARY_WRITE_FENCE_UNPROVEN", structural(copy.deepcopy(case))["blocking_states"])
        self.assertIn("PRIMARY_WRITE_FENCE_UNPROVEN", standalone(copy.deepcopy(case))["blocking_states"])

    def test_missing_failover_authority_blocks(self):
        case = base_case(); case["authority"]["failover"] = "BLOCKED"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "FAILOVER_NOT_AUTHORIZED_OR_ELIGIBLE")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "FAILOVER_NOT_AUTHORIZED_OR_ELIGIBLE")

    def test_failover_is_external_not_internal_actuation(self):
        case = base_case()
        for report in (structural(copy.deepcopy(case)), standalone(copy.deepcopy(case))):
            self.assertEqual(report["state"], "FAILOVER_ELIGIBLE")
            self.assertEqual(report["action"], "EXTERNAL_FAILOVER")
            self.assertFalse(report["promotion_authorized"])

    def test_applied_failover_requires_reality_validation(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        self.assertEqual(structural(copy.deepcopy(case))["state"], "RECOVERY_VALIDATION_REQUIRED")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "RECOVERY_VALIDATION_REQUIRED")

    def test_malformed_and_future_recovery_time_rejected(self):
        for value in ("not-a-time", "2026-08-14T05:00:00+09:00", "2026-08-14T04:04:00+09:00"):
            case = base_case(); case["emergency"]["recovery"] = valid_recovery(); case["emergency"]["recovery"]["applied_at"] = value
            with self.assertRaises(ValueError): structural(copy.deepcopy(case), bound_validator())
            with self.assertRaises(ValueError): standalone(copy.deepcopy(case), bound_validator())

    def test_wrong_fallback_reality_validation_is_rejected(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        self.assertEqual(structural(copy.deepcopy(case), bound_validator("different-fallback"))["state"], "RECOVERY_NOT_VALIDATED")
        self.assertEqual(standalone(copy.deepcopy(case), bound_validator("different-fallback"))["state"], "RECOVERY_NOT_VALIDATED")

    def test_stale_validation_after_time_is_rejected(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        def stale(_):
            r = bound_validator()(_); r["validated_at"] = "2026-08-14T04:05:30+09:00"; return r
        self.assertEqual(structural(copy.deepcopy(case), stale)["state"], "RECOVERY_NOT_VALIDATED")
        self.assertEqual(standalone(copy.deepcopy(case), stale)["state"], "RECOVERY_NOT_VALIDATED")

    def test_valid_recovery_is_temporary_and_debtful(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        for report in (structural(copy.deepcopy(case), bound_validator()), standalone(copy.deepcopy(case), bound_validator())):
            self.assertEqual(report["state"], "TEMPORARY_RECOVERY_VALIDATED")
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["automatic_failback_authorized"])
            self.assertEqual(set(report["recovery_debt"]), {"DISCOVERY_REFRESH", "ROOT_CAUSE_REVIEW", "METEOR_DARWIN", "PERMANENT_OCCUPANT_DECISION"})

    def test_automatic_failback_blocked(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery(); case["emergency"]["recovery"]["failback_requested"] = True
        self.assertEqual(structural(copy.deepcopy(case), bound_validator())["state"], "FAILBACK_BLOCKED_PENDING_DARWIN")
        self.assertEqual(standalone(copy.deepcopy(case), bound_validator())["state"], "FAILBACK_BLOCKED_PENDING_DARWIN")


class ArchitectureCounterDA(unittest.TestCase):
    def test_existing_provider_degradation_precedence_ambiguity_stays_visible(self):
        case = base_case(); case.pop("emergency")
        case["trigger"] = {"type": "PROVIDER_DEGRADATION", "evidence_state": "CURRENT_OBSERVED", "source_ref": "health:degraded", "stale_after": "2026-08-14T06:00:00+09:00", "materiality": "MATERIAL"}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "METEOR")
        self.assertEqual(report["candidate_disposition"], "STANDBY")
        self.assertEqual(report["next_state"], "STANDBY")

    def test_standalone_parity_does_not_create_promotion_authority(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        s = structural(copy.deepcopy(case), bound_validator())
        n = standalone(copy.deepcopy(case), bound_validator())
        self.assertEqual(n["state"], s["state"])
        self.assertFalse(n["promotion_authorized"])


if __name__ == "__main__":
    unittest.main()
