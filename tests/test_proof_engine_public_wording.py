from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.public_wording import (
    CHECKPOINT_PATH,
    MANIFEST_PATH,
    build_public_wording_draft,
    render_public_wording_markdown,
    verify_public_wording_draft,
)
from proof_engine_pilot.public_wording_cli import build_parser


class PublicWordingTests(unittest.TestCase):
    def test_committed_public_wording_draft_is_verified(self):
        bundle = verify_public_wording_draft()
        draft = bundle["draft"]
        self.assertEqual(draft["wording_count"], 6)
        self.assertEqual(draft["review_gate"]["state"], "PUBLICATION_REVIEW_REQUIRED")
        self.assertEqual(draft["output"]["publication_status"], "NOT_PUBLISHED")
        self.assertEqual(bundle["checkpoint"]["state"], "PUBLICATION_REVIEW_REQUIRED")
        self.assertFalse(bundle["checkpoint"]["publication_performed"])
        self.assertFalse(bundle["checkpoint"]["external_actions_performed"])

    def test_all_six_reviewed_assets_are_covered_once(self):
        draft = build_public_wording_draft()
        asset_ids = [item["source_asset"]["asset_id"] for item in draft["wordings"]]
        self.assertEqual(asset_ids, [f"ASSET-{index:03d}" for index in range(1, 7)])
        self.assertEqual(len(asset_ids), len(set(asset_ids)))

    def test_markdown_is_deterministic_and_not_published(self):
        bundle = verify_public_wording_draft()
        markdown = render_public_wording_markdown(bundle["draft"])
        self.assertEqual(markdown, bundle["markdown"])
        self.assertIn("Status: NOT PUBLISHED", markdown)
        self.assertIn("Publication, outreach, contracts", markdown)
        self.assertEqual(fingerprint(markdown), bundle["manifest"]["expected_markdown_fingerprint"])

    def test_resigned_publication_authority_fails_closed(self):
        draft = build_public_wording_draft()
        draft["authority"]["publication_authorized"] = True
        material = copy.deepcopy(draft)
        material.pop("draft_fingerprint")
        draft["draft_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "deterministic aggregation"):
            verify_public_wording_draft(draft=draft)

    def test_manufactured_review_decision_fails_closed(self):
        draft = build_public_wording_draft()
        draft["review_gate"]["decisions"] = [{"decision": "APPROVE_FOR_PUBLICATION"}]
        material = copy.deepcopy(draft)
        material.pop("draft_fingerprint")
        draft["draft_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "deterministic aggregation"):
            verify_public_wording_draft(draft=draft)

    def test_resigned_published_checkpoint_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["publication_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "unauthorized action"):
            verify_public_wording_draft(checkpoint=checkpoint)

    def test_manifest_rejects_wording_count_change(self):
        manifest = copy.deepcopy(load(MANIFEST_PATH))
        manifest["wording_count"] = 5
        material = copy.deepcopy(manifest)
        material.pop("manifest_fingerprint")
        manifest["manifest_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "manifest mismatch"):
            verify_public_wording_draft(manifest=manifest)

    def test_cli_has_no_publish_or_approve_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"generate", "render-markdown", "verify", "summary", "review-template"})


if __name__ == "__main__":
    unittest.main()
