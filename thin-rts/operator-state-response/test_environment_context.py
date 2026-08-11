import unittest

from environment_context import (
    EnvironmentConsent,
    EnvironmentObservation,
    environment_features,
    minimized_environment_record,
)


class EnvironmentContextTests(unittest.TestCase):
    def test_ephemeral_weather_never_persists_location(self):
        obs = EnvironmentObservation(
            coarse_location="Nagoya",
            outdoor_temp_c=30,
            outdoor_relative_humidity_pct=70,
            weather_source="provider",
        )
        record = minimized_environment_record(
            obs,
            EnvironmentConsent(weather_mode="EPHEMERAL", noise_mode="DENIED"),
        )
        self.assertNotIn("coarse_location", record)
        self.assertEqual(record["features"]["outdoor_temp_c"], 30.0)

    def test_coarse_location_requires_explicit_coarse_log_mode(self):
        obs = EnvironmentObservation(coarse_location="Nagoya", outdoor_temp_c=30)
        record = minimized_environment_record(
            obs,
            EnvironmentConsent(weather_mode="COARSE_LOG", noise_mode="DENIED"),
        )
        self.assertEqual(record["coarse_location"], "Nagoya")

    def test_denied_weather_strips_weather_features(self):
        obs = EnvironmentObservation(outdoor_temp_c=30, wind_mps=4, cabin_temp_c=33)
        record = minimized_environment_record(
            obs,
            EnvironmentConsent(weather_mode="DENIED", noise_mode="DENIED"),
        )
        self.assertNotIn("outdoor_temp_c", record["features"])
        self.assertNotIn("wind_mps", record["features"])
        # Direct cabin sensors are distinct from location/weather permission.
        self.assertEqual(record["features"]["cabin_temp_c"], 33.0)

    def test_noise_is_derived_only_and_requires_permission(self):
        obs = EnvironmentObservation(noise_laeq_db=52, noise_peak_db=71, subjective_noise_0_10=4)
        denied = minimized_environment_record(
            obs,
            EnvironmentConsent(weather_mode="DENIED", noise_mode="DENIED"),
        )
        allowed = minimized_environment_record(
            obs,
            EnvironmentConsent(weather_mode="DENIED", noise_mode="DERIVED_DB_ONLY"),
        )
        self.assertNotIn("noise_laeq_db", denied["features"])
        self.assertEqual(allowed["features"]["noise_laeq_db"], 52.0)
        # Subjective report is not microphone data and may remain as operator-provided context.
        self.assertEqual(denied["features"]["subjective_noise_0_10"], 4.0)

    def test_environment_features_do_not_create_fatigue_points(self):
        features = environment_features(
            EnvironmentObservation(outdoor_temp_c=35, noise_laeq_db=65, cabin_temp_c=40)
        )
        self.assertIn("outdoor_temp_c", features)
        self.assertNotIn("fatigue", features)
        self.assertNotIn("diagnosis", features)

    def test_invalid_measurement_fails_closed(self):
        with self.assertRaises(ValueError):
            environment_features(EnvironmentObservation(outdoor_relative_humidity_pct=140))


if __name__ == "__main__":
    unittest.main()
