from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ALLOWED_EVIDENCE, ProofEngineError, fingerprint, load, verify_run

PACKAGE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "reviews" / "round_0001"
REVISIONS_PATH = ROUND_DIR / "revised_candidates.json"
DECISION_INDEX_PATH = ROUND_DIR / "decision_index.json"
SUMMARY_PATH = ROUND_DIR / "review_summary.json"
CHECKPOINT_PATH = REPOSITORY_ROOT / "pilot_runs" / "reconnect_pilot_p3" / "review_checkpoint_0002.json"

REVIEW_ROUND_ID = "PROOF-ENGINE-REVIEW-ROUND-0001"
BASE_RUN_FINGERPRINT = "0935b4b594b3d80a0d38fe2cb95dc9a90eed82ba8591a7251cd4ef1dde9d7ee1"
APPROVED_ORIGINAL_IDS = {"ACH-003", "ACH-004", "ACH-005", "ACH-006", "ACH-008", "ACH-009", "ACH-011"}
REVISED_IDS = {"ACH-001", "ACH-002", "ACH-007", "ACH-010", "ACH-012"}
ALLOWED_RECORD_KINDS = {
    "PROJECT_OUTPUT",
    "PROCESS_BYPRODUCT",
    "INTEGRATION_BYPRODUCT",
    "AUDIT_REMEDIATION_BYPRODUCT",
    "REUSABILITY_SIGNAL",
}
EXPECTED_AUTHORITY_FIELDS = {
    "automatic_approval_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "outreach_authorized",
    "publication_authorized",
}
EXPECTED_AUTHOR = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_INSTRUCTION",
    "role": "PROJECT_OWNER",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _base_candidates(base_run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {candidate["candidate_id"]: candidate for candidate in base_run["candidates"]}


def verify_revision_ledger(ledger: dict[str, Any], base_run: dict[str, Any]) -> dict[str, Any]:
    _verify_fingerprint(ledger, "revisions_fingerprint", "revision ledger")
    if ledger.get("schema_version") != "PROOF-ENGINE-REVISION-LEDGER-V1":
        raise ProofEngineError("revision ledger schema mismatch")
    if ledger.get("review_round_id") != REVIEW_ROUND_ID:
        raise ProofEngineError("revision ledger round mismatch")
    if ledger.get("base_run_fingerprint") != BASE_RUN_FINGERPRINT:
        raise ProofEngineError("revision ledger base-run mismatch")

    revisions = ledger.get("revisions")
    if not isinstance(revisions, list) or len(revisions) != 5:
        raise ProofEngineError("revision ledger must contain exactly five revisions")

    base_by_id = _base_candidates(base_run)
    seen: set[str] = set()
    for revision in revisions:
        candidate_id = revision.get("candidate_id")
        if candidate_id not in REVISED_IDS or candidate_id in seen:
            raise ProofEngineError("unexpected or duplicate revised candidate")
        seen.add(candidate_id)
        original = base_by_id[candidate_id]
        _verify_fingerprint(revision, "candidate_fingerprint", f"revision {candidate_id}")
        if revision.get("schema_version") != "PROOF-ENGINE-CANDIDATE-REVISION-V1":
            raise ProofEngineError("candidate revision schema mismatch")
        if revision.get("revision_id") != f"{candidate_id}-R1" or revision.get("version") != 2:
            raise ProofEngineError("candidate revision identity mismatch")
        if revision.get("supersedes_candidate_fingerprint") != original["candidate_fingerprint"]:
            raise ProofEngineError("candidate revision lineage mismatch")
        if revision.get("record_kind") not in ALLOWED_RECORD_KINDS:
            raise ProofEngineError("candidate revision record kind mismatch")
        if not isinstance(revision.get("claim"), str) or revision["claim"] == original.get("claim"):
            raise ProofEngineError("candidate revision did not correct wording")
        if not isinstance(revision.get("factuality_note"), str) or not revision["factuality_note"]:
            raise ProofEngineError("candidate revision factuality note missing")
        if revision.get("evidence_label") not in ALLOWED_EVIDENCE:
            raise ProofEngineError("candidate revision evidence label mismatch")
        if revision.get("evidence_prs") != original.get("evidence_prs"):
            raise ProofEngineError("candidate revision changed its evidence boundary")
        if revision.get("status") != "REVIEW_REQUIRED":
            raise ProofEngineError("candidate revision must remain review-required until a separate decision")
        if revision.get("public_disclosure") != "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL":
            raise ProofEngineError("candidate revision publication boundary widened")
    if seen != REVISED_IDS:
        raise ProofEngineError("candidate revision set mismatch")
    return ledger


def _revision_by_id(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {revision["candidate_id"]: revision for revision in ledger["revisions"]}


def load_decision_chain(index: dict[str, Any]) -> list[dict[str, Any]]:
    _verify_fingerprint(index, "decision_index_fingerprint", "decision index")
    if index.get("schema_version") != "PROOF-ENGINE-DECISION-INDEX-V1":
        raise ProofEngineError("decision index schema mismatch")
    if index.get("review_round_id") != REVIEW_ROUND_ID:
        raise ProofEngineError("decision index round mismatch")
    if index.get("base_run_fingerprint") != BASE_RUN_FINGERPRINT:
        raise ProofEngineError("decision index base-run mismatch")
    if index.get("decision_count") != 17:
        raise ProofEngineError("decision index count mismatch")

    refs = index.get("segments")
    if not isinstance(refs, list) or len(refs) != 3:
        raise ProofEngineError("decision index must reference exactly three segments")
    all_decisions: list[dict[str, Any]] = []
    previous_segment: str | None = None
    expected_first = 1
    for number, ref in enumerate(refs, start=1):
        expected_path = f"decisions/segment_{number:03d}.json"
        if ref.get("path") != expected_path:
            raise ProofEngineError("decision segment path mismatch")
        segment = load(ROUND_DIR / expected_path)
        _verify_fingerprint(segment, "segment_fingerprint", f"decision segment {number}")
        if segment.get("schema_version") != "PROOF-ENGINE-DECISION-SEGMENT-V1":
            raise ProofEngineError("decision segment schema mismatch")
        if segment.get("review_round_id") != REVIEW_ROUND_ID:
            raise ProofEngineError("decision segment round mismatch")
        if segment.get("segment_id") != f"PROOF-REVIEW-0001-S{number:03d}":
            raise ProofEngineError("decision segment ID mismatch")
        if segment.get("previous_segment_fingerprint") != previous_segment:
            raise ProofEngineError("decision segment chain mismatch")
        if segment.get("segment_fingerprint") != ref.get("segment_fingerprint"):
            raise ProofEngineError("decision segment/index fingerprint mismatch")
        decisions = segment.get("decisions")
        if not isinstance(decisions, list) or not decisions:
            raise ProofEngineError("decision segment must contain decisions")
        expected_last = expected_first + len(decisions) - 1
        if segment.get("first_sequence") != expected_first or segment.get("last_sequence") != expected_last:
            raise ProofEngineError("decision segment sequence mismatch")
        if ref.get("first_sequence") != expected_first or ref.get("last_sequence") != expected_last:
            raise ProofEngineError("decision segment index range mismatch")
        all_decisions.extend(decisions)
        previous_segment = segment["segment_fingerprint"]
        expected_first = expected_last + 1
    if len(all_decisions) != 17:
        raise ProofEngineError("decision chain length mismatch")
    if index.get("final_decision_fingerprint") != all_decisions[-1].get("decision_fingerprint"):
        raise ProofEngineError("decision index final fingerprint mismatch")
    return all_decisions


def verify_decision_chain(
    index: dict[str, Any],
    decisions: list[dict[str, Any]],
    base_run: dict[str, Any],
    revisions: dict[str, Any],
) -> dict[str, Any]:
    if index.get("revisions_fingerprint") != revisions["revisions_fingerprint"]:
        raise ProofEngineError("decision index revision mismatch")
    base_by_id = _base_candidates(base_run)
    revision_by_id = _revision_by_id(revisions)
    original_approvals: set[str] = set()
    original_revisions: set[str] = set()
    revision_approvals: set[str] = set()
    previous: str | None = None

    for sequence, decision in enumerate(decisions, start=1):
        _verify_fingerprint(decision, "decision_fingerprint", f"decision {sequence}")
        if decision.get("schema_version") != "PROOF-ENGINE-HUMAN-DECISION-V1":
            raise ProofEngineError("decision schema mismatch")
        if decision.get("decision_id") != f"PROOF-REVIEW-0001-D{sequence:03d}":
            raise ProofEngineError("decision ID mismatch")
        if decision.get("review_round_id") != REVIEW_ROUND_ID or decision.get("sequence") != sequence:
            raise ProofEngineError("decision identity mismatch")
        if decision.get("previous_decision_fingerprint") != previous:
            raise ProofEngineError("decision chain mismatch")
        previous = decision["decision_fingerprint"]
        if decision.get("authored_by") != EXPECTED_AUTHOR:
            raise ProofEngineError("decision is not bound to the explicit human instruction")
        authority = decision.get("authority")
        if not isinstance(authority, dict) or set(authority) != EXPECTED_AUTHORITY_FIELDS:
            raise ProofEngineError("decision authority fields missing or unknown")
        if any(authority[field] is not False for field in EXPECTED_AUTHORITY_FIELDS):
            raise ProofEngineError("candidate approval widened external authority")

        target = decision.get("target", {})
        candidate_id = target.get("candidate_id")
        decision_type = decision.get("decision_type")
        if target.get("source") == "BASE_RUN" and target.get("candidate_version") == 1:
            if candidate_id not in base_by_id or target.get("candidate_fingerprint") != base_by_id[candidate_id]["candidate_fingerprint"]:
                raise ProofEngineError("decision base-candidate mismatch")
            if decision_type == "APPROVE" and candidate_id in APPROVED_ORIGINAL_IDS:
                original_approvals.add(candidate_id)
                if decision.get("revision_ref") is not None:
                    raise ProofEngineError("original approval unexpectedly references a revision")
            elif decision_type == "REVISE" and candidate_id in REVISED_IDS:
                original_revisions.add(candidate_id)
                revision = revision_by_id[candidate_id]
                expected_ref = {"revision_id": revision["revision_id"], "candidate_fingerprint": revision["candidate_fingerprint"]}
                if decision.get("revision_ref") != expected_ref:
                    raise ProofEngineError("revision decision does not link the factual correction")
            else:
                raise ProofEngineError("unexpected base-candidate decision")
        elif target.get("source") == "REVISION_LEDGER" and target.get("candidate_version") == 2:
            if decision_type != "APPROVE" or candidate_id not in REVISED_IDS:
                raise ProofEngineError("unexpected revised-candidate decision")
            revision = revision_by_id[candidate_id]
            if target.get("candidate_fingerprint") != revision["candidate_fingerprint"]:
                raise ProofEngineError("revised-candidate approval fingerprint mismatch")
            if decision.get("revision_ref") is not None:
                raise ProofEngineError("revision approval unexpectedly references another revision")
            revision_approvals.add(candidate_id)
        else:
            raise ProofEngineError("decision target source or version mismatch")

    if original_approvals != APPROVED_ORIGINAL_IDS:
        raise ProofEngineError("seven original approvals are incomplete")
    if original_revisions != REVISED_IDS:
        raise ProofEngineError("five original revision decisions are incomplete")
    if revision_approvals != REVISED_IDS:
        raise ProofEngineError("five factual revisions are not all approved")
    return index


def build_summary(
    base_run: dict[str, Any],
    revisions: dict[str, Any],
    index: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    revision_by_id = _revision_by_id(revisions)
    approvals = {
        (d["target"]["candidate_id"], d["target"]["candidate_version"]): d
        for d in decisions
        if d["decision_type"] == "APPROVE"
    }
    effective: list[dict[str, Any]] = []
    base_by_id = _base_candidates(base_run)
    for candidate_id in sorted(base_by_id):
        if candidate_id in APPROVED_ORIGINAL_IDS:
            approval = approvals[(candidate_id, 1)]
            effective.append({
                "approval_decision_fingerprint": approval["decision_fingerprint"],
                "approval_decision_id": approval["decision_id"],
                "candidate_fingerprint": base_by_id[candidate_id]["candidate_fingerprint"],
                "candidate_id": candidate_id,
                "candidate_version": 1,
                "effective_status": "APPROVED_FOR_INTERNAL_ASSET_DRAFT",
                "source": "BASE_RUN",
            })
        else:
            revision = revision_by_id[candidate_id]
            approval = approvals[(candidate_id, 2)]
            effective.append({
                "approval_decision_fingerprint": approval["decision_fingerprint"],
                "approval_decision_id": approval["decision_id"],
                "candidate_fingerprint": revision["candidate_fingerprint"],
                "candidate_id": candidate_id,
                "candidate_version": 2,
                "effective_status": "APPROVED_FOR_INTERNAL_ASSET_DRAFT",
                "revision_id": revision["revision_id"],
                "source": "REVISION_LEDGER",
            })
    summary = {
        "authority": {field: False for field in sorted(EXPECTED_AUTHORITY_FIELDS)},
        "base_run_fingerprint": BASE_RUN_FINGERPRINT,
        "counts": {
            "base_candidates": 12,
            "effective_candidates_approved": 12,
            "originals_approved": 7,
            "originals_revised": 5,
            "revisions_approved": 5,
        },
        "decision_index_fingerprint": index["decision_index_fingerprint"],
        "effective_candidates": effective,
        "factuality_policy": {
            "project_outputs_and_byproducts_may_replace_personal_achievement_wording": True,
            "result_and_personal_authorship_are_separate": True,
            "revised_originals_remain_preserved": True,
            "unsupported_generalization_is_downgraded": True,
        },
        "next_action": "Generate an internal six-part public-asset draft from the twelve effective approved candidates and stop before publication.",
        "original_candidate_preservation": {
            "base_run_fingerprint": BASE_RUN_FINGERPRINT,
            "base_run_path": "proof_engine_pilot/runs/p3_run_0001.json",
            "originals_deleted": False,
            "originals_modified": False,
            "revision_mode": "APPEND_ONLY",
        },
        "output_asset": {
            "publication_status": "NOT_PUBLISHED",
            "reason": "Candidate review is complete, but publication wording and release remain a separate human gate.",
            "source_candidate_ids": [item["candidate_id"] for item in effective],
            "state": "READY_FOR_INTERNAL_DRAFT",
        },
        "review_round_id": REVIEW_ROUND_ID,
        "review_state": "ALL_EFFECTIVE_CANDIDATES_APPROVED",
        "revisions_fingerprint": revisions["revisions_fingerprint"],
        "schema_version": "PROOF-ENGINE-REVIEW-SUMMARY-V1",
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return summary


def verify_summary(
    summary: dict[str, Any],
    base_run: dict[str, Any],
    revisions: dict[str, Any],
    index: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    _verify_fingerprint(summary, "summary_fingerprint", "review summary")
    if summary != build_summary(base_run, revisions, index, decisions):
        raise ProofEngineError("review summary does not match deterministic aggregation")
    return summary


def verify_checkpoint(checkpoint: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    _verify_fingerprint(checkpoint, "checkpoint_fingerprint", "review checkpoint")
    links = {
        "base_run_fingerprint": BASE_RUN_FINGERPRINT,
        "review_round_id": REVIEW_ROUND_ID,
        "revisions_fingerprint": summary["revisions_fingerprint"],
        "decision_index_fingerprint": summary["decision_index_fingerprint"],
        "summary_fingerprint": summary["summary_fingerprint"],
    }
    for field, expected in links.items():
        if checkpoint.get(field) != expected:
            raise ProofEngineError(f"review checkpoint link mismatch: {field}")
    if checkpoint.get("state") != "REVIEW_COMPLETE_PUBLICATION_NOT_AUTHORIZED":
        raise ProofEngineError("review checkpoint state mismatch")
    if checkpoint.get("effective_candidate_count") != 12 or checkpoint.get("original_candidate_count") != 12:
        raise ProofEngineError("review checkpoint candidate counts mismatch")
    if checkpoint.get("originals_preserved") is not True:
        raise ProofEngineError("review checkpoint does not preserve originals")
    if checkpoint.get("external_actions_performed") is not False or checkpoint.get("publication_performed") is not False:
        raise ProofEngineError("review checkpoint records an unauthorized external action")
    return checkpoint


def verify_review_round(
    revisions: dict[str, Any] | None = None,
    index: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_run = verify_run()
    if base_run["run_fingerprint"] != BASE_RUN_FINGERPRINT:
        raise ProofEngineError("base candidate run changed after review started")
    revisions = load(REVISIONS_PATH) if revisions is None else revisions
    index = load(DECISION_INDEX_PATH) if index is None else index
    summary = load(SUMMARY_PATH) if summary is None else summary
    checkpoint = load(CHECKPOINT_PATH) if checkpoint is None else checkpoint
    verify_revision_ledger(revisions, base_run)
    decisions = load_decision_chain(index)
    verify_decision_chain(index, decisions, base_run, revisions)
    verify_summary(summary, base_run, revisions, index, decisions)
    verify_checkpoint(checkpoint, summary)
    return summary


def effective_candidate_records() -> list[dict[str, Any]]:
    base_run = verify_run()
    revisions = verify_revision_ledger(load(REVISIONS_PATH), base_run)
    index = load(DECISION_INDEX_PATH)
    decisions = load_decision_chain(index)
    verify_decision_chain(index, decisions, base_run, revisions)
    summary = verify_summary(load(SUMMARY_PATH), base_run, revisions, index, decisions)
    base_by_id = _base_candidates(base_run)
    revision_by_id = _revision_by_id(revisions)
    result: list[dict[str, Any]] = []
    for ref in summary["effective_candidates"]:
        source = revision_by_id if ref["source"] == "REVISION_LEDGER" else base_by_id
        result.append(copy.deepcopy(source[ref["candidate_id"]]))
    return result
