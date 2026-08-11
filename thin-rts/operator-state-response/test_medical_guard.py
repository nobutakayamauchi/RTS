import unittest

from medical_guard import evaluate_medical_guard


class MedicalGuardTests(unittest.TestCase):
    def test_emergency_red_flag_overrides_work_optimization(self):
        result = evaluate_medical_guard(("headache", "altered_consciousness"))
        self.assertEqual(result.level, "EMERGENCY")
        self.assertIn("STOP_WORK", result.action)
        self.assertEqual(result.semantics, "SAFETY_TRIAGE_NOT_DIAGNOSIS")

    def test_heat_symptoms_without_emergency_stay_caution(self):
        result = evaluate_medical_guard(("dizziness", "nausea"), heat_exposure=True)
        self.assertEqual(result.level, "HEAT_CAUTION")

    def test_heat_cannot_drink_is_emergency(self):
        result = evaluate_medical_guard(("nausea",), heat_exposure=True, cannot_drink=True)
        self.assertEqual(result.level, "EMERGENCY")

    def test_collapsed_is_prompt_triage_not_fatigue_label(self):
        result = evaluate_medical_guard(("fainted_or_collapsed",))
        self.assertEqual(result.level, "PROMPT_TRIAGE")
        self.assertNotEqual(result.semantics, "DIAGNOSIS")

    def test_no_reported_flags_is_explicitly_limited(self):
        result = evaluate_medical_guard(())
        self.assertEqual(result.level, "NONE")
        self.assertIn("REPORTED_FIELDS", result.action)


if __name__ == "__main__":
    unittest.main()
