import unittest

import eta


class ETAMeteorAttacks(unittest.TestCase):
    def obs(self, start, end, task="meteor", terminal="READY_FOR_REVIEW"):
        return eta.normalize_record({
            "task_class": task,
            "started_at": start,
            "human_hinge_at": end,
            "terminal": terminal,
        })

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(eta.ETAError):
            self.obs("2026-08-11T22:00:00", "2026-08-11T22:04:00+09:00")

    def test_zero_or_negative_duration_is_rejected(self):
        for end in ("2026-08-11T22:00:00+09:00", "2026-08-11T21:59:00+09:00"):
            with self.subTest(end=end):
                with self.assertRaises(eta.ETAError):
                    self.obs("2026-08-11T22:00:00+09:00", end)

    def test_outlier_does_not_move_median_to_outlier(self):
        rows = [
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:04:00+09:00"),
            self.obs("2026-08-11T22:10:00+09:00", "2026-08-11T22:14:00+09:00"),
            self.obs("2026-08-11T22:20:00+09:00", "2026-08-11T22:24:00+09:00"),
            self.obs("2026-08-11T22:30:00+09:00", "2026-08-11T23:30:00+09:00"),
        ]
        result = eta.estimate(rows, "meteor")
        self.assertEqual(result["median_minutes"], 4.0)
        self.assertEqual(result["confidence"], "LOW")

    def test_recent_window_prevents_ancient_history_from_dominating(self):
        rows = []
        for day in range(1, 11):
            rows.append(self.obs(
                f"2026-07-{day:02d}T22:00:00+09:00",
                f"2026-07-{day:02d}T22:30:00+09:00",
            ))
        for minute in (3, 4, 4, 5):
            rows.append(self.obs(
                "2026-08-11T22:00:00+09:00",
                f"2026-08-11T22:{minute:02d}:00+09:00",
            ))
        result = eta.estimate(rows, "meteor", window=4)
        self.assertEqual(result["samples"], 4)
        self.assertLessEqual(result["come_back_after_minutes"], 5)

    def test_small_sample_never_claims_high_confidence(self):
        rows = [
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:04:00+09:00"),
            self.obs("2026-08-11T22:10:00+09:00", "2026-08-11T22:14:00+09:00"),
        ]
        self.assertEqual(eta.estimate(rows, "meteor")["confidence"], "LOW")

    def test_long_tail_pushes_return_target_later_than_median(self):
        rows = []
        for i, minutes in enumerate((3, 3, 4, 4, 5, 5, 8, 20)):
            start_minute = i * 2
            rows.append(self.obs(
                f"2026-08-11T20:{start_minute:02d}:00+09:00",
                f"2026-08-11T20:{start_minute + minutes:02d}:00+09:00",
            ))
        result = eta.estimate(rows, "meteor")
        self.assertGreaterEqual(result["come_back_after_minutes"], result["median_minutes"])
        self.assertGreater(result["late_after_minutes"], result["come_back_after_minutes"])

    def test_invalid_window_and_fallback_are_rejected(self):
        with self.assertRaises(eta.ETAError):
            eta.estimate([], "meteor", window=0)
        with self.assertRaises(eta.ETAError):
            eta.estimate([], "meteor", fallback_minutes=0)


if __name__ == "__main__":
    unittest.main()
