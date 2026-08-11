import unittest

from effect_catalog import estimate_performance_impact


class EffectCatalogTests(unittest.TestCase):
    def test_five_hours_sleep_matches_acute_attention_profile_not_bac_comparator(self):
        impact = estimate_performance_impact(sleep_hours_24h=5.0)
        self.assertIn("acute_sleep_restriction_2_6h", impact.matched_profiles)
        self.assertEqual(impact.axes["reaction"].grade, "MODERATE")
        self.assertEqual(impact.axes["accuracy"].grade, "MODERATE")
        self.assertEqual(impact.axes["judgment"].grade, "UNKNOWN")
        self.assertEqual(impact.comparative_references, ())
        self.assertIn("continuous_awake_hours_unknown_no_alcohol_comparator_match", impact.notes)

    def test_bac_comparator_requires_continuous_awake_hours(self):
        impact = estimate_performance_impact(continuous_awake_hours=18.0)
        self.assertIn("prolonged_wake_17_19h", impact.matched_profiles)
        self.assertEqual(impact.axes["reaction"].grade, "HIGH")
        self.assertEqual(impact.axes["accuracy"].grade, "HIGH")
        self.assertTrue(any("BAC 0.05%" in item for item in impact.comparative_references))

    def test_repeated_five_hour_profile_requires_multiday_history(self):
        acute_only = estimate_performance_impact(sleep_hours_24h=5.0)
        repeated = estimate_performance_impact(sleep_hours_24h=5.0, sleep_restriction_nights=3)
        self.assertNotIn("chronic_sleep_restriction_5h_7d", acute_only.matched_profiles)
        self.assertIn("chronic_sleep_restriction_5h_7d", repeated.matched_profiles)

    def test_no_match_is_unknown_not_zero(self):
        impact = estimate_performance_impact(sleep_hours_24h=8.0)
        self.assertEqual(impact.matched_profiles, ())
        self.assertTrue(all(axis.grade == "UNKNOWN" for axis in impact.axes.values()))
        self.assertIn("no_catalog_profile_matched", impact.notes)


if __name__ == "__main__":
    unittest.main()
