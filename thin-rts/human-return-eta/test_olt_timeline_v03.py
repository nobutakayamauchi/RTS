import json
from pathlib import Path
import unittest


DATA = Path(__file__).with_name("olt_timeline_v0_3.json")


class OLTTimelineV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_monthly_shares_recompute_and_stay_weak(self):
        for row in self.data["portfolio_monthly"]:
            self.assertEqual(row["evidence"], "WEAK")
            total = row["tracked_total"]
            computed = sum(row[k] for k in ("RTS", "RTS-AGE", "RTS-minicompany", "rts-video-flow"))
            self.assertEqual(total, computed)
            if total == 0:
                self.assertNotIn("shares", row)
                continue
            shares = row["shares"]
            self.assertAlmostEqual(sum(shares.values()), 1.0, places=12)
            for key in ("RTS", "RTS-AGE", "RTS-minicompany", "rts-video-flow"):
                self.assertAlmostEqual(shares[key], row[key] / total, places=12)

    def test_focus_migration_sequence_is_recovered(self):
        rows = {r["period"]: r for r in self.data["portfolio_monthly"]}
        self.assertEqual(rows["2026-02"]["dominant_surface"], "RTS")
        self.assertEqual(rows["2026-05"]["dominant_surface"], "RTS-AGE")
        self.assertEqual(rows["2026-06"]["dominant_surface"], "RTS-AGE")
        self.assertEqual(rows["2026-07"]["dominant_surface"], "RTS-minicompany≈RTS")
        self.assertEqual(rows["2026-08-01..12"]["dominant_surface"], "RTS")

    def test_rts_burst_peak_is_output_proxy_only(self):
        bursts = self.data["rts_bursts"]
        for row in bursts:
            self.assertEqual(row["evidence"], "WEAK")
            self.assertAlmostEqual(row["pr_per_day"], row["prs"] / row["days"], places=12)
        peak = max(bursts, key=lambda r: r["pr_per_day"])
        self.assertEqual(peak["window"], "2026-03-01..07")
        self.assertAlmostEqual(peak["pr_per_day"], 104 / 7, places=12)
        self.assertFalse(self.data["timeline_invariants"]["pr_burst_is_fatigue_evidence"])
        self.assertFalse(self.data["timeline_invariants"]["zero_pr_means_zero_work"])

    def test_selected_decision_rollup_recomputes(self):
        rows = [r for r in self.data["selected_decisions"] if r["rollup"]]
        self.assertEqual(sum(r["J"] for r in rows), self.data["rollup"]["selected_J"])
        self.assertEqual(sum(r["R"] for r in rows), self.data["rollup"]["selected_R"])
        self.assertEqual(sum(1 for r in rows if r["class"] == "D3"), self.data["rollup"]["selected_D3"])
        self.assertEqual(self.data["rollup"], {"selected_J": 21, "selected_R": 7, "selected_D3": 3})
        self.assertEqual(len({r["dedup_group"] for r in rows}), len(rows))
        self.assertTrue(all(r["evidence"] == "STRONG" for r in rows))

    def test_weak_proxy_never_becomes_direct_semantic_load(self):
        self.assertFalse(self.data["timeline_invariants"]["portfolio_proxy_is_human_load"])
        self.assertEqual(self.data["timeline_invariants"]["canonical_load"], "(E,J,O,R,X)")
        self.assertFalse(self.data["timeline_invariants"]["unknown_equals_zero"])

    def test_video_judgment_pressure_discrepancy_is_fail_closed(self):
        discrepancy = next(
            d for d in self.data["known_source_discrepancies"]
            if d["id"] == "V03-DASH-JPR-VIDEO"
        )
        self.assertEqual(discrepancy["source_value"], 0)
        self.assertIsNone(discrepancy["canonical_value"])
        self.assertIn("UNOBSERVED", discrepancy["reason"])

    def test_full_materialization_remains_unproven(self):
        self.assertEqual(
            self.data["timeline_invariants"]["full_event_level_materialization"],
            "NOT_PROVEN",
        )


if __name__ == "__main__":
    unittest.main()
