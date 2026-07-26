from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .publication_review import effective_wording_records, verify_publication_review

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
AUTHORIZATION_PATH = PACKAGE_DIR / "releases" / "round_0001" / "release_authorization.json"
DOCUMENT_PATH = ROOT / "docs" / "portfolio" / "RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "publication_release_checkpoint_0008.json"

AUTHORIZATION_SCHEMA = "PROOF-ENGINE-PUBLICATION-RELEASE-AUTHORIZATION-V1"
AUTHORIZATION_ID = "PROOF-ENGINE-PUBLICATION-RELEASE-AUTHORIZATION-0001"
CHECKPOINT_SCHEMA = "PROOF-ENGINE-PUBLICATION-RELEASE-CHECKPOINT-V1"
CHECKPOINT_ID = "PROOF-ENGINE-PUBLICATION-RELEASE-CHECKPOINT-0008"
ROUND_ID = "PROOF-ENGINE-PUBLICATION-REVIEW-ROUND-0001"
PUBLIC_PATH = "docs/portfolio/RTS_EVIDENCE_BACKED_PROJECT_OUTPUTS.md"
EXPECTED_DOCUMENT_FINGERPRINT = "682ec3d73373ea2228c4d270b5ca74bec8c59050781e7322dbfcfba1c9b50369"
EXPECTED_AUTHORIZATION_FINGERPRINT = "51fc24ed079a834102da79be8a6ec8381ee6b1c971e05e3fc72815681a298f91"

EXPECTED_HUMAN_AUTHORIZATION = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_RELEASE_AUTHORIZATION",
    "role": "PROJECT_OWNER",
    "instruction": "じゃとりあえずこれもやろっか。",
}
EXPECTED_AUTHORITY = {
    "publication_authorized": True,
    "target_repository_write_authorized": True,
    "social_posting_authorized": False,
    "direct_outreach_authorized": False,
    "contract_authorized": False,
    "provider_execution_authorized": False,
    "adjacent_repository_write_authorized": False,
    "automatic_republication_authorized": False,
}
EXPECTED_SURFACE = {
    "repository": "nobutakayamauchi/RTS",
    "repository_visibility": "PUBLIC",
    "target_branch": "main",
    "exact_path": PUBLIC_PATH,
    "publication_mode": "REPOSITORY_DOCUMENT_ONLY",
    "document_fingerprint": EXPECTED_DOCUMENT_FINGERPRINT,
    "release_timing": "IMMEDIATE_ON_MERGE",
    "root_readme_link_authorized": False,
}
EXPECTED_SOURCE = {
    "publication_review_contract_fingerprint": "e66845480c8b82a6c0d6d35e0039e20c464d1f6a41e880e5304ec4e59c46f383",
    "source_draft_fingerprint": "91a21a9eb8119fc474d2f6a1c3429ae265c7c1997066f8148e2a612ef6167782",
    "effective_wording_count": 6,
    "revision_count": 3,
}
EXPECTED_RESTRICTIONS = {
    "allowed_publication_paths": [PUBLIC_PATH],
    "release_metadata_may_be_recorded_in_repository": True,
    "content_must_match_authorized_fingerprint": True,
    "publication_on_any_other_surface_requires_new_human_authorization": True,
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _pr_links(numbers: list[int]) -> str:
    links = [f"[#{number}](https://github.com/nobutakayamauchi/RTS/pull/{number})" for number in numbers]
    if len(links) == 1:
        return links[0]
    if len(links) == 2:
        return " and ".join(links)
    return ", ".join(links[:-1]) + ", and " + links[-1]


def render_release_markdown(records: list[dict[str, Any]] | None = None) -> str:
    wordings = effective_wording_records() if records is None else records
    if len(wordings) != 6 or [item["wording_id"] for item in wordings] != [f"WORDING-{index:03d}" for index in range(1, 7)]:
        raise ProofEngineError("release wording set mismatch")

    lines = [
        "# RTS Evidence-Backed Project Outputs",
        "",
        "This document summarizes six repository-observed outputs from the RTS governed pilot. Each statement is bounded by committed evidence, separates human direction from AI-tool assistance, and states what has not yet been established.",
        "",
    ]
    for index, wording in enumerate(wordings, start=1):
        evidence_label = "PR" if len(wording["evidence_prs"]) == 1 else "PRs"
        lines.extend([
            f"## {index}. {wording['headline']}",
            "",
            wording["summary"],
            "",
            f"**Why it matters:** {wording['why_it_matters']}",
            "",
            f"**Evidence:** {wording['proof_note']} {evidence_label}: {_pr_links(wording['evidence_prs'])}.",
            "",
            "**Human role:** " + "; ".join(wording["contribution_map"]["human"]).capitalize() + ".",
            "",
            "**AI-tool role:** " + "; ".join(wording["contribution_map"]["ai_tool"]).capitalize() + ".",
            "",
            f"**Limits:** {wording['factuality_note']}",
            "",
        ])
    lines.extend([
        "---",
        "",
        "This publication is limited to this repository document. It does not authorize social posting, direct outreach, contracting, external execution, or publication on another surface.",
        "",
    ])
    return "\n".join(lines)


def verify_release_authorization(value: dict[str, Any] | None = None) -> dict[str, Any]:
    authorization = load(AUTHORIZATION_PATH) if value is None else copy.deepcopy(value)
    authorization_fp = _verify_fingerprint(authorization, "authorization_fingerprint", "publication release authorization")
    if authorization_fp != EXPECTED_AUTHORIZATION_FINGERPRINT:
        raise ProofEngineError("publication release authorization fingerprint is not approved")
    if authorization.get("schema_version") != AUTHORIZATION_SCHEMA or authorization.get("authorization_id") != AUTHORIZATION_ID:
        raise ProofEngineError("publication release authorization identity mismatch")
    if authorization.get("review_round_id") != ROUND_ID or authorization.get("decision") != "AUTHORIZE_RELEASE":
        raise ProofEngineError("publication release decision mismatch")
    if authorization.get("human_authorization") != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("publication release is not bound to explicit human authorization")
    if authorization.get("source") != EXPECTED_SOURCE:
        raise ProofEngineError("publication release source mismatch")
    if authorization.get("release_surface") != EXPECTED_SURFACE:
        raise ProofEngineError("publication release surface mismatch")
    if authorization.get("authority") != EXPECTED_AUTHORITY:
        raise ProofEngineError("publication release authority widened")
    if authorization.get("restrictions") != EXPECTED_RESTRICTIONS:
        raise ProofEngineError("publication release restrictions mismatch")
    return authorization


def verify_publication_release(
    *,
    authorization: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    document_text: str | None = None,
) -> dict[str, Any]:
    review = verify_publication_review()
    if review["summary"].get("review_state") != "ALL_WORDINGS_APPROVED_FOR_RELEASE_GATE":
        raise ProofEngineError("publication release review gate not satisfied")
    if review["summary"].get("release_authorization_status") != "REQUIRED":
        raise ProofEngineError("publication release source state mismatch")

    auth = verify_release_authorization(authorization)
    expected_document = render_release_markdown(effective_wording_records(review))
    actual_document = DOCUMENT_PATH.read_text(encoding="utf-8") if document_text is None else document_text
    if actual_document != expected_document:
        raise ProofEngineError("published document does not match the approved effective wording set")
    document_fp = fingerprint(actual_document)
    if document_fp != EXPECTED_DOCUMENT_FINGERPRINT or document_fp != auth["release_surface"]["document_fingerprint"]:
        raise ProofEngineError("published document fingerprint mismatch")

    checkpoint_value = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    _verify_fingerprint(checkpoint_value, "checkpoint_fingerprint", "publication release checkpoint")
    if checkpoint_value.get("schema_version") != CHECKPOINT_SCHEMA or checkpoint_value.get("checkpoint_id") != CHECKPOINT_ID:
        raise ProofEngineError("publication release checkpoint identity mismatch")
    expected_links = {
        "release_authorization_fingerprint": auth["authorization_fingerprint"],
        "source_review_round_id": ROUND_ID,
        "document_path": PUBLIC_PATH,
        "document_fingerprint": document_fp,
        "published_wording_count": 6,
        "repository_visibility": "PUBLIC",
        "target_branch": "main",
    }
    for field, expected in expected_links.items():
        if checkpoint_value.get(field) != expected:
            raise ProofEngineError(f"publication release checkpoint mismatch: {field}")
    if checkpoint_value.get("state") != "PUBLISHED_TO_AUTHORIZED_REPOSITORY_DOCUMENT":
        raise ProofEngineError("publication release checkpoint state mismatch")
    if checkpoint_value.get("publication_performed") is not True or checkpoint_value.get("external_actions_performed") is not True:
        raise ProofEngineError("publication release checkpoint does not record publication")
    if checkpoint_value.get("original_wording_drafts_preserved") is not True or checkpoint_value.get("release_scope_respected") is not True:
        raise ProofEngineError("publication release preservation or scope mismatch")
    for field in (
        "social_posting_performed",
        "direct_outreach_performed",
        "contract_action_performed",
        "adjacent_repository_write_performed",
    ):
        if checkpoint_value.get(field) is not False:
            raise ProofEngineError(f"publication release exceeded scope: {field}")

    return {
        "authorization": auth,
        "document": actual_document,
        "document_fingerprint": document_fp,
        "checkpoint": checkpoint_value,
        "effective_wordings": review["summary"]["effective_wordings"],
    }
