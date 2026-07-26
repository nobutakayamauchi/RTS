from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .asset_draft import build_internal_asset_draft
from .core import ProofEngineError, fingerprint, load

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "asset_reviews" / "round_0001"
INDEX_PATH = ROUND_DIR / "decision_index.json"
SUMMARY_PATH = ROUND_DIR / "review_summary.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "asset_review_checkpoint_0005.json"

ROUND_ID = "PROOF-ENGINE-ASSET-REVIEW-ROUND-0001"
DRAFT_ID = "PROOF-ENGINE-INTERNAL-ASSET-DRAFT-0001"
INDEX_SCHEMA = "PROOF-ENGINE-ASSET-REVIEW-INDEX-V1"
SEGMENT_SCHEMA = "PROOF-ENGINE-ASSET-REVIEW-SEGMENT-V1"
DECISION_SCHEMA = "PROOF-ENGINE-ASSET-REVIEW-DECISION-V1"
SUMMARY_SCHEMA = "PROOF-ENGINE-ASSET-REVIEW-SUMMARY-V1"
CHECKPOINT_SCHEMA = "PROOF-ENGINE-ASSET-REVIEW-CHECKPOINT-V1"
CHECKPOINT_ID = "PROOF-ENGINE-ASSET-REVIEW-CHECKPOINT-0005"
SEGMENT_PATH = "proof_engine_pilot/asset_reviews/round_0001/decisions/segment_001.json"
SEGMENT_ID = "PROOF-ENGINE-ASSET-REVIEW-0001-SEGMENT-001"
EXPECTED_AUTHOR = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_INSTRUCTION",
    "role": "PROJECT_OWNER",
}
EXPECTED_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "publication_authorized": False,
}
EXPECTED_BASIS = {
    "factuality": "PASS",
    "contribution_separation": "PASS",
    "non_overlap": "PASS",
    "privacy_boundary": "PASS",
    "internal_source_readiness": "PASS",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def load_decisions(
    index: dict[str, Any],
    segment_overrides: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    entries = index.get("segments")
    if not isinstance(entries, list) or len(entries) != 1:
        raise ProofEngineError("asset review segment index mismatch")
    decisions: list[dict[str, Any]] = []
    previous_segment = None
    overrides = segment_overrides or {}
    for position, entry in enumerate(entries, start=1):
        if entry.get("path") != SEGMENT_PATH or entry.get("segment_id") != SEGMENT_ID:
            raise ProofEngineError("asset review segment reference mismatch")
        segment = copy.deepcopy(overrides[SEGMENT_PATH]) if SEGMENT_PATH in overrides else load(ROOT / SEGMENT_PATH)
        segment_fp = _verify_fingerprint(segment, "segment_fingerprint", "asset review segment")
        if segment.get("schema_version") != SEGMENT_SCHEMA or segment.get("review_round_id") != ROUND_ID:
            raise ProofEngineError("asset review segment identity mismatch")
        if segment.get("segment_id") != SEGMENT_ID or segment.get("segment_id") != entry.get("segment_id"):
            raise ProofEngineError("asset review segment ID mismatch")
        if segment_fp != entry.get("segment_fingerprint"):
            raise ProofEngineError("asset review segment/index mismatch")
        if segment.get("previous_segment_fingerprint") != previous_segment:
            raise ProofEngineError("asset review segment chain mismatch")
        if segment.get("decision_count") != len(segment.get("decisions", [])) or segment.get("decision_count") != entry.get("decision_count"):
            raise ProofEngineError("asset review segment count mismatch")
        decisions.extend(segment["decisions"])
        previous_segment = segment_fp
    return decisions


def verify_asset_review(
    *,
    index: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    segment_overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    draft = build_internal_asset_draft()
    if draft.get("draft_id") != DRAFT_ID:
        raise ProofEngineError("asset review source draft identity mismatch")
    assets = {item["asset_id"]: item for item in draft["assets"]}
    if len(assets) != 6:
        raise ProofEngineError("asset review source count mismatch")

    index = load(INDEX_PATH) if index is None else copy.deepcopy(index)
    index_fp = _verify_fingerprint(index, "decision_index_fingerprint", "asset review index")
    if index.get("schema_version") != INDEX_SCHEMA or index.get("review_round_id") != ROUND_ID:
        raise ProofEngineError("asset review index identity mismatch")
    if index.get("source_draft_id") != DRAFT_ID or index.get("source_draft_fingerprint") != draft["draft_fingerprint"]:
        raise ProofEngineError("asset review source draft mismatch")
    decisions = load_decisions(index, segment_overrides)
    if index.get("decision_count") != len(decisions) or len(decisions) != 6:
        raise ProofEngineError("asset review decision count mismatch")

    previous = None
    seen: set[str] = set()
    for position, decision in enumerate(decisions, start=1):
        decision_fp = _verify_fingerprint(decision, "decision_fingerprint", f"asset review decision {position}")
        if decision.get("schema_version") != DECISION_SCHEMA:
            raise ProofEngineError("asset review decision schema mismatch")
        if decision.get("review_round_id") != ROUND_ID or decision.get("sequence") != position:
            raise ProofEngineError("asset review decision identity mismatch")
        if decision.get("decision_id") != f"PROOF-ASSET-REVIEW-0001-D{position:03d}":
            raise ProofEngineError("asset review decision order mismatch")
        if decision.get("previous_decision_fingerprint") != previous:
            raise ProofEngineError("asset review decision chain mismatch")
        previous = decision_fp
        if decision.get("authored_by") != EXPECTED_AUTHOR:
            raise ProofEngineError("asset review decision is not bound to the explicit human instruction")
        if decision.get("decision_type") != "APPROVE":
            raise ProofEngineError("asset review contains non-approved asset")
        if decision.get("approval_scope") != "APPROVED_AS_INTERNAL_SOURCE_FOR_PUBLIC_WORDING_DRAFT":
            raise ProofEngineError("asset review approval scope mismatch")
        if decision.get("authority") != EXPECTED_AUTHORITY:
            raise ProofEngineError("asset review authority widened")
        if decision.get("review_basis") != EXPECTED_BASIS:
            raise ProofEngineError("asset review basis mismatch")
        target = decision.get("target", {})
        asset_id = target.get("asset_id")
        if asset_id not in assets or asset_id in seen:
            raise ProofEngineError("asset review target set mismatch")
        seen.add(asset_id)
        if target.get("asset_fingerprint") != assets[asset_id]["asset_fingerprint"]:
            raise ProofEngineError("asset review target fingerprint mismatch")
        if target.get("draft_id") != DRAFT_ID or target.get("draft_fingerprint") != draft["draft_fingerprint"]:
            raise ProofEngineError("asset review target draft mismatch")
        if not isinstance(decision.get("reason"), str) or not decision["reason"].strip():
            raise ProofEngineError("asset review reason is empty")
    if seen != set(assets):
        raise ProofEngineError("asset review coverage incomplete")
    if index.get("last_decision_fingerprint") != previous:
        raise ProofEngineError("asset review final decision mismatch")

    summary = load(SUMMARY_PATH) if summary is None else copy.deepcopy(summary)
    summary_fp = _verify_fingerprint(summary, "summary_fingerprint", "asset review summary")
    if summary.get("schema_version") != SUMMARY_SCHEMA or summary.get("review_round_id") != ROUND_ID:
        raise ProofEngineError("asset review summary identity mismatch")
    if summary.get("source_draft_id") != DRAFT_ID or summary.get("source_draft_fingerprint") != draft["draft_fingerprint"]:
        raise ProofEngineError("asset review summary source mismatch")
    if summary.get("decision_index_fingerprint") != index_fp:
        raise ProofEngineError("asset review summary/index mismatch")
    if summary.get("counts") != {"assets_reviewed": 6, "approved": 6, "revised": 0, "rejected": 0, "redacted": 0, "expired": 0}:
        raise ProofEngineError("asset review summary counts mismatch")
    if summary.get("review_state") != "ALL_INTERNAL_ASSETS_APPROVED":
        raise ProofEngineError("asset review state mismatch")
    if summary.get("authority") != EXPECTED_AUTHORITY or summary.get("publication_status") != "NOT_PUBLISHED":
        raise ProofEngineError("asset review publication boundary mismatch")
    effective = summary.get("effective_assets", [])
    if len(effective) != 6 or {item.get("asset_id") for item in effective} != set(assets):
        raise ProofEngineError("asset review effective set mismatch")
    decision_by_asset = {item["target"]["asset_id"]: item for item in decisions}
    for item in effective:
        asset_id = item["asset_id"]
        decision = decision_by_asset[asset_id]
        if item.get("asset_fingerprint") != assets[asset_id]["asset_fingerprint"]:
            raise ProofEngineError("asset review effective fingerprint mismatch")
        if item.get("decision_id") != decision["decision_id"] or item.get("decision_fingerprint") != decision["decision_fingerprint"]:
            raise ProofEngineError("asset review effective decision mismatch")
        if item.get("effective_status") != "APPROVED_AS_INTERNAL_SOURCE_FOR_PUBLIC_WORDING_DRAFT":
            raise ProofEngineError("asset review effective status mismatch")

    checkpoint = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    _verify_fingerprint(checkpoint, "checkpoint_fingerprint", "asset review checkpoint")
    if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA or checkpoint.get("checkpoint_id") != CHECKPOINT_ID:
        raise ProofEngineError("asset review checkpoint identity mismatch")
    if checkpoint.get("review_round_id") != ROUND_ID:
        raise ProofEngineError("asset review checkpoint round mismatch")
    links = {"source_draft_fingerprint": draft["draft_fingerprint"], "decision_index_fingerprint": index_fp, "summary_fingerprint": summary_fp}
    for field, expected in links.items():
        if checkpoint.get(field) != expected:
            raise ProofEngineError(f"asset review checkpoint mismatch: {field}")
    if checkpoint.get("state") != "PUBLIC_WORDING_DRAFT_READY" or checkpoint.get("approved_asset_count") != 6:
        raise ProofEngineError("asset review checkpoint state mismatch")
    if checkpoint.get("original_internal_assets_preserved") is not True:
        raise ProofEngineError("asset review source records not preserved")
    if checkpoint.get("publication_performed") is not False or checkpoint.get("external_actions_performed") is not False:
        raise ProofEngineError("asset review checkpoint records unauthorized action")

    return {"draft": draft, "index": index, "decisions": decisions, "summary": summary, "checkpoint": checkpoint}
