from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from loop_core.core import evaluate
from loop_core.models import (
    AUTHORITY,
    LoopCoreError,
    pretty_json,
    sha256_file,
    validate_evaluation,
)


class LoopCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in (
            "freezer/index/items.json",
            "freezer/index/build_priority.json",
            "asset_manifest/index/assets.json",
        ):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
        self.items = {
            "generated_at": "2026-07-24T01:00:00Z",
            "count": 3,
            "items": [
                {
                    "item_id": "RTS-FRZ-000005",
                    "version": 2,
                    "title": "Read-only",
                    "status": "FROZEN",
                    "build_authority": "NOT_APPROVED",
                    "preflight_state": "MISSING",
                },
                {
                    "item_id": "RTS-FRZ-000006",
                    "version": 2,
                    "title": "Controller",
                    "status": "FROZEN",
                    "build_authority": "NOT_APPROVED",
                    "preflight_state": "MISSING",
                },
                {
                    "item_id": "RTS-FRZ-000007",
                    "version": 2,
                    "title": "Learning",
                    "status": "FROZEN",
                    "build_authority": "NOT_APPROVED",
                    "preflight_state": "MISSING",
                },
            ],
        }
        self.build = {
            "generated_at": "2026-07-24T01:00:00Z",
            "count": 3,
            "policy": {},
            "items": [
                {
                    "item_id": "RTS-FRZ-000005",
                    "status": "FROZEN",
                    "recommendation": "ASSESSMENT_REQUIRED",
                    "build_authority": "NOT_APPROVED",
                    "ranking_score": 80.0,
                },
                {
                    "item_id": "RTS-FRZ-000006",
                    "status": "FROZEN",
                    "recommendation": "ASSESSMENT_REQUIRED",
                    "build_authority": "NOT_APPROVED",
                    "ranking_score": 70.0,
                },
                {
                    "item_id": "RTS-FRZ-000007",
                    "status": "FROZEN",
                    "recommendation": "ASSESSMENT_REQUIRED",
                    "build_authority": "NOT_APPROVED",
                    "ranking_score": 60.0,
                },
            ],
        }
        self.assets = {
            "generated_at": "2026-07-24T00:00:00Z",
            "count": 1,
            "assets": [{"asset_id": "RTS-AM-A0001"}],
        }
        self._write()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self) -> None:
        (self.root / "freezer/index/items.json").write_text(
            json.dumps(self.items), encoding="utf-8"
        )
        (self.root / "freezer/index/build_priority.json").write_text(
            json.dumps(self.build), encoding="utf-8"
        )
        (self.root / "asset_manifest/index/assets.json").write_text(
            json.dumps(self.assets), encoding="utf-8"
        )

    def test_deterministic_and_input_preserving(self) -> None:
        governed = [
            self.root / "freezer/index/items.json",
            self.root / "freezer/index/build_priority.json",
            self.root / "asset_manifest/index/assets.json",
        ]
        before = {path: sha256_file(path) for path in governed}
        first = evaluate(self.root)
        second = evaluate(self.root)
        self.assertEqual(pretty_json(first), pretty_json(second))
        self.assertEqual(before, {path: sha256_file(path) for path in governed})
        self.assertEqual(first["authority"], AUTHORITY)
        self.assertFalse(first["implementation_authority_granted"])
        validate_evaluation(first)

    def test_wip_overload_stops(self) -> None:
        self.items["items"][0]["status"] = "IN_PROGRESS"
        self.items["items"][1]["status"] = "SELECTED"
        self._write()
        result = evaluate(self.root)
        self.assertEqual(result["state"], "OVERLOAD")
        self.assertEqual(result["audit_level"], "CRITICAL")
        self.assertEqual(result["recommendation"]["action"], "REDUCE_WIP")

    def test_one_active_item_does_not_start_another(self) -> None:
        self.items["items"][1]["status"] = "IN_PROGRESS"
        self._write()
        result = evaluate(self.root)
        self.assertEqual(result["state"], "FOCUS")
        self.assertEqual(result["recommendation"]["item_id"], "RTS-FRZ-000006")
        self.assertEqual(
            result["recommendation"]["action"],
            "CONTINUE_OR_VERIFY_ACTIVE_ITEM",
        )

    def test_missing_assessment_is_recommended(self) -> None:
        result = evaluate(self.root)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(
            result["recommendation"]["action"],
            "RUN_BUILD_ASSESSMENT",
        )
        self.assertEqual(result["recommendation"]["item_id"], "RTS-FRZ-000005")

    def test_non_pass_preflight_blocks_selection(self) -> None:
        self.build["items"][0]["recommendation"] = "BUILD_NOW"
        self.build["items"][0]["build_authority"] = "APPROVED"
        self.items["items"][0]["build_authority"] = "APPROVED"
        self.items["items"][0]["preflight_state"] = "STALE"
        self._write()
        result = evaluate(self.root)
        self.assertEqual(
            result["recommendation"]["action"],
            "RUN_IMPLEMENTATION_PREFLIGHT",
        )
        self.assertNotEqual(
            result["recommendation"]["action"],
            "REVIEW_FOR_SELECTION",
        )

    def test_build_now_without_approval_requests_approval(self) -> None:
        self.build["items"][0]["recommendation"] = "BUILD_NOW"
        self.items["items"][0]["preflight_state"] = "PASS"
        self._write()
        result = evaluate(self.root)
        self.assertEqual(
            result["recommendation"]["action"],
            "REQUEST_HUMAN_APPROVAL",
        )

    def test_completed_items_are_skipped(self) -> None:
        self.items["items"][0]["status"] = "COMPLETED"
        self.build["items"][0]["status"] = "COMPLETED"
        self._write()
        result = evaluate(self.root)
        self.assertEqual(result["recommendation"]["item_id"], "RTS-FRZ-000006")

    def test_optional_records_are_unverified(self) -> None:
        execution = self.root / "execution.json"
        evidence = self.root / "evidence.json"
        execution.write_text(
            json.dumps(
                [
                    {
                        "skill_id": "s",
                        "drive_id": "d",
                        "pack_id": "p",
                        "trigger": "t",
                        "result": "r",
                        "timestamp": "z",
                    }
                ]
            ),
            encoding="utf-8",
        )
        evidence.write_text(
            json.dumps(
                [
                    {
                        "evidence_id": "e",
                        "source_type": "file",
                        "source_ref": "x",
                        "retrieved_at": "z",
                    }
                ]
            ),
            encoding="utf-8",
        )
        result = evaluate(
            self.root,
            execution_records_path=execution,
            evidence_refs_path=evidence,
        )
        self.assertEqual(len(result["evidence"]["unverified"]), 2)
        self.assertEqual(result["evidence"]["assumed"], [])

    def test_optional_record_shape_fails_closed(self) -> None:
        execution = self.root / "execution.json"
        execution.write_text(json.dumps([{"skill_id": "s"}]), encoding="utf-8")
        with self.assertRaises(LoopCoreError):
            evaluate(self.root, execution_records_path=execution)

    def test_malformed_governed_input_fails_closed(self) -> None:
        self.items["count"] = 99
        self._write()
        with self.assertRaisesRegex(LoopCoreError, "count mismatch"):
            evaluate(self.root)

    def test_output_validator_rejects_extra_fields(self) -> None:
        result = evaluate(self.root)
        result["unexpected"] = True
        with self.assertRaisesRegex(LoopCoreError, "unknown fields"):
            validate_evaluation(result)

    def test_future_children_remain_unapproved(self) -> None:
        result = evaluate(self.root)
        self.assertEqual(result["authority"], "ADVISORY_ONLY")
        for item in self.items["items"][1:]:
            self.assertEqual(item["build_authority"], "NOT_APPROVED")
            self.assertEqual(item["status"], "FROZEN")


if __name__ == "__main__":
    unittest.main()
