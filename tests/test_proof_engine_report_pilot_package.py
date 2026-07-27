from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint
from proof_engine_pilot.report_pilot_package_cli import build_parser
from proof_engine_pilot.report_pilot_package_v2 import (
    build_pilot_package,
    verify_build_decision,
    verify_case_intake,
    verify_pilot_package,
)


class PilotPackageTests(unittest.TestCase):
    def test_package_builds_and_stops_at_human_acceptance(self):
        bundle = verify_pilot_package()
        self.assertEqual(bundle["summary"]["state"], "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT")
        self.assertEqual(bundle["summary"]["next_gate"], "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED")
        self.assertEqual(bundle["summary"]["repository"], "nobutakayamauchi/seminar-compass")
        self.assertEqual(bundle["summary"]["counts"], {
            "artifacts": 7,
            "report_sections": 9,
            "achievement_records": 6,
            "withheld_claims": 0,
            "acceptance_criteria": 15,
            "automated_pass": 6,
            "pending_human": 9,
        })
        self.assertFalse(bundle["summary"]["package_accepted"])
        self.assertFalse(bundle["summary"]["external_actions_performed"])

    def test_report_and_acceptance_packet_are_complete_but_unaccepted(self):
        bundle = build_pilot_package()
        self.assertEqual(len(bundle["report_json"]["sections"]), 9)
        for heading in (
            "### 1. Executive summary",
            "### 2. Repository scope",
            "### 3. Methodology",
            "### 4. Evidence inventory",
            "### 5. Effective achievement records",
            "### 6. Human and AI contribution map",
            "### 7. Withheld or unsupported claims",
            "### 8. Limitations",
            "### 9. Human review decision",
        ):
            self.assertEqual(bundle["report_markdown"].count(heading), 1)
        packet = bundle["acceptance_packet"]
        self.assertEqual(len(packet["criteria_results"]), 15)
        self.assertTrue(all(item["result"] is None for item in packet["criteria_results"]))
        self.assertIsNone(packet["decision"])
        self.assertFalse(packet["package_accepted"])

    def test_automated_verification_does_not_replace_human_criteria(self):
        summary = build_pilot_package()["verification_summary"]
        results = {item["criterion_id"]: item["result"] for item in summary["checks"]}
        self.assertEqual(sum(value == "PASS" for value in results.values()), 6)
        self.assertEqual(sum(value == "PENDING_HUMAN" for value in results.values()), 9)
        self.assertFalse(summary["package_accepted"])

    def test_build_decision_fails_closed_on_resigned_delivery_authority(self):
        decision = copy.deepcopy(build_pilot_package()["decision"])
        decision["delivery_authorized"] = True
        decision["decision_fingerprint"] = fingerprint({
            key: value for key, value in decision.items() if key != "decision_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_build_decision(decision)

    def test_case_intake_fails_closed_on_repository_substitution(self):
        intake = copy.deepcopy(build_pilot_package()["intake"])
        intake["source"]["repository"] = "other/repository"
        intake["intake_fingerprint"] = fingerprint({
            key: value for key, value in intake.items() if key != "intake_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_case_intake(intake)

    def test_checkpoint_fails_closed_on_external_action(self):
        bundle = verify_pilot_package()
        checkpoint = copy.deepcopy(bundle["checkpoint"])
        checkpoint["publication_performed"] = True
        checkpoint["checkpoint_fingerprint"] = fingerprint({
            key: value for key, value in checkpoint.items() if key != "checkpoint_fingerprint"
        })
        with self.assertRaises(ProofEngineError):
            verify_pilot_package(checkpoint=checkpoint)

    def test_cli_has_no_accept_deliver_publish_price_or_outreach_command(self):
        choices = build_parser()._subparsers._group_actions[0].choices
        self.assertEqual(set(choices), {
            "build-summary", "verify", "summary", "generate", "render-markdown",
            "evidence-inventory", "acceptance-template", "verification-summary", "package-index",
        })
        for forbidden in ("accept", "approve", "deliver", "publish", "price", "outreach", "contract"):
            self.assertNotIn(forbidden, choices)


if __name__ == "__main__":
    unittest.main()
