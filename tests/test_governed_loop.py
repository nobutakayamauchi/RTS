from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from governed_loop.common import GovernedLoopError, sha256_value
from governed_loop.corpus import _verify_forbidden_imports, verify_all
from governed_loop.generation import generate_run, source_paths
from governed_loop.models import run_material, validate_record


class GovernedLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def resign(self, run: dict) -> None:
        run["run_fingerprint"] = sha256_value(run_material(run))
        run["run_id"] = f"RTS-LOOP-RUN-{run['run_fingerprint'][:16].upper()}"

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(generate_run(self.root), generate_run(self.root))

    def test_current_run_is_one_shot_read_only(self) -> None:
        run = generate_run(self.root)
        self.assertEqual(run["mode"], "ONE_SHOT_READ_ONLY")
        self.assertEqual(run["status"], "RECONSTRUCTED")
        loop = run["components"]["read_only_loop"]
        self.assertEqual(loop["active_item_ids"], ["RTS-FRZ-000010"])
        self.assertEqual(loop["wip_count"], 1)
        self.assertEqual(loop["state"], "FOCUS")
        self.assertEqual(loop["recommendation_action"], "CONTINUE_OR_VERIFY_ACTIVE_ITEM")
        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000010")
        ledger = run["components"]["human_review_ledger"]
        self.assertEqual(ledger["record_count"], 0)
        self.assertEqual(ledger["state"], "NO_DECISIONS")
        self.assertEqual(ledger["approval_status"], "NOT_APPROVED")
        self.assertEqual(ledger["application_status"], "NOT_APPLIED")
        self.assertTrue(run["authority"]["read_only"])
        for field in (
            "external_execution_performed",
            "scheduler_authorized",
            "provider_authorized",
            "adjacent_repository_write_authorized",
            "skill_mutation_authorized",
            "automatic_rollback_authorized",
        ):
            self.assertFalse(run["authority"][field])

    def test_source_files_remain_unchanged(self) -> None:
        before = {path: path.read_bytes() for path in source_paths(self.root)}
        generate_run(self.root)
        after = {path: path.read_bytes() for path in source_paths(self.root)}
        self.assertEqual(before, after)

    def test_fingerprint_mutation_is_rejected(self) -> None:
        run = generate_run(self.root)
        run["components"]["read_only_loop"]["state"] = "CHANGED"
        with self.assertRaisesRegex(GovernedLoopError, "fingerprint mismatch"):
            validate_record(run)

    def test_widened_authority_is_rejected_even_when_resigned(self) -> None:
        run = generate_run(self.root)
        run["authority"]["provider_authorized"] = True
        self.resign(run)
        with self.assertRaisesRegex(GovernedLoopError, "authority boundary widened"):
            validate_record(run)

    def test_private_content_is_rejected(self) -> None:
        run = generate_run(self.root)
        run["evidence_summary"]["assumptions"].append("credential: secret")
        self.resign(run)
        with self.assertRaisesRegex(GovernedLoopError, "forbidden private marker"):
            validate_record(run)

    def test_source_path_escape_is_rejected(self) -> None:
        run = generate_run(self.root)
        run["source_fingerprints"][0]["path"] = "../escape.json"
        self.resign(run)
        with self.assertRaisesRegex(GovernedLoopError, "unsafe source_fingerprints"):
            validate_record(run)

    def test_controller_outcome_link_mismatch_is_rejected(self) -> None:
        run = generate_run(self.root)
        run["components"]["execution_controller"]["outcome_links"][0][
            "bundle_fingerprint"
        ] = "0" * 64
        self.resign(run)
        with self.assertRaisesRegex(GovernedLoopError, "bundle linkage mismatch"):
            validate_record(run)

    def test_wip_count_mismatch_is_rejected(self) -> None:
        run = generate_run(self.root)
        run["components"]["read_only_loop"]["wip_count"] += 1
        self.resign(run)
        with self.assertRaisesRegex(GovernedLoopError, "wip_count does not match"):
            validate_record(run)

    def test_human_review_application_authority_cannot_widen(self) -> None:
        run = generate_run(self.root)
        run["components"]["human_review_ledger"]["application_status"] = "APPLIED"
        self.resign(run)
        with self.assertRaisesRegex(GovernedLoopError, "application authority widened"):
            validate_record(run)

    def test_proposal_remains_pending_and_not_applied(self) -> None:
        run = generate_run(self.root)
        proposal = run["components"]["learning_proposal"]
        self.assertEqual(proposal["proposal_status"], "REVIEW_REQUIRED")
        self.assertEqual(proposal["review_status"], "PENDING")
        self.assertEqual(proposal["approval_status"], "NOT_APPROVED")
        self.assertEqual(proposal["application_status"], "NOT_APPLIED")

    def test_schema_encodes_non_authorizing_constants(self) -> None:
        schema = json.loads(
            (self.root / "governed_loop/schemas/loop_run.schema.json").read_text(
                encoding="utf-8"
            )
        )
        authority = schema["properties"]["authority"]["properties"]
        self.assertEqual(authority["read_only"]["const"], True)
        self.assertEqual(authority["provider_authorized"]["const"], False)
        self.assertEqual(
            authority["adjacent_repository_write_authorized"]["const"], False
        )
        self.assertEqual(authority["approval_status"]["const"], "NOT_APPROVED")
        self.assertEqual(authority["application_status"]["const"], "NOT_APPLIED")

    def test_forbidden_external_action_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(self.root / "governed_loop", root / "governed_loop")
            (root / "governed_loop" / "unsafe.py").write_text(
                "import subprocess\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                GovernedLoopError, "forbidden external-action import"
            ):
                _verify_forbidden_imports(root)

    def test_committed_fixture_matches(self) -> None:
        path = self.root / "governed_loop" / "runs" / "current.json"
        committed = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(committed, generate_run(self.root))
        summary = verify_all(self.root)
        self.assertEqual(summary["run_id"], committed["run_id"])
        self.assertEqual(summary["approval_status"], "NOT_APPROVED")


if __name__ == "__main__":
    unittest.main()
