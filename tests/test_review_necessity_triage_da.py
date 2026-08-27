from __future__ import annotations

import copy
import unittest

from review_necessity_triage import ReviewTriageError, triage_refinement_report, verify_triage_report
from tests.test_review_necessity_triage import make_j


class ReviewNecessityTriageDATests(unittest.TestCase):
    def test_weak_availability_signal_cannot_turn_pure_docs_surface_into_human_now(self):
        j = make_j("This guide introduces all the models available through the API.")
        triage = triage_refinement_report(j)
        record = triage["records"][0]
        self.assertEqual(record["classification"], "DEFER_LOW_VALUE")
        self.assertLessEqual(record["da"]["human_review_importance"], 1)
        self.assertEqual(record["evidence_drop_authority"], "NONE")

    def test_marketing_noise_cannot_hide_explicit_execution_contract(self):
        j = make_j("Our most advanced release now uses a managed planner in the execution runtime.")
        triage = triage_refinement_report(j)
        record = triage["records"][0]
        self.assertEqual(record["classification"], "HUMAN_NOW")
        self.assertTrue(record["da"]["explicit_contract_signal"])
        self.assertGreaterEqual(record["da"]["impact"], 4)

    def test_material_perspective_gap_cannot_be_averaged_into_later_review(self):
        j = make_j("The new model sets a quality and efficiency baseline for complex production workflows.")
        triage = triage_refinement_report(j)
        bad = copy.deepcopy(triage)
        record = bad["records"][0]
        record["da"]["impact"] = 3
        record["da"]["causal_reach"] = 3
        record["da"]["human_review_importance"] = 5
        record["counter_da"]["human_review_importance"] = 1
        record["perspective_gap"] = 4
        record["classification"] = "HUMAN_LATER"
        record["human_review_reason_codes"] = ["AVERAGED_SCORE"]
        with self.assertRaises(ReviewTriageError):
            verify_triage_report(bad)

    def test_truncated_upstream_cannot_receive_normal_priority(self):
        j = make_j("A request now uses a managed planner before tool execution.")
        j["audit"]["upstream_ambiguous_findings_truncated"] = True
        triage = triage_refinement_report(j)
        self.assertEqual(triage["status"], "REVIEW_BLOCKED")
        self.assertTrue(all(r["classification"] == "REVIEW_BLOCKED" for r in triage["records"]))

    def test_unresolved_identity_cannot_silently_disappear(self):
        j = make_j("A request now uses a managed planner before tool execution.")
        triage = triage_refinement_report(j)
        bad = copy.deepcopy(triage)
        bad["records"] = []
        bad["input_unresolved_count"] = 0
        with self.assertRaises(ReviewTriageError):
            verify_triage_report(bad, refinement_report=j)


if __name__ == "__main__":
    unittest.main()
