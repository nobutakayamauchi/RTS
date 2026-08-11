import json
import pathlib
import unittest

from operator_machine_model import (
    factorized_visible_output_amplification,
    observed_control_pressure,
    stages_per_decision_unit,
    visible_output_per_decision_unit,
    visible_output_per_stage,
)


HERE = pathlib.Path(__file__).resolve().parent


class OperatorMachineModelTests(unittest.TestCase):
    def test_march_strong_micro_pilot(self):
        data = json.loads((HERE / "human_machine_hinge_v0_1.json").read_text())
        pilot = data["strong_micro_pilot"]
        self.assertEqual(pilot["decision_hinges"], 2)
        self.assertEqual(pilot["decision_units"], 2)
        self.assertEqual(pilot["strong_bound_pr_stages"], 4)
        self.assertEqual(stages_per_decision_unit(4, 2), 2.0)
        self.assertEqual(pilot["median_first_stage_latency_seconds"], 48)

    def test_pre_hinge_false_match_is_retained_as_rejected(self):
        data = json.loads((HERE / "human_machine_hinge_v0_1.json").read_text())
        hinge = next(h for h in data["hinges"] if h["id"] == "H-20260306-024430")
        self.assertEqual(hinge["rejected_pre_hinge_prs"], [90, 91, 92])
        self.assertEqual(hinge["strong_bound_prs"], [])

    def test_july27_factorization(self):
        # Evidence-bounded governed window: 226 commit proxy / 16 stages / J>=10.
        self.assertAlmostEqual(visible_output_per_stage(226, 16), 14.125)
        self.assertAlmostEqual(stages_per_decision_unit(16, 10), 1.6)
        self.assertAlmostEqual(visible_output_per_decision_unit(226, 10), 22.6)
        self.assertAlmostEqual(factorized_visible_output_amplification(226, 16, 10), 22.6)

    def test_aug11_factorization(self):
        # Evidence-bounded /goal governed window: 107 commit proxy / 3 stages / J>=4.
        self.assertAlmostEqual(visible_output_per_stage(107, 3), 35.666666666666664)
        self.assertAlmostEqual(stages_per_decision_unit(3, 4), 0.75)
        self.assertAlmostEqual(visible_output_per_decision_unit(107, 4), 26.75)
        self.assertAlmostEqual(factorized_visible_output_amplification(107, 3, 4), 26.75)

    def test_observed_control_pressure_monthly_examples(self):
        self.assertAlmostEqual(observed_control_pressure(25.96333333333333, 2, 0, 2), 0.15406342277570934)
        self.assertAlmostEqual(observed_control_pressure(10.902222222222223, 9, 0, 0), 0.8255197717081124)
        self.assertAlmostEqual(observed_control_pressure(4.065555555555555, 6, 0, 0), 1.4758130636786009)
        self.assertAlmostEqual(observed_control_pressure(9.502222222222223, 19, 26.5, 15), 6.3669317118802615)
        self.assertAlmostEqual(observed_control_pressure(2, 17, 18.17, 17), 26.085)


if __name__ == "__main__":
    unittest.main()
