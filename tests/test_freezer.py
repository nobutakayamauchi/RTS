import json
import shutil
import tempfile
import unittest
from pathlib import Path

from freezer.cli import (
    FreezerError,
    add_item,
    compute_score,
    load_config,
    rebuild,
    revise_item,
    validate_item,
    verify,
)


class FreezerTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.config = load_config(self.repo_root)
        self.item = json.loads(
            (
                self.repo_root
                / "freezer"
                / "items"
                / "RTS-FRZ-000001"
                / "v001.json"
            ).read_text(encoding="utf-8")
        )

    def isolated_root(self, temp_dir: str) -> Path:
        temp_root = Path(temp_dir)
        shutil.copytree(self.repo_root / "freezer", temp_root / "freezer")
        return temp_root

    def test_seed_item_is_valid(self):
        validate_item(self.item, self.config)

    def test_priority_score_is_deterministic(self):
        self.assertEqual(compute_score(self.item, self.config), 65.25)

    def test_effort_reduction_improves_score(self):
        easier = json.loads(json.dumps(self.item))
        easier["priority"]["effort"] = 1
        self.assertGreater(
            compute_score(easier, self.config),
            compute_score(self.item, self.config),
        )

    def test_invalid_score_is_rejected(self):
        invalid = json.loads(json.dumps(self.item))
        invalid["priority"]["impact"] = 6
        with self.assertRaises(FreezerError):
            validate_item(invalid, self.config)

    def test_invalid_enum_values_are_rejected(self):
        for field, value in (
            ("status", "DONE"),
            ("type", "idea"),
            ("build_authority", "MAYBE"),
            ("recall_mode", "AUTO"),
        ):
            invalid = json.loads(json.dumps(self.item))
            invalid[field] = value
            with self.subTest(field=field):
                with self.assertRaises(FreezerError):
                    validate_item(invalid, self.config)

    def test_rebuild_and_verify_in_isolated_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            rows = rebuild(temp_root)
            self.assertEqual(rows[0]["item_id"], "RTS-FRZ-000001")
            self.assertEqual(verify(temp_root), [])

    def test_partial_priority_revision_preserves_other_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            changes = temp_root / "changes.json"
            changes.write_text(
                json.dumps({"priority": {"urgency": 5}}),
                encoding="utf-8",
            )
            revised = revise_item(temp_root, "RTS-FRZ-000001", changes)
            self.assertEqual(revised["version"], 2)
            self.assertEqual(revised["priority"]["urgency"], 5)
            self.assertEqual(revised["priority"]["impact"], 5)
            self.assertEqual(verify(temp_root), [])

    def test_unapproved_item_cannot_be_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            changes = temp_root / "changes.json"
            changes.write_text(
                json.dumps({"status": "SELECTED"}),
                encoding="utf-8",
            )
            with self.assertRaises(FreezerError):
                revise_item(temp_root, "RTS-FRZ-000001", changes)

    def test_completed_items_leave_priority_queue(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            item_path = (
                temp_root
                / "freezer"
                / "items"
                / "RTS-FRZ-000001"
                / "v001.json"
            )
            item = json.loads(item_path.read_text(encoding="utf-8"))
            item["status"] = "COMPLETED"
            item_path.write_text(
                json.dumps(item, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            rows = rebuild(temp_root)
            self.assertEqual(rows, [])
            all_items = json.loads(
                (temp_root / "freezer" / "index" / "items.json").read_text(encoding="utf-8")
            )
            self.assertEqual(all_items["count"], 1)

    def test_work_in_progress_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            second = json.loads(json.dumps(self.item))
            second["item_id"] = "RTS-FRZ-000002"
            second["title"] = "Second active item"
            second["status"] = "IN_PROGRESS"
            second["build_authority"] = "APPROVED"
            source = temp_root / "second.json"
            source.write_text(
                json.dumps(second, ensure_ascii=False),
                encoding="utf-8",
            )
            add_item(temp_root, source)

            changes = temp_root / "changes.json"
            changes.write_text(
                json.dumps(
                    {
                        "status": "IN_PROGRESS",
                        "build_authority": "APPROVED",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(FreezerError):
                revise_item(temp_root, "RTS-FRZ-000001", changes)


if __name__ == "__main__":
    unittest.main()
