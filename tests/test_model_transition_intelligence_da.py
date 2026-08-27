import unittest

from tests.test_model_transition_intelligence import bundle, claim, source
from model_transition_intelligence.core import TransitionError, compare_bundles


class ModelTransitionIntelligenceDATests(unittest.TestCase):
    def test_mapped_marketing_delta_cannot_hide_unmapped_contract_text_change(self):
        old_text = "Tagline: great.\nExecution model: client loop."
        new_text = "Tagline: amazing.\nExecution model: managed agents."
        old = bundle("old", [source("old-readme", "readme", old_text, [
            claim("m1", "other", "tagline", "MARKETING", "great", "Tagline: great")
        ], source_type="README")])
        new = bundle("new", [source("new-readme", "readme", new_text, [
            claim("m2", "other", "tagline", "MARKETING", "amazing", "Tagline: amazing")
        ], source_type="README")])
        report = compare_bundles(old, new)
        self.assertEqual(report["transition_state"], "REVIEW_REQUIRED")
        self.assertTrue(report["unmapped_text_changes"])

    def test_s3_is_not_hidden_architecture_proof(self):
        old = bundle("old", [source("old", "tools", "Tool loop owner: client.", [
            claim("a", "tools", "tool_loop_owner", "CONTRACT", "client", "Tool loop owner: client")
        ], source_type="TOOL_DOCS")])
        new = bundle("new", [source("new", "tools", "Tool loop owner: model runtime.", [
            claim("b", "tools", "tool_loop_owner", "CONTRACT", "model_runtime", "Tool loop owner: model runtime")
        ], source_type="TOOL_DOCS")])
        report = compare_bundles(old, new)
        self.assertEqual(report["severity"], "S3")
        self.assertEqual(report["hidden_architecture_claim"], "NONE")
        self.assertNotIn("neural", str(report).lower())

    def test_review_required_never_recommends_execution(self):
        old = bundle("old", [source("old", "api", "State model: local.", [
            claim("o", "state", "state_model", "CONTRACT", "local", "State model: local")
        ])])
        new1 = source("n1", "api-a", "State model: remote.", [
            claim("n1", "state", "state_model", "CONTRACT", "remote", "State model: remote")
        ])
        new2 = source("n2", "api-b", "State model: hybrid.", [
            claim("n2", "state", "state_model", "CONTRACT", "hybrid", "State model: hybrid")
        ], source_type="RELEASE_NOTES")
        report = compare_bundles(old, bundle("new", [new1, new2]))
        self.assertEqual(report["transition_state"], "REVIEW_REQUIRED")
        self.assertEqual(report["probe_requirements"]["execution_recommendation"], "HOLD_FOR_REVIEW")
        self.assertEqual(report["authority"]["execution_authority"], "NONE")

    def test_same_generation_comparison_fails(self):
        src = source("s", "api", "No change.", [])
        with self.assertRaises(TransitionError):
            compare_bundles(bundle("same", [src]), bundle("same", [source("s2", "api", "No change.", [])]))

    def test_probe_cap_never_exceeds_f_boundary(self):
        old = bundle("old", [source("old", "all", "Delegation model: none.", [
            claim("d1", "delegation", "delegation_model", "CONTRACT", "none", "Delegation model: none")
        ], source_type="MODEL_CARD")])
        new = bundle("new", [source("new", "all", "Delegation model: managed agents.", [
            claim("d2", "delegation", "delegation_model", "CONTRACT", "managed", "Delegation model: managed agents")
        ], source_type="MODEL_CARD")])
        report = compare_bundles(old, new)
        self.assertLessEqual(report["probe_requirements"]["max_probe_count"], 8)
        self.assertLessEqual(len(report["probe_requirements"]["preferred_f_dimensions"]), 6)


if __name__ == "__main__":
    unittest.main()
