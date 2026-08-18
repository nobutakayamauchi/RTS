from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "hybrid_marketing_crucible.py"
spec = importlib.util.spec_from_file_location("hybrid_marketing_crucible", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["hybrid_marketing_crucible"] = module
spec.loader.exec_module(module)

BASE = {"frozen_workload_ref": "hybrid-marketing/challenger-workload-v1", "authority_effect": "NONE"}


class Tests(unittest.TestCase):
    def run_case(self, ext, **kwargs):
        case = dict(BASE, extension_id=ext, **kwargs)
        return module.evaluate(case)

    def test_self_authorization_blocked(self):
        case = dict(BASE, extension_id="HM_EXT01_FILTER_AWARE_STAGE_TELEMETRY", authority_effect="PROMOTE")
        r = module.evaluate(case)
        self.assertEqual(r["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertIn("AUTHORITY_EFFECT_NOT_NONE", r["blocking_states"])

    def test_filter_attrition_not_false_bottleneck(self):
        r = self.run_case("HM_EXT01_FILTER_AWARE_STAGE_TELEMETRY", stage_objective="FILTER", throughput_state="LOW", downstream_quality_state="IMPROVED", rejection_semantics="DECLARED", causality_state="PROVEN_OR_BOUNDED")
        self.assertEqual(r["disposition"], "NO_BOTTLENECK_FILTER_WORKING")

    def test_low_filter_without_quality_proof_reopens(self):
        r = self.run_case("HM_EXT01_FILTER_AWARE_STAGE_TELEMETRY", stage_objective="FILTER", throughput_state="LOW", downstream_quality_state="UNKNOWN", rejection_semantics="DECLARED", causality_state="UNKNOWN")
        self.assertEqual(r["disposition"], "ANALYSIS_REOPEN")

    def test_transform_drop_can_be_bottleneck(self):
        r = self.run_case("HM_EXT01_FILTER_AWARE_STAGE_TELEMETRY", stage_objective="TRANSFORM", throughput_state="LOW", downstream_quality_state="DEGRADED", rejection_semantics="NOT_APPLICABLE", causality_state="PROVEN_OR_BOUNDED")
        self.assertEqual(r["disposition"], "BOTTLENECK_CANDIDATE")

    def test_proxy_gate_cannot_overclaim(self):
        r = self.run_case("HM_EXT02_EVIDENCE_CONSTRUCT_VALIDITY", measured_properties=["small_payment_capability"], claimed_properties=["large_purchase_fit"], construct_mapping_state="UNVALIDATED")
        self.assertEqual(r["disposition"], "BLOCK_CLAIM")
        self.assertTrue(any(x.startswith("UNSUPPORTED_PROXY_CLAIM:") for x in r["blocking_states"]))

    def test_direct_measure_claim_allowed(self):
        r = self.run_case("HM_EXT02_EVIDENCE_CONSTRUCT_VALIDITY", measured_properties=["rollback_pass"], claimed_properties=["rollback_pass"], construct_mapping_state="NOT_NEEDED")
        self.assertEqual(r["disposition"], "BOUND_CLAIM_TO_EVIDENCE_SCOPE")

    def test_validated_proxy_mapping_allowed_but_bounded(self):
        r = self.run_case("HM_EXT02_EVIDENCE_CONSTRUCT_VALIDITY", measured_properties=["probe_x"], claimed_properties=["risk_y"], construct_mapping_state="VALIDATED")
        self.assertEqual(r["disposition"], "BOUND_CLAIM_TO_EVIDENCE_SCOPE")

    def test_short_circuit_when_all_unique_obligations_satisfied(self):
        r = self.run_case("HM_EXT03_EVIDENCE_SATISFIED_SHORT_CIRCUIT", downstream_preconditions_state="PASS", authority_state="AUTHORIZED", skip_reason="EVIDENCE_ALREADY_SATISFIED", remaining_stages=[{"id": "EDUCATION_ONLY", "unique_obligation_state": "SATISFIED"}, {"id": "OPTIONAL_FORMAT", "unique_obligation_state": "NOT_APPLICABLE"}])
        self.assertEqual(r["disposition"], "SHORT_CIRCUIT_ELIGIBLE")

    def test_short_circuit_blocked_if_unique_obligation_missing(self):
        r = self.run_case("HM_EXT03_EVIDENCE_SATISFIED_SHORT_CIRCUIT", downstream_preconditions_state="PASS", authority_state="AUTHORIZED", skip_reason="EVIDENCE_ALREADY_SATISFIED", remaining_stages=[{"id": "SECURITY_GATE", "unique_obligation_state": "UNSATISFIED"}])
        self.assertEqual(r["disposition"], "NO_SHORT_CIRCUIT")

    def test_short_circuit_not_just_for_speed(self):
        r = self.run_case("HM_EXT03_EVIDENCE_SATISFIED_SHORT_CIRCUIT", downstream_preconditions_state="PASS", authority_state="AUTHORIZED", skip_reason="TIME_PRESSURE_ONLY", remaining_stages=[])
        self.assertEqual(r["disposition"], "NO_SHORT_CIRCUIT")

    def test_pareto_heuristic_cannot_skip_unique_obligation(self):
        r = self.run_case("HM_EXT03_EVIDENCE_SATISFIED_SHORT_CIRCUIT", downstream_preconditions_state="PASS", authority_state="AUTHORIZED", skip_reason="PARETO_HEURISTIC_ONLY", remaining_stages=[])
        self.assertEqual(r["disposition"], "NO_SHORT_CIRCUIT")

    def test_sunk_cost_not_consent(self):
        r = self.run_case("HM_EXT04_COMMITMENT_CONTAMINATION_GUARD", historical_commitment={"present": True, "type": "payment"}, proposed_inference="CONSENT", current_explicit_state="MISSING")
        self.assertEqual(r["disposition"], "BLOCK_INFERENCE")

    def test_prior_approval_not_current_authority(self):
        r = self.run_case("HM_EXT04_COMMITMENT_CONTAMINATION_GUARD", historical_commitment={"present": True, "type": "prior_approval"}, proposed_inference="AUTHORITY", current_explicit_state="STALE")
        self.assertEqual(r["disposition"], "BLOCK_INFERENCE")

    def test_current_explicit_state_governs(self):
        r = self.run_case("HM_EXT04_COMMITMENT_CONTAMINATION_GUARD", historical_commitment={"present": True, "type": "effort"}, proposed_inference="CONSENT", current_explicit_state="EXPLICIT_CURRENT")
        self.assertEqual(r["disposition"], "CURRENT_STATE_GOVERNS")

    def test_human_gate_with_visible_decline_and_no_pressure_is_valid(self):
        r = self.run_case("HM_EXT05_HUMAN_GATE_AGENCY_PRESERVATION", gate_requires_human_choice=True, decline_path_state="VISIBLE_AND_ACTIONABLE", material_consequence_disclosure_state="PASS", current_decision_state="EXPLICIT_CURRENT", system_applied_pressure=[])
        self.assertEqual(r["disposition"], "HUMAN_GATE_AGENCY_BOUND")

    def test_hidden_decline_path_blocks_human_gate_validity(self):
        r = self.run_case("HM_EXT05_HUMAN_GATE_AGENCY_PRESERVATION", gate_requires_human_choice=True, decline_path_state="HIDDEN", material_consequence_disclosure_state="PASS", current_decision_state="EXPLICIT_CURRENT", system_applied_pressure=[])
        self.assertEqual(r["disposition"], "BLOCK_HUMAN_GATE_VALIDITY")
        self.assertIn("MEANINGFUL_DECLINE_PATH_MISSING", r["blocking_states"])

    def test_sunk_cost_pressure_cannot_validate_human_gate(self):
        r = self.run_case("HM_EXT05_HUMAN_GATE_AGENCY_PRESERVATION", gate_requires_human_choice=True, decline_path_state="VISIBLE_AND_ACTIONABLE", material_consequence_disclosure_state="PASS", current_decision_state="EXPLICIT_CURRENT", system_applied_pressure=["SUNK_COST_LEVERAGE"])
        self.assertEqual(r["disposition"], "BLOCK_HUMAN_GATE_VALIDITY")
        self.assertIn("AGENCY_PRESSURE:SUNK_COST_LEVERAGE", r["blocking_states"])

    def test_reference_class_shift_cannot_fake_improvement(self):
        r = self.run_case("HM_EXT06_REFERENCE_CLASS_FREEZE", comparison_claim="IMPROVED", frozen_reference_class_ref="benchmark@v1", current_reference_class_ref="premium-market@v2", measurement_protocol_state="PASS", reference_change_authority="AUTHORIZED_NEW_FRAME", paired_old_reference_evidence="MISSING")
        self.assertEqual(r["disposition"], "BLOCK_COMPARISON_CLAIM")
        self.assertIn("REFERENCE_CLASS_SHIFT_CONTAMINATES_DELTA", r["blocking_states"])

    def test_same_reference_class_supports_bounded_comparison(self):
        r = self.run_case("HM_EXT06_REFERENCE_CLASS_FREEZE", comparison_claim="IMPROVED", frozen_reference_class_ref="benchmark@v1", current_reference_class_ref="benchmark@v1", measurement_protocol_state="PASS", reference_change_authority="NOT_NEEDED", paired_old_reference_evidence="PASS")
        self.assertEqual(r["disposition"], "REFERENCE_CLASS_BOUND")

    def test_authorized_new_reference_starts_new_baseline_only(self):
        r = self.run_case("HM_EXT06_REFERENCE_CLASS_FREEZE", comparison_claim="NEW_FRAME_BASELINE", frozen_reference_class_ref="market-A@v1", current_reference_class_ref="market-B@v1", measurement_protocol_state="PASS", reference_change_authority="AUTHORIZED_NEW_FRAME", paired_old_reference_evidence="MISSING")
        self.assertEqual(r["disposition"], "NEW_REFERENCE_BASELINE_ONLY")


if __name__ == "__main__":
    unittest.main()
