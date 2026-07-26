from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.cross_repo_validation import (
    CAMPAIGN_PATH,
    CHECKPOINT_PATH,
    ROUND_ORDER,
    build_parser,
    generate_run,
    verify_bundle,
    verify_campaign,
)


class CrossRepositoryValidationTests(unittest.TestCase):
    def test_committed_three_repository_bundle_is_verified(self):
        bundle = verify_bundle()
        self.assertEqual(bundle["run"]["candidate_count"], 16)
        self.assertEqual(bundle["checkpoint"]["completed_rounds"], ROUND_ORDER)
        self.assertEqual(bundle["checkpoint"]["state"], "THREE_REPOSITORY_HUMAN_REVIEW_REQUIRED")
        self.assertFalse(bundle["checkpoint"]["publication_performed"])
        self.assertFalse(bundle["checkpoint"]["original_source_repositories_modified"])

    def test_rounds_execute_in_order_with_expected_roles(self):
        run = verify_bundle()["run"]
        self.assertEqual([item["round_id"] for item in run["rounds"]], ROUND_ORDER)
        self.assertEqual([item["role"] for item in run["rounds"]], [
            "GENERALIZATION_TEST",
            "PRIVATE_BUSINESS_REPOSITORY_TEST",
            "NEGATIVE_CONTROL",
        ])
        self.assertEqual(run["comparison"]["candidate_count_by_round"], {"ROUND-2": 6, "ROUND-3": 8, "ROUND-4": 2})

    def test_unmerged_seminar_prs_are_excluded_from_candidate_evidence(self):
        round_two = verify_bundle()["run"]["rounds"][0]
        self.assertEqual(round_two["excluded_unmerged_prs"], [17, 18])
        used = {number for candidate in round_two["candidates"] for number in candidate["evidence_prs"]}
        self.assertFalse({17, 18} & used)

    def test_negative_control_withholds_unverified_completion_claims(self):
        round_four = verify_bundle()["run"]["rounds"][2]
        self.assertEqual(round_four["candidate_count"], 2)
        self.assertEqual(len(round_four["withheld_claims"]), 3)
        text = " ".join(item["claim"] for item in round_four["withheld_claims"])
        self.assertIn("end-to-end", text)
        self.assertIn("production-ready", text)

    def test_private_repository_uses_metadata_only_snapshot(self):
        round_three = verify_bundle()["run"]["rounds"][1]
        self.assertEqual(round_three["visibility"], "PRIVATE")
        self.assertEqual(round_three["source_mode"], "READ_ONLY_METADATA_SNAPSHOT")
        self.assertFalse(verify_bundle()["checkpoint"]["private_repository_payload_copied"])

    def test_learning_preflight_is_applied_before_commit(self):
        campaign = verify_campaign()
        for round_value in campaign["rounds"]:
            for candidate in round_value["candidates"]:
                self.assertIn("record_kind", candidate)
                self.assertIn("factuality_note", candidate)
                self.assertIn("contribution_map", candidate)

    def test_resigned_campaign_cannot_use_unmerged_pr_as_evidence(self):
        campaign = copy.deepcopy(load(CAMPAIGN_PATH))
        campaign["rounds"][0]["candidates"][0]["evidence_prs"].append(17)
        material = copy.deepcopy(campaign)
        material.pop("campaign_fingerprint")
        campaign["campaign_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "unmerged or out-of-scope"):
            verify_campaign(campaign)

    def test_resigned_checkpoint_target_write_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["target_repository_writes_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "exceeded boundary"):
            verify_bundle(checkpoint=checkpoint)

    def test_unknown_checkpoint_action_field_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["provider_execution_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "schema fields mismatch"):
            verify_bundle(checkpoint=checkpoint)

    def test_committed_run_is_deterministic(self):
        self.assertEqual(verify_bundle()["run"], generate_run())

    def test_cli_has_no_apply_publish_or_write_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "review-template"})


if __name__ == "__main__":
    unittest.main()
