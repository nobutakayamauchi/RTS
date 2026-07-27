from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_template import REQUIRED_SECTIONS, verify_report_template

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
REVIEW_DIR = PACKAGE_DIR / "report_reviews" / "round_0001"
CONTRACT_PATH = REVIEW_DIR / "review_contract.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_template_review_checkpoint_0014.json"

SOURCE_CONTRACT_FINGERPRINT = "483c0e377c415c6be05f218a0f7a3bb06fac720a6f2b12f1c8b3916df3501a69"
SOURCE_MANIFEST_FINGERPRINT = "b47f479e19516d51d58f29f94030111f16b9d12f854fca110b86b9ebda257d2c"
SOURCE_CHECKPOINT_FINGERPRINT = "3a31c2ff82ee2b173d9ea9035eac87e753d9a85ec864d6563f990bae937f90fd"
REVIEW_CONTRACT_FINGERPRINT = "683ccfb57054b732b9cb8f75f84a43def7f20d90a01ac4503d83ad8dba2d8da0"

EXPECTED_HUMAN_AUTHORIZATION = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_NEXT_WORK_INSTRUCTION",
    "role": "PROJECT_OWNER",
    "instruction": "次を行う",
}
EXPECTED_REVIEWER = {
    "type": "AI_ASSISTANT",
    "role": "DELEGATED_REPORT_TEMPLATE_REVIEWER",
    "decision_origin": "AI_REVIEW_UNDER_EXPLICIT_HUMAN_NEXT_WORK_AUTHORIZATION",
}
AUTHORITY_FIELDS = {
    "automatic_approval_authorized",
    "automatic_rewrite_authorized",
    "contract_authorized",
    "delivery_authorized",
    "external_execution_authorized",
    "outreach_authorized",
    "pricing_authorized",
    "publication_authorized",
    "target_repository_write_authorized",
}
REVIEW_CRITERIA = [
    "FACTUALITY_AND_SCOPE_BOUNDING",
    "FULL_SECTION_RENDERING",
    "PLAIN_LANGUAGE_VALUE_CLARITY",
    "HUMAN_AI_CONTRIBUTION_SEPARATION",
    "PRIVATE_REPOSITORY_BOUNDARY",
    "HUMAN_DECISION_AUTHENTICITY",
    "PRODUCTIZATION_REVIEW_READINESS",
]
REQUIRED_DECISION_FIELDS = [
    "decision",
    "reviewer_identity",
    "reviewed_template_fingerprint",
    "reviewed_report_fingerprints",
    "factuality_confirmed",
    "privacy_boundary_confirmed",
    "contribution_separation_confirmed",
    "pricing_authorized",
    "delivery_authorized",
    "publication_authorized",
]
CHECKPOINT_FIELDS = {
    "schema_version",
    "checkpoint_id",
    "source_template_checkpoint_fingerprint",
    "review_contract_fingerprint",
    "revised_template_fingerprint",
    "revised_pack_fingerprint",
    "revised_markdown_fingerprint",
    "report_count",
    "effective_candidate_count",
    "withheld_claim_count",
    "source_template_preserved",
    "source_reports_preserved",
    "state",
    "publication_performed",
    "delivery_performed",
    "pricing_performed",
    "outreach_performed",
    "contract_action_performed",
    "external_actions_performed",
    "target_repository_writes_performed",
    "next_action",
    "checkpoint_fingerprint",
}

ROUND_SUMMARIES = {
    "ROUND-2": {
        "reader_summary": "The selected merged evidence supports a small browser-based learning-reconstruction MVP, bounded output behavior, and a controlled branch and pull-request bridge.",
        "verified_value": "The repository demonstrates concrete product and workflow outputs while excluding unmerged proposals from completed-achievement evidence.",
    },
    "ROUND-3": {
        "reader_summary": "The selected metadata supports a human-gated media workflow, auditable manual publication records, and structured reference intake without copying customer-specific payload.",
        "verified_value": "The repository demonstrates business-workflow controls and traceable manual execution boundaries without claiming revenue or automatic publishing.",
    },
    "ROUND-4": {
        "reader_summary": "The repository supports only a video-workflow scaffold and a frozen review-required state; runtime capability remains unverified.",
        "verified_value": "The negative control shows that the reporting process can preserve useful scaffold evidence without promoting it to a finished product claim.",
    },
}

VALUE_BY_KIND = {
    "PROJECT_OUTPUT": "Concrete repository capability or deliverable supported by the selected evidence.",
    "PROCESS_BYPRODUCT": "Reviewable process result that should not be presented as a standalone finished product.",
    "AUDIT_REMEDIATION_BYPRODUCT": "Evidence-backed correction or audit result preserved as a process outcome.",
    "INTEGRATION_BYPRODUCT": "Integration result that remains bounded to the observed repository context.",
    "REUSABILITY_SIGNAL": "Potential reuse signal that does not establish external effectiveness.",
    "PERSONAL_ACHIEVEMENT": "Human achievement claim that requires direct attribution evidence.",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _verify_false_authority(value: Any, label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != AUTHORITY_FIELDS:
        raise ProofEngineError(f"{label} authority fields mismatch")
    if any(value[field] is not False for field in AUTHORITY_FIELDS):
        raise ProofEngineError(f"{label} authority widened")
    return value


def verify_review_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "report template review contract")
    if value.get("contract_fingerprint") != REVIEW_CONTRACT_FINGERPRINT:
        raise ProofEngineError("report template review contract deterministic fingerprint mismatch")
    if value.get("schema_version") != "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-REVIEW-CONTRACT-V1":
        raise ProofEngineError("report template review contract schema mismatch")
    if value.get("contract_id") != "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-REVIEW-CONTRACT-0001":
        raise ProofEngineError("report template review contract identity mismatch")
    if value.get("human_authorization") != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("report template review is not bound to the explicit next-work instruction")
    if value.get("reviewer") != EXPECTED_REVIEWER:
        raise ProofEngineError("report template review attribution mismatch")
    if value.get("source") != {
        "template_contract_fingerprint": SOURCE_CONTRACT_FINGERPRINT,
        "template_manifest_fingerprint": SOURCE_MANIFEST_FINGERPRINT,
        "template_checkpoint_fingerprint": SOURCE_CHECKPOINT_FINGERPRINT,
        "report_count": 3,
        "effective_candidate_count": 16,
        "withheld_claim_count": 5,
    }:
        raise ProofEngineError("report template review source mismatch")
    if value.get("review_criteria") != REVIEW_CRITERIA:
        raise ProofEngineError("report template review criteria mismatch")
    findings = value.get("findings")
    if not isinstance(findings, list) or [item.get("finding_id") for item in findings] != [
        "REPORT-TEMPLATE-REVIEW-F001",
        "REPORT-TEMPLATE-REVIEW-F002",
        "REPORT-TEMPLATE-REVIEW-F003",
    ]:
        raise ProofEngineError("report template review findings mismatch")
    if [item.get("label") for item in findings] != [
        "MARKDOWN_SECTION_COVERAGE_INCOMPLETE",
        "REVIEW_CRITERIA_UNDERSPECIFIED",
        "PLAIN_LANGUAGE_VALUE_LAYER_MISSING",
    ] or any(item.get("severity") != "REVISE" for item in findings):
        raise ProofEngineError("report template review finding content mismatch")
    decisions = value.get("decisions", {})
    if decisions.get("source_template") != "REVISE":
        raise ProofEngineError("report template review did not revise the source template")
    if decisions.get("source_reports") != [
        {"report_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-2", "decision": "REVISE"},
        {"report_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-3", "decision": "REVISE"},
        {"report_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-4", "decision": "REVISE"},
    ]:
        raise ProofEngineError("report template review report decisions mismatch")
    if decisions.get("revised_template") != "READY_FOR_HUMAN_PRODUCTIZATION_REVIEW" or decisions.get("revised_reports") != "READY_FOR_HUMAN_PRODUCTIZATION_REVIEW":
        raise ProofEngineError("report template review terminal decision mismatch")
    requirements = value.get("revision_requirements", {})
    if not isinstance(requirements, dict) or not requirements or any(item is not True for item in requirements.values()):
        raise ProofEngineError("report template review requirements weakened")
    if value.get("terminal") != {
        "state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "delivery_status": "NOT_DELIVERED",
        "pricing_status": "NOT_PRICED",
    }:
        raise ProofEngineError("report template review terminal boundary mismatch")
    _verify_false_authority(value.get("authority"), "report template review contract")
    return value


def _decorate_record(record: dict[str, Any]) -> dict[str, Any]:
    revised = copy.deepcopy(record)
    kind = revised["record_kind"]
    revised["reader_summary"] = revised["claim"]
    revised["value_interpretation"] = VALUE_BY_KIND.get(
        kind,
        "Evidence-backed repository result bounded to the selected source material.",
    )
    revised["evidence_strength"] = revised["evidence_label"]
    revised["evidence_boundary"] = revised["factuality_note"]
    revised["source_record_fingerprint"] = revised["achievement_record_fingerprint"]
    revised.pop("achievement_record_fingerprint")
    revised["achievement_record_version"] = 2
    revised["achievement_record_fingerprint"] = fingerprint(revised)
    return revised


def _revised_report(source_report: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    report = copy.deepcopy(source_report)
    source_report_fingerprint = report["report_fingerprint"]
    report.pop("report_fingerprint")
    round_id = report["round_id"]
    summary = ROUND_SUMMARIES[round_id]
    sections = report["sections"]

    sections["executive_summary"].update({
        "reader_summary": summary["reader_summary"],
        "verified_value": summary["verified_value"],
        "decision_boundary": "This report is evidence-backed and internally reviewed by an AI assistant under human authorization, but productization, pricing, delivery, and publication still require a separate human decision.",
    })
    sections["repository_scope"].update({
        "included_evidence": "Only the fixed selected repository snapshot and eligible reviewed records are included.",
        "excluded_evidence": "Unmerged, unselected, private-payload, or otherwise unsupported material is not treated as completed-achievement evidence.",
    })
    sections["methodology"].update({
        "evidence_eligibility_policy": "Merged and explicitly eligible evidence may support a completed record; unsupported claims remain visible as withheld.",
        "review_attribution_policy": "The project owner authorized the review work. The AI assistant performed the template and wording assessment; no direct human wording judgment is manufactured.",
    })
    inventory = sections["evidence_inventory"]
    inventory.update({
        "merged_pr_count": len(inventory["merged_prs"]),
        "excluded_unmerged_pr_count": len(inventory["excluded_unmerged_prs"]),
        "evidence_boundary_note": "The inventory identifies evidence references; it does not independently verify external platform outcomes or commercial impact.",
    })
    sections["effective_achievement_records"] = [
        _decorate_record(item) for item in sections["effective_achievement_records"]
    ]
    sections["human_and_ai_contribution_map"].update({
        "reader_note": "Human entries describe goals, constraints, approvals, or manual external actions. AI-tool entries describe implementation, drafting, analysis, and verification support.",
    })
    sections["human_review_decision"] = {
        "state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
        "review_criteria": copy.deepcopy(REVIEW_CRITERIA),
        "required_decision_fields": copy.deepcopy(REQUIRED_DECISION_FIELDS),
        "allowed_decisions": ["APPROVE_FOR_PRODUCTIZATION", "REVISE", "REJECT", "REDACT", "EXPIRE"],
        "decisions": [],
        "pricing_authorized": False,
        "delivery_authorized": False,
        "publication_authorized": False,
    }
    if list(sections) != REQUIRED_SECTIONS:
        raise ProofEngineError(f"revised report section order mismatch: {round_id}")

    report.update({
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-DRAFT-V2",
        "report_version": 2,
        "revision_of_report_fingerprint": source_report_fingerprint,
        "review_contract_fingerprint": contract["contract_fingerprint"],
        "review_origin": {
            "human_authorization": copy.deepcopy(EXPECTED_HUMAN_AUTHORIZATION),
            "reviewer": copy.deepcopy(EXPECTED_REVIEWER),
        },
        "draft_state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "delivery_status": "NOT_DELIVERED",
        "pricing_status": "NOT_PRICED",
        "authority": copy.deepcopy(contract["authority"]),
    })
    report["report_fingerprint"] = fingerprint(report)
    return report


def _revised_template(source_template: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    template = copy.deepcopy(source_template)
    source_template_fingerprint = template["template_fingerprint"]
    template.pop("template_fingerprint")
    template.update({
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-V2",
        "template_id": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-0002",
        "template_version": 2,
        "revision_of_template_fingerprint": source_template_fingerprint,
        "review_contract_fingerprint": contract["contract_fingerprint"],
        "purpose": "Convert reviewed repository evidence into a complete, reader-facing, fact-bounded achievement discovery report while keeping productization, pricing, delivery, and publication behind an explicit human decision.",
        "reader_presentation_contract": {
            "all_required_sections_rendered": True,
            "plain_language_summary_required": True,
            "value_interpretation_required": True,
            "evidence_boundary_required": True,
            "human_ai_contribution_map_rendered": True,
        },
        "productization_review_contract": {
            "review_criteria": copy.deepcopy(REVIEW_CRITERIA),
            "required_decision_fields": copy.deepcopy(REQUIRED_DECISION_FIELDS),
            "human_decision_required": True,
            "ai_may_not_manufacture_human_approval": True,
        },
        "required_report_states": {
            "draft_state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
            "publication_status": "NOT_PUBLISHED",
            "delivery_status": "NOT_DELIVERED",
            "pricing_status": "NOT_PRICED",
        },
        "authority": copy.deepcopy(contract["authority"]),
    })
    template["rendering_policy"].update({
        "all_required_sections_rendered": True,
        "plain_language_value_layer_required": True,
        "human_ai_contribution_map_rendered": True,
        "human_productization_decision_required": True,
    })
    template["template_fingerprint"] = fingerprint(template)
    return template


def build_report_template_review(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    review_contract = verify_review_contract(contract)
    source = verify_report_template()
    if source["checkpoint"]["checkpoint_fingerprint"] != SOURCE_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("report template review source checkpoint drift")
    if source["pack"]["counts"] != {
        "reports": 3,
        "effective_achievement_records": 16,
        "withheld_claims": 5,
    }:
        raise ProofEngineError("report template review source counts drift")

    revised_template = _revised_template(source["template"], review_contract)
    revised_reports = [_revised_report(item, review_contract) for item in source["pack"]["reports"]]
    revised_pack = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-DEMONSTRATION-PACK-V2",
        "pack_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMONSTRATION-PACK-0002",
        "pack_version": 2,
        "revision_of_pack_fingerprint": source["pack"]["pack_fingerprint"],
        "review_contract_fingerprint": review_contract["contract_fingerprint"],
        "template_fingerprint": revised_template["template_fingerprint"],
        "reports": revised_reports,
        "counts": copy.deepcopy(source["pack"]["counts"]),
        "state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "delivery_status": "NOT_DELIVERED",
        "pricing_status": "NOT_PRICED",
    }
    revised_pack["pack_fingerprint"] = fingerprint(revised_pack)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-REVIEW-SUMMARY-V1",
        "review_id": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-REVIEW-0001",
        "source_template_fingerprint": source["template"]["template_fingerprint"],
        "source_pack_fingerprint": source["pack"]["pack_fingerprint"],
        "review_contract_fingerprint": review_contract["contract_fingerprint"],
        "review_origin": {
            "human_authorization": copy.deepcopy(EXPECTED_HUMAN_AUTHORIZATION),
            "reviewer": copy.deepcopy(EXPECTED_REVIEWER),
        },
        "source_decisions": {
            "template": "REVISE",
            "reports_revised": 3,
        },
        "findings": copy.deepcopy(review_contract["findings"]),
        "revised_template_fingerprint": revised_template["template_fingerprint"],
        "revised_pack_fingerprint": revised_pack["pack_fingerprint"],
        "counts": {
            "templates_reviewed": 1,
            "templates_revised": 1,
            "reports_reviewed": 3,
            "reports_revised": 3,
            "effective_achievement_records": 16,
            "withheld_claims": 5,
        },
        "source_artifacts_preserved": True,
        "state": "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED",
        "publication_status": "NOT_PUBLISHED",
        "delivery_status": "NOT_DELIVERED",
        "pricing_status": "NOT_PRICED",
        "authority": copy.deepcopy(review_contract["authority"]),
        "next_action": "The human project owner reviews the revised template and three revised demonstration reports before any pricing, delivery, outreach, contract, or publication decision.",
    }
    summary["review_fingerprint"] = fingerprint(summary)
    return {
        "source": source,
        "contract": review_contract,
        "template": revised_template,
        "pack": revised_pack,
        "summary": summary,
    }


def render_revised_markdown(bundle: dict[str, Any] | None = None) -> str:
    value = build_report_template_review() if bundle is None else bundle
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Revised Internal Demonstration",
        "",
        "Status: HUMAN_PRODUCTIZATION_REVIEW_REQUIRED / NOT_PRICED / NOT_PUBLISHED / NOT_DELIVERED",
        "",
        "The source template and source reports remain preserved. This revision was prepared by an AI assistant under explicit human authorization and does not constitute human productization approval.",
        "",
    ]
    for report in value["pack"]["reports"]:
        sections = report["sections"]
        scope = sections["repository_scope"]
        inventory = sections["evidence_inventory"]
        lines.extend([
            f"## {report['repository']}",
            "",
            "### 1. Executive summary",
            "",
            sections["executive_summary"]["reader_summary"],
            "",
            f"**Verified value:** {sections['executive_summary']['verified_value']}",
            "",
            f"**Decision boundary:** {sections['executive_summary']['decision_boundary']}",
            "",
            "### 2. Repository scope",
            "",
            f"- Visibility: {scope['visibility']}",
            f"- Source mode: {scope['source_mode']}",
            f"- Snapshot: {scope['snapshot_ref']}",
            f"- Validation role: {scope['role']}",
            f"- Included: {scope['included_evidence']}",
            f"- Excluded: {scope['excluded_evidence']}",
            "",
            "### 3. Methodology",
            "",
        ])
        lines.extend(f"- {item}" for item in sections["methodology"]["steps"])
        lines.extend([
            f"- Evidence policy: {sections['methodology']['evidence_eligibility_policy']}",
            f"- Review attribution: {sections['methodology']['review_attribution_policy']}",
            "",
            "### 4. Evidence inventory",
            "",
            f"- README blob: `{inventory['readme_blob_sha']}`",
            f"- Source round fingerprint: `{inventory['source_round_fingerprint']}`",
            f"- Eligible merged PRs: {inventory['merged_pr_count']}",
            f"- Excluded unmerged PRs: {inventory['excluded_unmerged_pr_count']}",
        ])
        for item in inventory["merged_prs"]:
            lines.append(f"  - PR #{item['number']}: {item['title']} ({item['status']})")
        if inventory["excluded_unmerged_prs"]:
            lines.append("- Excluded PR numbers: " + ", ".join(f"#{item}" for item in inventory["excluded_unmerged_prs"]))
        lines.extend([
            f"- Boundary: {inventory['evidence_boundary_note']}",
            "",
            "### 5. Effective achievement records",
            "",
        ])
        for record in sections["effective_achievement_records"]:
            lines.extend([
                f"#### {record['candidate_id']} — {record['record_kind']}",
                "",
                record["reader_summary"],
                "",
                f"- Value interpretation: {record['value_interpretation']}",
                f"- Evidence strength: {record['evidence_strength']}",
                f"- Evidence PRs: {', '.join('#' + str(number) for number in record['evidence_prs'])}",
                f"- Evidence boundary: {record['evidence_boundary']}",
                f"- Lineage: {record['lineage']['source']} / version {record['lineage']['candidate_version']}",
                "",
            ])
        lines.extend(["### 6. Human and AI contribution map", ""])
        for item in sections["human_and_ai_contribution_map"]["records"]:
            lines.extend([
                f"#### {item['candidate_id']}",
                "",
                "- Human: " + ("; ".join(item["human"]) if item["human"] else "None recorded"),
                "- AI tool: " + ("; ".join(item["ai_tool"]) if item["ai_tool"] else "None recorded"),
                "- Collaborator: " + ("; ".join(item["collaborator"]) if item["collaborator"] else "None recorded"),
                "- Inherited: " + ("; ".join(item["inherited"]) if item["inherited"] else "None recorded"),
                "",
            ])
        lines.extend([
            sections["human_and_ai_contribution_map"]["reader_note"],
            "",
            "### 7. Withheld or unsupported claims",
            "",
        ])
        withheld = sections["withheld_or_unsupported_claims"]
        lines.extend(
            [f"- {item['claim']} — {item['reason']}" for item in withheld]
            if withheld else ["- None in the selected evidence boundary."]
        )
        lines.extend(["", "### 8. Limitations", ""])
        lines.extend(f"- {item}" for item in sections["limitations"])
        gate = sections["human_review_decision"]
        lines.extend([
            "",
            "### 9. Human review decision",
            "",
            f"- State: {gate['state']}",
            "- Decisions recorded: none",
            "- Required review criteria: " + ", ".join(gate["review_criteria"]),
            "- Pricing authorized: false",
            "- Delivery authorized: false",
            "- Publication authorized: false",
            "",
        ])
    lines.extend([
        "## Productization gate",
        "",
        "No report or template in this revised demonstration has been approved for pricing, outreach, contracting, delivery, or publication.",
        "",
    ])
    return "\n".join(lines)


def verify_report_template_review(
    *,
    contract: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_report_template_review(contract)
    template = bundle["template"]
    pack = bundle["pack"]
    summary = bundle["summary"]
    _verify_fingerprint(template, "template_fingerprint", "revised report template")
    _verify_fingerprint(pack, "pack_fingerprint", "revised report demonstration pack")
    _verify_fingerprint(summary, "review_fingerprint", "report template review summary")

    if pack["counts"] != {"reports": 3, "effective_achievement_records": 16, "withheld_claims": 5}:
        raise ProofEngineError("revised report pack counts mismatch")
    if pack["state"] != "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED":
        raise ProofEngineError("revised report pack state mismatch")
    if pack["publication_status"] != "NOT_PUBLISHED" or pack["delivery_status"] != "NOT_DELIVERED" or pack["pricing_status"] != "NOT_PRICED":
        raise ProofEngineError("revised report pack boundary widened")
    for report in pack["reports"]:
        if list(report["sections"]) != REQUIRED_SECTIONS:
            raise ProofEngineError("revised report section set mismatch")
        gate = report["sections"]["human_review_decision"]
        if gate["decisions"]:
            raise ProofEngineError("revised report manufactured a human productization decision")
        if gate["review_criteria"] != REVIEW_CRITERIA or gate["required_decision_fields"] != REQUIRED_DECISION_FIELDS:
            raise ProofEngineError("revised report productization gate mismatch")
        if report["authority"] != bundle["contract"]["authority"]:
            raise ProofEngineError("revised report authority mismatch")
    round3 = next(item for item in pack["reports"] if item["round_id"] == "ROUND-3")
    if round3["sections"]["repository_scope"]["source_mode"] != "READ_ONLY_METADATA_SNAPSHOT":
        raise ProofEngineError("revised private report source boundary widened")
    round4 = next(item for item in pack["reports"] if item["round_id"] == "ROUND-4")
    if len(round4["sections"]["withheld_or_unsupported_claims"]) != 3:
        raise ProofEngineError("revised negative-control withheld claims drift")

    markdown = render_revised_markdown(bundle)
    for heading in (
        "### 1. Executive summary",
        "### 2. Repository scope",
        "### 3. Methodology",
        "### 4. Evidence inventory",
        "### 5. Effective achievement records",
        "### 6. Human and AI contribution map",
        "### 7. Withheld or unsupported claims",
        "### 8. Limitations",
        "### 9. Human review decision",
    ):
        if markdown.count(heading) != 3:
            raise ProofEngineError(f"revised Markdown section coverage mismatch: {heading}")
    markdown_fingerprint = fingerprint(markdown)

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("report template review checkpoint schema fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "report template review checkpoint")
    expected_links = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-REVIEW-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-TEMPLATE-REVIEW-CHECKPOINT-0014",
        "source_template_checkpoint_fingerprint": SOURCE_CHECKPOINT_FINGERPRINT,
        "review_contract_fingerprint": REVIEW_CONTRACT_FINGERPRINT,
        "revised_template_fingerprint": template["template_fingerprint"],
        "revised_pack_fingerprint": pack["pack_fingerprint"],
        "revised_markdown_fingerprint": markdown_fingerprint,
    }
    for field, expected in expected_links.items():
        if cp.get(field) != expected:
            raise ProofEngineError(f"report template review checkpoint link mismatch: {field}")
    if (cp.get("report_count"), cp.get("effective_candidate_count"), cp.get("withheld_claim_count")) != (3, 16, 5):
        raise ProofEngineError("report template review checkpoint counts mismatch")
    if cp.get("source_template_preserved") is not True or cp.get("source_reports_preserved") is not True:
        raise ProofEngineError("report template review checkpoint did not preserve sources")
    if cp.get("state") != "HUMAN_PRODUCTIZATION_REVIEW_REQUIRED":
        raise ProofEngineError("report template review checkpoint state mismatch")
    for field in (
        "publication_performed",
        "delivery_performed",
        "pricing_performed",
        "outreach_performed",
        "contract_action_performed",
        "external_actions_performed",
        "target_repository_writes_performed",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"report template review checkpoint exceeded boundary: {field}")
    return {**bundle, "markdown": markdown, "markdown_fingerprint": markdown_fingerprint, "checkpoint": cp}
