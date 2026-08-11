import json
from collections import defaultdict
from pathlib import Path
import unittest

import olt


DATA = Path(__file__).with_name("olt_recovery_v0_5.json")


class OLTRecoveryV05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.rows = cls.data["daily_project"]

    def test_recovered_summary_recomputes(self):
        self.assertEqual(sum(r["exact_human"] for r in self.rows), 57)
        self.assertEqual(sum(r["exact_chat"] for r in self.rows), 37)
        self.assertAlmostEqual(sum(r["active_min"] for r in self.rows), 225.9, places=9)
        self.assertEqual(len({r["date"] for r in self.rows}), 26)
        self.assertEqual(self.data["summary"]["observed_days"], 26)

    def test_every_daily_project_score_and_coverage_recomputes(self):
        for row in self.rows:
            with self.subTest(date=row["date"], project=row["project"]):
                partial = olt.PartialLoadVector(**row["load"])
                self.assertAlmostEqual(olt.axis_coverage(partial), row["coverage"], places=12)
                self.assertAlmostEqual(olt.lower_bound_score(partial), row["olt_lower_bound"], places=9)

    def test_daily_fusion_keeps_unknown_axes_unknown(self):
        grouped = defaultdict(list)
        for row in self.rows:
            grouped[row["date"]].append(olt.PartialLoadVector(**row["load"]))
        july23 = olt.fuse_partial_vectors(grouped["2026-07-23"])
        self.assertAlmostEqual(july23.E, 2.057777777777778)
        self.assertEqual(july23.J, 3)
        self.assertEqual(july23.R, 3)
        self.assertIsNone(july23.O)
        self.assertIsNone(july23.X)
        self.assertAlmostEqual(olt.lower_bound_score(july23), 18.389942419951872, places=9)

    def test_march_architecture_line_is_real_human_evidence(self):
        march = [r for r in self.rows if r["date"].startswith("2026-03-")]
        self.assertEqual(sum(r["exact_chat"] for r in march), 10)
        self.assertEqual(sum((r["load"]["J"] or 0) for r in march), 9)
        self.assertEqual({r["date"] for r in march}, {"2026-03-03", "2026-03-06", "2026-03-13", "2026-03-16"})

    def test_july27_remains_observed_peak_after_v05_breadth_recovery(self):
        grouped = defaultdict(list)
        for row in self.rows:
            grouped[row["date"]].append(olt.PartialLoadVector(**row["load"]))
        scored = {date: olt.lower_bound_score(olt.fuse_partial_vectors(vectors)) for date, vectors in grouped.items()}
        peak_day = max(scored, key=scored.get)
        self.assertEqual(peak_day, "2026-07-27")
        self.assertAlmostEqual(scored[peak_day], 61.529922924947165, places=9)
        self.assertEqual(self.data["summary"]["peak_day"], peak_day)

    def test_june29_spec_delegate_reference_intake_anchor(self):
        row = next(r for r in self.rows if r["date"] == "2026-06-29")
        self.assertEqual(row["project"], "RTS-minicompany")
        self.assertEqual(row["exact_chat"], 3)
        self.assertAlmostEqual(row["load"]["E"], 3.0655555555555556)
        self.assertEqual(row["load"]["J"], 4)
        self.assertAlmostEqual(row["olt_lower_bound"], 18.034685343617372, places=9)

    def test_monthly_vectors_recompute_from_observed_daily_rows(self):
        by_month = defaultdict(list)
        for row in self.rows:
            by_month[row["date"][:7]].append(olt.PartialLoadVector(**row["load"]))
        monthly = {r["month"]: r for r in self.data["monthly_fused"]}
        for month, row in monthly.items():
            if row["observed_days"] == 0:
                self.assertTrue(all(value is None for value in row["load"].values()))
                self.assertIsNone(row["olt_mass"])
                continue
            fused = olt.fuse_partial_vectors(by_month[month])
            expected = olt.PartialLoadVector(**row["load"])
            self.assertEqual(fused.as_dict(), expected.as_dict())
            self.assertAlmostEqual(olt.axis_coverage(fused), row["coverage"], places=12)
            self.assertAlmostEqual(olt.lower_bound_score(fused), row["olt_mass"], places=9)

    def test_monthly_exact_counts_match_summary(self):
        monthly = self.data["monthly_fused"]
        self.assertEqual(sum(r["exact_human"] for r in monthly), 57)
        self.assertEqual(sum(r["exact_chat"] for r in monthly), 37)
        self.assertAlmostEqual(sum(r["active_min"] for r in monthly), 225.9, places=9)
        march = next(r for r in monthly if r["month"] == "2026-03")
        self.assertEqual(march["load"]["J"], 9)
        self.assertAlmostEqual(march["olt_mass"], 36.2438428408327, places=9)

    def test_recovery_coverage_is_not_workload_coverage(self):
        recovery = {r["month"]: r for r in self.data["recovery_coverage"]}
        self.assertEqual(recovery["2026-03"]["next_target"], "PR #1-#130 stage-to-chat binding")
        self.assertEqual(recovery["2026-08"]["observed_days"], 7)
        self.assertEqual(recovery["2026-08"]["days_in_scope"], 12)
        self.assertEqual(self.data["summary"]["historical_status"], "PARTIAL")

    def test_role_transition_is_hypothesis_not_causal_fact(self):
        interpretation = self.data["interpretation"]
        self.assertIn("HYPOTHESIS", interpretation["status"])
        self.assertEqual(
            interpretation["next_material_test"],
            "Bind March PR #1-#130 stages to recovered exact ChatGPT decision timestamps and measure machine-visible work between human hinges.",
        )


if __name__ == "__main__":
    unittest.main()
