from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.core import ProofEngineError, fingerprint, load
from proof_engine_pilot.release import (
    AUTHORIZATION_PATH,
    CHECKPOINT_PATH,
    DOCUMENT_PATH,
    EXPECTED_DOCUMENT_FINGERPRINT,
    render_release_markdown,
    verify_publication_release,
)
from proof_engine_pilot.release_cli import build_parser


class PublicationReleaseTests(unittest.TestCase):
    def test_committed_release_is_public_and_bounded(self):
        bundle = verify_publication_release()
        checkpoint = bundle["checkpoint"]
        self.assertEqual(checkpoint["state"], "PUBLISHED_TO_AUTHORIZED_REPOSITORY_DOCUMENT")
        self.assertTrue(checkpoint["publication_performed"])
        self.assertTrue(checkpoint["external_actions_performed"])
        self.assertEqual(checkpoint["published_wording_count"], 6)
        self.assertEqual(checkpoint["document_fingerprint"], EXPECTED_DOCUMENT_FINGERPRINT)
        self.assertFalse(checkpoint["social_posting_performed"])
        self.assertFalse(checkpoint["direct_outreach_performed"])
        self.assertFalse(checkpoint["contract_action_performed"])
        self.assertFalse(checkpoint["adjacent_repository_write_performed"])

    def test_document_is_deterministically_rendered_from_effective_wordings(self):
        document = DOCUMENT_PATH.read_text(encoding="utf-8")
        self.assertEqual(document, render_release_markdown())
        self.assertEqual(fingerprint(document), EXPECTED_DOCUMENT_FINGERPRINT)
        self.assertEqual(document.count("\n## "), 6)

    def test_human_authorization_is_exact_and_surface_is_single_path(self):
        authorization = load(AUTHORIZATION_PATH)
        self.assertEqual(authorization["human_authorization"]["instruction"], "じゃとりあえずこれもやろっか。")
        self.assertEqual(authorization["release_surface"]["exact_path"], "docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md")
        self.assertEqual(authorization["restrictions"]["allowed_publication_paths"], ["docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md"])
        self.assertFalse(authorization["release_surface"]["root_readme_link_authorized"])

    def test_resigned_authority_widening_fails_closed(self):
        authorization = copy.deepcopy(load(AUTHORIZATION_PATH))
        authorization["authority"]["social_posting_authorized"] = True
        material = copy.deepcopy(authorization)
        material.pop("authorization_fingerprint")
        authorization["authorization_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "fingerprint is not approved|authority widened"):
            verify_publication_release(authorization=authorization)

    def test_altered_public_document_fails_closed(self):
        document = DOCUMENT_PATH.read_text(encoding="utf-8") + "\nUnapproved addition.\n"
        with self.assertRaisesRegex(ProofEngineError, "does not match"):
            verify_publication_release(document_text=document)

    def test_resigned_checkpoint_scope_expansion_fails_closed(self):
        checkpoint = copy.deepcopy(load(CHECKPOINT_PATH))
        checkpoint["direct_outreach_performed"] = True
        material = copy.deepcopy(checkpoint)
        material.pop("checkpoint_fingerprint")
        checkpoint["checkpoint_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "exceeded scope"):
            verify_publication_release(checkpoint=checkpoint)

    def test_cli_has_no_publish_or_outreach_command(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary"})


if __name__ == "__main__":
    unittest.main()
