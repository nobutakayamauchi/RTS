from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from learning_proposals.corpus import verify_all as verify_learning_proposals
from outcome_evidence.corpus import load_corpus
from skill_regression.corpus import verify_all as verify_skill_regression

from .common import (
    HumanReviewLedgerError,
    ensure_inside,
    load_json,
    optional_time,
    pretty_json,
    sha256_file,
    sha256_value,
)
from .models import (
    DECISION_SCHEMA,
    LEDGER_ID,
    IMPLEMENTER_IDENTITY,
    MANIFEST_SCHEMA,
    PROPOSER_IDENTITY,
    POLICY_SCHEMA,
    SCOPE_SCHEMA,
    SUMMARY_SCHEMA,
    validate_decision,
    validate_manifest,
    validate_policy,
    validate_scope,
    validate_summary,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent
POLICY_PATH = "human_review_ledger/policy/v1.json"
SCOPE_PATH = "human_review_ledger/reviewer_scopes/default.json"
MANIFEST_PATH = "human_review_ledger/ledger/manifest.json"
CURRENT_PATH = "human_review_ledger/ledger/current.json"
DECISIONS_PREFIX = "human_review_ledger/ledger/decisions/"
SCHEMA_PATHS = {
    "human_review_ledger/schemas/policy.schema.json": POLICY_SCHEMA,
    "human_review_ledger/schemas/reviewer_scope.schema.json": SCOPE_SCHEMA,
    "human_review_ledger/schemas/decision.schema.json": DECISION_SCHEMA,
    "human_review_ledger/schemas/manifest.schema.json": MANIFEST_SCHEMA,
    "human_review_ledger/schemas/current_summary.schema.json": SUMMARY_SCHEMA,
}
FORBIDDEN_IMPORTS = {"subprocess", "socket", "requests", "urllib", "http", "ftplib"}


def _verify_forbidden_imports(root: Path) -> None:
    package = root / "human_review_ledger"
    for path in sorted(package.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            raise HumanReviewLedgerError(f"invalid Python syntax: {path}: {exc}") from exc
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for name in names:
                if name.split(".", 1)[0] in FORBIDDEN_IMPORTS:
                    raise HumanReviewLedgerError(f"forbidden external-action import in {path}: {name}")


def _verify_schema_ids(root: Path) -> None:
    for relative, expected in SCHEMA_PATHS.items():
        schema = load_json(root / relative)
        if not isinstance(schema, dict) or schema.get("$id") != expected:
            raise HumanReviewLedgerError(f"schema identifier mismatch: {relative}")
        if schema.get("additionalProperties") is not False:
            raise HumanReviewLedgerError(f"schema must fail closed: {relative}")


def load_policy(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    value = load_json(root / POLICY_PATH)
    if not isinstance(value, dict):
        raise HumanReviewLedgerError("policy must be an object")
    return validate_policy(value)


def load_scope(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    value = load_json(root / SCOPE_PATH)
    if not isinstance(value, dict):
        raise HumanReviewLedgerError("reviewer scope must be an object")
    return validate_scope(value)


def current_source_fingerprints(
    root: Path = DEFAULT_ROOT,
    *,
    policy: dict[str, Any] | None = None,
    scope: dict[str, Any] | None = None,
) -> dict[str, str]:
    root = root.resolve()
    policy = policy or load_policy(root)
    scope = scope or load_scope(root)
    proposal_summary = verify_learning_proposals(root)
    proposal = load_json(root / "learning_proposals/proposals/feature-build-v1.json")
    pending = load_json(root / "learning_proposals/reviews/feature-build-v1.pending.json")
    bundles = load_corpus(root)
    regression = verify_skill_regression(root)
    rollback = load_json(root / "skill_regression/rollback/feature-build-v1.json")
    if proposal_summary["proposal_fingerprint"] != proposal["proposal_fingerprint"]:
        raise HumanReviewLedgerError("proposal verifier and committed proposal disagree")
    if proposal.get("generator_identity") != PROPOSER_IDENTITY:
        raise HumanReviewLedgerError("governed proposal generator identity mismatch")
    outcome_material = [
        {"bundle_id": bundle["bundle_id"], "bundle_fingerprint": bundle["bundle_fingerprint"]}
        for bundle in sorted(bundles, key=lambda row: row["bundle_id"])
    ]
    return {
        "proposal": proposal["proposal_fingerprint"],
        "pending_review": pending["decision_fingerprint"],
        "outcome_evidence": sha256_value(outcome_material),
        "regression_result": regression["result_fingerprint"],
        "rollback": rollback["rollback_fingerprint"],
        "policy": policy["policy_fingerprint"],
        "reviewer_scope": scope["scope_fingerprint"],
    }


def decision_path(record: dict[str, Any]) -> str:
    return f"{DECISIONS_PREFIX}{record['sequence']:06d}-{record['decision_id']}.json"


def manifest_for_records(root: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for record in records:
        relative = decision_path(record)
        path = root / relative
        rows.append(
            {
                "sequence": record["sequence"],
                "path": relative,
                "file_sha256": sha256_file(path),
                "decision_id": record["decision_id"],
                "decision_fingerprint": record["decision_fingerprint"],
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "ledger_id": LEDGER_ID,
        "record_count": len(rows),
        "records": rows,
        "head_fingerprint": rows[-1]["decision_fingerprint"] if rows else None,
        "manifest_fingerprint": "",
    }
    manifest["manifest_fingerprint"] = sha256_value(
        {key: value for key, value in manifest.items() if key != "manifest_fingerprint"}
    )
    return validate_manifest(manifest)


def load_records(
    root: Path,
    *,
    policy: dict[str, Any],
    scope: dict[str, Any],
    allow_test_only: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_value = load_json(root / MANIFEST_PATH)
    if not isinstance(manifest_value, dict):
        raise HumanReviewLedgerError("ledger manifest must be an object")
    manifest = validate_manifest(manifest_value)
    decision_directory = root / DECISIONS_PREFIX
    actual_paths = (
        sorted(
            path.relative_to(root).as_posix()
            for path in decision_directory.glob("*.json")
            if path.is_file()
        )
        if decision_directory.exists()
        else []
    )
    manifest_paths = [row["path"] for row in manifest["records"]]
    if actual_paths != manifest_paths:
        missing = sorted(set(manifest_paths) - set(actual_paths))
        extras = sorted(set(actual_paths) - set(manifest_paths))
        raise HumanReviewLedgerError(
            f"decision directory and manifest disagree; missing={missing}; unmanifested={extras}"
        )
    proposal = load_json(root / "learning_proposals/proposals/feature-build-v1.json")
    if not isinstance(proposal, dict) or proposal.get("generator_identity") != PROPOSER_IDENTITY:
        raise HumanReviewLedgerError("governed proposal generator identity mismatch")
    expected_proposer_identity = proposal["generator_identity"]
    if policy["separation_of_duties"]["implementer_identity"] != IMPLEMENTER_IDENTITY:
        raise HumanReviewLedgerError("governed implementer identity mismatch")
    records: list[dict[str, Any]] = []
    prior_fingerprint: str | None = None
    decision_ids: set[str] = set()
    for row in manifest["records"]:
        path = ensure_inside(root, root / row["path"])
        if sha256_file(path) != row["file_sha256"]:
            raise HumanReviewLedgerError(f"decision file digest mismatch: {row['path']}")
        value = load_json(path)
        if not isinstance(value, dict):
            raise HumanReviewLedgerError(f"decision must be an object: {row['path']}")
        decision = validate_decision(
            value,
            policy=policy,
            scope=scope,
            allow_test_only=allow_test_only,
            expected_proposer_identity=expected_proposer_identity,
        )
        if decision["sequence"] != row["sequence"]:
            raise HumanReviewLedgerError("manifest and decision sequence disagree")
        if decision["decision_id"] != row["decision_id"]:
            raise HumanReviewLedgerError("manifest and decision identifier disagree")
        if decision["decision_fingerprint"] != row["decision_fingerprint"]:
            raise HumanReviewLedgerError("manifest and decision fingerprint disagree")
        if decision["decision_id"] in decision_ids:
            raise HumanReviewLedgerError("duplicate decision_id")
        if decision["previous_decision_fingerprint"] != prior_fingerprint:
            raise HumanReviewLedgerError("decision chain is discontinuous")
        decision_ids.add(decision["decision_id"])
        prior_fingerprint = decision["decision_fingerprint"]
        records.append(decision)
    return manifest, records


def summarize_records(
    records: list[dict[str, Any]],
    *,
    source_fingerprints: dict[str, str],
    policy: dict[str, Any],
    scope: dict[str, Any],
    as_of: str | None = None,
) -> dict[str, Any]:
    if not records:
        summary: dict[str, Any] = {
            "schema_version": SUMMARY_SCHEMA,
            "ledger_id": LEDGER_ID,
            "state": "NO_DECISIONS",
            "record_count": 0,
            "current_decision_id": None,
            "current_decision_type": None,
            "current_decision_fingerprint": None,
            "current_sequence": 0,
            "approval_status": "NOT_APPROVED",
            "application_status": "NOT_APPLIED",
            "stale": False,
            "expired": False,
            "policy_fingerprint": policy["policy_fingerprint"],
            "reviewer_scope_fingerprint": scope["scope_fingerprint"],
            "summary_fingerprint": "",
        }
    else:
        current = records[-1]
        stale = current["source_fingerprints"] != source_fingerprints
        expired = current["decision_type"] == "EXPIRE"
        clock = (
            optional_time(as_of, "as_of")
            if as_of is not None
            else datetime.now(timezone.utc)
        )
        if current["expires_at"] is not None:
            expiry = optional_time(current["expires_at"], "expires_at")
            expired = expired or bool(clock and expiry and clock >= expiry)
        approval = (
            "APPROVED"
            if current["decision_type"] == "APPROVE" and not stale and not expired
            else "NOT_APPROVED"
        )
        summary = {
            "schema_version": SUMMARY_SCHEMA,
            "ledger_id": LEDGER_ID,
            "state": "STALE_DECISION" if stale else "EXPIRED_DECISION" if expired else "CURRENT_DECISION",
            "record_count": len(records),
            "current_decision_id": current["decision_id"],
            "current_decision_type": current["decision_type"],
            "current_decision_fingerprint": current["decision_fingerprint"],
            "current_sequence": current["sequence"],
            "approval_status": approval,
            "application_status": "NOT_APPLIED",
            "stale": stale,
            "expired": expired,
            "policy_fingerprint": policy["policy_fingerprint"],
            "reviewer_scope_fingerprint": scope["scope_fingerprint"],
            "summary_fingerprint": "",
        }
    summary["summary_fingerprint"] = sha256_value(
        {key: value for key, value in summary.items() if key != "summary_fingerprint"}
    )
    return validate_summary(summary)


def tracked_paths(root: Path, manifest: dict[str, Any] | None = None) -> list[Path]:
    paths = [
        root / POLICY_PATH,
        root / SCOPE_PATH,
        root / MANIFEST_PATH,
        root / CURRENT_PATH,
        root / "human_review_ledger/templates/decision.blank.json",
        root / "human_review_ledger/README.md",
        *[root / relative for relative in SCHEMA_PATHS],
    ]
    if manifest is not None:
        paths.extend(ensure_inside(root, root / row["path"]) for row in manifest["records"])
    return sorted(set(paths), key=lambda path: path.relative_to(root).as_posix())


def summarize(
    root: Path = DEFAULT_ROOT,
    *,
    as_of: str | None = None,
    allow_test_only: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    policy = load_policy(root)
    scope = load_scope(root)
    sources = current_source_fingerprints(root, policy=policy, scope=scope)
    _, records = load_records(
        root,
        policy=policy,
        scope=scope,
        allow_test_only=allow_test_only,
    )
    return summarize_records(
        records,
        source_fingerprints=sources,
        policy=policy,
        scope=scope,
        as_of=as_of,
    )


def verify_all(
    root: Path = DEFAULT_ROOT,
    *,
    allow_test_only: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    _verify_forbidden_imports(root)
    _verify_schema_ids(root)
    policy = load_policy(root)
    scope = load_scope(root)
    manifest_value = load_json(root / MANIFEST_PATH)
    if not isinstance(manifest_value, dict):
        raise HumanReviewLedgerError("ledger manifest must be an object")
    manifest = validate_manifest(manifest_value)
    before = {path: sha256_file(path) for path in tracked_paths(root, manifest)}
    sources = current_source_fingerprints(root, policy=policy, scope=scope)
    manifest, records = load_records(
        root,
        policy=policy,
        scope=scope,
        allow_test_only=allow_test_only,
    )
    derived = summarize_records(
        records,
        source_fingerprints=sources,
        policy=policy,
        scope=scope,
    )
    committed = load_json(root / CURRENT_PATH)
    if not isinstance(committed, dict):
        raise HumanReviewLedgerError("committed current summary must be an object")
    validate_summary(committed)
    if pretty_json(committed) != pretty_json(derived):
        raise HumanReviewLedgerError("committed current summary is stale")
    after = {path: sha256_file(path) for path in tracked_paths(root, manifest)}
    if before != after:
        raise HumanReviewLedgerError("read-only verification changed governed ledger sources")
    return {
        "ledger_id": LEDGER_ID,
        "record_count": derived["record_count"],
        "state": derived["state"],
        "current_decision_id": derived["current_decision_id"],
        "current_decision_type": derived["current_decision_type"],
        "current_decision_fingerprint": derived["current_decision_fingerprint"],
        "approval_status": derived["approval_status"],
        "application_status": derived["application_status"],
        "stale": derived["stale"],
        "expired": derived["expired"],
        "policy_fingerprint": policy["policy_fingerprint"],
        "reviewer_scope_fingerprint": scope["scope_fingerprint"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "summary_fingerprint": derived["summary_fingerprint"],
    }
