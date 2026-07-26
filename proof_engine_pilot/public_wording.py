from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .asset_review import verify_asset_review
from .core import ProofEngineError, fingerprint, load
from .learning import preflight_candidate

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
MANIFEST_PATH = PACKAGE_DIR / "wording" / "round_0001" / "public_wording_manifest.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "public_wording_checkpoint_0006.json"

EXPECTED_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "publication_authorized": False,
}

WORDING_BLUEPRINTS = [
    {
        "wording_id": "WORDING-001",
        "asset_id": "ASSET-001",
        "headline": "A governed loop that turns project intent into a verifiable, resumable workflow",
        "summary": "RTS includes a deterministic, repository-local loop that ingests a Seed contract, links eight verification stages, records checkpoints, and stops at explicit human gates. The current implementation is read-only and does not grant unattended execution authority.",
        "why_it_matters": "Complex AI-assisted projects can preserve scope, evidence, review state, and recovery points instead of depending on a single uninterrupted conversation.",
        "proof_note": "Verified through committed Seed, run, lifecycle, checkpoint, resume, completion, and CI records in RTS.",
        "limit_note": "Demonstrated inside RTS as a governed project output. Production autonomy and effectiveness outside this repository are not established.",
        "audiences": ["AI-assisted solo developers", "solo founders", "small technical teams", "project evaluators"],
    },
    {
        "wording_id": "WORDING-002",
        "asset_id": "ASSET-002",
        "headline": "One active change, with human approval at consequential transitions",
        "summary": "During the governed pilot, RTS enforced WIP=1 across selection, implementation, verification, and completion, while explicit human decisions controlled consequential transitions.",
        "why_it_matters": "A single active work item reduces parallel scope drift and makes it clearer which change is being evaluated, approved, completed, or stopped.",
        "proof_note": "Verified in the lifecycle and approval records for the governed pilot.",
        "limit_note": "This is a process result observed in the RTS pilot, not evidence that the same policy is optimal for every team or organization.",
        "audiences": ["solo developers", "project leads", "small teams", "AI workflow designers"],
    },
    {
        "wording_id": "WORDING-003",
        "asset_id": "ASSET-003",
        "headline": "Append-only human decisions with fail-closed integrity checks",
        "summary": "RTS includes a Human Review Ledger that preserves decisions as an append-only chain and rejects stale expiry, proposer mismatch, unmanifested decision files, and other invalid review states.",
        "why_it_matters": "The system can distinguish a recorded human decision from stale, altered, or unregistered material before any later application step is considered.",
        "proof_note": "Verified through ledger fixtures, deterministic fingerprints, integrity checks, regression tests, and accepted review corrections.",
        "limit_note": "The ledger records and verifies review evidence; it does not itself authorize publication, contracts, external execution, or repository writes.",
        "audiences": ["AI system builders", "reviewers", "auditors", "small technical teams"],
    },
    {
        "wording_id": "WORDING-004",
        "asset_id": "ASSET-004",
        "headline": "Inspect intended changes and rollback points before granting write authority",
        "summary": "RTS includes a non-applying Promotion Application Preview that exposes target files, before-and-after hashes, blockers, validation steps, and rollback anchors before any write authority is granted.",
        "why_it_matters": "An operator can examine what would change, how it would be checked, and where recovery would begin without applying the change.",
        "proof_note": "Verified through the committed preview schema, deterministic fixtures, parser-based inspection, safety checks, and CI tests.",
        "limit_note": "The preview is intentionally non-applying. It does not write to a target repository or approve the proposed change.",
        "audiences": ["repository maintainers", "AI-assisted developers", "reviewers", "release operators"],
    },
    {
        "wording_id": "WORDING-005",
        "asset_id": "ASSET-005",
        "headline": "Governance depth selected from the exact risk and authority context",
        "summary": "RTS includes an Adaptive Governance Compiler that deterministically selects G0-G4 governance profiles from the requested action, affected paths, reversibility, and authority context. Independent review findings were incorporated as fail-closed fixes and regression tests.",
        "why_it_matters": "Low-risk work can avoid unnecessary ceremony while sensitive or irreversible work retains stronger review, rollback, and testing requirements.",
        "proof_note": "Verified through deterministic compilation, context-bound verification, fixed profiles, independent review findings, accepted repairs, and full regression tests.",
        "limit_note": "The compiler has been tested inside RTS. It does not prove universal risk classification quality or replace human judgment for consequential decisions.",
        "audiences": ["AI workflow designers", "technical leads", "repository maintainers", "governance reviewers"],
    },
    {
        "wording_id": "WORDING-006",
        "asset_id": "ASSET-006",
        "headline": "From a long project conversation to a machine-verifiable Seed and scope decision",
        "summary": "A long project conversation was converted into a verified Seed Pack, ingested by the governed loop, and reduced to a bounded P0 scope decision with explicit future branches and stopping conditions.",
        "why_it_matters": "Unstructured intent can become a resumable project contract that preserves goals, constraints, exclusions, privacy boundaries, and the next human decision.",
        "proof_note": "The Seed Pack, manifest, scope profiles, P0 run, checkpoint, and related CI records are verified in RTS.",
        "limit_note": "The ingestion result is verified for this case. Similar internal patterns recur inside RTS, but effectiveness and reuse outside RTS remain unobserved.",
        "audiences": ["solo founders", "AI-assisted developers", "project planners", "collaborators and evaluators"],
    },
]


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def build_public_wording_draft() -> dict[str, Any]:
    review = verify_asset_review()
    source_assets = {item["asset_id"]: item for item in review["draft"]["assets"]}
    approvals = {item["asset_id"]: item for item in review["summary"]["effective_assets"]}
    if set(source_assets) != set(approvals) or len(source_assets) != 6:
        raise ProofEngineError("public wording source set mismatch")

    wordings = []
    covered = []
    for blueprint in WORDING_BLUEPRINTS:
        asset_id = blueprint["asset_id"]
        if asset_id not in source_assets or asset_id in covered:
            raise ProofEngineError("public wording source asset mismatch")
        source = source_assets[asset_id]
        approval = approvals[asset_id]
        if approval["asset_fingerprint"] != source["asset_fingerprint"]:
            raise ProofEngineError("public wording approval/source mismatch")

        wording = {
            "wording_id": blueprint["wording_id"],
            "candidate_id": blueprint["wording_id"],
            "source_asset": {
                "asset_id": asset_id,
                "asset_fingerprint": source["asset_fingerprint"],
                "approval_decision_id": approval["decision_id"],
                "approval_decision_fingerprint": approval["decision_fingerprint"],
            },
            "language": "en",
            "headline": blueprint["headline"],
            "claim": blueprint["summary"],
            "summary": blueprint["summary"],
            "why_it_matters": blueprint["why_it_matters"],
            "proof_note": blueprint["proof_note"],
            "record_kind": source["record_kind"],
            "factuality_note": blueprint["limit_note"],
            "contribution_map": copy.deepcopy(source["contribution_map"]),
            "evidence_label": source["evidence_label"],
            "evidence_prs": copy.deepcopy(source["evidence_prs"]),
            "audiences": copy.deepcopy(blueprint["audiences"]),
            "public_disclosure": "INTERNAL_UNTIL_SEPARATE_PUBLICATION_APPROVAL",
            "publication_status": "NOT_PUBLISHED",
            "review_status": "PUBLICATION_REVIEW_REQUIRED",
        }
        wording["wording_fingerprint"] = fingerprint(wording)
        preflight = preflight_candidate(wording)
        if preflight["result"] != "PASS":
            raise ProofEngineError(f"public wording learning preflight failed: {wording['wording_id']}")
        wordings.append(wording)
        covered.append(asset_id)

    if covered != [f"ASSET-{index:03d}" for index in range(1, 7)]:
        raise ProofEngineError("public wording source order mismatch")

    source_fingerprints = review["draft"]["source_fingerprints"]
    draft = {
        "schema_version": "PROOF-ENGINE-PUBLIC-WORDING-DRAFT-V1",
        "draft_id": "PROOF-ENGINE-PUBLIC-WORDING-DRAFT-0001",
        "source_fingerprints": {
            "internal_asset_draft": review["draft"]["draft_fingerprint"],
            "asset_review_summary": review["summary"]["summary_fingerprint"],
            "asset_review_index": review["summary"]["decision_index_fingerprint"],
            "learning_policy": source_fingerprints["learning_policy"],
            "learning_ruleset": source_fingerprints["learning_ruleset"],
        },
        "authority": copy.deepcopy(EXPECTED_AUTHORITY),
        "language": "en",
        "wording_count": 6,
        "wordings": wordings,
        "coverage": {
            "approved_internal_asset_count": 6,
            "covered_asset_ids": covered,
            "duplicates_allowed": False,
            "all_approved_assets_covered_once": True,
        },
        "learning_preflight": {
            "mode": "SUGGEST_ONLY",
            "required_result": "PASS",
            "wording_results": [
                {"wording_id": item["wording_id"], "result": "PASS", "issues": []}
                for item in wordings
            ],
        },
        "review_gate": {
            "state": "PUBLICATION_REVIEW_REQUIRED",
            "allowed_decisions": ["APPROVE_FOR_PUBLICATION", "REVISE", "REJECT", "REDACT", "EXPIRE"],
            "decisions": [],
        },
        "output": {
            "state": "READY_FOR_PUBLICATION_REVIEW",
            "publication_status": "NOT_PUBLISHED",
            "reason": "Audience-facing wording exists, but publication requires a separate explicit human decision.",
        },
        "next_action": "Human reviews the six audience-facing drafts, records append-only publication decisions, and separately authorizes any actual release.",
    }
    draft["draft_fingerprint"] = fingerprint(draft)
    return draft


def render_public_wording_markdown(draft: dict[str, Any] | None = None) -> str:
    value = build_public_wording_draft() if draft is None else draft
    lines = [
        "# RTS Evidence-Backed Project Outputs — Publication Draft",
        "",
        "> Status: NOT PUBLISHED. These six drafts require a separate human publication decision.",
        "",
    ]
    for index, wording in enumerate(value["wordings"], start=1):
        lines.extend([
            f"## {index}. {wording['headline']}",
            "",
            wording["summary"],
            "",
            f"**Why it matters:** {wording['why_it_matters']}",
            "",
            f"**Evidence:** {wording['proof_note']} PR references: "
            + ", ".join(f"#{number}" for number in wording["evidence_prs"])
            + ".",
            "",
            "**Human role:** " + "; ".join(wording["contribution_map"]["human"]) + ".",
            "",
            "**AI-tool role:** " + "; ".join(wording["contribution_map"]["ai_tool"]) + ".",
            "",
            f"**Limits:** {wording['factuality_note']}",
            "",
        ])
    lines.extend([
        "---",
        "",
        "Publication, outreach, contracts, external execution, automatic rewriting, and automatic approval remain unauthorized.",
        "",
    ])
    return "\n".join(lines)


def verify_public_wording_draft(
    draft: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = build_public_wording_draft()
    candidate = expected if draft is None else copy.deepcopy(draft)
    _verify_fingerprint(candidate, "draft_fingerprint", "public wording draft")
    if candidate != expected:
        raise ProofEngineError("public wording draft does not match deterministic aggregation")
    if candidate.get("authority") != EXPECTED_AUTHORITY:
        raise ProofEngineError("public wording authority widened")
    if candidate.get("wording_count") != 6 or candidate.get("language") != "en":
        raise ProofEngineError("public wording count or language mismatch")
    if candidate.get("coverage") != {
        "approved_internal_asset_count": 6,
        "covered_asset_ids": [f"ASSET-{index:03d}" for index in range(1, 7)],
        "duplicates_allowed": False,
        "all_approved_assets_covered_once": True,
    }:
        raise ProofEngineError("public wording coverage mismatch")
    if candidate.get("review_gate") != {
        "state": "PUBLICATION_REVIEW_REQUIRED",
        "allowed_decisions": ["APPROVE_FOR_PUBLICATION", "REVISE", "REJECT", "REDACT", "EXPIRE"],
        "decisions": [],
    }:
        raise ProofEngineError("public wording review gate mismatch")
    if candidate.get("output") != {
        "state": "READY_FOR_PUBLICATION_REVIEW",
        "publication_status": "NOT_PUBLISHED",
        "reason": "Audience-facing wording exists, but publication requires a separate explicit human decision.",
    }:
        raise ProofEngineError("public wording publication boundary mismatch")
    for wording in candidate["wordings"]:
        _verify_fingerprint(wording, "wording_fingerprint", f"public wording {wording.get('wording_id')}")
        if wording.get("publication_status") != "NOT_PUBLISHED" or wording.get("review_status") != "PUBLICATION_REVIEW_REQUIRED":
            raise ProofEngineError("public wording item publication boundary mismatch")
        if preflight_candidate(wording)["result"] != "PASS":
            raise ProofEngineError("public wording item no longer passes learning preflight")

    markdown = render_public_wording_markdown(candidate)
    markdown_fingerprint = fingerprint(markdown)

    manifest = load(MANIFEST_PATH) if manifest is None else copy.deepcopy(manifest)
    _verify_fingerprint(manifest, "manifest_fingerprint", "public wording manifest")
    if manifest != {
        "schema_version": "PROOF-ENGINE-PUBLIC-WORDING-MANIFEST-V1",
        "manifest_id": "PROOF-ENGINE-PUBLIC-WORDING-MANIFEST-0001",
        "draft_id": candidate["draft_id"],
        "expected_draft_fingerprint": candidate["draft_fingerprint"],
        "expected_markdown_fingerprint": markdown_fingerprint,
        "wording_count": 6,
        "review_state": "PUBLICATION_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "manifest_fingerprint": manifest["manifest_fingerprint"],
    }:
        raise ProofEngineError("public wording manifest mismatch")

    checkpoint = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    _verify_fingerprint(checkpoint, "checkpoint_fingerprint", "public wording checkpoint")
    links = {
        "source_asset_review_summary_fingerprint": candidate["source_fingerprints"]["asset_review_summary"],
        "draft_fingerprint": candidate["draft_fingerprint"],
        "markdown_fingerprint": markdown_fingerprint,
        "manifest_fingerprint": manifest["manifest_fingerprint"],
    }
    for field, expected_value in links.items():
        if checkpoint.get(field) != expected_value:
            raise ProofEngineError(f"public wording checkpoint mismatch: {field}")
    if checkpoint.get("schema_version") != "PROOF-ENGINE-PUBLIC-WORDING-CHECKPOINT-V1" or checkpoint.get("checkpoint_id") != "PROOF-ENGINE-PUBLIC-WORDING-CHECKPOINT-0006":
        raise ProofEngineError("public wording checkpoint identity mismatch")
    if checkpoint.get("state") != "PUBLICATION_REVIEW_REQUIRED" or checkpoint.get("wording_count") != 6:
        raise ProofEngineError("public wording checkpoint state mismatch")
    if checkpoint.get("original_internal_assets_preserved") is not True:
        raise ProofEngineError("public wording source assets were not preserved")
    if checkpoint.get("publication_performed") is not False or checkpoint.get("external_actions_performed") is not False:
        raise ProofEngineError("public wording checkpoint records unauthorized action")

    return {
        "draft": candidate,
        "markdown": markdown,
        "markdown_fingerprint": markdown_fingerprint,
        "manifest": manifest,
        "checkpoint": checkpoint,
    }
