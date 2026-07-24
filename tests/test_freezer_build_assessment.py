import json
import shutil
import tempfile
import unittest
from pathlib import Path

from freezer.build_assessment import (
    BuildAssessmentError,
    assessment_state,
    build_index_rows,
    create_assessment,
    derive,
    gate_payload,
    load_current_assessment,
    rebuild_index,
    validate_record,
    verify_assessments,
)


class BuildAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def isolated_root(self, temp_dir: str) -> Path:
        root = Path(temp_dir)
        shutil.copytree(self.repo_root / "freezer", root / "freezer")
        return root

    def write_json(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def payload(
        self,
        *,
        performed: bool = True,
        confidence: float = 5,
        asset_savings: float = 6,
    ) -> dict:
        repositories = ["owner/repo"] if performed else []
        queries = ["reuse schema test"] if performed else []
        assets = []
        if performed:
            assets.append(
                {
                    "repository": "owner/repo",
                    "path": "path/to/asset.py",
                    "ref": "main",
                    "kind": "code",
                    "reuse_mode": "ADAPT",
                    "license_status": "OWNED",
                    "estimated_hours_saved": asset_savings,
                    "notes": "Reusable validation and storage pattern.",
                }
            )
        return {
            "assessor": "test-review",
            "rationale": "The candidate was compared against repository evidence and implementation cost.",
            "expected_effect": {
                "impact": 5,
                "strategic_fit": 5,
                "revenue_leverage": 4,
                "risk_reduction": 5,
                "recurrence": 5,
                "confidence": confidence,
            },
            "implementation": {
                "from_scratch_hours": 10,
                "integration_hours": 1,
                "validation_hours": 1,
                "unknown_buffer_hours": 0,
            },
            "github_scan": {
                "performed": performed,
                "repositories": repositories,
                "queries": queries,
                "assets": assets,
                "gaps": ["Search coverage is not guaranteed."],
            },
            "risks": ["Reuse may hide integration work."],
        }

    def current_item_path(self, root: Path, item_id: str) -> Path:
        pointer = json.loads(
            (root / "freezer" / "items" / item_id / "current.json").read_text(
                encoding="utf-8"
            )
        )
        return root / pointer["path"]

    def mutate_current_item(self, root: Path, item_id: str, changes: dict) -> dict:
        path = self.current_item_path(root, item_id)
        item = json.loads(path.read_text(encoding="utf-8"))
        item.update(changes)
        path.write_text(
            json.dumps(item, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return item

    def test_seed_assessment_is_valid_and_build_now(self):
        record = json.loads(
            (
                self.repo_root
                / "freezer"
                / "assessments"
                / "RTS-FRZ-000002"
                / "ba001.json"
            ).read_text(encoding="utf-8")
        )
        validate_record(record)
        self.assertEqual(record["derived"]["recommendation"], "BUILD_NOW")
        self.assertEqual(record["derived"]["decision_score"], 75.37)
        self.assertEqual(record["derived"]["reuse_hours_saved"], 10.0)
        self.assertEqual(record["derived"]["net_hours"], 10.0)

    def test_derive_is_deterministic(self):
        result = derive(self.payload())
        self.assertEqual(result, derive(self.payload()))
        self.assertEqual(result["recommendation"], "BUILD_NOW")

    def test_more_reuse_improves_decision_score_and_net_hours(self):
        low = derive(self.payload(asset_savings=1))
        high = derive(self.payload(asset_savings=7))
        self.assertGreater(high["decision_score"], low["decision_score"])
        self.assertLess(high["net_hours"], low["net_hours"])
        self.assertGreater(high["implementation_efficiency"], low["implementation_efficiency"])

    def test_missing_github_scan_requires_research(self):
        result = derive(self.payload(performed=False))
        self.assertEqual(result["recommendation"], "RESEARCH_REQUIRED")

    def test_low_confidence_requires_research(self):
        result = derive(self.payload(confidence=1))
        self.assertEqual(result["recommendation"], "RESEARCH_REQUIRED")

    def test_unknown_input_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            payload = self.payload()
            payload["surprise"] = "not allowed"
            source = self.write_json(root / "assessment.json", payload)
            with self.assertRaisesRegex(BuildAssessmentError, "unknown fields"):
                create_assessment(root, "RTS-FRZ-000001", source)

    def test_append_only_assessment_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            first = create_assessment(
                root,
                "RTS-FRZ-000001",
                self.write_json(root / "a1.json", self.payload()),
            )
            second_payload = self.payload(asset_savings=5)
            second = create_assessment(
                root,
                "RTS-FRZ-000001",
                self.write_json(root / "a2.json", second_payload),
            )
            self.assertEqual(first["assessment_version"], 1)
            self.assertEqual(second["assessment_version"], 2)
            self.assertTrue(
                root.joinpath(
                    "freezer", "assessments", "RTS-FRZ-000001", "ba001.json"
                ).exists()
            )
            self.assertEqual(
                load_current_assessment(root, "RTS-FRZ-000001")["assessment_version"],
                2,
            )

    def test_priority_change_does_not_stale_assessment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            create_assessment(
                root,
                "RTS-FRZ-000001",
                self.write_json(root / "assessment.json", self.payload()),
            )
            item = self.mutate_current_item(
                root,
                "RTS-FRZ-000001",
                {
                    "priority": {
                        "impact": 5,
                        "urgency": 5,
                        "strategic_fit": 5,
                        "readiness": 3,
                        "revenue_value": 4,
                        "dependency_value": 4,
                        "risk_reduction": 4,
                        "confidence": 4,
                        "effort": 3,
                        "uncertainty": 2,
                    }
                },
            )
            self.assertEqual(assessment_state(root, item)["state"], "CURRENT")

    def test_substantive_change_stales_assessment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            create_assessment(
                root,
                "RTS-FRZ-000001",
                self.write_json(root / "assessment.json", self.payload()),
            )
            item = self.mutate_current_item(
                root,
                "RTS-FRZ-000001",
                {"summary": "The implementation plan materially changed."},
            )
            self.assertEqual(assessment_state(root, item)["state"], "STALE")

    def test_tampered_derived_values_are_rejected(self):
        record = json.loads(
            (
                self.repo_root
                / "freezer"
                / "assessments"
                / "RTS-FRZ-000002"
                / "ba001.json"
            ).read_text(encoding="utf-8")
        )
        record["derived"]["decision_score"] += 1
        with self.assertRaisesRegex(BuildAssessmentError, "do not match inputs"):
            validate_record(record)

    def test_build_index_penalizes_missing_assessment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            rows = build_index_rows(root)
            row = next(row for row in rows if row["item_id"] == "RTS-FRZ-000001")
            self.assertEqual(row["assessment_state"], "MISSING")
            self.assertEqual(row["recommendation"], "ASSESSMENT_REQUIRED")
            self.assertEqual(row["ranking_score"], 22.84)

    def test_current_assessment_contributes_to_combined_ranking(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            create_assessment(
                root,
                "RTS-FRZ-000001",
                self.write_json(root / "assessment.json", self.payload()),
            )
            rows = build_index_rows(root)
            row = next(row for row in rows if row["item_id"] == "RTS-FRZ-000001")
            self.assertEqual(row["assessment_state"], "CURRENT")
            self.assertIsNotNone(row["build_score"])
            self.assertGreater(row["ranking_score"], 22.84)

    def test_active_item_without_assessment_fails_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            self.mutate_current_item(
                root,
                "RTS-FRZ-000001",
                {"status": "SELECTED", "build_authority": "APPROVED"},
            )
            rebuild_index(root)
            errors = verify_assessments(root)
            self.assertTrue(any("current build assessment" in error for error in errors))

    def test_active_item_with_build_now_assessment_passes_assessment_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            create_assessment(
                root,
                "RTS-FRZ-000001",
                self.write_json(root / "assessment.json", self.payload()),
            )
            self.mutate_current_item(
                root,
                "RTS-FRZ-000001",
                {"status": "SELECTED", "build_authority": "APPROVED"},
            )
            rebuild_index(root)
            errors = verify_assessments(root)
            self.assertEqual(errors, [])

    def test_stale_build_index_is_detected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            index = root / "freezer" / "index" / "build_priority.json"
            payload = json.loads(index.read_text(encoding="utf-8"))
            payload["items"][0]["ranking_score"] = 99
            self.write_json(index, payload)
            errors = verify_assessments(root)
            self.assertTrue(any("stale build priority index" in error for error in errors))

    def test_full_gate_is_true_for_ready_seed_when_status_is_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.isolated_root(temp_dir)
            self.mutate_current_item(root, "RTS-FRZ-000002", {"status": "READY"})
            rebuild_index(root)
            payload = gate_payload(root, "RTS-FRZ-000002")
            self.assertEqual(payload["assessment_state"], "CURRENT")
            self.assertEqual(payload["recommendation"], "BUILD_NOW")
            self.assertEqual(payload["preflight_state"], "PASS")
            self.assertTrue(payload["selection_ready"])


if __name__ == "__main__":
    unittest.main()
