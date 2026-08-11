import json
from pathlib import Path
import unittest

import olt


DATA = Path(__file__).with_name("olt_actual_v0_2.json")


class OLTActualV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(DATA.read_text(encoding="utf-8"))

    def test_all_lower_bounds_and_axis_coverage_recompute(self):
        for row in self.rows:
            with self.subTest(window=row["window"]):
                partial = olt.PartialLoadVector(**row["load"])
                self.assertAlmostEqual(
                    olt.axis_coverage(partial), row["axis_coverage"], places=12
                )
                self.assertAlmostEqual(
                    olt.lower_bound_score(partial), row["olt_lower_bound"], places=9
                )

    def test_missing_axes_remain_unobserved_not_zero(self):
        pre = next(r for r in self.rows if "Pre-Kernel" in r["window"])
        self.assertIsNone(pre["load"]["J"])
        self.assertIsNone(pre["load"]["O"])
        self.assertEqual(pre["axis_coverage"], 0.2)

    def test_amplification_ratios_recompute(self):
        for row in self.rows:
            if row["commits_per_stage"] is None:
                continue
            with self.subTest(window=row["window"]):
                self.assertAlmostEqual(
                    olt.amplification_ratio(row["raw_commits"], row["governed_stages"]),
                    row["commits_per_stage"],
                    places=9,
                )

    def test_judgment_pressure_ratios_recompute_only_when_recorded(self):
        for row in self.rows:
            if "judgment_pressure_ratio" not in row:
                continue
            load = row["load"]
            with self.subTest(window=row["window"]):
                self.assertAlmostEqual(
                    olt.judgment_pressure_ratio(load["J"], load["R"], load["O"]),
                    row["judgment_pressure_ratio"],
                    places=9,
                )

    def test_current_largest_lower_bound_is_rts_july_27(self):
        peak = max(self.rows, key=lambda row: row["olt_lower_bound"])
        self.assertEqual(peak["project"], "RTS")
        self.assertEqual(peak["window"], "2026-07-27 PR #276–#291")
        self.assertAlmostEqual(peak["olt_lower_bound"], 52.205955016318626)

    def test_extreme_commit_amplification_is_not_load_axis(self):
        sale = next(r for r in self.rows if r["window"] == "PR #91 public-sale authority")
        self.assertEqual(sale["commits_per_stage"], 361.0)
        self.assertNotIn("Gamma", sale["load"])
        self.assertEqual(set(sale["load"]), set(olt.OLT_AXES))

    def test_ratio_denominators_fail_closed(self):
        with self.assertRaises(olt.OLTError):
            olt.amplification_ratio(100, 0)
        with self.assertRaises(olt.OLTError):
            olt.judgment_pressure_ratio(2, 3, 0)


if __name__ == "__main__":
    unittest.main()
