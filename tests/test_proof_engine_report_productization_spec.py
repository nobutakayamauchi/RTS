from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_productization_spec import (
    build_internal_productization_spec,
    build_pilot_package_review_template,
    verify_acceptance_contract,
    verify_internal_productization_spec,
    verify_product_spec_build_contract,
    verify_product_specification,
)
from proof_engine_pilot.report_productization_spec_cli import build_parser


def resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result[field] = fingerprint({key: item for key, item in result.items() if key != field})
    return result


class InternalProductSpecificationTests(unittest.TestCase):
    def test_specification_verifies_and_stops_at_human_gate(self):
        bundle = verify_internal_productization_spec()
        self.assertEqual(
            bundle["summary"]["state"],
            "HUMAN_PILOT_PACKAGE_BUILD_REVIEW_REQUIRED",
        )
        self.assertEqual(bundle["summary"]["counts"], {
            "required_sections": 9,
            "workflow_steps": 8,
            "acceptance_criteria": 15,
            "commercial_unknowns": 7,
            "effective_achievement_records_in_source_pack": 16,
            "withheld_claims_in_source_pack": 5,
        })
        self.assertEqual(
            bundle["spec"]["target"]["first_delivery_mode"],
            "OPERATOR_ASSISTED_SINGLE_CASE",
        )
        self.assertEqual(bundle["spec"]["target"]["pricing_status"], "UNDECIDED")
        self.assertFalse(bundle["summary"]["pilot_package_build_authorized"])
        self.assertFalse(bundle["summary"]["external_actions_performed"])
        self.assertIn("Pilot package build authorized: false", bundle["markdown"])

    def test_build_contract_fails_closed_on_authority_widening_when_resigned(self):
        contract = copy.deepcopy(build_internal_productization_spec()["build_contract"])
        contract["authority"]["pricing_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_product_spec_build_contract(resign(contract, "contract_fingerprint"))

    def test_spec_fails_closed_on_manufactured_pricing_when_resigned(self):
        specification = copy.deepcopy(build_internal_productization_spec()["spec"])
        specification["target"]["pricing_status"] = "PRICED"
        with self.assertRaises(ProofEngineError):
            verify_product_specification(resign(specification, "spec_fingerprint"))

    def test_acceptance_fails_closed_on_manufactured_human_decision(self):
        contract = copy.deepcopy(build_internal_productization_spec()["acceptance"])
        contract["decision_contract"]["decisions"] = [{"decision": "APPROVE_PILOT_PACKAGE_BUILD"}]
        with self.assertRaises(ProofEngineError):
            verify_acceptance_contract(resign(contract, "contract_fingerprint"))

    def test_acceptance_fails_closed_on_missing_criterion(self):
        contract = copy.deepcopy(build_internal_productization_spec()["acceptance"])
        contract["criteria"].pop()
        with self.assertRaises(ProofEngineError):
            verify_acceptance_contract(resign(contract, "contract_fingerprint"))

    def test_checkpoint_fails_closed_on_unknown_field(self):
        checkpoint = copy.deepcopy(verify_internal_productization_spec()["checkpoint"])
        checkpoint["unknown"] = False
        with self.assertRaises(ProofEngineError):
            verify_internal_productization_spec(
                checkpoint=resign(checkpoint, "checkpoint_fingerprint")
            )

    def test_checkpoint_fails_closed_on_external_action(self):
        checkpoint = copy.deepcopy(verify_internal_productization_spec()["checkpoint"])
        checkpoint["publication_performed"] = True
        with self.assertRaises(ProofEngineError):
            verify_internal_productization_spec(
                checkpoint=resign(checkpoint, "checkpoint_fingerprint")
            )

    def test_review_template_does_not_manufacture_decision(self):
        template = build_pilot_package_review_template()
        self.assertIsNone(template["decision"])
        self.assertIsNone(template["reviewer_identity"])
        self.assertFalse(template["pilot_package_build_authorized"])
        self.assertFalse(template["pricing_authorized"])
        self.assertFalse(template["delivery_authorized"])
        self.assertEqual(len(template["criteria_results"]), 15)

    def test_cli_has_no_build_price_publish_or_delivery_command(self):
        parser = build_parser()
        choices = parser._subparsers._group_actions[0].choices
        self.assertEqual(
            set(choices),
            {"verify", "summary", "spec", "acceptance", "review-template", "render-markdown"},
        )
        for forbidden in (
            "build",
            "approve",
            "price",
            "outreach",
            "contract",
            "deliver",
            "publish",
        ):
            self.assertNotIn(forbidden, choices)


if __name__ == "__main__":
    unittest.main()
