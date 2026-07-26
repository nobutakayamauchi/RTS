from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Any

from asset_manifest.core import load_current_snapshot, verify as verify_asset_manifest
from execution_controller.cli import command_verify as verify_execution_controller
from human_review_ledger.corpus import verify_all as verify_human_review_ledger
from learning_proposals.corpus import verify_all as verify_learning_proposals
from loop_core.core import evaluate
from loop_core.models import validate_evaluation
from outcome_evidence.corpus import corpus_summary, load_corpus
from promotion_application_preview.corpus import verify_all as verify_promotion_application_preview
from skill_regression.corpus import verify_all as verify_skill_regression

from .common import (
    GovernedLoopError,
    ensure_inside,
    load_json,
    reject_private_content,
    sha256_file,
    sha256_value,
)
from .models import MODE, SCHEMA_VERSION, STATUS, VERIFICATION_ORDER, run_material, validate_record

SOURCE_PATHS = (
    "asset_manifest/snapshots/current.json",
    "asset_manifest/index/assets.json",
    "asset_manifest/index/repositories.json",
    "freezer/index/items.json",
    "freezer/index/build_priority.json",
    "governed_loop/schemas/loop_run.schema.json",
    "human_review_ledger/policy/v1.json",
    "human_review_ledger/reviewer_scopes/default.json",
    "human_review_ledger/ledger/manifest.json",
    "human_review_ledger/ledger/current.json",
    "human_review_ledger/schemas/decision.schema.json",
    "human_review_ledger/schemas/policy.schema.json",
    "human_review_ledger/schemas/reviewer_scope.schema.json",
    "human_review_ledger/schemas/manifest.schema.json",
    "human_review_ledger/schemas/current_summary.schema.json",
    "outcome_evidence/examples/escalation.json",
    "outcome_evidence/examples/recovery.json",
    "outcome_evidence/examples/success.json",
    "skill_regression/datasets/feature-build-v1.json",
    "skill_regression/results/feature-build-v1.json",
    "skill_regression/rollback/feature-build-v1.json",
    "skill_regression/snapshots/feature-build/baseline.json",
    "skill_regression/snapshots/feature-build/candidate.json",
    "learning_proposals/proposals/feature-build-v1.json",
    "learning_proposals/reviews/feature-build-v1.pending.json",
    "promotion_application_preview/schemas/preview.schema.json",
    "promotion_application_preview/previews/current.json",
)


def source_paths(root: Path) -> list[Path]:
    root = root.resolve()
    pointer = load_json(root / "asset_manifest" / "snapshots" / "current.json")
    if not isinstance(pointer, dict) or not isinstance(pointer.get("path"), str):
        raise GovernedLoopError("invalid Asset Manifest current pointer")
    snapshot = ensure_inside(root, root / pointer["path"])
    paths = [ensure_inside(root, root / relative) for relative in SOURCE_PATHS]
    paths.append(snapshot)
    return sorted(set(paths), key=lambda path: path.relative_to(root).as_posix())


def source_fingerprints(root: Path) -> list[dict[str, str]]:
    root = root.resolve()
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in source_paths(root)
    ]


def _verify_sources(root: Path) -> dict[str, Any]:
    errors = verify_asset_manifest(root)
    if errors:
        raise GovernedLoopError(f"asset manifest verification failed: {'; '.join(errors)}")
    asset_snapshot = load_current_snapshot(root)

    first_evaluation = evaluate(root)
    second_evaluation = evaluate(root)
    validate_evaluation(first_evaluation)
    if first_evaluation != second_evaluation:
        raise GovernedLoopError("read-only loop evaluation is not deterministic")

    with contextlib.redirect_stdout(io.StringIO()):
        verify_execution_controller()

    bundles = load_corpus(root)
    outcome = corpus_summary(root)
    regression = verify_skill_regression(root)
    proposal = verify_learning_proposals(root)
    human_review = verify_human_review_ledger(root)
    promotion_preview = verify_promotion_application_preview(root)
    return {
        "asset_snapshot": asset_snapshot,
        "loop_evaluation": first_evaluation,
        "bundles": bundles,
        "outcome_summary": outcome,
        "regression_summary": regression,
        "proposal_summary": proposal,
        "human_review_summary": human_review,
        "promotion_preview_summary": promotion_preview,
    }


def generate_run(root: Path) -> dict[str, Any]:
    root = root.resolve()
    before = source_fingerprints(root)
    sources = _verify_sources(root)
    after = source_fingerprints(root)
    if before != after:
        raise GovernedLoopError("read-only generation failed: governed source changed")

    snapshot_pointer = load_json(root / "asset_manifest" / "snapshots" / "current.json")
    snapshot_path = ensure_inside(root, root / snapshot_pointer["path"])
    snapshot = sources["asset_snapshot"]
    evaluation = sources["loop_evaluation"]
    bundles = sorted(sources["bundles"], key=lambda row: row["bundle_id"])
    outcome = sources["outcome_summary"]
    regression = sources["regression_summary"]
    proposal = sources["proposal_summary"]
    human_review = sources["human_review_summary"]
    promotion_preview = sources["promotion_preview_summary"]

    outcome_links = [
        {
            "bundle_id": bundle["bundle_id"],
            "bundle_fingerprint": bundle["bundle_fingerprint"],
            "plan_fingerprint": bundle["controller"]["plan_fingerprint"],
            "authorization_fingerprint": bundle["controller"]["authorization_fingerprint"],
            "terminal_state": bundle["controller"]["terminal_state"],
            "execution_scope": bundle["execution_scope"],
            "outcome_classification": bundle["outcome_classification"],
        }
        for bundle in bundles
    ]

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "",
        "run_fingerprint": "",
        "mode": MODE,
        "status": STATUS,
        "as_of": evaluation["as_of"],
        "verification_order": list(VERIFICATION_ORDER),
        "source_fingerprints": before,
        "components": {
            "asset_manifest": {
                "verification": "PASSED",
                "snapshot_version": snapshot["snapshot_version"],
                "snapshot_path": snapshot_pointer["path"],
                "snapshot_sha256": sha256_file(snapshot_path),
                "asset_count": len(snapshot["assets"]),
                "repository_count": len(snapshot["repositories"]),
            },
            "read_only_loop": {
                "verification": "PASSED",
                "evaluation_id": evaluation["evaluation_id"],
                "authority": evaluation["authority"],
                "state": evaluation["state"],
                "audit_level": evaluation["audit_level"],
                "wip_count": evaluation["wip"]["count"],
                "active_item_ids": evaluation["wip"]["active_item_ids"],
                "recommendation_action": evaluation["recommendation"]["action"],
                "recommendation_item_id": evaluation["recommendation"]["item_id"],
            },
            "execution_controller": {
                "verification": "PASSED",
                "execution_scope": "LOCAL_DRY_RUN_ONLY",
                "external_execution_performed": False,
                "outcome_links": outcome_links,
            },
            "outcome_evidence": {
                "verification": "PASSED",
                "bundle_count": outcome["bundle_count"],
                "bundle_ids": outcome["bundle_ids"],
                "bundle_fingerprints": [
                    bundle["bundle_fingerprint"] for bundle in bundles
                ],
                "classifications": outcome["classifications"],
                "execution_scope": outcome["execution_scope"],
                "promotion_eligibility": outcome["promotion_eligibility"],
            },
            "skill_regression": {
                "verification": "PASSED",
                "dataset_id": regression["dataset_id"],
                "result_fingerprint": regression["result_fingerprint"],
                "recommendation": regression["recommendation"],
                "promotion_eligibility": regression["promotion_eligibility"],
                "regressions": regression["regressions"],
                "improvements": regression["improvements"],
                "safety_failures": regression["safety_failures"],
                "candidate_pass_rate": regression["candidate_pass_rate"],
            },
            "learning_proposal": {
                "verification": "PASSED",
                "proposal_id": proposal["proposal_id"],
                "proposal_fingerprint": proposal["proposal_fingerprint"],
                "proposal_status": proposal["proposal_status"],
                "review_status": proposal["review_status"],
                "recommendation": proposal["recommendation"],
                "approval_status": proposal["approval_status"],
                "application_status": proposal["application_status"],
            },
            "human_review_ledger": {
                "verification": "PASSED",
                "ledger_id": human_review["ledger_id"],
                "record_count": human_review["record_count"],
                "state": human_review["state"],
                "current_decision_id": human_review["current_decision_id"],
                "current_decision_type": human_review["current_decision_type"],
                "current_decision_fingerprint": human_review["current_decision_fingerprint"],
                "approval_status": human_review["approval_status"],
                "application_status": human_review["application_status"],
                "stale": human_review["stale"],
                "expired": human_review["expired"],
                "policy_fingerprint": human_review["policy_fingerprint"],
                "reviewer_scope_fingerprint": human_review["reviewer_scope_fingerprint"],
                "manifest_fingerprint": human_review["manifest_fingerprint"],
                "summary_fingerprint": human_review["summary_fingerprint"],
            },
            "promotion_application_preview": {
                "verification": "PASSED",
                "preview_id": promotion_preview["preview_id"],
                "preview_fingerprint": promotion_preview["preview_fingerprint"],
                "state": promotion_preview["state"],
                "blocker_count": promotion_preview["blocker_count"],
                "approval_status": promotion_preview["approval_status"],
                "application_status": promotion_preview["application_status"],
                "target_write_authorized": promotion_preview["target_write_authorized"],
                "adjacent_repository_write_authorized": promotion_preview["adjacent_repository_write_authorized"],
            },
        },
        "evidence_summary": {
            "confirmed_facts": [
                "all eight repository-local component verification stages passed in the fixed governed order",
                "the current loop evaluation observed exactly the active items recorded in the FREEZER index",
                "three governed outcome bundles remain linked to exact controller plan and authorization fingerprints",
                "the deterministic Skill regression result contains zero regressions and zero safety failures",
                "the learning proposal and pending review remain reconstructable from exact committed sources",
                "the Human Review Ledger verifies as an empty non-authorizing append-only ledger with no manufactured human decision",
                "the Promotion Application Preview verifies as BLOCKED and non-applying with exact target and rollback hashes",
            ],
            "assumptions": [
                "repository-local component verification is sufficient for the bounded one-shot integration claim",
                "future human review will interpret this run without treating it as Skill-application authority",
            ],
            "unverified_claims": [
                "no external business or user success was observed",
                "no live provider execution or adjacent-repository application was exercised",
                "real-run pilot value has not yet been measured",
            ],
            "risks": [
                "component contracts may drift after this run and require a newly generated fingerprint set",
                "SIMULATED_ONLY outcomes could be overgeneralized beyond their bounded local claim",
                "a future adapter could attempt scheduling, provider use, or adjacent writes without a new gate",
            ],
        },
        "authority": {
            "read_only": True,
            "external_execution_performed": False,
            "scheduler_authorized": False,
            "provider_authorized": False,
            "adjacent_repository_write_authorized": False,
            "skill_mutation_authorized": False,
            "approval_status": "NOT_APPROVED",
            "application_status": "NOT_APPLIED",
            "automatic_rollback_authorized": False,
        },
    }
    reject_private_content(record)
    digest = sha256_value(run_material(record))
    record["run_id"] = f"RTS-LOOP-RUN-{digest[:16].upper()}"
    record["run_fingerprint"] = digest
    return validate_record(record)
