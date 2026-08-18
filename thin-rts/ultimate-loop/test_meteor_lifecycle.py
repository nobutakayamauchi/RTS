import copy
import unittest
from datetime import datetime, timezone

import lifecycle

AT = datetime(2026, 8, 13, 3, 0, tzinfo=timezone.utc)


def valid_replacement_case():
    return {
        "frame_id": "frame-core-capability",
        "current_state": "STABLE",
        "integrity_applicability": "NOT_APPLICABLE",
        "authority": {"promote": "AUTHORIZED", "failover": "BLOCKED"},
        "policy": {"observe_delta_pct": 5, "meteor_delta_pct": 15, "full_replace_delta_pct": 30},
        "trigger": {
            "type": "PERFORMANCE_JUMP",
            "evidence_state": "CURRENT_OBSERVED",
            "source_ref": "external:benchmark-plus-real-workload",
            "stale_after": "2026-08-20T00:00:00Z",
            "materiality": "MATERIAL"
        },
        "candidate": {
            "candidate_id": "challenger",
            "performance_delta_pct": 45,
            "replacement_value": "MATERIAL_WIN",
            "resilience_value": "MEDIUM",
            "stability_state": "SURVIVED",
            "same_frozen_workload": "PASS",
            "recovery_probe": "PASS",
            "migration_state": "PASS",
            "rollback_state": "PASS",
            "failure_domain_independence": "VERIFIED"
        },
        "recovery": {
            "backup_present": True,
            "fresh_restore_test": "PASS",
            "canonical_material": "PASS",
            "succession_packet": "PASS",
            "phoenix_test": "PASS"
        }
    }


class MeteorLifecycleDeaths(unittest.TestCase):
    def test_death_01_score_only_cannot_promote_unstable_candidate(self):
        case = valid_replacement_case()
        case["candidate"]["performance_delta_pct"] = 300
        case["candidate"]["stability_state"] = "UNPROVEN"
        case["candidate"]["same_frozen_workload"] = "NOT_RUN"
        report = lifecycle.evaluate(case, AT)
        self.assertNotEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")
        self.assertEqual(report["candidate_disposition"], "SHADOW")

    def test_death_02_stale_challenger_signal_cannot_open_meteor(self):
        case = valid_replacement_case()
        case["trigger"]["stale_after"] = "2026-08-13T02:59:59Z"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "NONE")
        self.assertIn("TRIGGER_EVIDENCE_STALE", report["blocking_states"])

    def test_death_03_unverified_discovery_cannot_open_meteor(self):
        case = valid_replacement_case()
        case["trigger"]["evidence_state"] = "RUMOR"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "NONE")
        self.assertIn("TRIGGER_EVIDENCE_NOT_CURRENT", report["blocking_states"])

    def test_death_04_large_gain_with_failed_migration_cannot_replace(self):
        case = valid_replacement_case()
        case["candidate"]["performance_delta_pct"] = 120
        case["candidate"]["migration_state"] = "FAIL"
        report = lifecycle.evaluate(case, AT)
        self.assertNotEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")

    def test_death_05_large_gain_with_failed_rollback_cannot_replace(self):
        case = valid_replacement_case()
        case["candidate"]["rollback_state"] = "FAIL"
        report = lifecycle.evaluate(case, AT)
        self.assertNotEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")

    def test_death_06_material_win_with_blocked_authority_cannot_replace(self):
        case = valid_replacement_case()
        case["authority"]["promote"] = "BLOCKED"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "FULL_REPLACEMENT_READY_AUTHORITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])

    def test_death_07_same_failure_domain_label_is_not_resilience_proof(self):
        case = valid_replacement_case()
        case["trigger"] = {
            "type": "DEPENDENCY_FAILURE",
            "evidence_state": "CURRENT_OBSERVED",
            "source_ref": "external:provider-outage",
            "stale_after": "2026-08-14T00:00:00Z",
            "materiality": "MATERIAL",
            "failure_domain_scope": "MATERIAL"
        }
        case["authority"]["failover"] = "AUTHORIZED"
        case["candidate"]["failure_domain_independence"] = "LABEL_ONLY"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "REJECTED_FOR_EMERGENCY")
        self.assertIn("FAILURE_DOMAIN_INDEPENDENCE_UNPROVEN", report["blocking_states"])

    def test_death_08_backup_presence_cannot_satisfy_recovery(self):
        case = valid_replacement_case()
        case["recovery"] = {
            "backup_present": True,
            "fresh_restore_test": "NOT_RUN",
            "canonical_material": "UNKNOWN",
            "succession_packet": "PASS",
            "phoenix_test": "PASS"
        }
        report = lifecycle.evaluate(case, AT)
        self.assertIn("BACKUP_NOT_RECOVERY", report["blocking_states"])

    def test_death_09_recovery_cannot_be_substituted_for_phoenix(self):
        case = valid_replacement_case()
        case["recovery"]["phoenix_test"] = "NOT_RUN"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["recovery_state"], "RECOVERABLE")
        self.assertIn("SUCCESSION_WITHOUT_PHOENIX_TEST", report["blocking_states"])

    def test_death_10_unknown_future_event_reopens_design_instead_of_guessing(self):
        case = valid_replacement_case()
        case["trigger"]["type"] = "UNMODELED_ERA_SHIFT"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["next_state"], "BUILD")
        self.assertIn("UNKNOWN_TRIGGER_TYPE", report["blocking_states"])

    def test_death_11_small_gain_high_resilience_is_preserved_not_forced_into_primary(self):
        case = valid_replacement_case()
        case["candidate"].update({
            "performance_delta_pct": 3,
            "replacement_value": "SMALL_WIN",
            "resilience_value": "HIGH",
            "stability_state": "UNPROVEN",
            "same_frozen_workload": "NOT_RUN"
        })
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "STANDBY")
        self.assertFalse(report["transition_authorized"])

    def test_death_12_non_material_new_thing_does_not_consume_meteor(self):
        case = valid_replacement_case()
        case["trigger"]["materiality"] = "NON_MATERIAL"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["watch_action"], "OBSERVE")

    def test_control_valid_material_replacement_survives(self):
        report = lifecycle.evaluate(valid_replacement_case(), AT)
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")
        self.assertTrue(report["transition_authorized"])


if __name__ == "__main__":
    unittest.main()
