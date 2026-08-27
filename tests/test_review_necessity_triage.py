from __future__ import annotations

import unittest

from review_necessity_triage import ReviewTriageError, triage_refinement_report, verify_triage_report
from semantic_claim_refinement import refine_intake_report
from tests.test_semantic_claim_refinement import make_intake


def make_j(body: str):
    intake = make_intake(body)
    refined = refine_intake_report(intake)
    return refined


class ReviewNecessityTriageTests(unittest.TestCase):
    def test_high_impact_execution_change_is_human_now(self):
        j = make_j("A request now uses a managed planner before tool execution.")
        self.assertEqual(j["status"], "REVIEW_REQUIRED")
        triage = triage_refinement_report(j)
        verify_triage_report(triage, refinement_report=j)
        record = triage["records"][0]
        self.assertEqual(record["classification"], "HUMAN_NOW")
        self.assertGreaterEqual(record["da"]["impact"], 4)
        self.assertIn("H_ARCHITECTURE_CLASSIFICATION", record["da"]["causal_paths"])

    def test_low_immediate_impact_high_future_causal_reach_is_human_now(self):
        j = make_j("A legacy model remains available while teams migrate to the new model.")
        triage = triage_refinement_report(j)
        record = triage["records"][0]
        self.assertLess(record["da"]["impact"], 4)
        self.assertGreaterEqual(record["da"]["causal_reach"], 4)
        self.assertEqual(record["classification"], "HUMAN_NOW")
        self.assertIn("FUTURE_CAUSAL_REACH", record["human_review_reason_codes"])

    def test_marketing_positioning_is_not_silently_dropped(self):
        j = make_j("The new model sets a quality and efficiency baseline for complex production workflows.")
        triage = triage_refinement_report(j)
        record = triage["records"][0]
        self.assertEqual(record["classification"], "HUMAN_LATER")
        self.assertFalse(record["semantic_correctness_decided"])
        self.assertEqual(record["evidence_drop_authority"], "NONE")

    def test_every_unresolved_finding_is_preserved(self):
        j = make_j("A request now uses a new runtime policy. Another request now uses a different execution policy.")
        triage = triage_refinement_report(j)
        self.assertEqual(triage["input_unresolved_count"], len(triage["records"]))
        verify_triage_report(triage, refinement_report=j)

    def test_stale_refinement_fingerprint_fails_verification(self):
        j = make_j("A request now uses a managed planner before tool execution.")
        triage = triage_refinement_report(j)
        changed = make_j("A legacy model remains available while teams migrate to the new model.")
        with self.assertRaises(ReviewTriageError):
            verify_triage_report(triage, refinement_report=changed)

    def test_authority_and_probability_boundaries(self):
        j = make_j("A request now uses a managed planner before tool execution.")
        triage = triage_refinement_report(j)
        self.assertEqual(triage["execution_authority"], "NONE")
        self.assertEqual(triage["profile_application_authority"], "NONE")
        self.assertEqual(triage["promotion_authority"], "NONE")
        self.assertEqual(triage["hidden_architecture_claim"], "NONE")
        self.assertTrue(triage["audit"]["causal_reach_is_heuristic_not_probability"])
        self.assertFalse(triage["records"][0]["da"]["causal_reach_is_probability"])


if __name__ == "__main__":
    unittest.main()
