import copy
import unittest
from datetime import datetime, timezone

import lifecycle

AT = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)


def base_case():
    return {
        "frame_id": "frame-llm-router",
        "current_state": "STABLE",
        "material_durable": True,
        "integrity_applicability": "NOT_APPLICABLE",
        "authority": {"promote": "BLOCKED", "failover": "BLOCKED"},
        "policy": {
            "observe_delta_pct": 5,
            "meteor_delta_pct": 15,
            "full_replace_delta_pct": 30,
        },
        "recovery": {
            "backup_present": True,
            "fresh_restore_test": "PASS",
            "canonical_material": "PASS",
            "succession_packet": "PASS",
            "phoenix_test": "PASS",
        },
    }


def material_trigger(trigger_type="NEW_CAPABILITY"):
    return {
        "type": trigger_type,
        "evidence_state": "CURRENT_OBSERVED",
        "source_ref": "external:current-observation",
        "stale_after": "2026-08-20T00:00:00Z",
        "materiality": "MATERIAL",
    }


def candidate(**overrides):
    value = {
        "candidate_id": "candidate-b",
        "performance_delta_pct": 20,
        "replacement_value": "PARTIAL_WIN",
        "resilience_value": "MEDIUM",
        "stability_state": "SURVIVED",
        "same_frozen_workload": "PASS",
        "recovery_probe": "PASS",
        "migration_state": "PASS",
        "rollback_state": "PASS",
        "failure_domain_independence": "VERIFIED",
    }
    value.update(overrides)
    return value


class LifecycleTests(unittest.TestCase):
    def test_stable_current_trigger_enters_meteor(self):
        case = base_case()
        case["trigger"] = material_trigger()
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "METEOR")
        self.assertEqual(report["next_state"], "METEOR")
        self.assertEqual(report["classification"], "PASS")

    def test_non_material_novelty_only_observes(self):
        case = base_case()
        case["trigger"] = material_trigger()
        case["trigger"]["materiality"] = "NON_MATERIAL"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "OBSERVE")
        self.assertEqual(report["next_state"], "WATCH")

    def test_stale_trigger_fails_closed(self):
        case = base_case()
        case["trigger"] = material_trigger()
        case["trigger"]["stale_after"] = "2026-08-13T02:00:00Z"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertIn("TRIGGER_EVIDENCE_STALE", report["blocking_states"])
        self.assertEqual(report["watch_action"], "NONE")

    def test_unknown_trigger_reopens_inner_loop(self):
        case = base_case()
        case["trigger"] = material_trigger("ALIEN_EVENT")
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "INNER_LOOP_REOPEN")
        self.assertEqual(report["next_state"], "BUILD")
        self.assertIn("UNKNOWN_TRIGGER_TYPE", report["blocking_states"])

    def test_backup_without_fresh_restore_is_not_recovery(self):
        case = base_case()
        case["recovery"]["fresh_restore_test"] = "NOT_RUN"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["recovery_state"], "UNKNOWN_OR_BLOCKED")
        self.assertIn("BACKUP_NOT_RECOVERY", report["blocking_states"])

    def test_succession_packet_without_phoenix_test_is_not_regeneration_proof(self):
        case = base_case()
        case["recovery"]["phoenix_test"] = "NOT_RUN"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["recovery_state"], "RECOVERABLE")
        self.assertIn("SUCCESSION_WITHOUT_PHOENIX_TEST", report["blocking_states"])

    def test_build_cannot_freeze_without_recovery_when_durable(self):
        case = base_case()
        case["current_state"] = "BUILD"
        case["core_acceptance"] = "PASS"
        case["authority"]["promote"] = "AUTHORIZED"
        case["recovery"] = {"backup_present": False}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["next_state"], "BUILD")
        self.assertIn("DURABLE_CORE_RECOVERY_NOT_PROVEN", report["blocking_states"])

    def test_build_completion_evidence_does_not_create_authority(self):
        case = base_case()
        case["current_state"] = "BUILD"
        case["core_acceptance"] = "PASS"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["next_state"], "BUILD")
        self.assertIn("CORE_PROMOTION_AUTHORITY_BLOCKED", report["blocking_states"])

    def test_small_gain_unstable_candidate_can_be_standby_if_resilient(self):
        case = base_case()
        case["candidate"] = candidate(
            performance_delta_pct=3,
            replacement_value="SMALL_WIN",
            resilience_value="HIGH",
            stability_state="UNPROVEN",
            same_frozen_workload="NOT_RUN",
            recovery_probe="PASS",
        )
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "STANDBY")
        self.assertEqual(report["next_state"], "STANDBY")
        self.assertFalse(report["transition_authorized"])

    def test_unstable_large_gain_candidate_never_becomes_primary(self):
        case = base_case()
        case["candidate"] = candidate(
            performance_delta_pct=80,
            replacement_value="MATERIAL_WIN",
            stability_state="UNPROVEN",
            same_frozen_workload="NOT_RUN",
            resilience_value="MEDIUM",
        )
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "SHADOW")
        self.assertFalse(report["transition_authorized"])

    def test_winning_candidate_still_needs_promotion_authority(self):
        case = base_case()
        case["candidate"] = candidate(
            performance_delta_pct=45,
            replacement_value="MATERIAL_WIN",
        )
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "FULL_REPLACEMENT_READY_AUTHORITY_BLOCKED")
        self.assertIn("PROMOTION_AUTHORITY_BLOCKED", report["blocking_states"])
        self.assertFalse(report["transition_authorized"])

    def test_authorized_survived_material_winner_can_be_eligible(self):
        case = base_case()
        case["authority"]["promote"] = "AUTHORIZED"
        case["candidate"] = candidate(
            performance_delta_pct=45,
            replacement_value="MATERIAL_WIN",
        )
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")
        self.assertEqual(report["next_state"], "STABLE")
        self.assertTrue(report["transition_authorized"])

    def test_partial_replacement_is_distinct_from_full(self):
        case = base_case()
        case["authority"]["promote"] = "AUTHORIZED"
        case["candidate"] = candidate(
            performance_delta_pct=18,
            replacement_value="PARTIAL_WIN",
        )
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "PARTIAL_REPLACEMENT_ELIGIBLE")
        self.assertEqual(report["next_state"], "PARTIAL")

    def test_emergency_requires_recovery_probe(self):
        case = base_case()
        case["trigger"] = material_trigger("PRIMARY_UNAVAILABLE")
        case["candidate"] = candidate(recovery_probe="NOT_RUN")
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "REJECTED_FOR_EMERGENCY")
        self.assertIn("EMERGENCY_FALLBACK_UNPROVEN", report["blocking_states"])

    def test_failure_domain_emergency_requires_independence_evidence(self):
        case = base_case()
        case["trigger"] = material_trigger("DEPENDENCY_FAILURE")
        case["trigger"]["failure_domain_scope"] = "MATERIAL"
        case["candidate"] = candidate(failure_domain_independence="LABEL_ONLY")
        report = lifecycle.evaluate(case, AT)
        self.assertIn("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN", report["blocking_states"])
        self.assertEqual(report["candidate_disposition"], "REJECTED_FOR_EMERGENCY")

    def test_emergency_technical_fit_does_not_create_failover_authority(self):
        case = base_case()
        case["trigger"] = material_trigger("PRIMARY_UNAVAILABLE")
        case["candidate"] = candidate(resilience_value="HIGH")
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "STANDBY")
        self.assertIn("FAILOVER_AUTHORITY_BLOCKED", report["blocking_states"])
        self.assertFalse(report["transition_authorized"])

    def test_authorized_emergency_fallback_enters_recovery(self):
        case = base_case()
        case["authority"]["failover"] = "AUTHORIZED"
        case["trigger"] = material_trigger("PRIMARY_UNAVAILABLE")
        case["candidate"] = candidate(resilience_value="HIGH")
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "EMERGENCY_FAILOVER_ELIGIBLE")
        self.assertEqual(report["next_state"], "RECOVERY")
        self.assertTrue(report["transition_authorized"])


if __name__ == "__main__":
    unittest.main()
