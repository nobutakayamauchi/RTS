import unittest

from decision_sentinel import (
    DecisionSentinelError,
    DecisionState,
    classify_revision_outcome,
    review_pressure,
)


class DecisionSentinelTests(unittest.TestCase):
    def test_high_quality_local_decision_stays_green(self):
        result = review_pressure(
            DecisionState(severity=1, evidence_quality=0.95, axis_coverage=0.8)
        )
        self.assertEqual(result["level"], "GREEN")
        self.assertEqual(result["semantics"], "HEURISTIC_REVIEW_PRESSURE_NOT_ERROR_PROBABILITY")

    def test_d3_low_quality_forces_red(self):
        result = review_pressure(
            DecisionState(severity=3, evidence_quality=0.55, axis_coverage=0.8)
        )
        self.assertEqual(result["level"], "RED")
        self.assertEqual(
            result["action"],
            "HOLD_IRREVERSIBLE_ACTION_UNTIL_EVIDENCE_OR_AUTHORITY_RECHECK",
        )

    def test_d3_counterevidence_forces_red_even_with_good_quality(self):
        result = review_pressure(
            DecisionState(
                severity=3,
                evidence_quality=0.9,
                axis_coverage=1.0,
                unresolved_counterevidence=True,
            )
        )
        self.assertEqual(result["level"], "RED")

    def test_revision_and_switching_raise_pressure_without_calling_it_error_probability(self):
        low = review_pressure(
            DecisionState(severity=2, evidence_quality=0.9, axis_coverage=0.8)
        )
        high = review_pressure(
            DecisionState(
                severity=2,
                evidence_quality=0.9,
                axis_coverage=0.8,
                recent_revision_load=8,
                recent_context_switch_load=6,
            )
        )
        self.assertGreater(high["drp_100"], low["drp_100"])
        self.assertNotIn("error_probability", high)
        self.assertEqual(high["semantics"], "HEURISTIC_REVIEW_PRESSURE_NOT_ERROR_PROBABILITY")

    def test_revision_is_not_automatically_wrong(self):
        self.assertEqual(classify_revision_outcome("NEW_EVIDENCE"), "NOT_ERROR_LABEL")
        self.assertEqual(classify_revision_outcome("SCOPE_CHANGE"), "NOT_ERROR_LABEL")
        self.assertEqual(classify_revision_outcome("ROUTINE_ITERATION"), "NOT_ERROR_LABEL")
        self.assertEqual(classify_revision_outcome("CORRECTIVE_ERROR"), "NEGATIVE_LABEL_CANDIDATE")
        self.assertEqual(classify_revision_outcome("UNKNOWN"), "UNRESOLVED_LABEL")

    def test_invalid_quality_rejected(self):
        with self.assertRaises(DecisionSentinelError):
            review_pressure(DecisionState(severity=2, evidence_quality=1.1, axis_coverage=1.0))


if __name__ == "__main__":
    unittest.main()
