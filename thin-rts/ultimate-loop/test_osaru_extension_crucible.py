from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "osaru_extension_crucible.py"

spec = importlib.util.spec_from_file_location("osaru_extension_crucible", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["osaru_extension_crucible"] = module
spec.loader.exec_module(module)


class OsaruExtensionCrucibleTests(unittest.TestCase):
    def base(self, extension_id: str) -> dict:
        return {
            "extension_id": extension_id,
            "frozen_workload_ref": "ultimate-loop-method/osaru-mine-extensions-v1",
            "authority_effect": "NONE",
        }

    def test_extension_cannot_self_authorize(self):
        case = self.base("EXT03_BOTTLENECK_REENTRY_ROUTING")
        case.update({
            "authority_effect": "PROMOTE",
            "observed_failure_stage": "DISCOVERY",
            "causality_state": "PROVEN",
            "proposed_reentry": "DISCOVERY_REFRESH",
        })
        report = module.evaluate(case)
        self.assertEqual(report["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertFalse(report["canonical_promotion_authorized"])
        self.assertIn("AUTHORITY_EFFECT_NOT_NONE", report["blocking_states"])

    def test_first_party_signal_is_not_universal(self):
        case = self.base("EXT01_FIRST_PARTY_SIGNAL_BINDING")
        case.update({"human_or_user_surface": False, "mandatory_for_all_workloads": True})
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "REJECT_UNIVERSAL_GATE")
        self.assertIn("FIRST_PARTY_FORCED_ON_INAPPLICABLE_WORKLOAD", report["blocking_states"])

    def test_first_party_signal_can_survive_conditionally(self):
        case = self.base("EXT01_FIRST_PARTY_SIGNAL_BINDING")
        case.update({
            "human_or_user_surface": True,
            "mandatory_for_all_workloads": False,
            "first_party_evidence_state": "CURRENT_BOUND",
            "consent_privacy_state": "PASS",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "COMPOSE_CONDITIONAL_PROFILE")

    def compiler_case(self) -> dict:
        case = self.base("EXT02_CANONICAL_SOURCE_COMPILER")
        case.update({
            "canonical_source_ref": "canon/record-1",
            "canonical_fact_fingerprint": "abc123",
            "adapters": [
                {"id": "public", "fact_fingerprint": "abc123", "provenance_state": "PASS", "private_field_leakage": False},
                {"id": "ops", "fact_fingerprint": "abc123", "provenance_state": "PASS", "private_field_leakage": False},
            ],
        })
        return case

    def test_compiler_survives_only_as_bounded_contract(self):
        report = module.evaluate(self.compiler_case())
        self.assertEqual(report["disposition"], "COMPOSE_BOUNDED_ADAPTER_CONTRACT")

    def test_compiler_dies_on_fact_drift(self):
        case = self.compiler_case()
        case["adapters"][1]["fact_fingerprint"] = "drifted"
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "STANDBY_RESEARCH")
        self.assertIn("FACT_DRIFT:ops", report["blocking_states"])

    def test_compiler_dies_on_private_leak(self):
        case = self.compiler_case()
        case["adapters"][0]["private_field_leakage"] = True
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "STANDBY_RESEARCH")
        self.assertIn("PRIVATE_FIELD_LEAKAGE:public", report["blocking_states"])

    def test_reentry_router_refuses_correlation_as_root_cause(self):
        case = self.base("EXT03_BOTTLENECK_REENTRY_ROUTING")
        case.update({
            "observed_failure_stage": "POST_DEPLOY_METRIC",
            "causality_state": "CORRELATED_ONLY",
            "proposed_reentry": "POST_DEPLOY_DEBUG",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "ANALYSIS_REOPEN")
        self.assertNotIn("WRONG_REENTRY_ROUTE", report["blocking_states"])

    def test_reentry_router_rejects_wrong_local_gate(self):
        case = self.base("EXT03_BOTTLENECK_REENTRY_ROUTING")
        case.update({
            "observed_failure_stage": "DEPLOYMENT",
            "causality_state": "PROVEN",
            "proposed_reentry": "DA_COUNTER_DA",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "REJECT_ROUTE")
        self.assertIn("WRONG_REENTRY_ROUTE", report["blocking_states"])

    def test_reentry_router_survives_for_proven_stage(self):
        case = self.base("EXT03_BOTTLENECK_REENTRY_ROUTING")
        case.update({
            "observed_failure_stage": "IMPLEMENTATION",
            "causality_state": "PROVEN",
            "proposed_reentry": "DA_COUNTER_DA",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "COMPOSE_TYPED_REENTRY_ROUTER")

    def test_scale_business_gain_cannot_outrank_safety(self):
        case = self.base("EXT04_SCALE_PROOF_GATE")
        case.update({
            "safety_state": "FAIL",
            "correctness_state": "PASS",
            "local_loop_proof": "PASS",
            "scale_guardrails": "PASS",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "BLOCK_SCALE")
        self.assertIn("SAFETY_OR_CORRECTNESS_NOT_PROVEN", report["blocking_states"])

    def test_scale_dependent_learning_is_not_blocked_by_universal_local_rule(self):
        case = self.base("EXT04_SCALE_PROOF_GATE")
        case.update({
            "safety_state": "PASS",
            "correctness_state": "PASS",
            "local_loop_proof": "NOT_PROVEN",
            "behavior_scale_dependent": True,
            "scale_guardrails": "PASS",
            "bounded_scale_probe": "AUTHORIZED",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "BOUNDED_SCALE_PROBE_ONLY")

    def test_proven_local_loop_can_enter_bounded_scale_profile(self):
        case = self.base("EXT04_SCALE_PROOF_GATE")
        case.update({
            "safety_state": "PASS",
            "correctness_state": "PASS",
            "local_loop_proof": "PASS",
            "behavior_scale_dependent": False,
            "scale_guardrails": "PASS",
        })
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "COMPOSE_BOUNDED_SCALE_PROFILE")

    def succession_case(self) -> dict:
        case = self.base("EXT05_DECISION_CAPABILITY_SUCCESSION")
        case.update({
            "canonical_material_state": "PASS",
            "retrieval_state": "PASS",
            "held_out_decision_state": "PASS",
            "authority_compliance_state": "PASS",
            "escalation_state": "PASS",
            "creator_intervention": False,
        })
        return case

    def test_retrieval_alone_is_not_successor_competence(self):
        case = self.succession_case()
        case["held_out_decision_state"] = "NOT_TESTED"
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "STANDBY_RESEARCH")
        self.assertIn("RETRIEVAL_NOT_COMPETENCE", report["blocking_states"])
        self.assertIn("HELD_OUT_DECISIONS_UNPROVEN", report["blocking_states"])

    def test_successor_must_respect_authority(self):
        case = self.succession_case()
        case["authority_compliance_state"] = "FAIL"
        report = module.evaluate(case)
        self.assertEqual(report["disposition"], "STANDBY_RESEARCH")
        self.assertIn("SUCCESSOR_AUTHORITY_COMPLIANCE_UNPROVEN", report["blocking_states"])

    def test_decision_succession_survives_as_phoenix_extension_candidate(self):
        report = module.evaluate(self.succession_case())
        self.assertEqual(report["disposition"], "COMPOSE_PHOENIX_SUCCESSION_EXTENSION")
        self.assertFalse(report["canonical_promotion_authorized"])


if __name__ == "__main__":
    unittest.main()
