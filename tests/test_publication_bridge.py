import unittest
from urllib.parse import parse_qs, urlparse

from publication_bridge import (
    NOTE_EDITOR_URL,
    X_INTENT_BASE,
    PublicationBridgeError,
    build_handoff,
    note_actions,
    parse_x_blocks,
    x_actions,
)


def approved_manifest():
    return {
        "bundle_id": "PA-TEST",
        "human_review_state": "APPROVED_FOR_COPY",
        "verification_warnings": [],
        "external_publication_performed": False,
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

    def test_handoff_records_no_automation_credentials_or_private_api(self):
        handoff = build_handoff(approved_manifest(), {"x": "hello", "note": "# T\n\nB"})
        self.assertEqual(handoff["state"], "APPROVED_FOR_HANDOFF")
        self.assertEqual(handoff["publication_authority"], "USER_ONLY")
        self.assertFalse(handoff["automatic_publication"])
        self.assertFalse(handoff["credential_storage"])
        self.assertFalse(handoff["private_api_usage"])

    def test_unapproved_source_fails_closed(self):
        manifest = approved_manifest()
        manifest["human_review_state"] = "DRAFT"
        with self.assertRaises(PublicationBridgeError):
            build_handoff(manifest, {"x": "hello"})

    def test_warnings_fail_closed(self):
        manifest = approved_manifest()
        manifest["verification_warnings"] = ["unsupported claim"]
        with self.assertRaises(PublicationBridgeError):
            build_handoff(manifest, {"x": "hello"})

    def test_x_parser_preserves_text(self):
        draft = "[X POST 1/2]\na\n\nline\n\n[X POST 2/2]\nb"
        self.assertEqual(parse_x_blocks(draft), ["a\n\nline", "b"])


if __name__ == "__main__":
    unittest.main()
