from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_pilot_acceptance import (
    build_pilot_acceptance_review,
    verify_acceptance_decision,
    verify_pilot_acceptance,
)
from proof_engine_pilot.report_pilot_acceptance_cli import build_parser
from proof_engine_pilot.report_pilot_package_v2 import verify_pilot_package


def resign(value: dict, field: str) -> dict:
    result = copy.deepcopy(value)
    result[field] = fingerprint({key: item for key, item in result.items() if key != field})
    return result


class PilotPackageAcceptanceTests(unittest.TestCase):
    def test_acceptance_verifies_all_criteria_and_stops_before_external_work(self):
        bundle = verify_pilot_acceptance()
        self.assertEqual(bundle["summary"]["state"], "INTERNAL_PILOT_PACKAGE_ACCEPTED")
        self.assertEqual(
            bundle["summary"]["next_gate"],
            "HUMAN_INTERNAL_OPERATIONAL_VALIDATION_PLAN_REVIEW_REQUIRED",
        )
        self.assertTrue(bundle["summary"]["package_accepted"])
        self.assertEqual(bundle["summary"]["counts"], {
            "criteria": 15,
            "criteria_passed": 15,
            "automated_criteria": 6,
            "human_or_combined_criteria": 9,
            "artifacts": 7,
            "achievement_records": 6,
            "withheld_claims": 0,
        })
        self.assertTrue(all(item["result"] == "PASS" for item in bundle["decision"]["criteria_results"]))
        self.assertFalse(bundle["decision"]["pricing_authorized"])
        self.assertFalse(bundle["decision"]["delivery_authorized"])
        self.assertFalse(bundle["decision"]["publication_authorized"])
        self.assertIn("Package accepted for internal single-case use: true", bundle["markdown"])

    def test_decision_fails_closed_on_missing_criterion_when_resigned(self):
        decision = copy.deepcopy(build_pilot_acceptance_review()["decision"])
        decision["criteria_results"].pop()
        with self.assertRaises(ProofEngineError):
            verify_acceptance_decision(resign(decision, "decision_fingerprint"))

    def test_decision_fails_closed_on_authority_widening_when_resigned(self):
        decision = copy.deepcopy(build_pilot_acceptance_review()["decision"])
        decision["pricing_authorized"] = True
        with self.assertRaises(ProofEngineError):
            verify_acceptance_decision(resign(decision, "decision_fingerprint"))

    def test_review_fails_closed_when_excluded_pr_supports_claim(self):
        package = copy.deepcopy(verify_pilot_package())
        package["report_json"]["sections"]["effective_achievement_records"][0]["evidence_prs"].append(17)
        with self.assertRaises(ProofEngineError):
            verify_acceptance_decision(package=package)

    def test_review_fails_closed_when_factuality_boundary_is_removed(self):
        package = copy.deepcopy(verify_pilot_package())
        package["report_json"]["sections"]["effective_achievement_records"][0]["evidence_boundary"] = ""
        with self.assertRaises(ProofEngineError):
            verify_acceptance_decision(package=package)

    def test_checkpoint_fails_closed_on_unknown_field(self):
        checkpoint = copy.deepcopy(verify_pilot_acceptance()["checkpoint"])
        checkpoint["unknown"] = False
        with self.assertRaises(ProofEngineError):
            verify_pilot_acceptance(checkpoint=resign(checkpoint, "checkpoint_fingerprint"))

    def test_checkpoint_fails_closed_on_external_action(self):
        checkpoint = copy.deepcopy(verify_pilot_acceptance()["checkpoint"])
        checkpoint["publication_performed"] = True
        with self.assertRaises(ProofEngineError):
            verify_pilot_acceptance(checkpoint=resign(checkpoint, "checkpoint_fingerprint"))

    def test_cli_exposes_review_outputs_but_no_external_action(self):
        parser = build_parser()
        choices = parser._subparsers._group_actions[0].choices
        self.assertEqual(set(choices), {"verify", "decision", "summary", "render-markdown"})
        for forbidden in (
            "price",
            "outreach",
            "contract",
            "deliver",
            "publish",
            "execute",
            "write-target",
        ):
            self.assertNotIn(forbidden, choices)


if __name__ == "__main__":
    unittest.main()
