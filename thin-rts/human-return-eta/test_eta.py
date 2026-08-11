import json
from pathlib import Path
import tempfile
import unittest

import eta


class ETABaselineTests(unittest.TestCase):
    def obs(self, start, end, task="meteor", terminal="READY_FOR_REVIEW"):
        return eta.normalize_record({
            "task_class": task,
            "started_at": start,
            "human_hinge_at": end,
            "terminal": terminal,
        })

    def test_cold_start_is_explicit(self):
        result = eta.estimate([], "unknown")
        self.assertEqual(result["samples"], 0)
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["basis"], "COLD_START_FALLBACK")
        self.assertGreater(result["late_after_minutes"], result["come_back_after_minutes"])

    def test_task_classes_are_not_mixed(self):
        rows = [
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:04:00+09:00", task="meteor"),
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:40:00+09:00", task="cloud"),
        ]
        result = eta.estimate(rows, "meteor")
        self.assertEqual(result["samples"], 1)
        self.assertEqual(result["come_back_after_minutes"], 4)

    def test_timezone_offsets_can_differ(self):
        row = self.obs("2026-08-11T13:00:00+00:00", "2026-08-11T22:05:00+09:00")
        self.assertAlmostEqual(row.duration_minutes, 5.0)

    def test_early_error_is_legitimate_human_hinge(self):
        rows = [
            self.obs("2026-08-11T22:00:00+09:00", "2026-08-11T22:02:00+09:00", terminal="ERROR"),
            self.obs("2026-08-11T22:10:00+09:00", "2026-08-11T22:14:00+09:00"),
            self.obs("2026-08-11T22:20:00+09:00", "2026-08-11T22:25:00+09:00", terminal="APPROVAL_REQUIRED"),
        ]
        result = eta.estimate(rows, "meteor")
        self.assertEqual(result["samples"], 3)
        self.assertIn("ERROR", result["terminal_mix"])
        self.assertIn("APPROVAL_REQUIRED", result["terminal_mix"])

    def test_duplicate_jsonl_observation_is_deduplicated(self):
        record = {
            "task_class": "meteor",
            "started_at": "2026-08-11T22:00:00+09:00",
            "human_hinge_at": "2026-08-11T22:04:00+09:00",
            "terminal": "READY_FOR_REVIEW",
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "h.jsonl"
            path.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n", encoding="utf-8")
            rows = eta.load_jsonl(path)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
