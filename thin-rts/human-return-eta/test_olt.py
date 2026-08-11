import unittest

import olt


class OLTTests(unittest.TestCase):
    def test_pre_kernel_worked_example(self):
        eligible_gaps = [10, 10, 10, 10, 10, 10, 10, 8.7]
        value = olt.activity_load(17, eligible_gaps)
        self.assertAlmostEqual(value, 22.2466666667, places=6)

    def test_governed_pr_example(self):
        value = olt.orchestration_load(4, 56.2167)
        self.assertAlmostEqual(value, 7.74778, places=4)

    def test_quality_and_automation_materialized_sample(self):
        self.assertAlmostEqual(olt.data_quality(3, 7, 5), 10 / 15)
        self.assertAlmostEqual(olt.automation_rate(3, 7), 0.7)

    def test_decision_and_revision_weights_are_bounded(self):
        self.assertEqual(olt.decision_load([1, 2, 3]), 6)
        self.assertEqual(olt.revision_load([1, 2, 3]), 6)
        with self.assertRaises(olt.OLTError):
            olt.decision_load([4])
        with self.assertRaises(olt.OLTError):
            olt.revision_load([0])

    def test_context_switches_only_count_inside_active_window(self):
        projects = ["RTS", "Vlog", "RTS", "X", "RTS"]
        gaps = [5, 5, 35, 5]
        self.assertEqual(olt.context_switch_load(projects, gaps), 3)

    def test_display_score_is_bounded_but_not_primary_identity(self):
        vector = olt.LoadVector(E=22.25, J=8, O=7.75, R=3, X=2)
        score = olt.display_score(vector)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)

    def test_vector_distance_uses_vector_not_display_score(self):
        a = olt.LoadVector(E=20, J=0, O=0, R=0, X=0)
        b = olt.LoadVector(E=0, J=8, O=0, R=0, X=0)
        self.assertGreater(olt.vector_distance(a, b), 0)

    def test_project_shares(self):
        result = olt.work_share({"RTS": 35, "Vlog": 50, "Other": 15})
        self.assertAlmostEqual(result["RTS"], 0.35)
        self.assertAlmostEqual(sum(result.values()), 1.0)

    def test_invalid_actor_empty_sets_fail_closed(self):
        with self.assertRaises(olt.OLTError):
            olt.data_quality(0, 0, 0)
        with self.assertRaises(olt.OLTError):
            olt.automation_rate(0, 0)


if __name__ == "__main__":
    unittest.main()
