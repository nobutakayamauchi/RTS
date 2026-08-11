import unittest

import olt
import olt_eta


class OLTETATests(unittest.TestCase):
    def run(self, minutes, vector, task="meteor", strength="STRONG"):
        return olt_eta.HistoricalRun(
            duration_minutes=minutes,
            load=vector,
            task_class=task,
            evidence_strength=strength,
        )

    def test_near_vectors_dominate_distant_vectors(self):
        target = olt.LoadVector(E=10, J=4, O=3, R=2, X=1)
        runs = [
            self.run(5, olt.LoadVector(E=10, J=4, O=3, R=2, X=1)),
            self.run(6, olt.LoadVector(E=11, J=4, O=3, R=2, X=1)),
            self.run(40, olt.LoadVector(E=40, J=16, O=20, R=10, X=8)),
        ]
        result = olt_eta.estimate_from_vector(runs, target, task_class="meteor")
        self.assertLessEqual(result["come_back_after_minutes"], 6)
        self.assertEqual(result["basis"], "OLT_VECTOR_PRIOR")

    def test_weak_exact_match_does_not_automatically_beat_strong_near_match(self):
        target = olt.LoadVector(E=10, J=4, O=3, R=2, X=1)
        runs = [
            self.run(
                30,
                target,
                strength="WEAK",
            ),
            self.run(
                6,
                olt.LoadVector(E=10.5, J=4, O=3, R=2, X=1),
                strength="STRONG",
            ),
            self.run(
                7,
                olt.LoadVector(E=10.2, J=4.2, O=3, R=2, X=1),
                strength="STRONG",
            ),
        ]
        result = olt_eta.estimate_from_vector(runs, target, task_class="meteor")
        self.assertLess(result["p80_minutes"], 30)

    def test_task_class_match_gets_small_boost_not_hard_filter(self):
        target = olt.LoadVector(E=8, J=3, O=2, R=1, X=1)
        runs = [
            self.run(8, target, task="other"),
            self.run(6, target, task="meteor"),
        ]
        result = olt_eta.estimate_from_vector(runs, target, task_class="meteor")
        self.assertEqual(result["class_matched_neighbors"], 1)
        self.assertEqual(result["come_back_after_minutes"], 8)

    def test_direct_history_eventually_eliminates_prior_influence(self):
        direct = {
            "come_back_after_minutes": 4,
            "samples": 8,
            "basis": "RECENT_CLASS_HISTORY",
        }
        prior = {
            "come_back_after_minutes": 12,
            "basis": "OLT_VECTOR_PRIOR",
        }
        result = olt_eta.blend_with_direct_history(direct, prior)
        self.assertEqual(result["come_back_after_minutes"], 4)
        self.assertEqual(result["olt_influence"], 0.0)

    def test_sparse_direct_history_can_be_nudged_by_olt_prior(self):
        direct = {
            "come_back_after_minutes": 4,
            "samples": 2,
            "basis": "RECENT_CLASS_HISTORY",
        }
        prior = {
            "come_back_after_minutes": 8,
            "basis": "OLT_VECTOR_PRIOR",
        }
        result = olt_eta.blend_with_direct_history(direct, prior)
        self.assertEqual(result["basis"], "DIRECT_PLUS_OLT_VECTOR_PRIOR")
        self.assertGreater(result["come_back_after_minutes"], 4)
        self.assertLess(result["come_back_after_minutes"], 8)

    def test_invalid_duration_and_evidence_strength_fail_closed(self):
        target = olt.LoadVector(E=1, J=1, O=1, R=1, X=1)
        with self.assertRaises(olt_eta.OLTETAError):
            olt_eta.estimate_from_vector([self.run(0, target)], target)
        with self.assertRaises(olt_eta.OLTETAError):
            olt_eta.estimate_from_vector(
                [self.run(5, target, strength="TRUST_ME")],
                target,
            )


if __name__ == "__main__":
    unittest.main()
