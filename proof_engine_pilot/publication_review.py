from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .learning import preflight_candidate
from .public_wording import verify_public_wording_draft

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "publication_reviews" / "round_0001"
CONTRACT_PATH = ROUND_DIR / "review_contract.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "publication_review_checkpoint_0007.json"

ROUND_ID = "PROOF-ENGINE-PUBLICATION-REVIEW-ROUND-0001"
CONTRACT_ID = "PROOF-ENGINE-PUBLICATION-REVIEW-CONTRACT-0001"
CONTRACT_SCHEMA = "PROOF-ENGINE-PUBLICATION-REVIEW-CONTRACT-V1"
CHECKPOINT_ID = "PROOF-ENGINE-PUBLICATION-REVIEW-CHECKPOINT-0007"
CHECKPOINT_SCHEMA = "PROOF-ENGINE-PUBLICATION-REVIEW-CHECKPOINT-V1"
SOURCE_DRAFT_ID = "PROOF-ENGINE-PUBLIC-WORDING-DRAFT-0001"
SOURCE_DRAFT_FINGERPRINT = "91a21a9eb8119fc474d2f6a1c3429ae265c7c1997066f8148e2a612ef6167782"

EXPECTED_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "publication_authorized": False,
}
EXPECTED_HUMAN_AUTHORIZATION = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_REVIEW_DELEGATION",
    "role": "PROJECT_OWNER",
    "instruction": "オッケー、じゃあやってみようか。",
}
EXPECTED_REVIEWER = {
    "type": "AI_ASSISTANT",
    "role": "DELEGATED_PUBLICATION_WORDING_REVIEWER",
    "decision_origin": "AI_REVIEW_UNDER_EXPLICIT_HUMAN_DELEGATION",
}
EXPECTED_CRITERIA = {
    "factuality": "REQUIRED",
    "contribution_separation": "REQUIRED",
    "reader_clarity": "REQUIRED",
    "scope_bounding": "REQUIRED",
    "privacy_boundary": "REQUIRED",
    "release_authority": "SEPARATE_HUMAN_GATE_REQUIRED",
}
EXPECTED_RELEASE_BOUNDARY = {
    "wording_review_may_complete": True,
    "actual_publication_may_occur": False,
    "separate_human_release_authorization_required": True,
}
EXPECTED_INITIAL_DECISIONS = [
    {
        "wording_id": "WORDING-001",
        "decision": "APPROVE_FOR_PUBLICATION",
        "reason": "The wording is fact-bounded, separates human and AI-tool roles, and clearly states that production autonomy and external effectiveness are unestablished.",
    },
    {
        "wording_id": "WORDING-002",
        "decision": "REVISE",
        "reason": "The isolated headline should explicitly bound WIP=1 to the governed pilot rather than sounding universal.",
    },
    {
        "wording_id": "WORDING-003",
        "decision": "REVISE",
        "reason": "Replace the unclear phrase 'stale expiry' with reader-facing language about expired or stale decisions.",
    },
    {
        "wording_id": "WORDING-004",
        "decision": "APPROVE_FOR_PUBLICATION",
        "reason": "The wording accurately describes a non-applying preview and clearly denies write and approval authority.",
    },
    {
        "wording_id": "WORDING-005",
        "decision": "REVISE",
        "reason": "The headline should describe governance as derived from declared change context rather than imply exact measurement of risk.",
    },
    {
        "wording_id": "WORDING-006",
        "decision": "APPROVE_FOR_PUBLICATION",
        "reason": "The wording is limited to the verified case and explicitly states that external reuse and effectiveness remain unobserved.",
    },
]
EXPECTED_REVISION_DECISIONS = [
    {
        "wording_id": "WORDING-002",
        "revision_id": "WORDING-002-R1",
        "decision": "APPROVE_FOR_PUBLICATION",
        "reason": "The revised headline explicitly scopes the result to the governed pilot.",
    },
    {
        "wording_id": "WORDING-003",
        "revision_id": "WORDING-003-R1",
        "decision": "APPROVE_FOR_PUBLICATION",
        "reason": "The revised summary is clearer without changing the verified integrity behavior.",
    },
    {
        "wording_id": "WORDING-005",
        "revision_id": "WORDING-005-R1",
        "decision": "APPROVE_FOR_PUBLICATION",
        "reason": "The revised headline is aligned with the compiler's declared inputs and does not overstate risk accuracy.",
    },
]
REVISION_PATCHES = {
    "WORDING-002": {
        "headline": "One active work item in the governed pilot, with human approval at consequential transitions",
        "revision_reason": "Bound the WIP=1 claim to the observed governed pilot in the headline itself.",
    },
    "WORDING-003": {
        "summary": "RTS includes a Human Review Ledger that preserves decisions as an append-only chain and rejects expired or stale decisions, proposer mismatches, unmanifested decision files, and other invalid review states.",
        "claim": "RTS includes a Human Review Ledger that preserves decisions as an append-only chain and rejects expired or stale decisions, proposer mismatches, unmanifested decision files, and other invalid review states.",
        "revision_reason": "Replace unclear technical phrasing with reader-facing language while preserving the verified behavior.",
    },
    "WORDING-005": {
        "headline": "Governance depth derived from declared change and authority context",
        "revision_reason": "Describe the deterministic inputs without implying exact measurement of real-world risk.",
    },
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def verify_review_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "publication review contract")
    if value.get("schema_version") != CONTRACT_SCHEMA or value.get("contract_id") != CONTRACT_ID:
        raise ProofEngineError("publication review contract identity mismatch")
    if value.get("review_round_id") != ROUND_ID:
        raise ProofEngineError("publication review contract round mismatch")
    if value.get("source_draft_id") != SOURCE_DRAFT_ID or value.get("source_draft_fingerprint") != SOURCE_DRAFT_FINGERPRINT:
        raise ProofEngineError("publication review contract source mismatch")
    if value.get("human_authorization") != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("publication review delegation mismatch")
    if value.get("reviewer") != EXPECTED_REVIEWER:
        raise ProofEngineError("publication review reviewer attribution mismatch")
    if value.get("criteria") != EXPECTED_CRITERIA:
        raise ProofEngineError("publication review criteria mismatch")
    if value.get("authority") != EXPECTED_AUTHORITY or value.get("release_boundary") != EXPECTED_RELEASE_BOUNDARY:
        raise ProofEngineError("publication review authority widened")
    if value.get("initial_decisions") != EXPECTED_INITIAL_DECISIONS:
        raise ProofEngineError("publication review initial decisions mismatch")
    if value.get("revision_decisions") != EXPECTED_REVISION_DECISIONS:
        raise ProofEngineError("publication review revision decisions mismatch")
    return value


def _build_revision(original: dict[str, Any], revision_decision: dict[str, Any]) -> dict[str, Any]:
    wording_id = original["wording_id"]
    patch = REVISION_PATCHES[wording_id]
    revised = copy.deepcopy(original)
    revised.pop("wording_fingerprint")
    for field in ("headline", "summary", "claim"):
        if field in patch:
            revised[field] = patch[field]
    revised.update({
        "wording_version": 2,
        "revision_id": revision_decision["revision_id"],
        "revision_of_fingerprint": original["wording_fingerprint"],
        "revision_reason": patch["revision_reason"],
        "publication_status": "NOT_PUBLISHED",
        "review_status": "PUBLICATION_REVIEW_COMPLETED",
    })
    revised["wording_fingerprint"] = fingerprint(revised)
    if preflight_candidate(revised)["result"] != "PASS":
        raise ProofEngineError(f"revised publication wording failed learning preflight: {wording_id}")
    return revised


def build_publication_review(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    source_bundle = verify_public_wording_draft()
    source = source_bundle["draft"]
    if source.get("draft_id") != SOURCE_DRAFT_ID or source.get("draft_fingerprint") != SOURCE_DRAFT_FINGERPRINT:
        raise ProofEngineError("publication review source draft mismatch")
    review_contract = verify_review_contract(contract)
    originals = {item["wording_id"]: item for item in source["wordings"]}
    if set(originals) != {f"WORDING-{index:03d}" for index in range(1, 7)}:
        raise ProofEngineError("publication review source wording set mismatch")

    revision_decisions = {item["wording_id"]: item for item in review_contract["revision_decisions"]}
    effective_wordings = []
    revisions = []
    for decision in review_contract["initial_decisions"]:
        wording_id = decision["wording_id"]
        original = originals[wording_id]
        if decision["decision"] == "APPROVE_FOR_PUBLICATION":
            effective_wordings.append({
                "wording_id": wording_id,
                "wording_version": 1,
                "source": "ORIGINAL_DRAFT",
                "wording_fingerprint": original["wording_fingerprint"],
                "effective_status": "APPROVED_WORDING_AWAITING_RELEASE_AUTHORIZATION",
            })
        elif decision["decision"] == "REVISE":
            revision_decision = revision_decisions.get(wording_id)
            if revision_decision is None or revision_decision.get("decision") != "APPROVE_FOR_PUBLICATION":
                raise ProofEngineError("publication review revision approval missing")
            revised = _build_revision(original, revision_decision)
            revisions.append(revised)
            effective_wordings.append({
                "wording_id": wording_id,
                "wording_version": 2,
                "revision_id": revised["revision_id"],
                "source": "REVISION_LEDGER",
                "wording_fingerprint": revised["wording_fingerprint"],
                "effective_status": "APPROVED_WORDING_AWAITING_RELEASE_AUTHORIZATION",
            })
        else:
            raise ProofEngineError("publication review contains unsupported decision")

    if len(effective_wordings) != 6 or len(revisions) != 3:
        raise ProofEngineError("publication review effective counts mismatch")
    if {item["wording_id"] for item in effective_wordings} != set(originals):
        raise ProofEngineError("publication review coverage incomplete")

    summary = {
        "schema_version": "PROOF-ENGINE-PUBLICATION-REVIEW-SUMMARY-V1",
        "review_round_id": ROUND_ID,
        "source_draft_id": SOURCE_DRAFT_ID,
        "source_draft_fingerprint": SOURCE_DRAFT_FINGERPRINT,
        "review_contract_fingerprint": review_contract["contract_fingerprint"],
        "review_origin": {
            "human_authorization": copy.deepcopy(EXPECTED_HUMAN_AUTHORIZATION),
            "reviewer": copy.deepcopy(EXPECTED_REVIEWER),
        },
        "counts": {
            "wordings_reviewed": 6,
            "originals_approved": 3,
            "originals_revised": 3,
            "revisions_approved": 3,
            "effective_wordings": 6,
            "rejected": 0,
            "redacted": 0,
            "expired": 0,
        },
        "revisions": revisions,
        "effective_wordings": effective_wordings,
        "review_state": "ALL_WORDINGS_APPROVED_FOR_RELEASE_GATE",
        "publication_status": "NOT_PUBLISHED",
        "release_authorization_status": "REQUIRED",
        "authority": copy.deepcopy(EXPECTED_AUTHORITY),
        "original_wording_drafts_preserved": True,
        "next_action": "The human project owner selects the exact release surface and explicitly authorizes or withholds publication.",
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {"source": source, "contract": review_contract, "summary": summary}


def effective_wording_records(bundle: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    value = build_publication_review() if bundle is None else bundle
    originals = {item["wording_id"]: item for item in value["source"]["wordings"]}
    revisions = {item["wording_id"]: item for item in value["summary"]["revisions"]}
    return [
        copy.deepcopy(revisions[item["wording_id"]] if item["source"] == "REVISION_LEDGER" else originals[item["wording_id"]])
        for item in value["summary"]["effective_wordings"]
    ]


def verify_publication_review(
    *,
    contract: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_publication_review(contract)
    summary = bundle["summary"]
    _verify_fingerprint(summary, "summary_fingerprint", "publication review summary")
    if summary.get("counts") != {
        "wordings_reviewed": 6,
        "originals_approved": 3,
        "originals_revised": 3,
        "revisions_approved": 3,
        "effective_wordings": 6,
        "rejected": 0,
        "redacted": 0,
        "expired": 0,
    }:
        raise ProofEngineError("publication review summary counts mismatch")
    if summary.get("authority") != EXPECTED_AUTHORITY:
        raise ProofEngineError("publication review authority widened")
    if summary.get("review_state") != "ALL_WORDINGS_APPROVED_FOR_RELEASE_GATE":
        raise ProofEngineError("publication review state mismatch")
    if summary.get("publication_status") != "NOT_PUBLISHED" or summary.get("release_authorization_status") != "REQUIRED":
        raise ProofEngineError("publication review release boundary mismatch")
    if summary.get("original_wording_drafts_preserved") is not True:
        raise ProofEngineError("publication review source drafts were not preserved")

    checkpoint_value = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    _verify_fingerprint(checkpoint_value, "checkpoint_fingerprint", "publication review checkpoint")
    if checkpoint_value.get("schema_version") != CHECKPOINT_SCHEMA or checkpoint_value.get("checkpoint_id") != CHECKPOINT_ID:
        raise ProofEngineError("publication review checkpoint identity mismatch")
    if checkpoint_value.get("review_round_id") != ROUND_ID:
        raise ProofEngineError("publication review checkpoint round mismatch")
    if checkpoint_value.get("source_draft_fingerprint") != SOURCE_DRAFT_FINGERPRINT:
        raise ProofEngineError("publication review checkpoint source mismatch")
    if checkpoint_value.get("review_contract_fingerprint") != bundle["contract"]["contract_fingerprint"]:
        raise ProofEngineError("publication review checkpoint contract mismatch")
    if checkpoint_value.get("effective_wording_count") != 6 or checkpoint_value.get("revision_count") != 3:
        raise ProofEngineError("publication review checkpoint counts mismatch")
    if checkpoint_value.get("state") != "RELEASE_AUTHORIZATION_REQUIRED":
        raise ProofEngineError("publication review checkpoint state mismatch")
    if checkpoint_value.get("original_wording_drafts_preserved") is not True:
        raise ProofEngineError("publication review checkpoint does not preserve drafts")
    if checkpoint_value.get("separate_human_release_authorization_required") is not True:
        raise ProofEngineError("publication review checkpoint bypasses release gate")
    if checkpoint_value.get("publication_performed") is not False or checkpoint_value.get("external_actions_performed") is not False:
        raise ProofEngineError("publication review checkpoint records unauthorized action")
    bundle["checkpoint"] = checkpoint_value
    return bundle
