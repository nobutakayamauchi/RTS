from __future__ import annotations

from pathlib import Path
from typing import Any

from human_review_ledger.corpus import verify_all as verify_human_review_ledger
from learning_proposals.corpus import verify_all as verify_learning_proposals
from skill_regression.corpus import verify_all as verify_skill_regression

from .common import PromotionApplicationPreviewError, load_json, sha256_value
from .models import MODE, SCHEMA_VERSION, fingerprint_material, validate_preview

PROPOSAL_PATH = "learning_proposals/proposals/feature-build-v1.json"
PENDING_REVIEW_PATH = "learning_proposals/reviews/feature-build-v1.pending.json"
LEDGER_CURRENT_PATH = "human_review_ledger/ledger/current.json"
LEDGER_MANIFEST_PATH = "human_review_ledger/ledger/manifest.json"
REGRESSION_RESULT_PATH = "skill_regression/results/feature-build-v1.json"
ROLLBACK_PATH = "skill_regression/rollback/feature-build-v1.json"
BASELINE_PATH = "skill_regression/snapshots/feature-build/baseline.json"
CANDIDATE_PATH = "skill_regression/snapshots/feature-build/candidate.json"


def _read(root: Path, relative: str) -> dict[str, Any]:
    value = load_json(root / relative)
    if not isinstance(value, dict):
        raise PromotionApplicationPreviewError(f"{relative} must contain an object")
    return value


def generate_preview(root: Path) -> dict[str, Any]:
    root = root.resolve()
    proposal_summary = verify_learning_proposals(root)
    ledger_summary = verify_human_review_ledger(root)
    regression_summary = verify_skill_regression(root)

    proposal = _read(root, PROPOSAL_PATH)
    pending = _read(root, PENDING_REVIEW_PATH)
    ledger_current = _read(root, LEDGER_CURRENT_PATH)
    ledger_manifest = _read(root, LEDGER_MANIFEST_PATH)
    regression = _read(root, REGRESSION_RESULT_PATH)
    rollback = _read(root, ROLLBACK_PATH)
    baseline = _read(root, BASELINE_PATH)
    candidate = _read(root, CANDIDATE_PATH)

    if proposal_summary["proposal_fingerprint"] != proposal["proposal_fingerprint"]:
        raise PromotionApplicationPreviewError("proposal verifier and committed proposal disagree")
    if ledger_summary["summary_fingerprint"] != ledger_current["summary_fingerprint"]:
        raise PromotionApplicationPreviewError("ledger verifier and current summary disagree")
    if regression_summary["result_fingerprint"] != regression["result_fingerprint"]:
        raise PromotionApplicationPreviewError("regression verifier and committed result disagree")
    if pending["proposal_fingerprint"] != proposal["proposal_fingerprint"]:
        raise PromotionApplicationPreviewError("pending review does not match the proposal")

    blockers = sorted({
        "human review approval is not current",
        "proposal remains pending human review",
        "regression promotion eligibility remains NOT_ELIGIBLE",
        "target and adjacent-repository writes are not authorized",
    })
    if ledger_summary["approval_status"] == "APPROVED":
        blockers.remove("human review approval is not current")
    if proposal_summary["review_status"] != "PENDING":
        blockers.remove("proposal remains pending human review")
    if regression_summary["promotion_eligibility"] != "NOT_ELIGIBLE":
        blockers.remove("regression promotion eligibility remains NOT_ELIGIBLE")

    preview: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "preview_id": "",
        "preview_fingerprint": "",
        "mode": MODE,
        "state": "BLOCKED",
        "generated_from": {
            "proposal_id": proposal["proposal_id"],
            "proposal_fingerprint": proposal["proposal_fingerprint"],
            "pending_review_fingerprint": pending["decision_fingerprint"],
            "ledger_id": ledger_current["ledger_id"],
            "ledger_record_count": ledger_current["record_count"],
            "ledger_state": ledger_current["state"],
            "ledger_current_decision_fingerprint": ledger_current["current_decision_fingerprint"],
            "ledger_approval_status": ledger_current["approval_status"],
            "ledger_summary_fingerprint": ledger_current["summary_fingerprint"],
            "ledger_manifest_fingerprint": ledger_manifest["manifest_fingerprint"],
            "regression_result_fingerprint": regression["result_fingerprint"],
            "rollback_fingerprint": rollback["rollback_fingerprint"],
            "baseline_snapshot_fingerprint": baseline["snapshot_fingerprint"],
            "candidate_snapshot_fingerprint": candidate["snapshot_fingerprint"],
        },
        "proposed_change_set": [
            {
                "operation": "REPLACE_FILE",
                "repository": baseline["source"]["repository"],
                "path": baseline["source"]["path"],
                "expected_before_sha256": baseline["content_sha256"],
                "proposed_after_sha256": candidate["content_sha256"],
            }
        ],
        "prerequisites": sorted([
            "a separately authored current human APPROVE decision",
            "an exact unchanged target content fingerprint",
            "an explicit application authority gate outside this preview",
            "a separately approved adjacent-repository execution adapter",
            "a verified rollback snapshot matching the expected target",
        ]),
        "blockers": blockers,
        "validation_steps": sorted([
            "compare the live target content hash with expected_before_sha256",
            "re-run the deterministic regression dataset before application",
            "re-verify proposal, review ledger, rollback, and preview fingerprints",
            "require a separate human application decision after preview review",
            "verify the candidate content hash before any target write",
        ]),
        "stop_conditions": sorted([
            "any governed fingerprint changes after preview generation",
            "human approval is absent, stale, expired, rejected, or superseded",
            "the live target content hash differs from expected_before_sha256",
            "the proposed target path escapes the separately approved scope",
            "the regression or rollback verifier no longer passes",
        ]),
        "rollback": {
            "rollback_id": rollback["rollback_id"],
            "rollback_fingerprint": rollback["rollback_fingerprint"],
            "restore_content_sha256": rollback["restore_content_sha256"],
            "human_approval_required": True,
            "automatic_rollback_authorized": False,
        },
        "authority": {
            "approval_status": "NOT_APPROVED",
            "application_status": "NOT_APPLIED",
            "target_write_authorized": False,
            "adjacent_repository_write_authorized": False,
            "skill_mutation_authorized": False,
            "commit_authorized": False,
            "merge_authorized": False,
            "external_action_authorized": False,
        },
    }
    fingerprint = sha256_value(fingerprint_material(preview))
    preview["preview_fingerprint"] = fingerprint
    preview["preview_id"] = f"RTS-PROMOTION-PREVIEW-{fingerprint[:16].upper()}"
    return validate_preview(preview)
