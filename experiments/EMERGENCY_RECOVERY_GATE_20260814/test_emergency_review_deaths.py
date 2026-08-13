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

spec = importlib.util.spec_from_file_location("lifecycle", ROOT / "thin-rts" / "ultimate-loop" / "lifecycle.py")
lifecycle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(lifecycle)
AT = datetime(2026, 8, 13, 19, 7, tzinfo=timezone.utc)


def validator(_):
    return {
        "state": "DEPLOYMENT_VALIDATED",
        "stable_eligible": True,
        "post_deployment_binding": ["o", "e", "s"],
        "validated_candidate_id": "fallback-b",
        "validated_at": "2026-08-14T04:06:30+09:00",
    }


def structural(case):
    return structural_prototype.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate, recovery_validator=validator)


def standalone(case):
    return standalone_prototype.evaluate(case, AT, recovery_validator=validator)


def manual(case):
    case["manual"] = {"operator_available": True, "runbook_current": True, "rto_satisfied": True}
    return manual_composition_reference.evaluate(case, AT, lifecycle_evaluator=lifecycle.evaluate)


class ReviewRegressions(unittest.TestCase):
    def test_newer_sample_does_not_invalidate_applied_recovery(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        case["emergency"]["health"]["observed_at"] = "2026-08-14T04:07:00+09:00"
        self.assertEqual(structural(copy.deepcopy(case))["state"], "TEMPORARY_RECOVERY_VALIDATED")
        self.assertEqual(standalone(copy.deepcopy(case))["state"], "TEMPORARY_RECOVERY_VALIDATED")

    def test_healthy_primary_does_not_erase_temporary_recovery(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        case["emergency"]["health"]["state"] = "HEALTHY"
        case["emergency"]["health"]["observed_at"] = "2026-08-14T04:07:00+09:00"
        for result in (structural(copy.deepcopy(case)), standalone(copy.deepcopy(case))):
            self.assertEqual(result["state"], "TEMPORARY_RECOVERY_VALIDATED")
            self.assertFalse(result["automatic_failback_authorized"])

    def test_trigger_snapshot_required_after_failover(self):
        case = base_case(); case["emergency"]["recovery"] = valid_recovery()
        del case["emergency"]["recovery"]["trigger_observed_at"]
        with self.assertRaises(ValueError): structural(copy.deepcopy(case))
        with self.assertRaises(ValueError): standalone(copy.deepcopy(case))

    def test_operation_mode_typo_fails_closed(self):
        case = base_case(); case["emergency"]["policy"]["operation_mode"] = "READ_WRITE_SINGLE_WRTER"
        with self.assertRaises(ValueError): structural(copy.deepcopy(case))
        with self.assertRaises(ValueError): standalone(copy.deepcopy(case))
        with self.assertRaises(ValueError): manual(copy.deepcopy(case))

    def test_manual_healthy_is_not_mapped_to_primary_unavailable(self):
        case = base_case(); case["emergency"]["health"]["state"] = "HEALTHY"
        result = manual(case)
        self.assertEqual(result["state"], "MANUAL_NO_FAILOVER_REQUIRED")
        self.assertFalse(result["failover_eligible"])

    def test_manual_unknown_is_not_mapped_to_primary_unavailable(self):
        case = base_case(); case["emergency"]["health"]["state"] = "UNKNOWN"
        result = manual(case)
        self.assertEqual(result["state"], "MANUAL_HEALTH_UNKNOWN")
        self.assertFalse(result["failover_eligible"])

    def test_manual_degraded_only_prepares(self):
        case = base_case(); case["emergency"]["health"]["state"] = "DEGRADED"
        result = manual(case)
        self.assertEqual(result["state"], "MANUAL_PREPARE_STANDBY")
        self.assertFalse(result["failover_eligible"])

    def test_manual_flapping_failed_does_not_failover(self):
        case = base_case(); case["emergency"]["health"]["hysteresis"] = "NOT_PASS"
        result = manual(case)
        self.assertEqual(result["state"], "MANUAL_OBSERVE_CONTINUE")
        self.assertFalse(result["failover_eligible"])

    def test_manual_stale_fallback_probe_fails_closed(self):
        case = base_case(); case["candidate"]["recovery_probe_stale_after"] = "2026-08-14T03:00:00+09:00"
        result = manual(case)
        self.assertEqual(result["state"], "MANUAL_FALLBACK_PROBE_STALE")
        self.assertFalse(result["survives"])


if __name__ == "__main__":
    unittest.main()
