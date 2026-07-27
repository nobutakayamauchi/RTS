from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_template_review import REVIEW_CRITERIA, verify_report_template_review

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
DECISION_DIR = PACKAGE_DIR / "productization_reviews" / "round_0001"
DECISION_PATH = DECISION_DIR / "decision.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_productization_checkpoint_0015.json"

SOURCE_REVIEW_CHECKPOINT_FINGERPRINT = "154bad31a6da7bcee696a796085499cddfbceb7ef8839552702c0a5b6f6c019f"
REVIEWED_TEMPLATE_FINGERPRINT = "579d086788e636317cd61392fc3af97de468ff27c9ba478e962a973bd91ad4f6"
REVIEWED_PACK_FINGERPRINT = "c95360f6ef1376914261eac574757ceb99f7f25c998b7be5752436200375f1bb"
REVIEWED_REPORT_FINGERPRINTS = {'PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-2': 'a644d21ccf98cbdadf810c2e5294776d22376995a69c5abd76b29e4066e864dc', 'PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-3': '48ef70f2a24842851fbfd2c19e30b360835a1a5248181090a91694dbd9ac395e', 'PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-4': 'd9b2b656fff3961ea249519776604d316a58b90d8f7f7dd29151ef969a63496c'}
DECISION_FINGERPRINT = "010f5a2d39e712b181ed227fe62cdb61680db890898a43994543833e3c27efd9"
SUMMARY_FINGERPRINT = "a12da055d6dfab92f5c6fe90ec10c604852282325006eb12b9cfdb75370d0339"

EXPECTED_HUMAN_AUTHORIZATION = {'type': 'HUMAN', 'identity': 'nobutakayamauchi', 'identity_source': 'CURRENT_CHAT_EXPLICIT_RESUME_INSTRUCTION', 'role': 'PROJECT_OWNER', 'instruction': '前回のチャットが長すぎる出て、作業が中断しているため、その中断している作業の続きからお願いします。'}
EXPECTED_SCOPE = "INTERNAL_PRODUCTIZATION_SPECIFICATION_ONLY"
EXPECTED_STATE = "APPROVED_FOR_INTERNAL_PRODUCTIZATION_SPECIFICATION"

DECISION_FIELDS = {
    "schema_version",
    "decision_id",
    "human_authorization",
    "decision",
    "reviewer_identity",
    "source_review_checkpoint_fingerprint",
    "reviewed_template_fingerprint",
    "reviewed_pack_fingerprint",
    "reviewed_report_fingerprints",
    "criteria_results",
    "factuality_confirmed",
    "privacy_boundary_confirmed",
    "contribution_separation_confirmed",
    "productization_scope",
    "pricing_authorized",
    "delivery_authorized",
    "publication_authorized",
    "outreach_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "target_repository_write_authorized",
    "automatic_approval_authorized",
    "automatic_rewrite_authorized",
    "next_stage",
    "decision_fingerprint",
}
FALSE_AUTHORITY_FIELDS = {
    "pricing_authorized",
    "delivery_authorized",
    "publication_authorized",
    "outreach_authorized",
    "contract_authorized",
    "external_execution_authorized",
    "target_repository_write_authorized",
    "automatic_approval_authorized",
    "automatic_rewrite_authorized",
}
CHECKPOINT_FIELDS = {
    "schema_version",
    "checkpoint_id",
    "source_review_checkpoint_fingerprint",
    "decision_fingerprint",
    "summary_fingerprint",
    "reviewed_template_fingerprint",
    "reviewed_pack_fingerprint",
    "reviewed_report_fingerprints",
    "decision",
    "productization_scope",
    "state",
    "pricing_performed",
    "delivery_performed",
    "publication_performed",
    "outreach_performed",
    "contract_action_performed",
    "external_actions_performed",
    "target_repository_writes_performed",
    "next_action",
    "checkpoint_fingerprint",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def verify_productization_decision(decision: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(DECISION_PATH) if decision is None else copy.deepcopy(decision)
    if set(value) != DECISION_FIELDS:
        raise ProofEngineError("productization decision schema fields mismatch")
    _verify_fingerprint(value, "decision_fingerprint", "productization decision")
    if value["decision_fingerprint"] != DECISION_FINGERPRINT:
        raise ProofEngineError("productization decision deterministic fingerprint mismatch")
    if value["schema_version"] != "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCTIZATION-DECISION-V1":
        raise ProofEngineError("productization decision schema mismatch")
    if value["decision_id"] != "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCTIZATION-DECISION-0001":
        raise ProofEngineError("productization decision identity mismatch")
    if value["human_authorization"] != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("productization decision is not bound to the explicit resume instruction")
    if value["decision"] != "APPROVE_FOR_PRODUCTIZATION":
        raise ProofEngineError("productization decision is not approved")
    if value["reviewer_identity"] != "nobutakayamauchi":
        raise ProofEngineError("productization reviewer identity mismatch")
    if value["source_review_checkpoint_fingerprint"] != SOURCE_REVIEW_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("productization decision source checkpoint mismatch")
    if value["reviewed_template_fingerprint"] != REVIEWED_TEMPLATE_FINGERPRINT:
        raise ProofEngineError("productization decision template mismatch")
    if value["reviewed_pack_fingerprint"] != REVIEWED_PACK_FINGERPRINT:
        raise ProofEngineError("productization decision pack mismatch")
    if value["reviewed_report_fingerprints"] != REVIEWED_REPORT_FINGERPRINTS:
        raise ProofEngineError("productization decision report fingerprints mismatch")
    expected_results = [{"criterion": item, "result": "PASS"} for item in REVIEW_CRITERIA]
    if value["criteria_results"] != expected_results:
        raise ProofEngineError("productization decision criteria mismatch")
    for field in (
        "factuality_confirmed",
        "privacy_boundary_confirmed",
        "contribution_separation_confirmed",
    ):
        if value[field] is not True:
            raise ProofEngineError(f"productization decision confirmation missing: {field}")
    if value["productization_scope"] != EXPECTED_SCOPE:
        raise ProofEngineError("productization decision scope widened")
    if value["next_stage"] != "INTERNAL_PRODUCTIZATION_SPECIFICATION":
        raise ProofEngineError("productization decision next stage mismatch")
    for field in FALSE_AUTHORITY_FIELDS:
        if value[field] is not False:
            raise ProofEngineError(f"productization decision authority widened: {field}")
    return value


def _source_links(source: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    report_links = {
        item["report_id"]: item["report_fingerprint"]
        for item in source["pack"]["reports"]
    }
    return report_links, {
        "source_review_checkpoint_fingerprint": source["checkpoint"]["checkpoint_fingerprint"],
        "reviewed_template_fingerprint": source["template"]["template_fingerprint"],
        "reviewed_pack_fingerprint": source["pack"]["pack_fingerprint"],
        "reviewed_report_fingerprints": report_links,
    }


def build_productization_review(
    decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = verify_report_template_review()
    reviewed_reports, source_links = _source_links(source)
    expected_links = {
        "source_review_checkpoint_fingerprint": SOURCE_REVIEW_CHECKPOINT_FINGERPRINT,
        "reviewed_template_fingerprint": REVIEWED_TEMPLATE_FINGERPRINT,
        "reviewed_pack_fingerprint": REVIEWED_PACK_FINGERPRINT,
        "reviewed_report_fingerprints": REVIEWED_REPORT_FINGERPRINTS,
    }
    if source_links != expected_links:
        raise ProofEngineError("productization review source drift")
    if reviewed_reports != REVIEWED_REPORT_FINGERPRINTS:
        raise ProofEngineError("productization review report order or fingerprint drift")

    approved = verify_productization_decision(decision)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCTIZATION-SUMMARY-V1",
        "review_id": "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCTIZATION-REVIEW-0001",
        "decision_fingerprint": approved["decision_fingerprint"],
        "source_review_checkpoint_fingerprint": approved["source_review_checkpoint_fingerprint"],
        "reviewed_template_fingerprint": approved["reviewed_template_fingerprint"],
        "reviewed_pack_fingerprint": approved["reviewed_pack_fingerprint"],
        "reviewed_report_fingerprints": copy.deepcopy(approved["reviewed_report_fingerprints"]),
        "decision": approved["decision"],
        "productization_scope": approved["productization_scope"],
        "criteria": {item["criterion"]: item["result"] for item in approved["criteria_results"]},
        "counts": {
            "templates_reviewed": 1,
            "reports_reviewed": 3,
            "effective_achievement_records": source["pack"]["counts"]["effective_achievement_records"],
            "withheld_claims": source["pack"]["counts"]["withheld_claims"],
        },
        "state": EXPECTED_STATE,
        "pricing_status": "NOT_PRICED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "next_action": "Build the internal productization specification and acceptance contract, then stop before pricing, outreach, contracting, delivery, or publication.",
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {"source": source, "decision": approved, "summary": summary}


def render_productization_markdown(bundle: dict[str, Any] | None = None) -> str:
    value = build_productization_review() if bundle is None else bundle
    decision = value["decision"]
    summary = value["summary"]
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Productization Review",
        "",
        "Status: APPROVED_FOR_INTERNAL_PRODUCTIZATION_SPECIFICATION / NOT_PRICED / NOT_PUBLISHED / NOT_DELIVERED",
        "",
        "The project owner resumed the interrupted work and approved the reviewed Template v2 and three revised demonstration reports only as inputs to the next internal productization-specification stage.",
        "",
        "## Decision",
        "",
        f"- Decision: {decision['decision']}",
        f"- Scope: {decision['productization_scope']}",
        f"- Reviewed template: `{decision['reviewed_template_fingerprint']}`",
        f"- Reviewed pack: `{decision['reviewed_pack_fingerprint']}`",
        "",
        "## Criteria",
        "",
    ]
    lines.extend(f"- {item['criterion']}: {item['result']}" for item in decision["criteria_results"])
    lines.extend([
        "",
        "## Boundaries",
        "",
        "- Pricing authorized: false",
        "- Outreach authorized: false",
        "- Contract authorized: false",
        "- Delivery authorized: false",
        "- Publication authorized: false",
        "- External execution authorized: false",
        "- Automatic approval authorized: false",
        "- Automatic rewriting authorized: false",
        "- Target-repository writes authorized: false",
        "",
        "## Next bounded stage",
        "",
        summary["next_action"],
        "",
    ])
    return "\n".join(lines)


def verify_productization_review(
    *,
    decision: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_productization_review(decision)
    summary = bundle["summary"]
    _verify_fingerprint(summary, "summary_fingerprint", "productization review summary")
    if summary["summary_fingerprint"] != SUMMARY_FINGERPRINT:
        raise ProofEngineError("productization review summary deterministic fingerprint mismatch")
    if summary["state"] != EXPECTED_STATE:
        raise ProofEngineError("productization review state mismatch")
    if summary["counts"] != {
        "templates_reviewed": 1,
        "reports_reviewed": 3,
        "effective_achievement_records": 16,
        "withheld_claims": 5,
    }:
        raise ProofEngineError("productization review counts mismatch")
    if set(summary["criteria"]) != set(REVIEW_CRITERIA) or any(
        result != "PASS" for result in summary["criteria"].values()
    ):
        raise ProofEngineError("productization review criteria did not pass")
    if (
        summary["pricing_status"],
        summary["delivery_status"],
        summary["publication_status"],
        summary["outreach_status"],
        summary["contract_status"],
    ) != ("NOT_PRICED", "NOT_DELIVERED", "NOT_PUBLISHED", "NOT_STARTED", "NOT_STARTED"):
        raise ProofEngineError("productization review external boundary widened")

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("productization checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "productization checkpoint")
    expected = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCTIZATION-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCTIZATION-CHECKPOINT-0015",
        "source_review_checkpoint_fingerprint": SOURCE_REVIEW_CHECKPOINT_FINGERPRINT,
        "decision_fingerprint": DECISION_FINGERPRINT,
        "summary_fingerprint": SUMMARY_FINGERPRINT,
        "reviewed_template_fingerprint": REVIEWED_TEMPLATE_FINGERPRINT,
        "reviewed_pack_fingerprint": REVIEWED_PACK_FINGERPRINT,
        "reviewed_report_fingerprints": REVIEWED_REPORT_FINGERPRINTS,
        "decision": "APPROVE_FOR_PRODUCTIZATION",
        "productization_scope": EXPECTED_SCOPE,
        "state": EXPECTED_STATE,
        "next_action": summary["next_action"],
    }
    for field, expected_value in expected.items():
        if cp[field] != expected_value:
            raise ProofEngineError(f"productization checkpoint mismatch: {field}")
    for field in (
        "pricing_performed",
        "delivery_performed",
        "publication_performed",
        "outreach_performed",
        "contract_action_performed",
        "external_actions_performed",
        "target_repository_writes_performed",
    ):
        if cp[field] is not False:
            raise ProofEngineError(f"productization checkpoint exceeded boundary: {field}")
    markdown = render_productization_markdown(bundle)
    return {**bundle, "checkpoint": cp, "markdown": markdown, "markdown_fingerprint": fingerprint(markdown)}
