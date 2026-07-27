from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_productization_spec_v2 import (
    POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT,
    PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT,
    PRODUCT_SPEC_FINGERPRINT,
    verify_internal_productization_spec_v2,
)
from .report_template import REQUIRED_SECTIONS
from .report_template_review import verify_report_template_review

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
PILOT_DIR = PACKAGE_DIR / "pilot_packages" / "round_0001"
BUILD_DECISION_PATH = PILOT_DIR / "build_decision.json"
CASE_INTAKE_PATH = PILOT_DIR / "case_intake.json"
MANIFEST_PATH = PILOT_DIR / "package_manifest.json"
ROLLBACK_PATH = PILOT_DIR / "rollback_record.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_pilot_package_checkpoint_0017.json"

CORRECTED_SPEC_CHECKPOINT_FINGERPRINT = "216727d62de7dd44d277729c57620e0c3652abc9584106fbe741dcabf6c2fbb1"
BUILD_DECISION_FINGERPRINT = "3e242b568004db22d8298fd3470afcd45045a88ca8406953484719546c3e5418"
CASE_INTAKE_FINGERPRINT = "2075eed3558283771d42f914ea67dfb25146c897342c1ea7f04d28b4ab04a23e"
MANIFEST_FINGERPRINT = "fda5147857c0c0441647d2ca3613c103a2665be8e907063ca3f9b5563e418dcb"
ROLLBACK_FINGERPRINT = "a745a3b87cd5dc3746186f0a452c9129c82ead4ed662f8de82bb45e7f39d5882"
SOURCE_REPORT_ID = "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-2"
SOURCE_REPORT_FINGERPRINT = "a644d21ccf98cbdadf810c2e5294776d22376995a69c5abd76b29e4066e864dc"
EXPECTED_BUILD_CRITERIA = [f"BLD-{number:03d}" for number in range(1, 7)]
EXPECTED_ACCEPTANCE_CRITERIA = [f"ACC-{number:03d}" for number in range(1, 16)]

# Filled after deterministic generation is probed in CI, then bound by the final checkpoint.
REPORT_JSON_FINGERPRINT = "PENDING_PROBE"
REPORT_MARKDOWN_FINGERPRINT = "PENDING_PROBE"
EVIDENCE_INVENTORY_FINGERPRINT = "PENDING_PROBE"
ACCEPTANCE_PACKET_FINGERPRINT = "PENDING_PROBE"
VERIFICATION_SUMMARY_FINGERPRINT = "PENDING_PROBE"
PACKAGE_INDEX_FINGERPRINT = "PENDING_PROBE"
SUMMARY_FINGERPRINT = "PENDING_PROBE"
CHECKPOINT_FINGERPRINT = "PENDING_PROBE"

FALSE_EXTERNAL_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "delivery_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "package_acceptance_authorized": False,
    "pricing_authorized": False,
    "publication_authorized": False,
    "target_repository_write_authorized": False,
}
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "corrected_spec_checkpoint_fingerprint",
    "build_decision_fingerprint", "case_intake_fingerprint", "manifest_fingerprint",
    "rollback_fingerprint", "source_report_fingerprint", "report_json_fingerprint",
    "report_markdown_fingerprint", "evidence_inventory_fingerprint",
    "acceptance_packet_fingerprint", "verification_summary_fingerprint",
    "package_index_fingerprint", "summary_fingerprint", "state", "next_gate",
    "pilot_package_built", "package_accepted", "pricing_performed",
    "outreach_performed", "contract_action_performed", "delivery_performed",
    "publication_performed", "external_actions_performed",
    "target_repository_writes_performed", "next_action", "checkpoint_fingerprint",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def verify_build_decision(decision: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(BUILD_DECISION_PATH) if decision is None else copy.deepcopy(decision)
    _verify_fingerprint(value, "decision_fingerprint", "pilot package build decision")
    if value.get("decision_fingerprint") != BUILD_DECISION_FINGERPRINT:
        raise ProofEngineError("pilot package build decision deterministic mismatch")
    if value.get("human_authorization") != {
        "type": "HUMAN", "identity": "nobutakayamauchi",
        "identity_source": "CURRENT_CHAT_EXPLICIT_BUILD_INSTRUCTION",
        "role": "PROJECT_OWNER", "instruction": "やる",
    }:
        raise ProofEngineError("pilot package build decision authorization mismatch")
    if value.get("decision") != "APPROVE_PILOT_PACKAGE_BUILD" or value.get("pilot_package_build_authorized") is not True:
        raise ProofEngineError("pilot package build is not authorized")
    if value.get("scope") != "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILD_ONLY":
        raise ProofEngineError("pilot package build scope widened")
    if value.get("reviewed_spec_checkpoint_fingerprint") != CORRECTED_SPEC_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("pilot package build spec checkpoint mismatch")
    if value.get("reviewed_spec_fingerprint") != PRODUCT_SPEC_FINGERPRINT:
        raise ProofEngineError("pilot package build spec mismatch")
    if value.get("reviewed_pre_build_contract_fingerprint") != PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT:
        raise ProofEngineError("pilot package build pre-build contract mismatch")
    if value.get("post_build_acceptance_contract_fingerprint") != POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT:
        raise ProofEngineError("pilot package build acceptance contract mismatch")
    results = value.get("criteria_results")
    if not isinstance(results, list) or [item.get("criterion_id") for item in results] != EXPECTED_BUILD_CRITERIA or any(item.get("result") != "PASS" for item in results):
        raise ProofEngineError("pilot package build criteria mismatch")
    selected = value.get("selected_case")
    if selected != {
        "repository": "seminar-compass", "snapshot_binding": "VERIFIED_SOURCE_REPORT_FINGERPRINT",
        "source_mode": "READ_ONLY_SNAPSHOT", "source_report_fingerprint": SOURCE_REPORT_FINGERPRINT,
        "source_report_id": SOURCE_REPORT_ID, "visibility": "PUBLIC",
    }:
        raise ProofEngineError("pilot package selected case mismatch")
    for field in (
        "automatic_approval_authorized", "automatic_rewrite_authorized",
        "contract_authorized", "delivery_authorized", "external_execution_authorized",
        "outreach_authorized", "pricing_authorized", "publication_authorized",
        "target_repository_write_authorized",
    ):
        if value.get(field) is not False:
            raise ProofEngineError(f"pilot package build authority widened: {field}")
    if value.get("privacy_boundary_confirmed") is not True or value.get("rollback_confirmed") is not True:
        raise ProofEngineError("pilot package build confirmations missing")
    return value


def verify_case_intake(intake: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(CASE_INTAKE_PATH) if intake is None else copy.deepcopy(intake)
    _verify_fingerprint(value, "intake_fingerprint", "pilot case intake")
    if value.get("intake_fingerprint") != CASE_INTAKE_FINGERPRINT:
        raise ProofEngineError("pilot case intake deterministic mismatch")
    if value.get("build_decision_fingerprint") != BUILD_DECISION_FINGERPRINT:
        raise ProofEngineError("pilot case intake decision mismatch")
    if value.get("source") != {
        "report_fingerprint": SOURCE_REPORT_FINGERPRINT, "report_id": SOURCE_REPORT_ID,
        "repository": "seminar-compass", "snapshot_binding": "DERIVE_AND_VERIFY_FROM_SOURCE_REPORT",
        "source_mode": "READ_ONLY_SNAPSHOT", "visibility": "PUBLIC",
    }:
        raise ProofEngineError("pilot case intake source mismatch")
    if value.get("operator", {}).get("wip_limit") != 1 or value.get("operator", {}).get("mode") != "OPERATOR_ASSISTED_SINGLE_CASE":
        raise ProofEngineError("pilot case intake operator boundary mismatch")
    privacy = value.get("privacy", {})
    if privacy != {
        "credentials_allowed": False, "private_payload_allowed": False,
        "source_visibility_required": "PUBLIC", "third_party_personal_data_allowed": False,
    }:
        raise ProofEngineError("pilot case intake privacy widened")
    if len(value.get("required_outputs", [])) != 7:
        raise ProofEngineError("pilot case intake output contract mismatch")
    return value


def verify_rollback_record(record: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(ROLLBACK_PATH) if record is None else copy.deepcopy(record)
    _verify_fingerprint(value, "rollback_fingerprint", "pilot package rollback record")
    if value.get("rollback_fingerprint") != ROLLBACK_FINGERPRINT:
        raise ProofEngineError("pilot package rollback deterministic mismatch")
    if value.get("build_decision_fingerprint") != BUILD_DECISION_FINGERPRINT or value.get("source_spec_checkpoint_fingerprint") != CORRECTED_SPEC_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("pilot package rollback source mismatch")
    if value.get("delete_or_rewrite_prior_records") is not False or value.get("external_action_performed") is not False:
        raise ProofEngineError("pilot package rollback boundary widened")
    return value


def verify_package_manifest(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(MANIFEST_PATH) if manifest is None else copy.deepcopy(manifest)
    _verify_fingerprint(value, "manifest_fingerprint", "pilot package manifest")
    if value.get("manifest_fingerprint") != MANIFEST_FINGERPRINT:
        raise ProofEngineError("pilot package manifest deterministic mismatch")
    if value.get("source") != {
        "build_decision_fingerprint": BUILD_DECISION_FINGERPRINT,
        "case_intake_fingerprint": CASE_INTAKE_FINGERPRINT,
        "corrected_spec_checkpoint_fingerprint": CORRECTED_SPEC_CHECKPOINT_FINGERPRINT,
        "post_build_acceptance_contract_fingerprint": POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT,
        "pre_build_review_contract_fingerprint": PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT,
        "product_spec_fingerprint": PRODUCT_SPEC_FINGERPRINT,
        "source_report_fingerprint": SOURCE_REPORT_FINGERPRINT,
        "source_report_id": SOURCE_REPORT_ID,
    }:
        raise ProofEngineError("pilot package manifest source mismatch")
    if value.get("expected_counts") != {
        "post_build_acceptance_criteria": 15, "required_artifacts": 7,
        "required_report_sections": 9, "source_effective_achievement_records": 6,
        "source_withheld_claims": 0,
    }:
        raise ProofEngineError("pilot package manifest counts mismatch")
    if len(value.get("artifact_contract", [])) != 7 or any(item.get("required") is not True for item in value["artifact_contract"]):
        raise ProofEngineError("pilot package manifest artifacts mismatch")
    authority = value.get("authority", {})
    if authority.get("pilot_package_build_authorized") is not True:
        raise ProofEngineError("pilot package manifest lacks build authority")
    for field, expected in FALSE_EXTERNAL_AUTHORITY.items():
        if authority.get(field) is not expected:
            raise ProofEngineError(f"pilot package manifest authority widened: {field}")
    if value.get("terminal") != {
        "state": "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT",
        "next_gate": "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
        "pricing_status": "NOT_PRICED", "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
    }:
        raise ProofEngineError("pilot package manifest terminal mismatch")
    return value


def _source_report() -> dict[str, Any]:
    bundle = verify_report_template_review()
    report = next((item for item in bundle["pack"]["reports"] if item["report_id"] == SOURCE_REPORT_ID), None)
    if report is None or report.get("report_fingerprint") != SOURCE_REPORT_FINGERPRINT:
        raise ProofEngineError("pilot package source report mismatch")
    if report.get("repository") != "seminar-compass" or list(report.get("sections", {})) != REQUIRED_SECTIONS:
        raise ProofEngineError("pilot package source report scope mismatch")
    if len(report["sections"]["effective_achievement_records"]) != 6 or report["sections"]["withheld_or_unsupported_claims"]:
        raise ProofEngineError("pilot package source report counts mismatch")
    return copy.deepcopy(report)


def render_report_markdown(report: dict[str, Any]) -> str:
    sections = report["sections"]
    scope, inventory = sections["repository_scope"], sections["evidence_inventory"]
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Internal Pilot Package", "",
        "Status: INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT / HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED / NOT_DELIVERED / NOT_PUBLISHED", "",
        f"## {report['repository']}", "", "### 1. Executive summary", "",
        sections["executive_summary"]["reader_summary"], "",
        f"**Verified value:** {sections['executive_summary']['verified_value']}", "",
        f"**Decision boundary:** {sections['executive_summary']['decision_boundary']}", "",
        "### 2. Repository scope", "", f"- Visibility: {scope['visibility']}",
        f"- Source mode: {scope['source_mode']}", f"- Snapshot: {scope['snapshot_ref']}",
        f"- Validation role: {scope['role']}", f"- Included: {scope['included_evidence']}",
        f"- Excluded: {scope['excluded_evidence']}", "", "### 3. Methodology", "",
    ]
    lines.extend(f"- {item}" for item in sections["methodology"]["steps"])
    lines.extend([
        f"- Evidence policy: {sections['methodology']['evidence_eligibility_policy']}",
        f"- Review attribution: {sections['methodology']['review_attribution_policy']}", "",
        "### 4. Evidence inventory", "", f"- README blob: `{inventory['readme_blob_sha']}`",
        f"- Source round fingerprint: `{inventory['source_round_fingerprint']}`",
        f"- Eligible merged PRs: {inventory['merged_pr_count']}",
        f"- Excluded unmerged PRs: {inventory['excluded_unmerged_pr_count']}",
    ])
    lines.extend(f"  - PR #{item['number']}: {item['title']} ({item['status']})" for item in inventory["merged_prs"])
    if inventory["excluded_unmerged_prs"]:
        lines.append("- Excluded PR numbers: " + ", ".join(f"#{item}" for item in inventory["excluded_unmerged_prs"]))
    lines.extend([f"- Boundary: {inventory['evidence_boundary_note']}", "", "### 5. Effective achievement records", ""])
    for record in sections["effective_achievement_records"]:
        lines.extend([
            f"#### {record['candidate_id']} — {record['record_kind']}", "", record["reader_summary"], "",
            f"- Value interpretation: {record['value_interpretation']}",
            f"- Evidence strength: {record['evidence_strength']}",
            f"- Evidence PRs: {', '.join('#' + str(number) for number in record['evidence_prs'])}",
            f"- Evidence boundary: {record['evidence_boundary']}",
            f"- Lineage: {record['lineage']['source']} / version {record['lineage']['candidate_version']}", "",
        ])
    lines.extend(["### 6. Human and AI contribution map", ""])
    for item in sections["human_and_ai_contribution_map"]["records"]:
        lines.extend([
            f"#### {item['candidate_id']}", "",
            "- Human: " + ("; ".join(item["human"]) if item["human"] else "None recorded"),
            "- AI tool: " + ("; ".join(item["ai_tool"]) if item["ai_tool"] else "None recorded"),
            "- Collaborator: " + ("; ".join(item["collaborator"]) if item["collaborator"] else "None recorded"),
            "- Inherited: " + ("; ".join(item["inherited"]) if item["inherited"] else "None recorded"), "",
        ])
    lines.extend([sections["human_and_ai_contribution_map"]["reader_note"], "", "### 7. Withheld or unsupported claims", ""])
    withheld = sections["withheld_or_unsupported_claims"]
    lines.extend([f"- {item['claim']} — {item['reason']}" for item in withheld] if withheld else ["- None in the selected evidence boundary."])
    lines.extend(["", "### 8. Limitations", ""])
    lines.extend(f"- {item}" for item in sections["limitations"])
    lines.extend([
        "", "### 9. Human review decision", "",
        "- Package acceptance state: HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
        "- Package acceptance decisions recorded: none",
        "- Source report remains unchanged and internally bound by fingerprint.",
        "- Pricing authorized: false", "- Delivery authorized: false", "- Publication authorized: false", "",
    ])
    return "\n".join(lines)


def build_pilot_package() -> dict[str, Any]:
    corrected_spec = verify_internal_productization_spec_v2()
    decision = verify_build_decision()
    intake = verify_case_intake()
    manifest = verify_package_manifest()
    rollback = verify_rollback_record()
    report_json = _source_report()
    report_markdown = render_report_markdown(report_json)
    report_json_fingerprint = fingerprint(report_json)
    report_markdown_fingerprint = fingerprint(report_markdown)
    sections = report_json["sections"]
    evidence_inventory = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-EVIDENCE-INVENTORY-V1",
        "package_id": manifest["package_id"], "source_report_id": report_json["report_id"],
        "source_report_fingerprint": report_json["report_fingerprint"], "repository": report_json["repository"],
        "evidence_inventory": copy.deepcopy(sections["evidence_inventory"]),
        "achievement_record_fingerprints": [item["achievement_record_fingerprint"] for item in sections["effective_achievement_records"]],
        "effective_achievement_record_count": len(sections["effective_achievement_records"]),
        "withheld_claims": copy.deepcopy(sections["withheld_or_unsupported_claims"]),
        "withheld_claim_count": len(sections["withheld_or_unsupported_claims"]),
    }
    evidence_inventory["inventory_fingerprint"] = fingerprint(evidence_inventory)
    acceptance = corrected_spec["acceptance"]
    acceptance_packet = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-PACKET-V1",
        "packet_id": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-ACCEPTANCE-PACKET-0001",
        "package_manifest_fingerprint": manifest["manifest_fingerprint"],
        "post_build_acceptance_contract_fingerprint": acceptance["contract_fingerprint"],
        "report_json_fingerprint": report_json_fingerprint,
        "report_markdown_fingerprint": report_markdown_fingerprint,
        "criteria_results": [{"criterion_id": item["criterion_id"], "result": None, "evidence": [], "note": ""} for item in acceptance["criteria"]],
        "allowed_decisions": copy.deepcopy(acceptance["decision_contract"]["allowed_decisions"]),
        "decision": None, "reviewer_identity": None, "privacy_confirmed": False,
        "authority_boundary_confirmed": False, "package_accepted": False,
        "pricing_authorized": False, "outreach_authorized": False,
        "contract_authorized": False, "delivery_authorized": False,
        "publication_authorized": False,
        "state": "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
    }
    acceptance_packet["packet_fingerprint"] = fingerprint(acceptance_packet)
    automated_pass = {"ACC-001", "ACC-003", "ACC-004", "ACC-010", "ACC-011", "ACC-013"}
    verification_summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-VERIFICATION-SUMMARY-V1",
        "verification_id": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-VERIFICATION-0001",
        "package_manifest_fingerprint": manifest["manifest_fingerprint"],
        "checks": [{"criterion_id": item["criterion_id"], "result": "PASS" if item["criterion_id"] in automated_pass else "PENDING_HUMAN"} for item in acceptance["criteria"]],
        "automated_pass_count": len(automated_pass), "pending_human_count": len(acceptance["criteria"]) - len(automated_pass),
        "overall": "AUTOMATED_PACKAGE_BUILD_VERIFIED_HUMAN_ACCEPTANCE_REQUIRED",
        "package_accepted": False, "external_actions_performed": False,
    }
    verification_summary["verification_fingerprint"] = fingerprint(verification_summary)
    artifacts = {
        "source_bound_input_manifest": intake["intake_fingerprint"],
        "deterministic_report_json": report_json_fingerprint,
        "reader_facing_report_markdown": report_markdown_fingerprint,
        "evidence_and_withheld_claim_inventory": evidence_inventory["inventory_fingerprint"],
        "human_acceptance_packet": acceptance_packet["packet_fingerprint"],
        "verification_summary": verification_summary["verification_fingerprint"],
        "rollback_record": rollback["rollback_fingerprint"],
    }
    package_index = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-INDEX-V1",
        "package_id": manifest["package_id"], "manifest_fingerprint": manifest["manifest_fingerprint"],
        "source_report_fingerprint": report_json["report_fingerprint"], "artifacts": artifacts,
        "artifact_count": len(artifacts), "state": "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT",
        "next_gate": "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
    }
    package_index["package_index_fingerprint"] = fingerprint(package_index)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-SUMMARY-V1",
        "summary_id": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-SUMMARY-0001",
        "build_decision_fingerprint": decision["decision_fingerprint"],
        "corrected_spec_checkpoint_fingerprint": corrected_spec["checkpoint"]["checkpoint_fingerprint"],
        "package_index_fingerprint": package_index["package_index_fingerprint"],
        "source_report_fingerprint": report_json["report_fingerprint"],
        "repository": report_json["repository"],
        "counts": {"artifacts": 7, "report_sections": 9, "achievement_records": 6, "withheld_claims": 0, "acceptance_criteria": 15, "automated_pass": len(automated_pass), "pending_human": 15 - len(automated_pass)},
        "state": "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT",
        "next_gate": "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
        "package_accepted": False, "pricing_status": "NOT_PRICED",
        "delivery_status": "NOT_DELIVERED", "publication_status": "NOT_PUBLISHED",
        "external_actions_performed": False,
        "next_action": "A human reviews the completed internal package against all fifteen post-build acceptance criteria before any delivery, publication, pricing, outreach, or contract action.",
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {
        "corrected_spec": corrected_spec, "decision": decision, "intake": intake,
        "manifest": manifest, "rollback": rollback, "report_json": report_json,
        "report_markdown": report_markdown, "report_json_fingerprint": report_json_fingerprint,
        "report_markdown_fingerprint": report_markdown_fingerprint,
        "evidence_inventory": evidence_inventory, "acceptance_packet": acceptance_packet,
        "verification_summary": verification_summary, "package_index": package_index,
        "summary": summary,
    }


def verify_pilot_package(*, checkpoint: dict[str, Any] | None = None) -> dict[str, Any]:
    first = build_pilot_package()
    second = build_pilot_package()
    for key in ("report_json_fingerprint", "report_markdown_fingerprint"):
        if first[key] != second[key]:
            raise ProofEngineError(f"pilot package non-deterministic: {key}")
    for key, field in (
        ("evidence_inventory", "inventory_fingerprint"),
        ("acceptance_packet", "packet_fingerprint"),
        ("verification_summary", "verification_fingerprint"),
        ("package_index", "package_index_fingerprint"),
        ("summary", "summary_fingerprint"),
    ):
        if first[key][field] != second[key][field]:
            raise ProofEngineError(f"pilot package non-deterministic: {key}")
    expected_dynamic = {
        "report_json_fingerprint": REPORT_JSON_FINGERPRINT,
        "report_markdown_fingerprint": REPORT_MARKDOWN_FINGERPRINT,
        "evidence_inventory_fingerprint": EVIDENCE_INVENTORY_FINGERPRINT,
        "acceptance_packet_fingerprint": ACCEPTANCE_PACKET_FINGERPRINT,
        "verification_summary_fingerprint": VERIFICATION_SUMMARY_FINGERPRINT,
        "package_index_fingerprint": PACKAGE_INDEX_FINGERPRINT,
        "summary_fingerprint": SUMMARY_FINGERPRINT,
    }
    actual_dynamic = {
        "report_json_fingerprint": first["report_json_fingerprint"],
        "report_markdown_fingerprint": first["report_markdown_fingerprint"],
        "evidence_inventory_fingerprint": first["evidence_inventory"]["inventory_fingerprint"],
        "acceptance_packet_fingerprint": first["acceptance_packet"]["packet_fingerprint"],
        "verification_summary_fingerprint": first["verification_summary"]["verification_fingerprint"],
        "package_index_fingerprint": first["package_index"]["package_index_fingerprint"],
        "summary_fingerprint": first["summary"]["summary_fingerprint"],
    }
    if all(value != "PENDING_PROBE" for value in expected_dynamic.values()) and actual_dynamic != expected_dynamic:
        raise ProofEngineError("pilot package deterministic bindings mismatch")
    if first["acceptance_packet"]["decision"] is not None or first["acceptance_packet"]["package_accepted"] is not False:
        raise ProofEngineError("pilot package manufactured human acceptance")
    if first["summary"]["state"] != "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT" or first["summary"]["next_gate"] != "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED":
        raise ProofEngineError("pilot package terminal state mismatch")
    if checkpoint is None and not CHECKPOINT_PATH.exists():
        return {**first, "dynamic_fingerprints": actual_dynamic}
    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("pilot package checkpoint fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "pilot package checkpoint")
    expected_checkpoint = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-CHECKPOINT-0017",
        "corrected_spec_checkpoint_fingerprint": CORRECTED_SPEC_CHECKPOINT_FINGERPRINT,
        "build_decision_fingerprint": BUILD_DECISION_FINGERPRINT,
        "case_intake_fingerprint": CASE_INTAKE_FINGERPRINT,
        "manifest_fingerprint": MANIFEST_FINGERPRINT,
        "rollback_fingerprint": ROLLBACK_FINGERPRINT,
        "source_report_fingerprint": SOURCE_REPORT_FINGERPRINT,
        **actual_dynamic,
        "state": "INTERNAL_SINGLE_CASE_PILOT_PACKAGE_BUILT",
        "next_gate": "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
        "pilot_package_built": True, "package_accepted": False,
        "next_action": first["summary"]["next_action"],
    }
    for field, expected in expected_checkpoint.items():
        if cp.get(field) != expected:
            raise ProofEngineError(f"pilot package checkpoint mismatch: {field}")
    for field in ("pricing_performed", "outreach_performed", "contract_action_performed", "delivery_performed", "publication_performed", "external_actions_performed", "target_repository_writes_performed"):
        if cp.get(field) is not False:
            raise ProofEngineError(f"pilot package checkpoint exceeded boundary: {field}")
    if CHECKPOINT_FINGERPRINT != "PENDING_PROBE" and cp["checkpoint_fingerprint"] != CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("pilot package checkpoint deterministic mismatch")
    return {**first, "checkpoint": cp, "dynamic_fingerprints": actual_dynamic}
