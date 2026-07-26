from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.asset_review import (
    CHECKPOINT_PATH,
    INDEX_PATH,
    SEGMENT_PATH,
    SUMMARY_PATH,
    verify_asset_review,
)
from proof_engine_pilot.asset_review_cli import build_parser
from proof_engine_pilot.core import ProofEngineError, fingerprint, load


class AssetReviewTests(unittest.TestCase):
    def _resigned_bundle(self, mutate_decisions=None, mutate_index=None, mutate_summary=None, mutate_checkpoint=None):
        index = copy.deepcopy(load(INDEX_PATH))
        summary = copy.deepcopy(load(SUMMARY_PATH))
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        segment = copy.deepcopy(load(INDEX_PATH.parent / "decisions" / "segment_001.json"))

        if mutate_decisions:
            mutate_decisions(segment["decisions"])
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
        if mutate_index:
            mutate_index(index)
        material = copy.deepcopy(index)
        material.pop("decision_index_fingerprint")
        index["decision_index_fingerprint"] = fingerprint(material)

        summary["decision_index_fingerprint"] = index["decision_index_fingerprint"]
        for item in summary["effective_assets"]:
            item["decision_fingerprint"] = by_asset[item["asset_id"]]["decision_fingerprint"]
        if mutate_summary:
            mutate_summary(summary)
        material = copy.deepcopy(summary)
        material.pop("summary_fingerprint")
        summary["summary_fingerprint"] = fingerprint(material)

        checkpoint["decision_index_fingerprint"] = index["decision_index_fingerprint"]
        checkpoint["summary_fingerprint"] = summary["summary_fingerprint"]
        if mutate_checkpoint:
            mutate_checkpoint(checkpoint)
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        return index, summary, checkpoint, {SEGMENT_PATH: segment}

    def test_committed_review_approves_six_internal_sources(self):
        bundle = verify_asset_review()
        self.assertEqual(bundle["summary"]["counts"]["approved"], 6)
        self.assertEqual(bundle["summary"]["review_state"], "ALL_INTERNAL_ASSETS_APPROVED")
        self.assertEqual(bundle["summary"]["publication_status"], "NOT_PUBLISHED")
        self.assertTrue(all(item["authored_by"]["type"] == "HUMAN" for item in bundle["decisions"]))
        self.assertFalse(bundle["checkpoint"]["publication_performed"])
        self.assertFalse(bundle["checkpoint"]["external_actions_performed"])
        self.assertTrue(bundle["checkpoint"]["original_internal_assets_preserved"])

    def test_resigned_authority_widening_fails_closed(self):
        bundle = self._resigned_bundle(
            mutate_decisions=lambda decisions: decisions[0]["authority"].__setitem__("publication_authorized", True)
        )
        with self.assertRaisesRegex(ProofEngineError, "authority widened"):
            verify_asset_review(index=bundle[0], summary=bundle[1], checkpoint=bundle[2], segment_overrides=bundle[3])

    def test_resigned_nonhuman_author_fails_closed(self):
        def mutate(decisions):
            decisions[0]["authored_by"] = {
                "type": "AI",
                "identity": "generated-reviewer",
                "identity_source": "AUTOMATIC",
                "role": "SYSTEM",
            }
        bundle = self._resigned_bundle(mutate_decisions=mutate)
        with self.assertRaisesRegex(ProofEngineError, "explicit human instruction"):
            verify_asset_review(index=bundle[0], summary=bundle[1], checkpoint=bundle[2], segment_overrides=bundle[3])

    def test_resigned_round_identity_fails_closed(self):
        bundle = self._resigned_bundle(
            mutate_index=lambda index: index.__setitem__("review_round_id", "OTHER-ROUND")
        )
        with self.assertRaisesRegex(ProofEngineError, "index identity mismatch"):
            verify_asset_review(index=bundle[0], summary=bundle[1], checkpoint=bundle[2], segment_overrides=bundle[3])

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
