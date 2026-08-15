import unittest

from post_adapter import PostAdapterError, build_bundle, register_adapter


def clean_source():
    return {
        "project_name": "BridgePatch",
        "update_type": "launch-prep",
        "summary": "The sales blocker review is complete and the remaining launch work is explicitly classified.",
        "facts": [
            {
                "claim": "The paid-intake application is not required for the v0 launch path.",
                "status": "VERIFIED",
                "source_ref": "goal-001",
            },
            {
                "claim": "A human approval gate remains before public sale.",
                "status": "VERIFIED",
                "source_ref": "goal-001",
            },
        ],
        "source_refs": [
            {
                "id": "goal-001",
                "kind": "repository-document",
                "locator": "docs/business-portfolio/SALES_BLOCKER_MATRIX_2026-08-15.md",
            }
        ],
        "audience": "small business operators and AI developers",
        "call_to_action": "Review the remaining blockers before launch.",
        "known_limits": ["This update does not itself publish the service."],
        "media_refs": ["sales flow diagram"],
    }


class PostAdapterTests(unittest.TestCase):
    def test_builds_four_distinct_channels_without_publication(self):
        bundle = build_bundle(clean_source(), generated_at="2026-08-15T09:40:00+00:00")

        self.assertTrue({"x", "note", "github", "instagram"}.issubset(bundle["outputs"]))
        self.assertEqual(bundle["manifest"]["human_review_state"], "DRAFT")
        self.assertFalse(bundle["manifest"]["external_publication_performed"])
        self.assertEqual(bundle["manifest"]["verification_warnings"], [])
        self.assertNotEqual(bundle["outputs"]["x"], bundle["outputs"]["note"])
        self.assertNotEqual(bundle["outputs"]["github"], bundle["outputs"]["instagram"])

    def test_unverified_fact_is_excluded_and_forces_review(self):
        source = clean_source()
        source["facts"].append(
            {
                "claim": "The service is already publicly selling to customers.",
                "status": "UNVERIFIED",
            }
        )

        bundle = build_bundle(source, generated_at="2026-08-15T09:40:00+00:00")

        self.assertEqual(bundle["manifest"]["human_review_state"], "REVIEW_REQUIRED")
        self.assertTrue(bundle["manifest"]["verification_warnings"])
        for output in bundle["outputs"].values():
            publishable_part = output.split("Human review warnings:", 1)[0]
            self.assertNotIn("already publicly selling", publishable_part)

    def test_missing_source_binding_fails_closed_when_no_fact_survives(self):
        source = clean_source()
        source["facts"] = [
            {
                "claim": "This should not become a public fact.",
                "status": "VERIFIED",
                "source_ref": "missing-source",
            }
        ]

        with self.assertRaises(PostAdapterError):
            build_bundle(source)

    def test_cannot_approve_bundle_while_warnings_remain(self):
        source = clean_source()
        source["facts"].append(
            {
                "claim": "Unverified revenue result.",
                "status": "UNVERIFIED",
            }
        )

        with self.assertRaises(PostAdapterError):
            build_bundle(source, review_state="APPROVED_FOR_COPY")

    def test_clean_bundle_can_be_approved_for_copy(self):
        bundle = build_bundle(
            clean_source(),
            generated_at="2026-08-15T09:40:00+00:00",
            review_state="APPROVED_FOR_COPY",
        )
        self.assertEqual(bundle["manifest"]["human_review_state"], "APPROVED_FOR_COPY")
        self.assertFalse(bundle["manifest"]["external_publication_performed"])

    def test_z_fifth_channel_can_be_added_without_changing_source_contract(self):
        build_bundle(clean_source())  # initialize the default adapters first
        register_adapter("internal", lambda source: f"INTERNAL: {source['summary']}\n")

        bundle = build_bundle(clean_source(), generated_at="2026-08-15T09:40:00+00:00")

        self.assertIn("internal", bundle["outputs"])
        self.assertIn("x", bundle["outputs"])
        self.assertIn("note", bundle["outputs"])
        self.assertEqual(bundle["normalized_source"]["project_name"], "BridgePatch")


if __name__ == "__main__":
    unittest.main()
