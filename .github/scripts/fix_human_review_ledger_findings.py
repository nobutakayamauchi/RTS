"""Apply and verify review fixes for Human Review Ledger v1.

Temporary candidate helper. Remove before merge.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one anchor in {path}, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_models() -> None:
    path = ROOT / "human_review_ledger/models.py"
    replace_once(
        path,
        'LEDGER_ID = "RTS-HUMAN-REVIEW-LEDGER-000001"\n',
        'LEDGER_ID = "RTS-HUMAN-REVIEW-LEDGER-000001"\n'
        'PROPOSER_IDENTITY = "rts-proposal-generator-v1"\n'
        'IMPLEMENTER_IDENTITY = "rts-implementation-agent-v1"\n',
    )
    replace_once(
        path,
        '        {"reviewer_must_differ_from_proposer", "reviewer_must_differ_from_implementer"},\n',
        '        {\n'
        '            "reviewer_must_differ_from_proposer",\n'
        '            "reviewer_must_differ_from_implementer",\n'
        '            "proposer_identity_source",\n'
        '            "implementer_identity",\n'
        '        },\n',
    )
    replace_once(
        path,
        '    if duties["reviewer_must_differ_from_proposer"] is not True or duties["reviewer_must_differ_from_implementer"] is not True:\n'
        '        raise HumanReviewLedgerError("policy separation-of-duties boundary widened")\n',
        '    if duties["reviewer_must_differ_from_proposer"] is not True or duties["reviewer_must_differ_from_implementer"] is not True:\n'
        '        raise HumanReviewLedgerError("policy separation-of-duties boundary widened")\n'
        '    if duties["proposer_identity_source"] != "learning_proposals/proposals/feature-build-v1.json#generator_identity":\n'
        '        raise HumanReviewLedgerError("policy proposer identity source mismatch")\n'
        '    if duties["implementer_identity"] != IMPLEMENTER_IDENTITY:\n'
        '        raise HumanReviewLedgerError("policy implementer identity mismatch")\n',
    )
    replace_once(
        path,
        '    allow_test_only: bool = False,\n) -> dict[str, Any]:\n',
        '    allow_test_only: bool = False,\n'
        '    expected_proposer_identity: str = PROPOSER_IDENTITY,\n'
        ') -> dict[str, Any]:\n',
    )
    replace_once(
        path,
        '    proposer = safe_id(duties["proposer_identity"], "proposer_identity")\n'
        '    implementer = safe_id(duties["implementer_identity"], "implementer_identity")\n'
        '    if duties["reviewer_differs_from_proposer"] is not True or identity == proposer:\n'
        '        raise HumanReviewLedgerError("reviewer must differ from proposer")\n'
        '    if duties["reviewer_differs_from_implementer"] is not True or identity == implementer:\n'
        '        raise HumanReviewLedgerError("reviewer must differ from implementer")\n',
        '    proposer = safe_id(duties["proposer_identity"], "proposer_identity")\n'
        '    implementer = safe_id(duties["implementer_identity"], "implementer_identity")\n'
        '    governed_proposer = safe_id(expected_proposer_identity, "expected_proposer_identity")\n'
        '    governed_implementer = safe_id(\n'
        '        policy["separation_of_duties"]["implementer_identity"],\n'
        '        "policy.separation_of_duties.implementer_identity",\n'
        '    )\n'
        '    if proposer != governed_proposer:\n'
        '        raise HumanReviewLedgerError("declared proposer identity does not match the governed proposal")\n'
        '    if implementer != governed_implementer:\n'
        '        raise HumanReviewLedgerError("declared implementer identity does not match the governed policy")\n'
        '    if duties["reviewer_differs_from_proposer"] is not True or identity == governed_proposer:\n'
        '        raise HumanReviewLedgerError("reviewer must differ from proposer")\n'
        '    if duties["reviewer_differs_from_implementer"] is not True or identity == governed_implementer:\n'
        '        raise HumanReviewLedgerError("reviewer must differ from implementer")\n',
    )


def patch_corpus() -> None:
    path = ROOT / "human_review_ledger/corpus.py"
    replace_once(
        path,
        'import ast\nfrom pathlib import Path\n',
        'import ast\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n',
    )
    replace_once(
        path,
        '    MANIFEST_SCHEMA,\n',
        '    IMPLEMENTER_IDENTITY,\n    MANIFEST_SCHEMA,\n    PROPOSER_IDENTITY,\n',
    )
    replace_once(
        path,
        '    if proposal_summary["proposal_fingerprint"] != proposal["proposal_fingerprint"]:\n'
        '        raise HumanReviewLedgerError("proposal verifier and committed proposal disagree")\n',
        '    if proposal_summary["proposal_fingerprint"] != proposal["proposal_fingerprint"]:\n'
        '        raise HumanReviewLedgerError("proposal verifier and committed proposal disagree")\n'
        '    if proposal.get("generator_identity") != PROPOSER_IDENTITY:\n'
        '        raise HumanReviewLedgerError("governed proposal generator identity mismatch")\n',
    )
    replace_once(
        path,
        '    manifest = validate_manifest(manifest_value)\n'
        '    records: list[dict[str, Any]] = []\n',
        '    manifest = validate_manifest(manifest_value)\n'
        '    decision_directory = root / DECISIONS_PREFIX\n'
        '    actual_paths = (\n'
        '        sorted(\n'
        '            path.relative_to(root).as_posix()\n'
        '            for path in decision_directory.glob("*.json")\n'
        '            if path.is_file()\n'
        '        )\n'
        '        if decision_directory.exists()\n'
        '        else []\n'
        '    )\n'
        '    manifest_paths = [row["path"] for row in manifest["records"]]\n'
        '    if actual_paths != manifest_paths:\n'
        '        missing = sorted(set(manifest_paths) - set(actual_paths))\n'
        '        extras = sorted(set(actual_paths) - set(manifest_paths))\n'
        '        raise HumanReviewLedgerError(\n'
        '            f"decision directory and manifest disagree; missing={missing}; unmanifested={extras}"\n'
        '        )\n'
        '    proposal = load_json(root / "learning_proposals/proposals/feature-build-v1.json")\n'
        '    if not isinstance(proposal, dict) or proposal.get("generator_identity") != PROPOSER_IDENTITY:\n'
        '        raise HumanReviewLedgerError("governed proposal generator identity mismatch")\n'
        '    expected_proposer_identity = proposal["generator_identity"]\n'
        '    if policy["separation_of_duties"]["implementer_identity"] != IMPLEMENTER_IDENTITY:\n'
        '        raise HumanReviewLedgerError("governed implementer identity mismatch")\n'
        '    records: list[dict[str, Any]] = []\n',
    )
    replace_once(
        path,
        '            allow_test_only=allow_test_only,\n        )\n',
        '            allow_test_only=allow_test_only,\n'
        '            expected_proposer_identity=expected_proposer_identity,\n'
        '        )\n',
    )
    replace_once(
        path,
        '        expired = current["decision_type"] == "EXPIRE"\n'
        '        if as_of is not None and current["expires_at"] is not None:\n'
        '            clock = optional_time(as_of, "as_of")\n'
        '            expiry = optional_time(current["expires_at"], "expires_at")\n'
        '            expired = bool(clock and expiry and clock >= expiry)\n',
        '        expired = current["decision_type"] == "EXPIRE"\n'
        '        clock = (\n'
        '            optional_time(as_of, "as_of")\n'
        '            if as_of is not None\n'
        '            else datetime.now(timezone.utc)\n'
        '        )\n'
        '        if current["expires_at"] is not None:\n'
        '            expiry = optional_time(current["expires_at"], "expires_at")\n'
        '            expired = expired or bool(clock and expiry and clock >= expiry)\n',
    )


def patch_policy_and_schema() -> None:
    policy_path = ROOT / "human_review_ledger/policy/v1.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    duties = policy["separation_of_duties"]
    duties["proposer_identity_source"] = "learning_proposals/proposals/feature-build-v1.json#generator_identity"
    duties["implementer_identity"] = "rts-implementation-agent-v1"
    policy["policy_fingerprint"] = ""
    policy["policy_fingerprint"] = sha256_value(
        {key: value for key, value in policy.items() if key != "policy_fingerprint"}
    )
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    schema_path = ROOT / "human_review_ledger/schemas/policy.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    separation = schema["properties"]["separation_of_duties"]
    separation["required"] = [
        "reviewer_must_differ_from_proposer",
        "reviewer_must_differ_from_implementer",
        "proposer_identity_source",
        "implementer_identity",
    ]
    separation["properties"]["proposer_identity_source"] = {
        "const": "learning_proposals/proposals/feature-build-v1.json#generator_identity"
    }
    separation["properties"]["implementer_identity"] = {
        "const": "rts-implementation-agent-v1"
    }
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    current_path = ROOT / "human_review_ledger/ledger/current.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    current["policy_fingerprint"] = policy["policy_fingerprint"]
    current["summary_fingerprint"] = ""
    current["summary_fingerprint"] = sha256_value(
        {key: value for key, value in current.items() if key != "summary_fingerprint"}
    )
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_tests() -> None:
    path = ROOT / "tests/test_human_review_ledger.py"
    insert = '''    def test_forged_proposer_field_cannot_bypass_independence(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(
                root,
                sequence=1,
                decision_type="REJECT",
                identity="rts-proposal-generator-v1",
            )
            record["separation_of_duties"]["proposer_identity"] = "someone-else"
            record["decision_fingerprint"] = sha256_value(
                fingerprint_material(record, "decision_fingerprint")
            )
            with self.assertRaisesRegex(HumanReviewLedgerError, "governed proposal"):
                validate_decision(
                    record,
                    policy=load_policy(root),
                    scope=load_scope(root),
                    allow_test_only=True,
                )

    def test_unmanifested_decision_file_is_rejected(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="REJECT")
            path = root / decision_path(record)
            write_json(path, record)
            with self.assertRaisesRegex(HumanReviewLedgerError, "unmanifested"):
                verify_all(root, allow_test_only=True)

    def test_normal_summary_expires_elapsed_approval(self) -> None:
        with self.copied_root() as temporary:
            root = Path(temporary)
            record = self.decision(root, sequence=1, decision_type="APPROVE")
            record["reviewed_at"] = "2025-01-01T00:00:00Z"
            record["expires_at"] = "2025-02-01T00:00:00Z"
            record["decision_fingerprint"] = sha256_value(
                fingerprint_material(record, "decision_fingerprint")
            )
            policy = load_policy(root)
            scope = load_scope(root)
            summary = summarize_records(
                [record],
                source_fingerprints=current_source_fingerprints(root, policy=policy, scope=scope),
                policy=policy,
                scope=scope,
            )
            self.assertEqual(summary["state"], "EXPIRED_DECISION")
            self.assertEqual(summary["approval_status"], "NOT_APPROVED")

'''
    replace_once(
        path,
        '    def test_schemas_encode_non_authorizing_constants(self) -> None:\n',
        insert + '    def test_schemas_encode_non_authorizing_constants(self) -> None:\n',
    )


def patch_readme() -> None:
    path = ROOT / "human_review_ledger/README.md"
    replace_once(
        path,
        "The reviewer must differ from both the proposal generator and the implementation identity, and the allowed reviewer role must exist in the current policy and reviewer-scope records.\n",
        "The reviewer must differ from both the generator identity read from the governed proposal and the implementation identity pinned by the current policy; self-asserted identities in a decision cannot replace those sources. The allowed reviewer role must exist in the current policy and reviewer-scope records.\n",
    )


def regenerate() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from governed_loop.common import pretty_json
    from governed_loop.generation import generate_run
    from human_review_ledger.corpus import verify_all

    summary = verify_all(ROOT)
    run = generate_run(ROOT)
    (ROOT / "governed_loop/runs/current.json").write_text(pretty_json(run), encoding="utf-8")
    print(summary["policy_fingerprint"], summary["summary_fingerprint"])
    print(run["run_id"], run["run_fingerprint"])


if __name__ == "__main__":
    patch_models()
    patch_corpus()
    patch_policy_and_schema()
    patch_tests()
    patch_readme()
    regenerate()
