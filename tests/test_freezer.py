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
from freezer.preflight import (
    PreflightError,
    create_preflight,
    preflight_state,
    validate_preflight,
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

    def preflight_payload(
        self,
        *,
        outcome: str = "PASS",
        decomposition_required: bool = False,
    ) -> dict:
        return {
            "outcome": outcome,
            "assessor": "test-review",
            "rationale": "The affected ground was inspected before construction.",
            "affected_boundaries": ["core_logic", "tests"],
            "existing_assumptions": ["Existing item storage remains append-only."],
            "data_migration": {
                "required": False,
                "notes": "No migration is needed for this test.",
            },
            "external_interfaces": [],
            "approval_changes": ["Human approval remains mandatory."],
            "public_documents": [],
            "regression_tests": ["Run the FREEZER unit tests."],
            "hidden_dependencies": [],
            "rollback_boundary": "Return to the commit before this candidate is selected.",
            "completion_conditions": ["The bounded candidate passes its tests."],
            "decomposition": {
                "required": decomposition_required,
                "child_candidates": ["Child A", "Child B"] if decomposition_required else [],
            },
            "risks": ["A hidden dependency may invalidate the plan."],
        }

    def write_json(self, path: Path, payload: dict) -> Path:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def create_pass_preflight(self, root: Path, item_id: str) -> dict:
        source = self.write_json(root / "preflight.json", self.preflight_payload())
        return create_preflight(root, item_id, source)

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
            self.assertEqual(rows[0]["preflight_state"], "MISSING")
            self.assertEqual(verify(temp_root), [])

    def test_partial_priority_revision_preserves_other_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            changes = self.write_json(
                temp_root / "changes.json",
                {"priority": {"urgency": 5}},
            )
            revised = revise_item(temp_root, "RTS-FRZ-000001", changes)
            self.assertEqual(revised["version"], 2)
            self.assertEqual(revised["priority"]["urgency"], 5)
            self.assertEqual(revised["priority"]["impact"], 5)
            self.assertEqual(verify(temp_root), [])

    def test_unapproved_item_cannot_be_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            changes = self.write_json(
                temp_root / "changes.json",
                {"status": "SELECTED"},
            )
            with self.assertRaises(FreezerError):
                revise_item(temp_root, "RTS-FRZ-000001", changes)

    def test_approved_item_without_preflight_cannot_be_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            changes = self.write_json(
                temp_root / "changes.json",
                {"status": "SELECTED", "build_authority": "APPROVED"},
            )
            with self.assertRaisesRegex(FreezerError, "PASS preflight"):
                revise_item(temp_root, "RTS-FRZ-000001", changes)

    def test_passing_preflight_allows_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            self.create_pass_preflight(temp_root, "RTS-FRZ-000001")
            changes = self.write_json(
                temp_root / "changes.json",
                {"status": "SELECTED", "build_authority": "APPROVED"},
            )
            revised = revise_item(temp_root, "RTS-FRZ-000001", changes)
            self.assertEqual(revised["status"], "SELECTED")
            self.assertEqual(preflight_state(temp_root, revised)["state"], "PASS")
            self.assertEqual(verify(temp_root), [])

    def test_status_and_authority_changes_do_not_stale_preflight(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            self.create_pass_preflight(temp_root, "RTS-FRZ-000001")
            authority = self.write_json(
                temp_root / "authority.json",
                {"build_authority": "APPROVED"},
            )
            revised = revise_item(temp_root, "RTS-FRZ-000001", authority)
            self.assertEqual(preflight_state(temp_root, revised)["state"], "PASS")

    def test_substantive_revision_makes_preflight_stale(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            self.create_pass_preflight(temp_root, "RTS-FRZ-000001")
            plan_change = self.write_json(
                temp_root / "plan-change.json",
                {"priority": {"urgency": 5}},
            )
            revised = revise_item(temp_root, "RTS-FRZ-000001", plan_change)
            self.assertEqual(preflight_state(temp_root, revised)["state"], "STALE")

            select = self.write_json(
                temp_root / "select.json",
                {"status": "SELECTED", "build_authority": "APPROVED"},
            )
            with self.assertRaisesRegex(FreezerError, "state=STALE"):
                revise_item(temp_root, "RTS-FRZ-000001", select)

    def test_decomposition_required_preflight_blocks_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = self.isolated_root(temp_dir)
            source = self.write_json(
                temp_root / "preflight.json",
                self.preflight_payload(
                    outcome="DECOMPOSE_REQUIRED",
                    decomposition_required=True,
                ),
            )
            create_preflight(temp_root, "RTS-FRZ-000001", source)
            select = self.write_json(
                temp_root / "select.json",
                {"status": "SELECTED", "build_authority": "APPROVED"},
            )
            with self.assertRaisesRegex(FreezerError, "DECOMPOSE_REQUIRED"):
                revise_item(temp_root, "RTS-FRZ-000001", select)

    def test_invalid_pass_preflight_is_rejected(self):
        record = self.preflight_payload()
        record.update(
            {
                "preflight_id": "RTS-PF-000001-001",
                "item_id": "RTS-FRZ-000001",
                "preflight_version": 1,
                "item_version_snapshot": 1,
                "item_fingerprint": "0" * 64,
                "created_at": "2026-07-24T00:00:00Z",
            }
        )
        record["regression_tests"] = []
        with self.assertRaises(PreflightError):
            validate_preflight(record)

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
            second["status"] = "FROZEN"
            second["build_authority"] = "NOT_APPROVED"
            source = self.write_json(temp_root / "second.json", second)
            add_item(temp_root, source)

            self.create_pass_preflight(temp_root, "RTS-FRZ-000002")
            activate_second = self.write_json(
                temp_root / "activate-second.json",
                {"status": "IN_PROGRESS", "build_authority": "APPROVED"},
            )
            revise_item(temp_root, "RTS-FRZ-000002", activate_second)

            self.create_pass_preflight(temp_root, "RTS-FRZ-000001")
            activate_first = self.write_json(
                temp_root / "activate-first.json",
                {"status": "IN_PROGRESS", "build_authority": "APPROVED"},
            )
            with self.assertRaisesRegex(FreezerError, "work-in-progress limit"):
                revise_item(temp_root, "RTS-FRZ-000001", activate_first)


if __name__ == "__main__":
    unittest.main()
