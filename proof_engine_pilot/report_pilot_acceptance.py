from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, canonical_json, fingerprint, load
from .report_pilot_package_v2 import verify_pilot_package
from .report_template import REQUIRED_SECTIONS

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
REVIEW_DIR = PACKAGE_DIR / "pilot_acceptance_reviews" / "round_0001"
DECISION_PATH = REVIEW_DIR / "decision.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_pilot_acceptance_checkpoint_0018.json"

SOURCE_PACKAGE_CHECKPOINT_FINGERPRINT = "64906aceb1c40a363438696709ee02ba658d278bfb2ee45112c201f10f569a70"
ACCEPTANCE_DECISION_FINGERPRINT = "81af71220d7d93b47fd349b3c51912ac27e4d223500632ca86df5358a803b84a"
PACKAGE_INDEX_FINGERPRINT = "9eced7c395949cb96b20092b2b9ce7a9a25ae70352c0f09e782aa6d8cfdef20a"
PACKAGE_MANIFEST_FINGERPRINT = "e30a88388bfeae449e753df624d6b699404a687bae06fec54d619ab73dd5af2e"
REPORT_JSON_FINGERPRINT = "60c4760c446f90277a4db49e99cedbbc51ef5d1889c3c458cdf0e624bf22bc41"
REPORT_MARKDOWN_FINGERPRINT = "5130e58f79d271a6d6172acf853273f206ec0882dd9a16c599b1651f4dda7c5e"
EVIDENCE_INVENTORY_FINGERPRINT = "4ee9f727bbc20627dbe18221b43445defff169b285b3514db5e8f5da999ca1d1"
ACCEPTANCE_PACKET_FINGERPRINT = "f1a4e4024d831f4fa22ccd12a70244c87641fba2fe4e0ab29914b3aa96d71895"
VERIFICATION_SUMMARY_FINGERPRINT = "d751596c9ff0d70b8bd07536be09191dd3cb274e24e7c6ec1885df3f3c135a42"
ROLLBACK_FINGERPRINT = "9bb6c0505a6eb39aa0f03ff15077b230576d99e87359c7423d9875f752583cc2"
POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT = "d8269e54f35946f750bf07a942c0587530cbdb45d9b47f54d15f936ba07755f9"
SUMMARY_FINGERPRINT = "2390bc5bf244bccc0cf276953ff8378f1af19c36db92eb22f0ab2649cfa07e81"
CHECKPOINT_FINGERPRINT = "c127b8e718a056671a8fbb1d9776e505e23cd416cd680bdeed0821f47f205611"
EXPECTED_CRITERION_IDS = [f"ACC-{number:03d}" for number in range(1, 16)]
AUTOMATED_CRITERIA = {"ACC-001", "ACC-003", "ACC-004", "ACC-010", "ACC-011", "ACC-013"}
EXPECTED_STATE = "INTERNAL_PILOT_PACKAGE_ACCEPTED"
EXPECTED_NEXT_GATE = "HUMAN_INTERNAL_OPERATIONAL_VALIDATION_PLAN_REVIEW_REQUIRED"
EXPECTED_NEXT_ACTION = "Define one bounded internal operational validation plan for a second approved public case, then stop before pricing, outreach, contracting, delivery, or publication."
EXPECTED_HUMAN_AUTHORIZATION = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_CONTINUE_INSTRUCTION",
    "role": "PROJECT_OWNER",
    "instruction": "続ける",
}
EXPECTED_DELEGATED_REVIEW = {
    "type": "AI_ASSISTANT",
    "role": "DELEGATED_POST_BUILD_PACKAGE_REVIEWER",
    "decision_origin": "AI_REVIEW_UNDER_EXPLICIT_HUMAN_CONTINUE_AUTHORIZATION",
}
FALSE_AUTHORITY_FIELDS = (
    "automatic_approval_authorized", "automatic_rewrite_authorized", "contract_authorized",
    "delivery_authorized", "external_execution_authorized", "outreach_authorized",
    "pricing_authorized", "publication_authorized", "target_repository_write_authorized",
)
REQUIRED_RECORD_FIELDS = {
    "candidate_id", "reader_summary", "record_kind", "value_interpretation",
    "evidence_strength", "evidence_prs", "evidence_boundary", "contribution_map", "lineage",
}
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "source_package_checkpoint_fingerprint",
    "acceptance_decision_fingerprint", "package_index_fingerprint", "report_json_fingerprint",
    "report_markdown_fingerprint", "summary_fingerprint", "state", "next_gate",
    "package_accepted", "pricing_performed", "outreach_performed", "contract_action_performed",
    "delivery_performed", "publication_performed", "external_actions_performed",
    "target_repository_writes_performed", "next_action", "checkpoint_fingerprint",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _verify_closed_authority(value: dict[str, Any], label: str) -> None:
    for field in FALSE_AUTHORITY_FIELDS:
        if value.get(field) is not False:
            raise ProofEngineError(f"{label} authority widened: {field}")


def _verify_package_review_evidence(package: dict[str, Any]) -> None:
    report = package["report_json"]
    markdown = package["report_markdown"]
    sections = report.get("sections", {})
    if list(sections) != REQUIRED_SECTIONS:
        raise ProofEngineError("accepted package report sections drifted")
    inventory = sections["evidence_inventory"]
    eligible = {item["number"] for item in inventory["merged_prs"] if item.get("status") == "MERGED"}
    excluded = set(inventory["excluded_unmerged_prs"])
    if len(eligible) != 7 or excluded != {17, 18} or eligible & excluded:
        raise ProofEngineError("accepted package evidence inventory mismatch")
    records = sections["effective_achievement_records"]
    if len(records) != 6:
        raise ProofEngineError("accepted package achievement count mismatch")
    candidate_ids = []
    for record in records:
        refs = set(record.get("evidence_prs", []))
        if not REQUIRED_RECORD_FIELDS <= set(record) or not refs or not refs <= eligible or refs & excluded:
            raise ProofEngineError("accepted package record contract mismatch")
        if not record.get("reader_summary") or not record.get("value_interpretation"):
            raise ProofEngineError("accepted package reader value missing")
        if "not" not in record.get("evidence_boundary", "").lower():
            raise ProofEngineError("accepted package factuality boundary missing")
        candidate_ids.append(record["candidate_id"])
    evidence_inventory = package["evidence_inventory"]
    withheld = sections["withheld_or_unsupported_claims"]
    if withheld != evidence_inventory["withheld_claims"] or len(withheld) != evidence_inventory["withheld_claim_count"]:
        raise ProofEngineError("accepted package withheld claims drifted")
    contribution = sections["human_and_ai_contribution_map"]["records"]
    if [item.get("candidate_id") for item in contribution] != candidate_ids:
        raise ProofEngineError("accepted package contribution identity mismatch")
    for item in contribution:
        if set(item) != {"candidate_id", "human", "ai_tool", "collaborator", "inherited"}:
            raise ProofEngineError("accepted package contribution fields mismatch")
        if not item["human"] or not item["ai_tool"]:
            raise ProofEngineError("accepted package contribution separation incomplete")
    scope = sections["repository_scope"]
    if (
        scope.get("repository") != "nobutakayamauchi/seminar-compass"
        or scope.get("visibility") != "PUBLIC"
        or scope.get("source_mode") != "READ_ONLY_SNAPSHOT"
        or scope.get("snapshot_ref") != "main"
    ):
        raise ProofEngineError("accepted package source scope mismatch")
    review_text = (canonical_json(report) + "\n" + markdown).lower()
    secret_markers = ("ghp_", "github_pat_", "akia", "begin private key", '"password":', '"secret":', '"access_token":')
    if any(marker in review_text for marker in secret_markers):
        raise ProofEngineError("accepted package contains credential-like material")
    reader_markers = (
        "**Verified value:**", "Evidence strength:", "Evidence boundary:",
        "### 6. Human and AI contribution map", "### 7. Withheld or unsupported claims",
        "### 8. Limitations", "### 9. Human review decision",
    )
    if any(marker not in markdown for marker in reader_markers):
        raise ProofEngineError("accepted package reader-facing report incomplete")
    if package["rollback"]["rollback_fingerprint"] != ROLLBACK_FINGERPRINT:
        raise ProofEngineError("accepted package rollback binding mismatch")
    if package["rollback"]["delete_or_rewrite_prior_records"] is not False:
        raise ProofEngineError("accepted package rollback mutates prior records")
    _verify_closed_authority(report["authority"], "accepted report")
    if package["checkpoint"]["checkpoint_fingerprint"] != SOURCE_PACKAGE_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("accepted package checkpoint drift")
    for field in (
        "pricing_performed", "outreach_performed", "contract_action_performed",
        "delivery_performed", "publication_performed", "external_actions_performed",
        "target_repository_writes_performed",
    ):
        if package["checkpoint"].get(field) is not False:
            raise ProofEngineError(f"accepted package exceeded internal scope: {field}")


def verify_acceptance_decision(
    decision: dict[str, Any] | None = None,
    *,
    package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verified_package = verify_pilot_package() if package is None else copy.deepcopy(package)
    _verify_package_review_evidence(verified_package)
    value = load(DECISION_PATH) if decision is None else copy.deepcopy(decision)
    _verify_fingerprint(value, "decision_fingerprint", "pilot package acceptance decision")
    if value.get("decision_fingerprint") != ACCEPTANCE_DECISION_FINGERPRINT:
        raise ProofEngineError("pilot package acceptance decision deterministic mismatch")
    if value.get("schema_version") != "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-DECISION-V1":
        raise ProofEngineError("pilot package acceptance decision schema mismatch")
    if value.get("decision_id") != "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-DECISION-0001":
        raise ProofEngineError("pilot package acceptance decision identity mismatch")
    if value.get("human_authorization") != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("pilot package acceptance lacks human continuation authority")
    if value.get("delegated_review") != EXPECTED_DELEGATED_REVIEW:
        raise ProofEngineError("pilot package acceptance review attribution mismatch")
    if value.get("decision") != "ACCEPT_PILOT_PACKAGE" or value.get("reviewer_identity") != "nobutakayamauchi" or value.get("package_accepted") is not True:
        raise ProofEngineError("pilot package acceptance decision mismatch")
    if value.get("acceptance_scope") != "INTERNAL_SINGLE_CASE_PACKAGE_ONLY":
        raise ProofEngineError("pilot package acceptance scope widened")
    expected_bindings = {
        "reviewed_acceptance_contract_fingerprint": POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT,
        "reviewed_package_fingerprint": PACKAGE_INDEX_FINGERPRINT,
        "reviewed_package_manifest_fingerprint": PACKAGE_MANIFEST_FINGERPRINT,
        "reviewed_package_checkpoint_fingerprint": SOURCE_PACKAGE_CHECKPOINT_FINGERPRINT,
        "reviewed_report_json_fingerprint": REPORT_JSON_FINGERPRINT,
        "reviewed_report_markdown_fingerprint": REPORT_MARKDOWN_FINGERPRINT,
        "reviewed_evidence_inventory_fingerprint": EVIDENCE_INVENTORY_FINGERPRINT,
        "reviewed_acceptance_packet_fingerprint": ACCEPTANCE_PACKET_FINGERPRINT,
        "reviewed_verification_summary_fingerprint": VERIFICATION_SUMMARY_FINGERPRINT,
    }
    for field, expected in expected_bindings.items():
        if value.get(field) != expected:
            raise ProofEngineError(f"pilot package acceptance binding mismatch: {field}")
    if verified_package["package_index"]["package_index_fingerprint"] != PACKAGE_INDEX_FINGERPRINT:
        raise ProofEngineError("pilot package acceptance reviewed package mismatch")
    if verified_package["manifest"]["manifest_fingerprint"] != PACKAGE_MANIFEST_FINGERPRINT:
        raise ProofEngineError("pilot package acceptance reviewed manifest mismatch")
    if verified_package["report_json_fingerprint"] != REPORT_JSON_FINGERPRINT or verified_package["report_markdown_fingerprint"] != REPORT_MARKDOWN_FINGERPRINT:
        raise ProofEngineError("pilot package acceptance reviewed report mismatch")
    results = value.get("criteria_results")
    if (
        not isinstance(results, list)
        or [item.get("criterion_id") for item in results] != EXPECTED_CRITERION_IDS
        or any(item.get("result") != "PASS" for item in results)
        or any(not item.get("evidence") or not item.get("note") for item in results)
    ):
        raise ProofEngineError("pilot package acceptance criteria incomplete")
    if value.get("privacy_confirmed") is not True or value.get("authority_boundary_confirmed") is not True:
        raise ProofEngineError("pilot package acceptance confirmations missing")
    _verify_closed_authority(value, "pilot package acceptance decision")
    if value.get("terminal") != {
        "state": EXPECTED_STATE,
        "next_gate": EXPECTED_NEXT_GATE,
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "next_action": EXPECTED_NEXT_ACTION,
    }:
        raise ProofEngineError("pilot package acceptance terminal boundary mismatch")
    return value


def build_pilot_acceptance_review(
    *, decision: dict[str, Any] | None = None, package: dict[str, Any] | None = None
) -> dict[str, Any]:
    verified_package = verify_pilot_package() if package is None else copy.deepcopy(package)
    verified_decision = verify_acceptance_decision(decision, package=verified_package)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-SUMMARY-V1",
        "summary_id": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-SUMMARY-0001",
        "source_package_checkpoint_fingerprint": SOURCE_PACKAGE_CHECKPOINT_FINGERPRINT,
        "acceptance_decision_fingerprint": verified_decision["decision_fingerprint"],
        "package_index_fingerprint": verified_package["package_index"]["package_index_fingerprint"],
        "report_json_fingerprint": verified_package["report_json_fingerprint"],
        "report_markdown_fingerprint": verified_package["report_markdown_fingerprint"],
        "counts": {
            "criteria": 15, "criteria_passed": 15, "automated_criteria": len(AUTOMATED_CRITERIA),
            "human_or_combined_criteria": 15 - len(AUTOMATED_CRITERIA),
            "artifacts": verified_package["package_index"]["artifact_count"],
            "achievement_records": len(verified_package["report_json"]["sections"]["effective_achievement_records"]),
            "withheld_claims": len(verified_package["report_json"]["sections"]["withheld_or_unsupported_claims"]),
        },
        "state": EXPECTED_STATE, "next_gate": EXPECTED_NEXT_GATE, "package_accepted": True,
        "acceptance_scope": verified_decision["acceptance_scope"], "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED", "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED", "publication_status": "NOT_PUBLISHED",
        "external_actions_performed": False, "next_action": EXPECTED_NEXT_ACTION,
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {"package": verified_package, "decision": verified_decision, "summary": summary}


def render_pilot_acceptance_markdown(bundle: dict[str, Any] | None = None) -> str:
    value = build_pilot_acceptance_review() if bundle is None else bundle
    decision = value["decision"]
    lines = [
        "# Evidence Report Internal Pilot Package — Acceptance Review", "",
        f"Status: {EXPECTED_STATE} / {EXPECTED_NEXT_GATE}", "", "## Decision", "",
        f"- Decision: {decision['decision']}", f"- Reviewer identity: {decision['reviewer_identity']}",
        f"- Scope: {decision['acceptance_scope']}",
        f"- Package fingerprint: `{decision['reviewed_package_fingerprint']}`",
        f"- Report JSON fingerprint: `{decision['reviewed_report_json_fingerprint']}`",
        f"- Report Markdown fingerprint: `{decision['reviewed_report_markdown_fingerprint']}`",
        "", "## Acceptance criteria", "",
    ]
    lines.extend(f"- {item['criterion_id']}: {item['result']} — {item['note']}" for item in decision["criteria_results"])
    lines.extend([
        "", "## Authority boundary", "", "- Package accepted for internal single-case use: true",
        "- Pricing authorized: false", "- Outreach authorized: false", "- Contract authorized: false",
        "- Delivery authorized: false", "- Publication authorized: false",
        "- External execution authorized: false", "- Automatic approval authorized: false",
        "- Automatic rewriting authorized: false", "- Target repository writes authorized: false",
        "", "## Next human gate", "", EXPECTED_NEXT_ACTION, "",
    ])
    return "\n".join(lines)


def verify_pilot_acceptance(
    *, decision: dict[str, Any] | None = None, checkpoint: dict[str, Any] | None = None,
    package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_pilot_acceptance_review(decision=decision, package=package)
    summary = bundle["summary"]
    _verify_fingerprint(summary, "summary_fingerprint", "pilot package acceptance summary")
    if summary["summary_fingerprint"] != SUMMARY_FINGERPRINT:
        raise ProofEngineError("pilot package acceptance summary deterministic mismatch")
    if summary["counts"] != {
        "criteria": 15, "criteria_passed": 15, "automated_criteria": 6,
        "human_or_combined_criteria": 9, "artifacts": 7, "achievement_records": 6,
        "withheld_claims": 0,
    }:
        raise ProofEngineError("pilot package acceptance counts mismatch")
    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("pilot package acceptance checkpoint fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "pilot package acceptance checkpoint")
    expected = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-CHECKPOINT-0018",
        "source_package_checkpoint_fingerprint": SOURCE_PACKAGE_CHECKPOINT_FINGERPRINT,
        "acceptance_decision_fingerprint": ACCEPTANCE_DECISION_FINGERPRINT,
        "package_index_fingerprint": PACKAGE_INDEX_FINGERPRINT,
        "report_json_fingerprint": REPORT_JSON_FINGERPRINT,
        "report_markdown_fingerprint": REPORT_MARKDOWN_FINGERPRINT,
        "summary_fingerprint": SUMMARY_FINGERPRINT, "state": EXPECTED_STATE,
        "next_gate": EXPECTED_NEXT_GATE, "package_accepted": True, "next_action": EXPECTED_NEXT_ACTION,
    }
    for field, expected_value in expected.items():
        if cp.get(field) != expected_value:
            raise ProofEngineError(f"pilot package acceptance checkpoint mismatch: {field}")
    for field in (
        "pricing_performed", "outreach_performed", "contract_action_performed", "delivery_performed",
        "publication_performed", "external_actions_performed", "target_repository_writes_performed",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"pilot package acceptance exceeded boundary: {field}")
    if cp["checkpoint_fingerprint"] != CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("pilot package acceptance checkpoint deterministic mismatch")
    markdown = render_pilot_acceptance_markdown(bundle)
    return {**bundle, "checkpoint": cp, "markdown": markdown, "markdown_fingerprint": fingerprint(markdown)}
