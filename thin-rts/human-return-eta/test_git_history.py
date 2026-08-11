from datetime import datetime
import unittest

import git_history


class GitHistoryTests(unittest.TestCase):
    def commit(self, sha, timestamp, subject="x"):
        return {
            "sha": sha,
            "timestamp": datetime.fromisoformat(timestamp),
            "subject": subject,
        }

    def test_adjacent_intervals_are_always_weak(self):
        rows = [
            self.commit("a" * 40, "2026-08-11T22:00:00+09:00"),
            self.commit("b" * 40, "2026-08-11T22:04:00+09:00"),
        ]
        out = git_history.adjacent_weak_history(
            rows,
            task_class="meteor",
            max_gap_minutes=30,
            weighted_chunks=2,
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["evidence_strength"], "WEAK")
        self.assertEqual(out[0]["weighted_chunks"], 2)
        self.assertTrue(out[0]["source"].startswith("git-adjacent:"))

    def test_large_idle_gap_is_not_imported(self):
        rows = [
            self.commit("a" * 40, "2026-08-11T20:00:00+09:00"),
            self.commit("b" * 40, "2026-08-11T22:00:00+09:00"),
        ]
        out = git_history.adjacent_weak_history(
            rows,
            task_class="meteor",
            max_gap_minutes=30,
        )
        self.assertEqual(out, [])

    def test_non_monotonic_pair_is_not_imported(self):
        rows = [
            self.commit("a" * 40, "2026-08-11T22:04:00+09:00"),
            self.commit("b" * 40, "2026-08-11T22:00:00+09:00"),
        ]
        out = git_history.adjacent_weak_history(
            rows,
            task_class="meteor",
            max_gap_minutes=30,
        )
        self.assertEqual(out, [])

    def test_invalid_limits_are_rejected(self):
        with self.assertRaises(git_history.GitHistoryError):
            git_history.adjacent_weak_history([], task_class="x", max_gap_minutes=0)
        with self.assertRaises(git_history.GitHistoryError):
            git_history.adjacent_weak_history(
                [], task_class="x", max_gap_minutes=30, weighted_chunks=0
            )


if __name__ == "__main__":
    unittest.main()
