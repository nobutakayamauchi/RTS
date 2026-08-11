import unittest

from operator_machine_model import (
    amplification_with_decision_lower_bound,
    launch_safe_orchestration,
    ratio_upper_bound_from_denominator_lower_bound,
)


class OperatorMachineDATests(unittest.TestCase):
    def test_lower_bound_denominator_creates_upper_bound(self):
        # If true J is 12 while only J>=10 is known, Y/10 must be ABOVE Y/12.
        reported_upper = ratio_upper_bound_from_denominator_lower_bound(226, 10)
        true_ratio_example = 226 / 12
        self.assertEqual(reported_upper, 22.6)
        self.assertGreater(reported_upper, true_ratio_example)

    def test_july_and_august_are_bound_aware_not_point_estimates(self):
        july = amplification_with_decision_lower_bound(226, 16, 10)
        aug = amplification_with_decision_lower_bound(107, 3, 4)
        self.assertAlmostEqual(july["gamma_j_upper"], 1.6)
        self.assertAlmostEqual(july["gamma_m_point_proxy"], 14.125)
        self.assertAlmostEqual(july["lambda_upper"], 22.6)
        self.assertAlmostEqual(aug["gamma_j_upper"], 0.75)
        self.assertAlmostEqual(aug["gamma_m_point_proxy"], 107 / 3)
        self.assertAlmostEqual(aug["lambda_upper"], 26.75)
        self.assertEqual(july["decision_denominator_semantics"], "LOWER_BOUND")

    def test_launch_orchestration_excludes_future_elapsed_time_by_construction(self):
        self.assertEqual(launch_safe_orchestration(3), 3.0)
        # The API deliberately accepts only stage count known at launch; no elapsed field exists.
        with self.assertRaises(TypeError):
            launch_safe_orchestration(3, 56.0)


if __name__ == "__main__":
    unittest.main()
