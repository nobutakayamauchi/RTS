from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_productization_spec_v2 import (
    build_internal_productization_spec_v2,
    build_pilot_package_review_template,
    verify_internal_productization_spec_v2,
    verify_post_build_acceptance_contract,
    verify_pre_build_review_contract,
)


class CorrectedProductizationSpecTests(unittest.TestCase):
    def test_pre_build_and_post_build_reviews_are_separate(self):
        bundle = verify_internal_productization_spec_v2()
        self.assertEqual(bundle["summary"]["state"], "HUMAN_PILOT_PACKAGE_BUILD_REVIEW_REQUIRED")
        self.assertEqual(bundle["summary"]["counts"]["pre_build_review_criteria"], 6)
        self.assertEqual(bundle["summary"]["counts"]["post_build_acceptance_criteria"], 15)
        template = bundle["review_template"]
        self.assertEqual(
            [item["criterion_id"] for item in template["criteria_results"]],
            [f"BLD-{number:03d}" for number in range(1, 7)],
        )
        self.assertEqual(template["post_build_acceptance_results"], [])
        self.assertIsNone(template["decision"])
        self.assertFalse(template["pilot_package_build_authorized"])

    def test_post_build_contract_cannot_authorize_build(self):
        bundle = build_internal_productization_spec_v2()
        allowed = bundle["acceptance"]["decision_contract"]["allowed_decisions"]
        self.assertIn("ACCEPT_PILOT_PACKAGE", allowed)
        self.assertNotIn("APPROVE_PILOT_PACKAGE_BUILD", allowed)
        self.assertEqual(bundle["acceptance"]["decision_contract"]["review_stage"], "POST_BUILD_PACKAGE_ACCEPTANCE")

    def test_pre_build_contract_fails_closed_on_resigned_authority_widening(self):
        contract = copy.deepcopy(build_internal_productization_spec_v2()["pre_build"])
        contract["authority"]["pricing_authorized"] = True
        contract["contract_fingerprint"] = fingerprint({
            key: value for key, value in contract.items() if key != "contract_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_pre_build_review_contract(contract)

    def test_post_build_contract_fails_closed_on_missing_criterion(self):
        contract = copy.deepcopy(build_internal_productization_spec_v2()["acceptance"])
        contract["criteria"].pop()
        contract["contract_fingerprint"] = fingerprint({
            key: value for key, value in contract.items() if key != "contract_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_post_build_acceptance_contract(contract)

    def test_checkpoint_fails_closed_on_unknown_field(self):
        bundle = verify_internal_productization_spec_v2()
        checkpoint = copy.deepcopy(bundle["checkpoint"])
        checkpoint["unknown"] = False
        checkpoint["checkpoint_fingerprint"] = fingerprint({
            key: value for key, value in checkpoint.items() if key != "checkpoint_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_internal_productization_spec_v2(checkpoint=checkpoint)

    def test_review_template_does_not_manufacture_post_build_results(self):
        template = build_pilot_package_review_template()
        self.assertEqual(template["review_stage"], "PRE_BUILD_AUTHORIZATION")
        self.assertEqual(template["post_build_acceptance_results"], [])
        self.assertIsNone(template["selected_case_report_fingerprint"])
        self.assertFalse(template["privacy_boundary_confirmed"])
        self.assertFalse(template["rollback_confirmed"])


if __name__ == "__main__":
    unittest.main()
