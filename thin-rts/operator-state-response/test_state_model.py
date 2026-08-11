import unittest

from state_model import BehaviorMetrics, OperatorStateInput, estimate_fatigue


class StateModelTests(unittest.TestCase):
    def test_sleep_shortfall_and_subjective_fatigue_raise_score(self):
        rested = estimate_fatigue(
            OperatorStateInput(sleep_hours_24h=7, subjective_fatigue_0_10=2, subjective_recovery_0_10=5)
        )
        deprived = estimate_fatigue(
            OperatorStateInput(sleep_hours_24h=3, subjective_fatigue_0_10=8, subjective_recovery_0_10=1)
        )
        self.assertGreater(deprived.operational_fatigue_100, rested.operational_fatigue_100)

    def test_behavior_without_personal_baseline_does_not_invent_fatigue(self):
        result = estimate_fatigue(
            OperatorStateInput(
                behavior=BehaviorMetrics(characters=100, typo_count=20, correction_count=20, message_count=5, loop_count=4),
            )
        )
        self.assertIsNone(result.components["behavior_anomaly"])
        self.assertIn("behavior_uncalibrated", result.notes)

    def test_personal_baseline_can_surface_behavior_anomaly(self):
        baseline = {
            "typo_rate": [0.01, 0.011, 0.012, 0.009, 0.0105, 0.0115],
            "correction_rate": [0.01, 0.012, 0.011, 0.009, 0.0105, 0.0115],
            "loop_rate": [0.0, 0.05, 0.0, 0.05, 0.02, 0.03],
        }
        result = estimate_fatigue(
            OperatorStateInput(
                behavior=BehaviorMetrics(
                    characters=1000,
                    typo_count=60,
                    correction_count=70,
                    message_count=10,
                    loop_count=4,
                ),
                behavior_baseline=baseline,
            )
        )
        self.assertIsNotNone(result.components["behavior_anomaly"])
        self.assertGreater(result.components["behavior_anomaly"], 0)
        self.assertIn("behavior_above_personal_baseline", result.notes)

    def test_recovery_event_without_reported_effect_gets_no_fake_credit(self):
        result = estimate_fatigue(
            OperatorStateInput(
                subjective_fatigue_0_10=7,
                recovery_events=("meal", "hydration"),
            )
        )
        self.assertIsNone(result.components["recovery_credit"])
        self.assertIn("recovery_event_logged_effect_unmeasured", result.notes)

    def test_reported_recovery_can_reduce_operational_estimate(self):
        low = estimate_fatigue(
            OperatorStateInput(subjective_fatigue_0_10=7, subjective_recovery_0_10=1)
        )
        high = estimate_fatigue(
            OperatorStateInput(subjective_fatigue_0_10=7, subjective_recovery_0_10=9)
        )
        self.assertLess(high.operational_fatigue_100, low.operational_fatigue_100)


if __name__ == "__main__":
    unittest.main()
