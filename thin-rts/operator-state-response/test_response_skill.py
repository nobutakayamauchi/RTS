import unittest

from response_skill import ResponseContext, evaluate_response
from state_model import OperatorStateInput
from vitals_model import Vitals


class ResponseSkillTests(unittest.TestCase):
    def test_compact_response_contains_return_fatigue_performance_and_questions(self):
        result = evaluate_response(
            OperatorStateInput(subjective_fatigue_0_10=6),
            ResponseContext(eta_return_minutes=7, eta_late_after_minutes=10, rework_minutes=2),
        )
        self.assertIn("RETURN 7m / LATE 10m / REWORK +2m", result.text)
        self.assertIn("FATIGUE_EST", result.text)
        self.assertIn("PERF_PRIOR", result.text)
        self.assertIn("ASK", result.text)

    def test_five_hours_sleep_can_have_low_subjective_fatigue_and_attention_prior(self):
        result = evaluate_response(
            OperatorStateInput(
                sleep_hours_24h=5.0,
                subjective_fatigue_0_10=2.0,
                subjective_recovery_0_10=7.0,
                bad_status_assessed=True,
            ),
            ResponseContext(),
        )
        self.assertIn("PERF_PRIOR J:UNKNOWN R:MODERATE A:MODERATE O:CAUTION", result.text)
        self.assertNotIn("COMPARATOR BAC", result.text)
        self.assertIn("acute_sleep_restriction_2_6h", result.log_record["performance_evidence_ids"])

    def test_alcohol_comparator_needs_matching_continuous_wakefulness(self):
        result = evaluate_response(
            OperatorStateInput(continuous_awake_hours=18.0, bad_status_assessed=True),
            ResponseContext(),
        )
        self.assertIn("COMPARATOR BAC 0.05%", result.text)
        self.assertIn("prolonged_wake_17_19h", result.log_record["performance_evidence_ids"])

    def test_emergency_suppresses_optimization_questions(self):
        result = evaluate_response(
            OperatorStateInput(bad_status=("altered_consciousness",)),
            ResponseContext(eta_return_minutes=5),
        )
        self.assertIn("MEDICAL EMERGENCY", result.text)
        self.assertEqual(result.questions, ())

    def test_personal_vital_deviation_is_displayed_as_baseline_delta(self):
        baseline = {"heart_rate_bpm": [60, 61, 62, 63, 59, 61.5]}
        result = evaluate_response(
            OperatorStateInput(subjective_fatigue_0_10=3, bad_status=("sleep_debt",)),
            ResponseContext(
                vitals=Vitals(heart_rate_bpm=90),
                vitals_baseline=baseline,
            ),
        )
        self.assertIn("VITAL_BASELINE Δ", result.text)
        self.assertIn("heart_rate_bpm", result.log_record["vital_z"])

    def test_no_raw_chat_text_field_is_created(self):
        result = evaluate_response(
            OperatorStateInput(subjective_fatigue_0_10=3),
            ResponseContext(),
        )
        self.assertNotIn("raw_text", result.log_record)
        self.assertNotIn("chat_text", result.log_record)


if __name__ == "__main__":
    unittest.main()
