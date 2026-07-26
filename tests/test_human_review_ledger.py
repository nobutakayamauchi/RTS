from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from human_review_ledger.cli import build_parser
from human_review_ledger.common import HumanReviewLedgerError, fingerprint_material, sha256_value, write_json
from human_review_ledger.corpus import (
    CURRENT_PATH,
    MANIFEST_PATH,
    current_source_fingerprints,
    decision_path,
    load_policy,
    load_scope,
    manifest_for_records,
    summarize_records,
    tracked_paths,
    verify_all,
)
from human_review_ledger.models import DECISION_SCHEMA, LEDGER_ID, validate_decision


class HumanReviewLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def copied_root(self) -> tempfile.TemporaryDirectory:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for name in (
            "human_review_ledger",
            "learning_proposals",
            "outcome_evidence",
            "skill_regression",
        ):
            shutil.copytree(self.root / name, root / name)
        temporary.root = root  # type: ignore[attr-defined]
        return temporary

    def decision(
        self,
        root: Path,
        *,
        sequence: int,
        decision_type: str,
        previous: str | None = None,
        source_override: dict[str, str] | None = None,
        identity: str = "human-reviewer-001",
    ) -> dict:
        policy = load_policy(root)
        scope = load_scope(root)
        sources = current_source_fingerprints(root, policy=policy, scope=scope)
        if source_override:
            sources.update(source_override)
        record = {
            "schema_version": DECISION_SCHEMA,
            "decision_id": f"RTS-HRL-DECISION-{sequence:06d}",
            "ledger_id": LEDGER_ID,
            "sequence": sequence,
            "previous_decision_fingerprint": previous,
            "decision_type": decision_type,
            "authored_by": {
                "type": "HUMAN",
                "identity": identity,
                "identity_source": "operator-attested-reviewer-directory",
                "role": "INDEPENDENT_REVIEWER",
            },
            "separation_of_duties": {
                "proposer_identity": "rts-proposal-generator-v1",
                "implementer_identity": "rts-implementation-agent-v1",
                "reviewer_differs_from_proposer": True,
                "reviewer_differs_from_implementer": True,
            },
            "reviewed_at": f"2026-08-{sequence:02d}T00:00:00Z",
            "expires_at": "2027-08-01T00:00:00Z" if decision_type == "APPROVE" else None,
            "rationale": f"TEST_ONLY deterministic {decision_type} fixture.",
            "conditions": ["retain-non-application-boundary"] if decision_type == "APPROVE" else [],
            "source_fingerprints": sources,
            "supersedes_decision_fingerprint": previous if decision_type in {"EXPIRE", "SUPERSEDE"} else None,
            "authority": {
                "approval_status": "APPROVED" if decision_type == "APPROVE" else "NOT_APPROVED",
                "application_status": "NOT_APPLIED",
                "skill_mutation_authorized": False,
                "adjacent_repository_write_authorized": False,
                "merge_authorized": False,
                "external_action_authorized": False,
            },
            "test_only": True,
            "decision_fingerprint": "",
        }
        record["decision_fingerprint"] = sha256_value(fingerprint_material(record, "decision_fingerprint"))
        return record

    def commit(self, root: Path, records: list[dict]) -> dict:
        for record in records:
            write_json(root / decision_path(record), record)
        manifest = manifest_for_records(root, records)
        write_json(root / MANIFEST_PATH, manifest)
        policy = load_policy(root)
        scope = load_scope(root)
        summary = summarize_records(
            records,
            source_fingerprints=current_source_fingerprints(root, policy=policy, scope=scope),
            policy=policy,
            scope=scope,
        )
        write_json(root / CURRENT_PATH, summary)
        return summary

    def test_committed_empty_ledger_verifies(self) -> None:
        summary = verify_all(self.root)
        self.assertEqual(summary["record_count"], 0)
        self.assertEqual(summary["state"], "NO_DECISIONS")
        self.assertEqual(summary["approval_status"], "NOT_APPROVED")
        self.assertEqual(summary["application_status"], "NOT_APPLIED")

    def test_all_decision_types_validate_in_test_only_copies(self) -> None:
        for decision_type in ("APPROVE", "REJECT", "RETURN_FOR_REVISION"):
            with self.subTest(decision_type=decision_type), self.copied_root() as temporary:
                root = Path(temporary)
                record = self.decision(root, sequence=1, decision_type=decision_type)
                self.commit(root, [record])
                result = verify_all(root, allow_test_only=True)
                self.assertEqual(result["current_decision_type"], decision_type)
                self.assertEqual(result["application_status"], "NOT_APPLIED")
        for decision_type in ("EXPIRE", "SUPERSEDE"):
            with self.subTest(decision_type=decision_type), self.copied_root() as temporary:
                root = Path(temporary)
                first = self.decision(root, sequence=1, decision_type="APPROVE")
                second = self.decision(
                    root,
                    sequence=2,
                    decision_type=decision_type,
                    previous=first["decision_fingerprint"],
                )
                self.commit(root, [first, second])
                result = verify_all(root, allow_test_only=True)
                self.assertEqual(result["current_decision_type"], decision_type)
                self.assertEqual(result["approval_status"], "NOT_APPROVED")

    def test_committed_verifier_rejects_test_only_decision(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="REJECT")
            self.commit(root, [record])
            with self.assertRaisesRegex(HumanReviewLedgerError, "TEST_ONLY"):
                verify_all(root)

    def test_self_review_is_rejected(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(
                root,
                sequence=1,
                decision_type="REJECT",
                identity="rts-proposal-generator-v1",
            )
            policy = load_policy(root)
            scope = load_scope(root)
            with self.assertRaisesRegex(HumanReviewLedgerError, "reviewer must differ from proposer"):
                validate_decision(record, policy=policy, scope=scope, allow_test_only=True)

    def test_widened_authority_is_rejected_even_when_resigned(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="REJECT")
            record["authority"]["merge_authorized"] = True
            record["decision_fingerprint"] = sha256_value(fingerprint_material(record, "decision_fingerprint"))
            with self.assertRaisesRegex(HumanReviewLedgerError, "authority boundary widened"):
                validate_decision(
                    record,
                    policy=load_policy(root),
                    scope=load_scope(root),
                    allow_test_only=True,
                )

    def test_chain_discontinuity_is_rejected(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            first = self.decision(root, sequence=1, decision_type="REJECT")
            second = self.decision(root, sequence=2, decision_type="REJECT", previous="0" * 64)
            self.commit(root, [first, second])
            with self.assertRaisesRegex(HumanReviewLedgerError, "chain is discontinuous"):
                verify_all(root, allow_test_only=True)

    def test_decision_file_deletion_is_rejected(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="REJECT")
            self.commit(root, [record])
            (root / decision_path(record)).unlink()
            with self.assertRaisesRegex(HumanReviewLedgerError, "missing file"):
                verify_all(root, allow_test_only=True)

    def test_manifest_path_escape_is_rejected(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="REJECT")
            self.commit(root, [record])
            manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
            manifest["records"][0]["path"] = "../escape.json"
            manifest["manifest_fingerprint"] = sha256_value(fingerprint_material(manifest, "manifest_fingerprint"))
            write_json(root / MANIFEST_PATH, manifest)
            with self.assertRaisesRegex(HumanReviewLedgerError, "path boundary"):
                verify_all(root, allow_test_only=True)

    def test_stale_source_invalidates_approval(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(
                root,
                sequence=1,
                decision_type="APPROVE",
                source_override={"proposal": "0" * 64},
            )
            summary = self.commit(root, [record])
            self.assertEqual(summary["state"], "STALE_DECISION")
            self.assertEqual(summary["approval_status"], "NOT_APPROVED")
            result = verify_all(root, allow_test_only=True)
            self.assertTrue(result["stale"])

    def test_elapsed_expiry_invalidates_approval(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="APPROVE")
            policy = load_policy(root)
            scope = load_scope(root)
            summary = summarize_records(
                [record],
                source_fingerprints=current_source_fingerprints(root, policy=policy, scope=scope),
                policy=policy,
                scope=scope,
                as_of="2028-01-01T00:00:00Z",
            )
            self.assertEqual(summary["state"], "EXPIRED_DECISION")
            self.assertEqual(summary["approval_status"], "NOT_APPROVED")

    def test_private_marker_is_rejected(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="REJECT")
            record["rationale"] = "credential: should never be stored"
            record["decision_fingerprint"] = sha256_value(fingerprint_material(record, "decision_fingerprint"))
            with self.assertRaisesRegex(HumanReviewLedgerError, "forbidden private marker"):
                validate_decision(
                    record,
                    policy=load_policy(root),
                    scope=load_scope(root),
                    allow_test_only=True,
                )

    def test_cli_has_no_create_or_apply_command(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("verify", help_text)
        self.assertIn("summary", help_text)
        self.assertIn("blank-template", help_text)
        self.assertNotIn("apply", help_text)
        self.assertNotIn("approve", help_text)

    def test_schemas_encode_non_authorizing_constants(self) -> None:
        policy_schema = json.loads(
            (self.root / "human_review_ledger/schemas/policy.schema.json").read_text(encoding="utf-8")
        )
        decision_schema = json.loads(
            (self.root / "human_review_ledger/schemas/decision.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(policy_schema["additionalProperties"])
        self.assertEqual(
            policy_schema["properties"]["authority"]["properties"]["application_status"]["const"],
            "NOT_APPLIED",
        )
        authority = decision_schema["properties"]["authority"]["properties"]
        self.assertEqual(authority["skill_mutation_authorized"]["const"], False)
        self.assertEqual(authority["adjacent_repository_write_authorized"]["const"], False)
        self.assertEqual(authority["merge_authorized"]["const"], False)
        self.assertEqual(authority["external_action_authorized"]["const"], False)

    def test_verify_is_read_only(self) -> None:
        manifest = json.loads((self.root / MANIFEST_PATH).read_text(encoding="utf-8"))
        before = {path: path.read_bytes() for path in tracked_paths(self.root, manifest)}
        verify_all(self.root)
        after = {path: path.read_bytes() for path in tracked_paths(self.root, manifest)}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
