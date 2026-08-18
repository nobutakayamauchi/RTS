import unittest

import integrity


class IntegrityTests(unittest.TestCase):
    def test_correlation_cannot_route_to_local_gate(self):
        report = integrity.evaluate({"failure_evidence": {"stage": "DEPLOYMENT", "causality_state": "CORRELATED_ONLY"}})
        self.assertEqual(report["reentry_route"], "ANALYSIS_REOPEN")

    def test_proven_deployment_failure_routes_to_identity(self):
        report = integrity.evaluate({"failure_evidence": {"stage": "DEPLOYMENT", "causality_state": "PROVEN"}})
        self.assertEqual(report["reentry_route"], "DEPLOYMENT_IDENTITY")

    def test_proven_post_deploy_failure_routes_to_debug(self):
        report = integrity.evaluate({"failure_evidence": {"stage": "POST_DEPLOY_METRIC", "causality_state": "PROVEN"}})
        self.assertEqual(report["reentry_route"], "POST_DEPLOY_DEBUG")

    def test_inference_cannot_become_observation(self):
        report = integrity.evaluate({"evidence": {"inference_treated_as": "OBSERVED_FACT"}})
        self.assertIn("INFERENCE_MASQUERADES_AS_OBSERVATION", report["blocking_states"])

    def test_unsupported_proxy_claim_blocks(self):
        report = integrity.evaluate({"evidence": {
            "measured_properties": ["small_payment_capability"],
            "claimed_properties": ["large_purchase_fit"],
            "construct_mapping_state": "UNVALIDATED",
        }})
        self.assertIn("UNSUPPORTED_PROXY_CLAIM:large_purchase_fit", report["blocking_states"])

    def test_selected_cohort_cannot_generalize(self):
        report = integrity.evaluate({"evidence": {
            "evidence_cohort_ref": "screened@v1",
            "claim_population_ref": "all@v1",
            "selection_history_state": "BOUND",
            "claim_scope": "POPULATION_GENERALIZATION",
            "transportability_state": "UNVALIDATED",
        }})
        self.assertIn("SELECTED_COHORT_NOT_POPULATION_EVIDENCE", report["blocking_states"])

    def test_post_intervention_state_is_not_intrinsic(self):
        report = integrity.evaluate({"evidence": {
            "intervention_history_state": "BOUND",
            "post_intervention_claim": "INTRINSIC_PROPERTY",
            "causal_identification_state": "UNVALIDATED",
        }})
        self.assertIn("INTERVENTION_CONTAMINATES_INTRINSIC_OR_CAUSAL_CLAIM", report["blocking_states"])

    def test_abstract_scope_escape_blocks(self):
        report = integrity.evaluate({"evidence": {
            "scope_relation": "EVIDENCE_NARROWER_THAN_CLAIM",
            "scope_bridge_validation_state": "MISSING",
        }})
        self.assertIn("ABSTRACTION_LEVEL_DRIFT", report["blocking_states"])

    def test_changed_dependency_marks_only_affected_artifact_stale(self):
        report = integrity.evaluate({"derived_artifacts": [
            {
                "id": "lp",
                "dependency_binding_state": "BOUND",
                "dependency_fields": ["target", "benefit"],
                "changed_upstream_fields": ["benefit"],
                "derived_from_upstream_revision": "concept@v1",
                "current_upstream_revision": "concept@v2",
                "recomputed_from_current": False,
                "bounded_revalidation_state": "MISSING",
            },
            {
                "id": "ops-note",
                "dependency_binding_state": "BOUND",
                "dependency_fields": ["internal_note"],
                "changed_upstream_fields": ["benefit"],
                "derived_from_upstream_revision": "concept@v1",
                "current_upstream_revision": "concept@v2",
                "recomputed_from_current": False,
            },
        ]})
        self.assertEqual(report["stale_artifacts"], ["lp"])
        self.assertIn("STALE_DEPENDENCY:lp:benefit", report["blocking_states"])

    def test_bounded_revalidation_restores_freshness(self):
        report = integrity.evaluate({"derived_artifacts": [{
            "id": "lp",
            "dependency_binding_state": "BOUND",
            "dependency_fields": ["benefit"],
            "changed_upstream_fields": ["benefit"],
            "derived_from_upstream_revision": "concept@v1",
            "current_upstream_revision": "concept@v2",
            "recomputed_from_current": False,
            "bounded_revalidation_state": "PASS",
        }]})
        self.assertEqual(report["freshness_state"], "PASS")

    def test_hidden_decline_path_invalidates_human_gate(self):
        report = integrity.evaluate({"human_gate": {
            "source": "HUMAN_GATE",
            "decline_path_state": "HIDDEN",
            "material_consequence_disclosure_state": "PASS",
            "current_decision_state": "EXPLICIT_CURRENT",
            "system_applied_pressure": [],
        }})
        self.assertIn("MEANINGFUL_DECLINE_PATH_MISSING", report["blocking_states"])

    def test_valid_current_human_gate_passes(self):
        report = integrity.evaluate({"human_gate": {
            "source": "HUMAN_GATE",
            "decline_path_state": "VISIBLE_AND_ACTIONABLE",
            "material_consequence_disclosure_state": "PASS",
            "current_decision_state": "EXPLICIT_CURRENT",
            "system_applied_pressure": [],
        }})
        self.assertEqual(report["human_gate_state"], "PASS")
        self.assertEqual(report["classification"], "PASS")

    def test_retrieval_does_not_imply_decision_succession(self):
        report = integrity.evaluate({"decision_succession": {
            "canonical_material_state": "PASS",
            "retrieval_state": "PASS",
            "held_out_decision_state": "NOT_TESTED",
            "authority_compliance_state": "PASS",
            "escalation_state": "PASS",
            "creator_intervention": False,
        }})
        self.assertEqual(report["decision_succession_state"], "NOT_READY")
        self.assertIn("HELD_OUT_DECISIONS_UNPROVEN", report["decision_succession_blocking_states"])

    def test_creator_absent_held_out_decision_succession_can_be_ready(self):
        report = integrity.evaluate({"decision_succession": {
            "canonical_material_state": "PASS",
            "retrieval_state": "PASS",
            "held_out_decision_state": "PASS",
            "authority_compliance_state": "PASS",
            "escalation_state": "PASS",
            "creator_intervention": False,
        }})
        self.assertEqual(report["decision_succession_state"], "DECISION_SUCCESSION_READY")
        self.assertEqual(report["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
