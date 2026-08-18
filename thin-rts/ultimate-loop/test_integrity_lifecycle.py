import unittest
from datetime import datetime, timezone

import lifecycle

AT = datetime(2026, 8, 18, 9, 30, tzinfo=timezone.utc)


def base_case():
    return {
        "frame_id": "frame-integrity-connection",
        "current_state": "STABLE",
        "material_durable": True,
        "integrity_applicability": "NOT_APPLICABLE",
        "integrity_applicability_evidence_ref": "workload:frozen-no-v0.2-integrity-surface",
        "authority": {"promote": "AUTHORIZED", "failover": "BLOCKED"},
        "policy": {"observe_delta_pct": 5, "meteor_delta_pct": 15, "full_replace_delta_pct": 30},
        "recovery": {
            "backup_present": True,
            "fresh_restore_test": "PASS",
            "canonical_material": "PASS",
            "succession_packet": "PASS",
            "phoenix_test": "PASS",
        },
        "candidate": {
            "candidate_id": "candidate-b",
            "performance_delta_pct": 45,
            "replacement_value": "MATERIAL_WIN",
            "resilience_value": "MEDIUM",
            "stability_state": "SURVIVED",
            "same_frozen_workload": "PASS",
            "recovery_probe": "PASS",
            "migration_state": "PASS",
            "rollback_state": "PASS",
            "failure_domain_independence": "VERIFIED",
        },
    }


def require_integrity(case):
    case["integrity_applicability"] = "REQUIRED"
    case.pop("integrity_applicability_evidence_ref", None)
    return case


class IntegrityLifecycleTests(unittest.TestCase):
    def test_explicit_not_applicable_preserves_legacy_eligible_path(self):
        report = lifecycle.evaluate(base_case(), AT)
        self.assertEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")
        self.assertTrue(report["transition_authorized"])
        self.assertEqual(report["integrity_applicability_state"], "NOT_APPLICABLE")

    def test_bare_not_applicable_label_cannot_bypass_integrity(self):
        case = base_case()
        case.pop("integrity_applicability_evidence_ref")
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])
        self.assertIn("NOT_APPLICABLE_EVIDENCE_REF_MISSING", report["blocking_states"])

    def test_undeclared_applicability_blocks_eligible_promotion(self):
        case = base_case()
        case.pop("integrity_applicability")
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])
        self.assertIn("INTEGRITY_APPLICABILITY_UNDECLARED", report["blocking_states"])

    def test_required_profile_cannot_be_omitted(self):
        case = require_integrity(base_case())
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])
        self.assertIn("REQUIRED_INTEGRITY_PROFILE_MISSING", report["blocking_states"])

    def test_required_empty_profile_cannot_pass(self):
        case = require_integrity(base_case())
        case["integrity"] = {}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])
        self.assertIn("REQUIRED_INTEGRITY_SECTION_MISSING", report["blocking_states"])

    def test_undeclared_applicability_blocks_core_freeze(self):
        case = base_case()
        case.pop("candidate")
        case.pop("integrity_applicability")
        case["current_state"] = "BUILD"
        case["core_acceptance"] = "PASS"
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["next_state"], "BUILD")
        self.assertIn("INTEGRITY_APPLICABILITY_UNDECLARED", report["blocking_states"])

    def test_invalid_human_gate_blocks_otherwise_eligible_promotion(self):
        case = require_integrity(base_case())
        case["integrity"] = {"human_gate": {
            "source": "HUMAN_GATE",
            "decline_path_state": "HIDDEN",
            "material_consequence_disclosure_state": "PASS",
            "current_decision_state": "EXPLICIT_CURRENT",
            "system_applied_pressure": [],
        }}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])
        self.assertIn("MEANINGFUL_DECLINE_PATH_MISSING", report["blocking_states"])

    def test_stale_derived_artifact_blocks_otherwise_eligible_promotion(self):
        case = require_integrity(base_case())
        case["integrity"] = {"derived_artifacts": [{
            "id": "deployment-manifest",
            "dependency_binding_state": "BOUND",
            "dependency_fields": ["route"],
            "changed_upstream_fields": ["route"],
            "derived_from_upstream_revision": "design@v1",
            "current_upstream_revision": "design@v2",
            "recomputed_from_current": False,
            "bounded_revalidation_state": "MISSING",
        }]}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])
        self.assertEqual(report["derived_artifact_freshness_state"], "STALE")

    def test_unrelated_upstream_change_does_not_block_promotion(self):
        case = require_integrity(base_case())
        case["integrity"] = {"derived_artifacts": [{
            "id": "deployment-manifest",
            "dependency_binding_state": "BOUND",
            "dependency_fields": ["route"],
            "changed_upstream_fields": ["internal_note"],
            "derived_from_upstream_revision": "design@v1",
            "current_upstream_revision": "design@v2",
            "recomputed_from_current": False,
        }]}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "FULL_REPLACEMENT_ELIGIBLE")
        self.assertTrue(report["transition_authorized"])

    def test_evidence_scope_failure_blocks_promotion(self):
        case = require_integrity(base_case())
        case["integrity"] = {"evidence": {
            "measured_properties": ["component_pass"],
            "claimed_properties": ["system_correct"],
            "construct_mapping_state": "UNVALIDATED",
        }}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["candidate_disposition"], "INTEGRITY_BLOCKED")
        self.assertFalse(report["transition_authorized"])

    def test_uncertain_failure_causality_reopens_analysis(self):
        case = require_integrity(base_case())
        case["integrity"] = {"failure_evidence": {"stage": "POST_DEPLOY_METRIC", "causality_state": "CORRELATED_ONLY"}}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["reentry_route"], "ANALYSIS_REOPEN")
        self.assertEqual(report["next_state"], "BUILD")
        self.assertFalse(report["transition_authorized"])

    def test_proven_post_deploy_failure_exposes_smallest_reentry_route(self):
        case = require_integrity(base_case())
        case.pop("candidate")
        case["integrity"] = {"failure_evidence": {"stage": "POST_DEPLOY_METRIC", "causality_state": "PROVEN"}}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["reentry_route"], "POST_DEPLOY_DEBUG")
        self.assertEqual(report["current_state"], "STABLE")

    def test_phoenix_ready_is_not_decision_succession_ready(self):
        case = require_integrity(base_case())
        case.pop("candidate")
        case["integrity"] = {"decision_succession": {
            "canonical_material_state": "PASS",
            "retrieval_state": "PASS",
            "held_out_decision_state": "NOT_TESTED",
            "authority_compliance_state": "PASS",
            "escalation_state": "PASS",
            "creator_intervention": False,
        }}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["recovery_state"], "PHOENIX_READY")
        self.assertEqual(report["decision_succession_state"], "NOT_READY")

    def test_decision_succession_can_be_ready_without_changing_authority(self):
        case = require_integrity(base_case())
        case.pop("candidate")
        case["integrity"] = {"decision_succession": {
            "canonical_material_state": "PASS",
            "retrieval_state": "PASS",
            "held_out_decision_state": "PASS",
            "authority_compliance_state": "PASS",
            "escalation_state": "PASS",
            "creator_intervention": False,
        }}
        report = lifecycle.evaluate(case, AT)
        self.assertEqual(report["decision_succession_state"], "DECISION_SUCCESSION_READY")
        self.assertFalse(report["transition_authorized"])


if __name__ == "__main__":
    unittest.main()
