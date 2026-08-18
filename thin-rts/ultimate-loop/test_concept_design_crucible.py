from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "concept_design_crucible.py"
spec = importlib.util.spec_from_file_location("concept_design_crucible", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["concept_design_crucible"] = module
spec.loader.exec_module(module)


def base(extension_id: str) -> dict:
    return {
        "extension_id": extension_id,
        "frozen_workload_ref": "workload/frozen-v1",
        "authority_effect": "NONE",
    }


class ConceptDesignCrucibleTests(unittest.TestCase):
    def test_challenger_cannot_self_authorize(self):
        case = base("CD_EXT02_OBSERVATION_INFERENCE_LAYERING")
        case.update({"authority_effect":"PROMOTE","raw_observation_state":"BOUND","inference_treated_as":"HYPOTHESIS"})
        report = module.evaluate(case)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertFalse(report["canonical_promotion_authorized"])

    def test_semantic_drift_is_blocked(self):
        case = base("CD_EXT01_SEMANTIC_INVARIANT_ADAPTER_GUARD")
        case.update({
            "protected_semantic_fingerprint":"core-A",
            "adapters":[
                {"id":"a","semantic_fingerprint":"core-A","provenance_state":"PASS"},
                {"id":"b","semantic_fingerprint":"core-B","provenance_state":"PASS"},
            ],
        })
        report = module.evaluate(case)
        self.assertIn("SEMANTIC_DRIFT:b", report["blocking_states"])
        self.assertEqual(report["disposition"], "STANDBY_RESEARCH")

    def test_presentation_variation_is_allowed(self):
        case = base("CD_EXT01_SEMANTIC_INVARIANT_ADAPTER_GUARD")
        case.update({
            "protected_semantic_fingerprint":"core-A",
            "presentation_identity_required":False,
            "adapters":[
                {"id":"short","semantic_fingerprint":"core-A","provenance_state":"PASS","presentation":"short"},
                {"id":"long","semantic_fingerprint":"core-A","provenance_state":"PASS","presentation":"long"},
            ],
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "COMPOSE_SEMANTIC_ADAPTER_GUARD")

    def test_style_lock_is_rejected(self):
        case = base("CD_EXT01_SEMANTIC_INVARIANT_ADAPTER_GUARD")
        case.update({
            "protected_semantic_fingerprint":"core-A",
            "presentation_identity_required":True,
            "adapters":[
                {"id":"a","semantic_fingerprint":"core-A","provenance_state":"PASS"},
                {"id":"b","semantic_fingerprint":"core-A","provenance_state":"PASS"},
            ],
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "REJECT_STYLE_LOCK")

    def test_inference_cannot_masquerade_as_observation(self):
        case = base("CD_EXT02_OBSERVATION_INFERENCE_LAYERING")
        case.update({"raw_observation_state":"BOUND","inference_treated_as":"OBSERVED_FACT"})
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "REJECT_EVIDENCE_COLLAPSE")
        self.assertIn("INFERENCE_MASQUERADES_AS_OBSERVATION", report["blocking_states"])

    def test_inference_may_remain_hypothesis(self):
        case = base("CD_EXT02_OBSERVATION_INFERENCE_LAYERING")
        case.update({"raw_observation_state":"BOUND","inference_treated_as":"HYPOTHESIS"})
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "COMPOSE_TYPED_INFERENCE_LAYER")

    def test_validated_inference_needs_independent_validation(self):
        case = base("CD_EXT02_OBSERVATION_INFERENCE_LAYERING")
        case.update({"raw_observation_state":"BOUND","inference_treated_as":"VALIDATED_INFERENCE","independent_validation_state":"FAIL"})
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "STANDBY_RESEARCH")
        self.assertIn("INFERENCE_VALIDATION_UNPROVEN", report["blocking_states"])

    def test_validated_inference_can_remain_separately_typed(self):
        case = base("CD_EXT02_OBSERVATION_INFERENCE_LAYERING")
        case.update({"raw_observation_state":"BOUND","inference_treated_as":"VALIDATED_INFERENCE","independent_validation_state":"PASS"})
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "COMPOSE_TYPED_INFERENCE_LAYER")

    def test_local_metric_win_cannot_hide_downstream_regression(self):
        case = base("CD_EXT03_END_TO_END_OBJECTIVE_BINDING")
        case.update({
            "downstream_surface":True,
            "local_metric_state":"PASS",
            "protected_downstream_outcome_state":"FAIL",
            "local_change_promotion_requested":True,
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "BLOCK_LOCAL_PROMOTION")
        self.assertIn("LOCAL_WIN_MASKS_END_TO_END_REGRESSION", report["blocking_states"])

    def test_downstream_profile_can_be_not_applicable(self):
        case = base("CD_EXT03_END_TO_END_OBJECTIVE_BINDING")
        case.update({"downstream_surface":False,"mandatory_for_all_workloads":False})
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "NOT_APPLICABLE_PROFILE")

    def test_material_context_failure_blocks_global_diagnosis(self):
        case = base("CD_EXT04_CONTEXT_CONDITIONED_TELEMETRY")
        case.update({
            "aggregate_state":"PASS",
            "context_definition_state":"EVIDENCE_BOUND",
            "context_materiality_state":"MATERIAL",
            "context_outcome_state":"FAIL",
            "posthoc_only":False,
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "TARGETED_ANALYSIS_REOPEN")
        self.assertIn("AGGREGATE_MASKS_MATERIAL_CONTEXT_FAILURE", report["blocking_states"])

    def test_arbitrary_posthoc_segment_cannot_veto_aggregate(self):
        case = base("CD_EXT04_CONTEXT_CONDITIONED_TELEMETRY")
        case.update({
            "aggregate_state":"PASS",
            "context_definition_state":"EVIDENCE_BOUND",
            "context_materiality_state":"MATERIAL",
            "context_outcome_state":"FAIL",
            "posthoc_only":True,
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "IGNORE_NONMATERIAL_CONTEXT")


if __name__ == "__main__":
    unittest.main()
