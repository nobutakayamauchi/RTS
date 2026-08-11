import unittest

from vitals_model import Vitals, VitalsModelError, personal_vital_deviation


class VitalsModelTests(unittest.TestCase):
    def test_no_baseline_means_uncalibrated_not_normal(self):
        result = personal_vital_deviation(Vitals(heart_rate_bpm=120), {})
        self.assertIsNone(result["heart_rate_bpm"])

    def test_personal_baseline_preserves_direction(self):
        baseline = {
            "heart_rate_bpm": [60, 62, 61, 63, 59, 61.5],
            "spo2_pct": [98, 99, 98.5, 99, 98, 98.5],
        }
        result = personal_vital_deviation(
            Vitals(heart_rate_bpm=85, spo2_pct=95),
            baseline,
        )
        self.assertGreater(result["heart_rate_bpm"], 0)
        self.assertLess(result["spo2_pct"], 0)

    def test_impossible_measurement_fails_closed_instead_of_becoming_anomaly(self):
        with self.assertRaises(VitalsModelError):
            personal_vital_deviation(Vitals(spo2_pct=150), {})
        with self.assertRaises(VitalsModelError):
            personal_vital_deviation(Vitals(heart_rate_bpm=-1), {})

    def test_invalid_baseline_measurement_also_fails_closed(self):
        with self.assertRaises(VitalsModelError):
            personal_vital_deviation(
                Vitals(spo2_pct=98),
                {"spo2_pct": [98, 99, 98, 150, 99, 98]},
            )

    def test_vital_deviation_is_not_medical_classification(self):
        result = personal_vital_deviation(
            Vitals(temperature_c=39),
            {"temperature_c": [36.4, 36.5, 36.6, 36.5, 36.4]},
        )
        self.assertIn("temperature_c", result)
        self.assertNotIn("diagnosis", result)


if __name__ == "__main__":
    unittest.main()
