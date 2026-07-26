from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .learning import preflight_candidate, verify_learning_bundle
from .review import effective_candidate_records, verify_review_round

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
MANIFEST_PATH = PACKAGE_DIR / "assets" / "round_0001" / "internal_asset_manifest.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "internal_asset_checkpoint_0004.json"

ASSET_BLUEPRINTS = [
    {
        "asset_id": "ASSET-001",
        "title": "Governed Loop Engine",
        "record_kind": "PROJECT_OUTPUT",
        "source_candidate_ids": ["ACH-001", "ACH-002", "ACH-007", "ACH-008"],
        "claim": "The RTS repository contains a deterministic, repository-local, read-only governed loop engine with staged integration boundaries, eight linked verification stages, checkpoint and resume records, a Seed contract, and a reset WIP state.",
        "factuality_note": "The repository artifacts and tests verify the resulting engine. The wording describes a project output produced through AI-assisted development under human-set goals, constraints, sequencing, review, and completion decisions.",
        "value": "Provides a reconstructable project-ingestion and control loop without granting unattended execution authority.",
        "human_contribution": ["set the usable-loop objective and scope", "defined safety, ordering, and completion boundaries", "reviewed failures and accepted the bounded result"],
        "ai_tool_contribution": ["proposed decomposition and implementation details", "generated code, fixtures, records, and tests", "applied review-driven corrections"],
        "evidence_label": "VERIFIED",
    },
    {
        "asset_id": "ASSET-002",
        "title": "WIP=1 and Human-Gated Delivery",
        "record_kind": "PROCESS_BYPRODUCT",
        "source_candidate_ids": ["ACH-003"],
        "claim": "WIP=1 and explicit human gates were enforced across selection, implementation, verification, and completion during the governed pilot.",
        "factuality_note": "The repository lifecycle records verify the policy in this pilot. This is a governed process result, not a claim that the policy has been validated across unrelated organizations.",
        "value": "Reduces parallel scope drift and keeps consequential transitions under explicit human control.",
        "human_contribution": ["set the WIP and approval policy", "made priority and continuation decisions", "approved lifecycle transitions"],
        "ai_tool_contribution": ["generated lifecycle records and verification support"],
        "evidence_label": "VERIFIED",
    },
    {
        "asset_id": "ASSET-003",
        "title": "Append-Only Human Review and Integrity Checks",
        "record_kind": "PROJECT_OUTPUT",
        "source_candidate_ids": ["ACH-004", "ACH-005"],
        "claim": "The repository contains an append-only Human Review Ledger with deterministic verification and fail-closed handling for stale expiry, proposer mismatch, and unmanifested decision files.",
        "factuality_note": "The ledger and integrity checks are verified in the cited repository history. Human review defined and accepted the authority boundary; AI tools assisted implementation and regression testing.",
        "value": "Makes decisions auditable while preventing stale or unregistered evidence from becoming application authority.",
        "human_contribution": ["defined the decision contract and authority boundary", "judged review findings and required fail-closed handling", "accepted the corrected result"],
        "ai_tool_contribution": ["implemented ledger, verification, and regression tests", "applied review-driven repairs"],
        "evidence_label": "VERIFIED",
    },
    {
        "asset_id": "ASSET-004",
        "title": "Promotion Application Preview",
        "record_kind": "PROJECT_OUTPUT",
        "source_candidate_ids": ["ACH-006"],
        "claim": "The repository contains a non-applying Promotion Application Preview that exposes target files, before-and-after hashes, blockers, validation steps, and rollback anchors before any write authority is granted.",
        "factuality_note": "The preview artifact and tests are verified. It describes a project output created through human-directed scope and safety constraints with AI-assisted implementation.",
        "value": "Lets an operator inspect intended changes and recovery points before granting application authority.",
        "human_contribution": ["defined scope, safety constraints, and acceptance boundaries", "reviewed the non-applying result"],
        "ai_tool_contribution": ["implemented schema, preview logic, fixtures, and tests"],
        "evidence_label": "VERIFIED",
    },
    {
        "asset_id": "ASSET-005",
        "title": "Adaptive Governance Compiler and Audit Remediation",
        "record_kind": "PROJECT_OUTPUT",
        "source_candidate_ids": ["ACH-009", "ACH-010"],
        "claim": "The repository contains an Adaptive Governance Compiler that selects deterministic G0-G4 profiles from exact change context; independent review findings were converted into accepted fail-closed fixes and regression tests.",
        "factuality_note": "The compiler output, review findings, repairs, and tests are verified. The statement does not attribute every discovery or code change directly to the human operator.",
        "value": "Reduces unnecessary ceremony for low-risk work while retaining stronger controls for sensitive or irreversible work.",
        "human_contribution": ["defined the governance model and risk thresholds", "judged review findings material", "required and accepted fail-closed corrections"],
        "ai_tool_contribution": ["implemented compiler and tests", "raised independent review findings", "implemented repairs and reran validation"],
        "evidence_label": "VERIFIED",
    },
    {
        "asset_id": "ASSET-006",
        "title": "Conversation-to-Seed Project Ingestion",
        "record_kind": "PROJECT_OUTPUT",
        "source_candidate_ids": ["ACH-011", "ACH-012"],
        "claim": "A long project conversation was converted into a verified Seed Pack and P0 scope-cut run; the same fingerprint, stale-state, CI, review, and completion pattern has recurred inside RTS, while external reuse remains unobserved.",
        "factuality_note": "The Seed Pack and P0 run are verified. Repetition inside RTS is evidence of a pattern, but effectiveness and reuse outside RTS remain unverified.",
        "value": "Shows how unstructured intent can become a resumable, machine-verifiable project contract without overstating cross-project generality.",
        "human_contribution": ["synthesized the product direction and selected scope", "set privacy and stopping boundaries", "required reconstruction and recovery evidence"],
        "ai_tool_contribution": ["structured documents and validation", "implemented recurring fingerprints, fixtures, and CI checks"],
        "evidence_label": "INFERRED",
    },
]

EXPECTED_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "publication_authorized": False,
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def build_internal_asset_draft() -> dict[str, Any]:
    summary = verify_review_round()
    learning = verify_learning_bundle()
    records = {item["candidate_id"]: item for item in effective_candidate_records()}
    refs = {item["candidate_id"]: item for item in summary["effective_candidates"]}
    if set(records) != set(refs) or len(records) != 12:
        raise ProofEngineError("effective candidate set mismatch")

    assets = []
    covered = []
    for blueprint in ASSET_BLUEPRINTS:
        source_ids = blueprint["source_candidate_ids"]
        if len(source_ids) != len(set(source_ids)):
            raise ProofEngineError("duplicate source candidate inside asset")
        evidence_prs = sorted({pr for candidate_id in source_ids for pr in records[candidate_id]["evidence_prs"]})
        source_candidates = []
        for candidate_id in source_ids:
            ref = refs[candidate_id]
            source_candidates.append({
                "candidate_id": candidate_id,
                "candidate_version": ref["candidate_version"],
                "candidate_fingerprint": ref["candidate_fingerprint"],
                "approval_decision_id": ref["approval_decision_id"],
                "approval_decision_fingerprint": ref["approval_decision_fingerprint"],
            })
        asset = {
            "asset_id": blueprint["asset_id"],
            "candidate_id": blueprint["asset_id"],
            "title": blueprint["title"],
            "claim": blueprint["claim"],
            "record_kind": blueprint["record_kind"],
            "factuality_note": blueprint["factuality_note"],
            "contribution_map": {
                "human": blueprint["human_contribution"],
                "ai_tool": blueprint["ai_tool_contribution"],
                "collaborator": [],
                "attribution_status": "INFERRED",
            },
            "evidence_label": blueprint["evidence_label"],
            "evidence_prs": evidence_prs,
            "public_disclosure": "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL",
            "source_candidates": source_candidates,
            "value_assessment": {
                "audience": "AI-assisted solo developers, solo founders, collaborators, and small teams",
                "evidence_label": "INFERRED",
                "value": blueprint["value"],
            },
            "status": "HUMAN_REVIEW_REQUIRED",
        }
        asset["asset_fingerprint"] = fingerprint(asset)
        preflight = preflight_candidate(asset)
        if preflight["result"] != "PASS":
            raise ProofEngineError(f"learning preflight failed for {asset['asset_id']}")
        assets.append(asset)
        covered.extend(source_ids)

    if len(covered) != 12 or len(set(covered)) != 12 or set(covered) != set(records):
        raise ProofEngineError("internal asset coverage mismatch")

    draft = {
        "schema_version": "PROOF-ENGINE-INTERNAL-ASSET-DRAFT-V1",
        "draft_id": "PROOF-ENGINE-INTERNAL-ASSET-DRAFT-0001",
        "source_fingerprints": {
            "base_run": summary["base_run_fingerprint"],
            "review_summary": summary["summary_fingerprint"],
            "learning_policy": learning["policy"]["policy_fingerprint"],
            "learning_ruleset": learning["ruleset"]["ruleset_fingerprint"],
        },
        "authority": copy.deepcopy(EXPECTED_AUTHORITY),
        "asset_count": 6,
        "assets": assets,
        "coverage": {
            "effective_candidate_count": 12,
            "covered_candidate_ids": sorted(covered),
            "duplicates_allowed": False,
            "all_effective_candidates_covered_once": True,
        },
        "learning_preflight": {
            "mode": "SUGGEST_ONLY",
            "required_result": "PASS",
            "asset_results": [{"asset_id": item["asset_id"], "result": "PASS", "issues": []} for item in assets],
        },
        "review_gate": {
            "state": "HUMAN_REVIEW_REQUIRED",
            "allowed_decisions": ["APPROVE", "REVISE", "REJECT", "REDACT", "EXPIRE"],
            "decisions": [],
        },
        "output": {
            "state": "READY_FOR_INTERNAL_REVIEW",
            "publication_status": "NOT_PUBLISHED",
            "reason": "The six consolidated drafts require a separate human wording and publication decision.",
        },
        "next_action": "Human reviews the six internal asset drafts and records append-only decisions; publication remains a separate gate.",
    }
    draft["draft_fingerprint"] = fingerprint(draft)
    return draft


def verify_internal_asset_draft(
    draft: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = build_internal_asset_draft()
    candidate = expected if draft is None else draft
    _verify_fingerprint(candidate, "draft_fingerprint", "internal asset draft")
    if candidate != expected:
        raise ProofEngineError("internal asset draft does not match deterministic aggregation")
    if candidate.get("authority") != EXPECTED_AUTHORITY:
        raise ProofEngineError("internal asset authority widened")
    if candidate.get("asset_count") != 6:
        raise ProofEngineError("internal asset count mismatch")
    if candidate.get("review_gate", {}).get("state") != "HUMAN_REVIEW_REQUIRED":
        raise ProofEngineError("internal asset review gate mismatch")
    if candidate.get("review_gate", {}).get("decisions") != []:
        raise ProofEngineError("internal asset draft contains manufactured decisions")
    if candidate.get("output") != {
        "state": "READY_FOR_INTERNAL_REVIEW",
        "publication_status": "NOT_PUBLISHED",
        "reason": "The six consolidated drafts require a separate human wording and publication decision.",
    }:
        raise ProofEngineError("internal asset publication boundary mismatch")

    manifest = load(MANIFEST_PATH) if manifest is None else manifest
    _verify_fingerprint(manifest, "manifest_fingerprint", "internal asset manifest")
    if manifest != {
        "schema_version": "PROOF-ENGINE-INTERNAL-ASSET-MANIFEST-V1",
        "manifest_id": "PROOF-ENGINE-INTERNAL-ASSET-MANIFEST-0001",
        "draft_id": candidate["draft_id"],
        "expected_draft_fingerprint": candidate["draft_fingerprint"],
        "asset_count": 6,
        "effective_candidate_count": 12,
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "manifest_fingerprint": manifest["manifest_fingerprint"],
    }:
        raise ProofEngineError("internal asset manifest mismatch")

    checkpoint = load(CHECKPOINT_PATH) if checkpoint is None else checkpoint
    _verify_fingerprint(checkpoint, "checkpoint_fingerprint", "internal asset checkpoint")
    if checkpoint.get("draft_fingerprint") != candidate["draft_fingerprint"]:
        raise ProofEngineError("internal asset checkpoint draft mismatch")
    if checkpoint.get("asset_count") != 6 or checkpoint.get("source_effective_candidate_count") != 12:
        raise ProofEngineError("internal asset checkpoint counts mismatch")
    if checkpoint.get("learning_policy_fingerprint") != candidate["source_fingerprints"]["learning_policy"]:
        raise ProofEngineError("internal asset checkpoint learning-policy mismatch")
    if checkpoint.get("state") != "INTERNAL_ASSET_REVIEW_REQUIRED":
        raise ProofEngineError("internal asset checkpoint state mismatch")
    if checkpoint.get("original_candidate_records_preserved") is not True:
        raise ProofEngineError("internal asset checkpoint does not preserve source records")
    if checkpoint.get("publication_performed") is not False or checkpoint.get("external_actions_performed") is not False:
        raise ProofEngineError("internal asset checkpoint records unauthorized action")
    return candidate
