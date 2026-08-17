from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("stage0_control.py")
spec = importlib.util.spec_from_file_location("reconstruction_furnace_stage0_control", MODULE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class Stage0ControlTests(unittest.TestCase):
    def test_pinned_seed_selects_c_and_go(self) -> None:
        manifest = mod.build_run_manifest(
            stage="STAGE0",
            seed_label="ULTIMATE_LOOP_RECONSTRUCTION_FURNACE_STAGE0",
            dataset_revision="608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b",
            evaluator_revision="70ec57e852e3f2d195790fe71f553e272c691833",
            split_count=2,
        )
        self.assertEqual(manifest.selected_splits, ("c", "go"))
        self.assertFalse(manifest.solver_dataset_access)
        self.assertEqual(
            manifest.seed_sha256,
            "050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b",
        )

    def test_candidate_order_is_deterministic_and_gold_agnostic(self) -> None:
        rows_a = [
            {"instance_id": "r__x-2", "patch": "gold-two"},
            {"instance_id": "r__x-1", "patch": "gold-one"},
        ]
        rows_b = [
            {"instance_id": "r__x-2", "patch": "completely-different"},
            {"instance_id": "r__x-1", "patch": "also-different"},
        ]
        order_a = [
            row["instance_id"]
            for row in mod.candidate_order(rows_a, split="c", seed_sha256="a" * 64)
        ]
        order_b = [
            row["instance_id"]
            for row in mod.candidate_order(rows_b, split="c", seed_sha256="a" * 64)
        ]
        self.assertEqual(order_a, order_b)

    def test_first_valid_is_first_three_of_three_not_cherry_pick(self) -> None:
        rows = [
            {"instance_id": "a"},
            {"instance_id": "b"},
            {"instance_id": "c"},
        ]
        selected = mod.choose_first_valid(rows, {"a": 2, "b": 3, "c": 3})
        self.assertEqual(selected["instance_id"], "b")

    def test_missing_validation_in_prefix_fails_closed(self) -> None:
        rows = [{"instance_id": "a"}, {"instance_id": "b"}]
        with self.assertRaises(mod.FurnaceControlError):
            mod.choose_first_valid(rows, {"b": 3})

    def test_resource_block_is_not_solver_failure(self) -> None:
        result = mod.resource_preflight(cpu_count=2, memory_gib=8)
        self.assertEqual(result["state"], "RESOURCE_BLOCKED")
        self.assertFalse(result["solver_failure"])
        self.assertIn("CPU_BELOW_REQUEST", result["blockers"])
        self.assertIn("MEMORY_BELOW_REQUEST", result["blockers"])

    def test_opaque_id_hides_instance_text(self) -> None:
        task_id = mod.opaque_task_id(
            instance_id="repo__repo-12345",
            seed_sha256="b" * 64,
            ordinal=1,
        )
        self.assertNotIn("repo", task_id.lower())
        self.assertNotIn("12345", task_id)


if __name__ == "__main__":
    unittest.main()
