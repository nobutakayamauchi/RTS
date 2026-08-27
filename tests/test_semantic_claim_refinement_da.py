from __future__ import annotations

import unittest

from semantic_claim_refinement import refine_intake_report
from tests.test_semantic_claim_refinement import make_intake


class SemanticClaimRefinementDATests(unittest.TestCase):
    def test_negated_capability_cannot_become_positive_claim(self):
        intake = make_intake("Requests do not dispatch several functions concurrently.")
        self.assertEqual(intake["status"], "REVIEW_REQUIRED")
        refined = refine_intake_report(intake)
        self.assertEqual(refined["status"], "REVIEW_REQUIRED")
        self.assertEqual(refined["audit"]["added_claim_count"], 0)
        self.assertEqual(refined["audit"]["resolved_count"], 0)
        self.assertEqual(refined["audit"]["unresolved"][0]["reason"], "NEGATION_OR_EXCEPTION")

    def test_multi_match_sentence_stays_reviewable(self):
        intake = make_intake(
            "Requests may dispatch several functions concurrently inside an isolated environment."
        )
        self.assertEqual(intake["status"], "REVIEW_REQUIRED")
        refined = refine_intake_report(intake)
        self.assertEqual(refined["status"], "REVIEW_REQUIRED")
        self.assertEqual(refined["audit"]["added_claim_count"], 0)
        self.assertEqual(refined["audit"]["resolved_count"], 0)
        self.assertEqual(refined["audit"]["unresolved"][0]["reason"], "MULTIPLE_ONTOLOGY_MATCHES")
        self.assertGreaterEqual(refined["audit"]["unresolved"][0]["candidate_count"], 2)


if __name__ == "__main__":
    unittest.main()
