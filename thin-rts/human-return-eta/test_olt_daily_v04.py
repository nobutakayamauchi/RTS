import json
from pathlib import Path
import unittest

import olt


DATA = Path(__file__).with_name("olt_daily_v0_4.json")


class OLTDailyV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_exact_human_totals_recompute(self):
        rows = self.data["exact_human"]["by_day"]
        self.assertEqual(sum(row["events"] for row in rows), 36)
        self.assertAlmostEqual(
            sum(row["active_minutes"] for row in rows),
            167.06666666666672,
            places=9,
        )
        self.assertEqual(self.data["exact_human"]["events"], 36)
        self.assertAlmostEqual(
            self.data["exact_human"]["active_minutes"],
            167.06666666666672,
            places=9,
        )

    def test_daily_exact_e_matches_canonical_formula(self):
        for anchor in self.data["exact_human"]["by_day"]:
            matching = [
                row for row in self.data["project_daily"]
                if row["date"] == anchor["date"] and row["project"] == anchor["project"]
            ]
            self.assertEqual(len(matching), 1)
            expected = anchor["events"] + anchor["active_minutes"] / 15.0
            self.assertAlmostEqual(matching[0]["load"]["E"], expected, places=9)

    def test_project_daily_scores_and_coverage_recompute(self):
        for row in self.data["project_daily"]:
            partial = olt.PartialLoadVector(**row["load"])
            with self.subTest(date=row["date"], project=row["project"]):
                self.assertAlmostEqual(olt.axis_coverage(partial), row["coverage"], places=12)
                self.assertAlmostEqual(
                    olt.lower_bound_score(partial), row["olt_lower_bound"], places=9
                )

    def test_july_27_fusion_adds_e_without_double_counting_j(self):
        row = next(
            row for row in self.data["project_daily"]
            if row["date"] == "2026-07-27" and row["project"] == "RTS"
        )
        self.assertAlmostEqual(row["load"]["E"], 5 + 36.66666666666667 / 15.0, places=9)
        self.assertEqual(row["load"]["J"], 10)
        self.assertEqual(row["load"]["O"], 26.5)
        self.assertEqual(row["load"]["R"], 10)
        self.assertIsNone(row["load"]["X"])
        self.assertAlmostEqual(row["olt_lower_bound"], 61.529922924947165, places=9)
        self.assertGreater(
            self.data["hotspot"]["v0_4_lower_bound"],
            self.data["hotspot"]["previous_v0_3_lower_bound"],
        )

    def test_july_23_unresolved_project_stays_separate_but_fuses_overall(self):
        rows = [row for row in self.data["project_daily"] if row["date"] == "2026-07-23"]
        self.assertEqual({row["project"] for row in rows}, {"RTS-minicompany", "UNRESOLVED_PROJECT"})
        unresolved = next(row for row in rows if row["project"] == "UNRESOLVED_PROJECT")
        mini = next(row for row in rows if row["project"] == "RTS-minicompany")
        fused = olt.fuse_partial_vectors([
            olt.PartialLoadVector(**unresolved["load"]),
            olt.PartialLoadVector(**mini["load"]),
        ])
        overall = next(row for row in self.data["overall_daily"] if row["date"] == "2026-07-23")
        self.assertEqual(fused.as_dict(), overall["load"])
        self.assertAlmostEqual(olt.lower_bound_score(fused), overall["olt_lower_bound"], places=9)
        self.assertIn("Do not link", self.data["unresolved_events"][0]["forbidden_link"])

    def test_partial_fusion_preserves_unknown_axes(self):
        fused = olt.fuse_partial_vectors([
            olt.PartialLoadVector(E=2.0, R=3.0),
            olt.PartialLoadVector(J=3.0),
        ])
        self.assertEqual(fused.E, 2.0)
        self.assertEqual(fused.J, 3.0)
        self.assertEqual(fused.R, 3.0)
        self.assertIsNone(fused.O)
        self.assertIsNone(fused.X)
        with self.assertRaises(olt.OLTError):
            olt.fuse_partial_vectors([])

    def test_unobserved_source_zero_cells_are_canonicalized_to_null(self):
        april = next(
            row for row in self.data["project_daily"]
            if row["date"] == "2026-04-19"
        )
        self.assertIsNone(april["load"]["O"])
        self.assertIsNone(april["load"]["X"])
        note = self.data["known_source_representation_notes"][0]
        self.assertIn("null", note["canonical"])
        self.assertFalse(self.data["invariants"]["missing_axis_equals_zero"])

    def test_no_fatigue_or_zero_work_is_inferred_from_missing_days(self):
        inv = self.data["invariants"]
        self.assertFalse(inv["blank_date_equals_zero_work"])
        self.assertFalse(inv["fatigue_from_gap_or_pr_drop"])
        self.assertEqual(inv["full_daily_materialization"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
