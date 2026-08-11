import unittest

import eta


class ETAHybridTests(unittest.TestCase):
    def obs(
        self,
        start,
        end,
        *,
        task="meteor",
        chunks=None,
        strength="STRONG",
    ):
        record = {
            "task_class": task,
            "started_at": start,
            "human_hinge_at": end,
            "terminal": "READY_FOR_REVIEW",
            "evidence_strength": strength,
        }
        if chunks is not None:
            record["weighted_chunks"] = chunks
        return eta.normalize_record(record)

    def test_hybrid_scales_same_class_history_by_target_chunks(self):
        rows = [
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:04:00+09:00", chunks=2),
            self.obs("2026-08-11T22:10:00+09:00", "2026-08-11T22:14:00+09:00", chunks=2),
        ]
        result = eta.estimate(rows, "meteor", target_chunks=3)
        self.assertEqual(result["basis"], "HYBRID_GIT_TIME_AND_CHUNK")
        self.assertEqual(result["come_back_after_minutes"], 6)
        self.assertEqual(result["chunk_estimate_minutes"], 6.0)
        self.assertEqual(result["historical_chunk_median"], 2.0)

    def test_explicit_chunk_prior_bootstraps_unseen_task(self):
        result = eta.estimate(
            [],
            "new-task",
            target_chunks=5,
            prior_minutes_per_chunk=1.5,
        )
        self.assertEqual(result["basis"], "CHUNK_PRIOR_ONLY")
        self.assertEqual(result["come_back_after_minutes"], 8)
        self.assertEqual(result["chunk_rate_source"], "EXPLICIT_CHUNK_PRIOR")

    def test_global_chunk_history_can_seed_unseen_class(self):
        rows = [
            self.obs(
                "2026-08-11T22:00:00+09:00",
                "2026-08-11T22:04:00+09:00",
                task="known",
                chunks=2,
            )
        ]
        result = eta.estimate(rows, "new-task", target_chunks=3)
        self.assertEqual(result["basis"], "CHUNK_PRIOR_ONLY")
        self.assertEqual(result["chunk_rate_source"], "GLOBAL_CHUNK_HISTORY")
        self.assertEqual(result["come_back_after_minutes"], 6)

    def test_weak_git_outlier_has_low_weight(self):
        rows = [
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:04:00+09:00"),
            self.obs("2026-08-11T22:10:00+09:00", "2026-08-11T22:14:00+09:00"),
            self.obs("2026-08-11T22:20:00+09:00", "2026-08-11T22:24:00+09:00"),
            self.obs(
                "2026-08-11T22:30:00+09:00",
                "2026-08-11T23:10:00+09:00",
                strength="WEAK",
            ),
        ]
        result = eta.estimate(rows, "meteor")
        self.assertEqual(result["p80_minutes"], 4.0)
        self.assertEqual(result["come_back_after_minutes"], 4)
        self.assertIn("WEAK", result["evidence_mix"])

    def test_invalid_chunk_and_evidence_strength_are_rejected(self):
        with self.assertRaises(eta.ETAError):
            eta.normalize_record({
                "task_class": "meteor",
                "started_at": "2026-08-11T22:00:00+09:00",
                "human_hinge_at": "2026-08-11T22:04:00+09:00",
                "terminal": "READY_FOR_REVIEW",
                "weighted_chunks": 0,
            })
        with self.assertRaises(eta.ETAError):
            eta.normalize_record({
                "task_class": "meteor",
                "started_at": "2026-08-11T22:00:00+09:00",
                "human_hinge_at": "2026-08-11T22:04:00+09:00",
                "terminal": "READY_FOR_REVIEW",
                "evidence_strength": "TRUST_ME",
            })

    def test_invalid_target_chunk_prior_is_rejected(self):
        with self.assertRaises(eta.ETAError):
            eta.estimate([], "meteor", target_chunks=0)
        with self.assertRaises(eta.ETAError):
            eta.estimate([], "meteor", target_chunks=1, prior_minutes_per_chunk=-1)


if __name__ == "__main__":
    unittest.main()
