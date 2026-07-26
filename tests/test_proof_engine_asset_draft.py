from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.asset_cli import build_parser
from proof_engine_pilot.asset_draft import build_internal_asset_draft, verify_internal_asset_draft
from proof_engine_pilot.core import ProofEngineError, fingerprint


class InternalAssetDraftTests(unittest.TestCase):
    def test_committed_draft_is_verified(self):
        value = verify_internal_asset_draft()
        self.assertEqual(value["asset_count"], 6)
        self.assertEqual(value["coverage"]["effective_candidate_count"], 12)
        self.assertTrue(value["coverage"]["all_effective_candidates_covered_once"])
        self.assertEqual(value["review_gate"]["state"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(value["output"]["publication_status"], "NOT_PUBLISHED")

    def test_generation_is_deterministic(self):
        self.assertEqual(build_internal_asset_draft(), verify_internal_asset_draft())

    def test_every_asset_passes_learning_preflight(self):
        value = verify_internal_asset_draft()
        self.assertTrue(all(item["result"] == "PASS" for item in value["learning_preflight"]["asset_results"]))
        self.assertTrue(all(item["issues"] == [] for item in value["learning_preflight"]["asset_results"]))

    def test_all_twelve_effective_candidates_are_covered_once(self):
        value = verify_internal_asset_draft()
        covered = [
            ref["candidate_id"]
            for asset in value["assets"]
            for ref in asset["source_candidates"]
        ]
        self.assertEqual(len(covered), 12)
        self.assertEqual(len(set(covered)), 12)
        self.assertEqual(sorted(covered), [f"ACH-{index:03d}" for index in range(1, 13)])

    def test_publication_or_manufactured_decision_fails_closed(self):
        value = copy.deepcopy(verify_internal_asset_draft())
        value["output"]["publication_status"] = "PUBLISHED"
        value["review_gate"]["decisions"] = [{"decision": "APPROVE"}]
        material = copy.deepcopy(value)
        material.pop("draft_fingerprint")
        value["draft_fingerprint"] = fingerprint(material)
        with self.assertRaises(ProofEngineError):
            verify_internal_asset_draft(draft=value)

    def test_cli_has_no_publish_apply_or_approve_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"generate", "verify", "summary", "review-template"})


if __name__ == "__main__":
    unittest.main()
