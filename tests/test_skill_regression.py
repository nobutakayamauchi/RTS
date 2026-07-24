from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from skill_regression.corpus import artifact_paths, load_artifacts, verify_all
from skill_regression.models import (
    SkillRegressionError,
    evaluate_dataset,
    fingerprint_material,
    load_json,
    pretty_json,
    sha256_file,
    sha256_value,
)


class SkillRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        shutil.copytree(self.repo_root / "skill_regression", self.root / "skill_regression")
        shutil.copytree(
            self.repo_root / "outcome_evidence" / "examples",
            self.root / "outcome_evidence" / "examples",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_json(self, path: Path, value: object) -> None:
        path.write_text(pretty_json(value), encoding="utf-8")

    def refingerprint(self, value: dict, field: str) -> None:
        value[field] = sha256_value(fingerprint_material(value, field))

    def test_verify_committed_dataset(self) -> None:
        summary = verify_all(self.root)
        self.assertEqual(summary["recommendation"], "RESEARCH_READY")
        self.assertEqual(summary["promotion_eligibility"], "NOT_ELIGIBLE")
        self.assertEqual(summary["regressions"], 0)
        self.assertEqual(summary["improvements"], 2)
        self.assertEqual(summary["safety_failures"], 0)
        self.assertEqual(summary["candidate_pass_rate"], 1.0)

    def test_evaluation_is_deterministic(self) -> None:
        artifacts = load_artifacts(self.root)
        first = evaluate_dataset(artifacts["baseline"], artifacts["candidate"], artifacts["rollback"], artifacts["dataset"])
        second = evaluate_dataset(artifacts["baseline"], artifacts["candidate"], artifacts["rollback"], artifacts["dataset"])
        self.assertEqual(first, second)
        self.assertEqual(first, artifacts["result"])

    def test_baseline_content_mutation_is_rejected(self) -> None:
        path = self.root / "skill_regression/snapshots/feature-build/baseline.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
        with self.assertRaisesRegex(SkillRegressionError, "content digest mismatch"):
            verify_all(self.root)

    def test_candidate_contract_regression_is_rejected(self) -> None:
        path = artifact_paths(self.root)["candidate"]
        candidate = load_json(path)
        candidate["contract"]["ordered_steps"].remove("handoff-writer")
        self.refingerprint(candidate, "snapshot_fingerprint")
        self.write_json(path, candidate)
        with self.assertRaisesRegex(SkillRegressionError, "expected outcomes"):
            verify_all(self.root)

    def test_rollback_restore_digest_mismatch_is_rejected(self) -> None:
        path = artifact_paths(self.root)["rollback"]
        rollback = load_json(path)
        rollback["restore_content_sha256"] = "0" * 64
        self.refingerprint(rollback, "rollback_fingerprint")
        self.write_json(path, rollback)
        with self.assertRaisesRegex(SkillRegressionError, "rollback restore digest mismatch"):
            verify_all(self.root)

    def test_threshold_weakening_is_rejected(self) -> None:
        path = artifact_paths(self.root)["dataset"]
        dataset = load_json(path)
        dataset["thresholds"]["maximum_regressions"] = 1
        self.refingerprint(dataset, "dataset_fingerprint")
        self.write_json(path, dataset)
        with self.assertRaisesRegex(SkillRegressionError, "immutable v1 policy"):
            verify_all(self.root)

    def test_promotion_eligibility_cannot_be_enabled(self) -> None:
        path = artifact_paths(self.root)["candidate"]
        candidate = load_json(path)
        candidate["promotion_eligibility"] = "ELIGIBLE"
        self.refingerprint(candidate, "snapshot_fingerprint")
        self.write_json(path, candidate)
        with self.assertRaisesRegex(SkillRegressionError, "never promotion eligible"):
            verify_all(self.root)

    def test_external_mutation_claim_is_rejected(self) -> None:
        path = artifact_paths(self.root)["baseline"]
        baseline = load_json(path)
        baseline["external_mutation_performed"] = True
        self.refingerprint(baseline, "snapshot_fingerprint")
        self.write_json(path, baseline)
        with self.assertRaisesRegex(SkillRegressionError, "must not claim external mutation"):
            verify_all(self.root)

    def test_snapshot_path_escape_is_rejected(self) -> None:
        path = artifact_paths(self.root)["candidate"]
        candidate = load_json(path)
        candidate["content_path"] = "../candidate.md"
        candidate["source"]["path"] = "../candidate.md"
        self.refingerprint(candidate, "snapshot_fingerprint")
        self.write_json(path, candidate)
        with self.assertRaisesRegex(SkillRegressionError, "repository-relative|must stay inside"):
            verify_all(self.root)

    def test_duplicate_fixture_id_is_rejected(self) -> None:
        path = artifact_paths(self.root)["dataset"]
        dataset = load_json(path)
        dataset["fixture_set"][1]["fixture_id"] = dataset["fixture_set"][0]["fixture_id"]
        self.refingerprint(dataset, "dataset_fingerprint")
        self.write_json(path, dataset)
        with self.assertRaisesRegex(SkillRegressionError, "uniquely sorted"):
            verify_all(self.root)

    def test_result_mutation_is_rejected(self) -> None:
        path = artifact_paths(self.root)["result"]
        result = load_json(path)
        result["summary"]["improvements"] = 99
        self.write_json(path, result)
        with self.assertRaisesRegex(SkillRegressionError, "result fingerprint mismatch"):
            verify_all(self.root)

    def test_verify_is_read_only(self) -> None:
        before = {
            path.relative_to(self.root).as_posix(): sha256_file(path)
            for path in sorted((self.root / "skill_regression").rglob("*"))
            if path.is_file()
        }
        verify_all(self.root)
        after = {
            path.relative_to(self.root).as_posix(): sha256_file(path)
            for path in sorted((self.root / "skill_regression").rglob("*"))
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_source_content_digest_mismatch_is_rejected(self) -> None:
        path = artifact_paths(self.root)["baseline"]
        baseline = load_json(path)
        baseline["source"]["source_content_sha256"] = "f" * 64
        self.refingerprint(baseline, "snapshot_fingerprint")
        self.write_json(path, baseline)
        with self.assertRaisesRegex(SkillRegressionError, "source and snapshot content digests must match"):
            verify_all(self.root)

    def test_missing_referenced_outcome_bundle_is_rejected(self) -> None:
        path = self.root / "outcome_evidence/examples/success.json"
        path.unlink()
        with self.assertRaisesRegex(SkillRegressionError, "missing referenced outcome bundle"):
            verify_all(self.root)

    def test_dataset_with_private_field_fails_closed(self) -> None:
        path = artifact_paths(self.root)["dataset"]
        dataset = load_json(path)
        dataset["fixture_set"][0]["requirements"]["prompt"] = "forbidden"
        self.refingerprint(dataset, "dataset_fingerprint")
        self.write_json(path, dataset)
        with self.assertRaisesRegex(SkillRegressionError, "unknown fields|forbidden private field"):
            verify_all(self.root)


if __name__ == "__main__":
    unittest.main()
