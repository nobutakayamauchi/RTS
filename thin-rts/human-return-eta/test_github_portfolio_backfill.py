import unittest

import github_portfolio_backfill as backfill


class GitHubPortfolioBackfillTests(unittest.TestCase):
    def commit(self, sha, timestamp):
        return {"sha": sha, "timestamp": timestamp}

    def test_repo_key_is_stable_and_name_not_exposed(self):
        key1 = backfill.stable_repo_key("Owner/PrivateRepo")
        key2 = backfill.stable_repo_key("owner/privaterepo")
        self.assertEqual(key1, key2)
        self.assertNotIn("private", key1.lower())
        self.assertEqual(len(key1), 20)

    def test_sessionization_splits_large_idle_gap(self):
        commits = [
            self.commit("a" * 40, "2026-08-11T10:00:00Z"),
            self.commit("b" * 40, "2026-08-11T10:04:00Z"),
            self.commit("c" * 40, "2026-08-11T12:00:00Z"),
            self.commit("d" * 40, "2026-08-11T12:03:00Z"),
        ]
        rows = backfill.sessionize_commits(
            commits,
            repo_full_name="owner/repo",
            max_gap_minutes=30,
        )
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["evidence_strength"] == "WEAK" for r in rows))
        self.assertTrue(all(r["terminal"] == "GIT_SESSION_END" for r in rows))

    def test_single_commit_session_is_not_fabricated_into_duration(self):
        commits = [self.commit("a" * 40, "2026-08-11T10:00:00Z")]
        rows = backfill.sessionize_commits(
            commits,
            repo_full_name="owner/repo",
            max_gap_minutes=30,
        )
        self.assertEqual(rows, [])

    def test_raw_repository_name_and_commit_message_are_not_emitted(self):
        commits = [
            self.commit("a" * 40, "2026-08-11T10:00:00Z"),
            self.commit("b" * 40, "2026-08-11T10:04:00Z"),
        ]
        rows = backfill.sessionize_commits(
            commits,
            repo_full_name="secret-owner/sensitive-private-project",
            max_gap_minutes=30,
        )
        payload = str(rows)
        self.assertNotIn("sensitive-private-project", payload)
        self.assertNotIn("secret-owner", payload)

    def test_invalid_repo_and_gap_are_rejected(self):
        with self.assertRaises(backfill.BackfillError):
            backfill.stable_repo_key("not-a-full-name")
        with self.assertRaises(backfill.BackfillError):
            backfill.sessionize_commits([], repo_full_name="owner/repo", max_gap_minutes=0)


if __name__ == "__main__":
    unittest.main()
