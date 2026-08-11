import json
from datetime import datetime
from pathlib import Path
import unittest


DATA = Path(__file__).with_name("march_hinge_binding_v0_1.json")


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


class MarchHingeBindingV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_strong_bound_stages_are_strictly_after_hinge(self):
        for binding in self.data["bindings"]:
            hinge = parse(binding["human_hinge"]["timestamp"])
            self.assertEqual(binding["evidence"], "STRONG")
            for stage in binding["stages"]:
                created = parse(stage["created_at"])
                self.assertGreater(created, hinge)
                expected = int((created - hinge).total_seconds())
                self.assertEqual(stage["delta_seconds_from_hinge"], expected)

    def test_readme_move_binding_has_expected_three_stage_shape(self):
        binding = next(b for b in self.data["bindings"] if b["id"].endswith("README-MOVE"))
        self.assertEqual([s["pr"] for s in binding["stages"]], [97, 98, 99])
        self.assertEqual(binding["machine_visible_stages"], 3)
        self.assertEqual(binding["first_stage_latency_seconds"], 42)
        self.assertEqual(binding["last_stage_merge_latency_seconds"], 302)

    def test_readme_reinforcement_patch_binding_is_subminute(self):
        binding = next(b for b in self.data["bindings"] if b["id"].endswith("README-REINFORCE"))
        self.assertEqual([s["pr"] for s in binding["stages"]], [101])
        self.assertEqual(binding["first_stage_latency_seconds"], 54)
        self.assertEqual(binding["last_stage_merge_latency_seconds"], 61)
        self.assertIn("structurally, not socially", binding["stages"][0]["semantic_evidence"])

    def test_semantically_tempting_pre_hinge_boundary_prs_are_rejected(self):
        rejected = self.data["rejected_candidates"][0]
        hinge = parse(rejected["human_hinge_timestamp"])
        start_text, end_text = rejected["candidate_created_range_jst"].split("..")
        self.assertLess(parse(start_text), hinge)
        self.assertLess(parse(end_text), hinge)
        self.assertEqual(rejected["candidate_prs"], [90, 91, 92])
        self.assertEqual(rejected["verdict"], "REJECT_TEMPORAL_CAUSAL_BINDING")

    def test_pilot_metrics_recompute(self):
        bindings = self.data["bindings"]
        stages = sum(len(b["stages"]) for b in bindings)
        commits = sum(b["machine_visible_commits"] for b in bindings)
        metrics = self.data["pilot_metrics"]
        self.assertEqual(metrics["strong_bound_hinges"], len(bindings))
        self.assertEqual(metrics["strong_bound_stages"], stages)
        self.assertEqual(metrics["strong_bound_commits"], commits)
        self.assertEqual(metrics["stages_per_bound_hinge"], stages / len(bindings))
        self.assertEqual(metrics["commits_per_bound_hinge"], commits / len(bindings))

    def test_pr_output_is_not_declared_human_load(self):
        self.assertFalse(self.data["rules"]["raw_pr_count_is_human_load"])
        self.assertFalse(self.data["rules"]["timestamp_proximity_alone_is_strong"])
        self.assertFalse(self.data["rules"]["semantic_similarity_with_pr_before_hinge_is_binding"])


if __name__ == "__main__":
    unittest.main()
