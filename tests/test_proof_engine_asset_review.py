from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.asset_review import (
    CHECKPOINT_PATH,
    INDEX_PATH,
    SUMMARY_PATH,
    verify_asset_review,
)
from proof_engine_pilot.asset_review_cli import build_parser
from proof_engine_pilot.core import ProofEngineError, fingerprint, load


class AssetReviewTests(unittest.TestCase):
    def test_committed_review_approves_six_internal_sources(self):
        bundle = verify_asset_review()
        self.assertEqual(bundle["summary"]["counts"]["approved"], 6)
        self.assertEqual(bundle["summary"]["review_state"], "ALL_INTERNAL_ASSETS_APPROVED")
        self.assertEqual(bundle["summary"]["publication_status"], "NOT_PUBLISHED")
        self.assertFalse(bundle["checkpoint"]["publication_performed"])
        self.assertFalse(bundle["checkpoint"]["external_actions_performed"])
        self.assertTrue(bundle["checkpoint"]["original_internal_assets_preserved"])

    def test_resigned_authority_widening_fails_closed(self):
        index = copy.deepcopy(load(INDEX_PATH))
        summary = copy.deepcopy(load(SUMMARY_PATH))
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        segment_path = index["segments"][0]["path"]
        segment = copy.deepcopy(load(INDEX_PATH.parent.parent.parent / "asset_reviews" / "round_0001" / "decisions" / "segment_001.json"))

        segment["decisions"][0]["authority"]["publication_authorized"] = True
        previous = None
        by_asset = {}
        for decision in segment["decisions"]:
            decision["previous_decision_fingerprint"] = previous
            material = copy.deepcopy(decision)
            material.pop("decision_fingerprint")
            decision["decision_fingerprint"] = fingerprint(material)
            previous = decision["decision_fingerprint"]
            by_asset[decision["target"]["asset_id"]] = decision
        material = copy.deepcopy(segment)
        material.pop("segment_fingerprint")
        segment["segment_fingerprint"] = fingerprint(material)

        index["segments"][0]["segment_fingerprint"] = segment["segment_fingerprint"]
        index["last_decision_fingerprint"] = previous
        material = copy.deepcopy(index)
        material.pop("decision_index_fingerprint")
        index["decision_index_fingerprint"] = fingerprint(material)

        summary["decision_index_fingerprint"] = index["decision_index_fingerprint"]
        for item in summary["effective_assets"]:
            item["decision_fingerprint"] = by_asset[item["asset_id"]]["decision_fingerprint"]
        material = copy.deepcopy(summary)
        material.pop("summary_fingerprint")
        summary["summary_fingerprint"] = fingerprint(material)

        checkpoint["decision_index_fingerprint"] = index["decision_index_fingerprint"]
        checkpoint["summary_fingerprint"] = summary["summary_fingerprint"]
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)

        with self.assertRaisesRegex(ProofEngineError, "authority widened"):
            verify_asset_review(
                index=index,
                summary=summary,
                checkpoint=checkpoint,
                segment_overrides={segment_path: segment},
            )

    def test_resigned_external_action_checkpoint_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["external_actions_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "unauthorized action"):
            verify_asset_review(checkpoint=checkpoint)

    def test_cli_has_no_approve_or_publish_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary", "effective"})


if __name__ == "__main__":
    unittest.main()
