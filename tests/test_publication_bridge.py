import unittest
from urllib.parse import parse_qs, urlparse

from publication_bridge import (
    NOTE_EDITOR_URL,
    X_INTENT_BASE,
    PublicationBridgeError,
    build_handoff,
    build_humanization_record,
    note_actions,
    parse_x_blocks,
    x_actions,
)


def approved_manifest(drafts=None):
    drafts = drafts or {"x": "hello", "note": "# T\n\nB"}
    return {
        "bundle_id": "PA-TEST",
        "human_review_state": "APPROVED_FOR_HANDOFF",
        "verification_warnings": [],
        "external_publication_performed": False,
        "humanization": build_humanization_record(
            drafts,
            reviewer="/human",
            evidence_preserved=True,
        ),
    }


class PublicationBridgeTests(unittest.TestCase):
    def test_x_thread_becomes_review_intents_without_posting(self):
        draft = "[X POST 1/2]\nfirst\n\n[X POST 2/2]\nsecond"
        actions = x_actions(draft)
        self.assertEqual(len(actions), 2)
        self.assertTrue(all(a.action == "OPEN_COMPOSER" for a in actions))
        self.assertTrue(all(a.requires_user_action for a in actions))
        self.assertTrue(all(a.url.startswith(X_INTENT_BASE) for a in actions))
        self.assertEqual(parse_qs(urlparse(actions[0].url).query)["text"], ["first"])
        self.assertEqual(parse_qs(urlparse(actions[1].url).query)["text"], ["second"])

    def test_note_is_copy_and_open_only(self):
        actions = note_actions("# Title\n\nBody")
        self.assertEqual([a.action for a in actions], ["COPY_TITLE", "COPY_BODY", "OPEN_EDITOR"])
        self.assertEqual(actions[-1].url, NOTE_EDITOR_URL)
        self.assertTrue(all(a.requires_user_action for a in actions))

    def test_handoff_requires_and_records_humanization(self):
        drafts = {"x": "hello", "note": "# T\n\nB"}
        handoff = build_handoff(approved_manifest(drafts), drafts)
        self.assertEqual(handoff["state"], "APPROVED_FOR_HANDOFF")
        self.assertEqual(handoff["humanization_mode"], "/human")
        self.assertTrue(handoff["humanization_verified"])
        self.assertEqual(handoff["publication_authority"], "USER_ONLY")
        self.assertFalse(handoff["automatic_publication"])
        self.assertFalse(handoff["credential_storage"])
        self.assertFalse(handoff["private_api_usage"])

    def test_approved_for_copy_without_human_fails_closed(self):
        manifest = approved_manifest({"x": "hello"})
        manifest["human_review_state"] = "APPROVED_FOR_COPY"
        with self.assertRaises(PublicationBridgeError):
            build_handoff(manifest, {"x": "hello"})

    def test_missing_human_attestation_fails_closed(self):
        manifest = approved_manifest({"x": "hello"})
        manifest.pop("humanization")
        with self.assertRaises(PublicationBridgeError):
            build_handoff(manifest, {"x": "hello"})

    def test_draft_changed_after_human_fails_closed(self):
        reviewed = {"x": "human final"}
        manifest = approved_manifest(reviewed)
        with self.assertRaises(PublicationBridgeError):
            build_handoff(manifest, {"x": "machine changed it later"})

    def test_human_record_requires_evidence_preservation(self):
        with self.assertRaises(PublicationBridgeError):
            build_humanization_record(
                {"x": "hello"}, reviewer="/human", evidence_preserved=False
            )

    def test_warnings_fail_closed(self):
        drafts = {"x": "hello"}
        manifest = approved_manifest(drafts)
        manifest["verification_warnings"] = ["unsupported claim"]
        with self.assertRaises(PublicationBridgeError):
            build_handoff(manifest, drafts)

    def test_x_parser_preserves_text(self):
        draft = "[X POST 1/2]\na\n\nline\n\n[X POST 2/2]\nb"
        self.assertEqual(parse_x_blocks(draft), ["a\n\nline", "b"])


if __name__ == "__main__":
    unittest.main()
