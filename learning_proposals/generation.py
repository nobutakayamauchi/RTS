from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import LearningProposalError, load_json, sha256_value
from .models import (
    ACTION,
    APPLICATION_STATUS,
    APPROVAL_STATUS,
    GENERATOR_IDENTITY,
    PROPOSAL_SCHEMA,
    PROPOSAL_STATUS,
    REVIEW_SCHEMA,
    proposal_material,
    review_material,
)

OUTCOME_PATHS = [
    "outcome_evidence/examples/success.json",
    "outcome_evidence/examples/escalation.json",
    "outcome_evidence/examples/recovery.json",
]
RESULT_PATH = "skill_regression/results/feature-build-v1.json"
DATASET_PATH = "skill_regression/datasets/feature-build-v1.json"
ROLLBACK_PATH = "skill_regression/rollback/feature-build-v1.json"
CANDIDATE_PATH = "skill_regression/snapshots/feature-build/candidate.json"


def _read(root: Path, relative: str) -> dict[str, Any]:
    value = load_json(root / relative)
    if not isinstance(value, dict):
        raise LearningProposalError(f"{relative} must contain an object")
    return value


def generate_proposal(root: Path) -> dict[str, Any]:
    outcomes = [_read(root, path) for path in OUTCOME_PATHS]
    result = _read(root, RESULT_PATH)
    dataset = _read(root, DATASET_PATH)
    rollback = _read(root, ROLLBACK_PATH)
    candidate = _read(root, CANDIDATE_PATH)

    outcome_rows = [
        {
            "bundle_id": item["bundle_id"],
            "bundle_fingerprint": item["bundle_fingerprint"],
            "scenario": item["scenario"],
            "outcome_classification": item["outcome_classification"],
            "execution_scope": item["execution_scope"],
            "terminal_state": item["controller"]["terminal_state"],
        }
        for item in outcomes
    ]
    proposal: dict[str, Any] = {
        "schema_version": PROPOSAL_SCHEMA,
        "proposal_id": "RTS-SKILL-PROPOSAL-000001",
        "generator_identity": GENERATOR_IDENTITY,
        "proposal_status": PROPOSAL_STATUS,
        "generated_from": {
            "outcome_bundles": outcome_rows,
            "regression": {
                "dataset_id": dataset["dataset_id"],
                "dataset_fingerprint": dataset["dataset_fingerprint"],
                "result_id": result["result_id"],
                "result_fingerprint": result["result_fingerprint"],
                "recommendation": result["recommendation"],
                "promotion_eligibility": result["promotion_eligibility"],
                "baseline_snapshot_fingerprint": result["baseline_snapshot_fingerprint"],
                "candidate_snapshot_id": candidate["snapshot_id"],
                "candidate_snapshot_fingerprint": result["candidate_snapshot_fingerprint"],
                "rollback_fingerprint": result["rollback_fingerprint"],
            },
            "rollback": {
                "rollback_id": rollback["rollback_id"],
                "rollback_fingerprint": rollback["rollback_fingerprint"],
                "restore_content_sha256": rollback["restore_content_sha256"],
                "human_approval_required": rollback["human_approval_required"],
                "mutation_authorized": rollback["mutation_authorized"],
                "adjacent_repository_write_authorized": rollback["adjacent_repository_write_authorized"],
            },
        },
        "evidence_summary": {
            "confirmed_facts": sorted([
                "candidate passes all four applicable deterministic fixtures",
                "regression result records two improvements and zero regressions",
                "rollback snapshot reconstructs the pinned baseline content hash",
                "the bounded local escalation claim is classified VERIFIED",
            ]),
            "assumptions": sorted([
                "recovery relevance is inferred from preserved local checkpoint evidence",
                "the candidate may improve future feature-build safety if separately approved and applied",
            ]),
            "unverified_claims": sorted([
                "external business or user success has not been observed",
                "the simulated success bundle remains UNVERIFIED",
                "the Skill rollback restoration path has not been executed",
            ]),
        },
        "recommendation": {
            "action": ACTION,
            "target_skill_id": candidate["skill_id"],
            "candidate_snapshot_id": candidate["snapshot_id"],
            "candidate_snapshot_fingerprint": candidate["snapshot_fingerprint"],
            "rationale": (
                "The local candidate satisfies the immutable deterministic regression policy and has an exact rollback snapshot. "
                "Because all governed outcomes are SIMULATED_ONLY and no external success or rollback execution was observed, "
                "the only authorized next action is separate human review."
            ),
        },
        "safeguards": {
            "approval_status": APPROVAL_STATUS,
            "application_status": APPLICATION_STATUS,
            "external_execution_performed": False,
            "mutation_authorized": False,
            "adjacent_repository_write_authorized": False,
            "self_approval_authorized": False,
            "automatic_rollback_authorized": False,
        },
        "blockers": sorted([
            "external outcome success remains unverified",
            "human approval has not been recorded",
            "real rollback restoration has not been exercised",
            "skill mutation and adjacent-repository writes are not authorized",
        ]),
    }
    proposal["proposal_fingerprint"] = sha256_value(proposal_material(proposal))
    return proposal


def generate_pending_review(proposal: dict[str, Any]) -> dict[str, Any]:
    review: dict[str, Any] = {
        "schema_version": REVIEW_SCHEMA,
        "decision_id": "RTS-SKILL-REVIEW-000001",
        "proposal_id": proposal["proposal_id"],
        "proposal_fingerprint": proposal["proposal_fingerprint"],
        "status": "PENDING",
        "reviewer": {"type": "UNASSIGNED", "identity": None},
        "generator_identity": GENERATOR_IDENTITY,
        "separation_of_duties": True,
        "rationale": "Human review has not yet occurred; this record is a non-authorizing review request.",
        "skill_mutation_authorized": False,
        "adjacent_repository_write_authorized": False,
        "application_status": APPLICATION_STATUS,
    }
    review["decision_fingerprint"] = sha256_value(review_material(review))
    return review
