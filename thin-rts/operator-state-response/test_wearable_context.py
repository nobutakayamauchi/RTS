import unittest

from wearable_context import (
    WearableConsent,
    WearableContextError,
    WearableObservation,
    minimized_wearable_record,
)


class WearableContextTests(unittest.TestCase):
    def test_denied_or_not_asked_does_not_persist(self):
        obs = WearableObservation(sleep_duration_minutes=300)
        self.assertIsNone(minimized_wearable_record(obs, WearableConsent("NOT_ASKED")))
        self.assertIsNone(minimized_wearable_record(obs, WearableConsent("DENIED")))

    def test_derived_only_drops_vendor_scores_but_keeps_sleep_and_vitals(self):
        record = minimized_wearable_record(
            WearableObservation(
                source_adapter="healthkit",
                source_device_class="ring",
                sleep_duration_minutes=300,
                resting_heart_rate_bpm=58,
                overnight_hrv_ms=42,
                vendor_readiness_score=61,
                vendor_sleep_score=74,
            ),
            WearableConsent("DERIVED_ONLY"),
        )
        self.assertIsNotNone(record)
        features = record["features"]
        self.assertEqual(features["sleep_duration_minutes"], 300.0)
        self.assertEqual(features["overnight_hrv_ms"], 42.0)
        self.assertNotIn("vendor_readiness_score", features)
        self.assertNotIn("vendor_sleep_score", features)

    def test_summary_only_preserves_vendor_score_without_reinterpreting_it(self):
        record = minimized_wearable_record(
            WearableObservation(vendor_readiness_score=61),
            WearableConsent("SUMMARY_ONLY"),
        )
        self.assertEqual(record["features"]["vendor_readiness_score"], 61.0)
        self.assertEqual(record["semantics"], "wellness_observation_not_diagnosis")
        self.assertNotIn("fatigue", record)
        self.assertNotIn("impairment", record)

    def test_impossible_values_fail_closed(self):
        with self.assertRaises(WearableContextError):
            minimized_wearable_record(
                WearableObservation(oxygen_saturation_pct=140),
                WearableConsent("DERIVED_ONLY"),
            )


if __name__ == "__main__":
    unittest.main()
