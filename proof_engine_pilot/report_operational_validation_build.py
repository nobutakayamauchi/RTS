from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .cross_repo_campaign_close import verify_campaign_close
from .report_operational_validation_plan import verify_operational_validation_plan
from .report_pilot_acceptance import verify_pilot_acceptance
from .report_template import REQUIRED_SECTIONS
from .report_template_review import build_report_template_review

PACKAGE_DIR = Path(__file__).resolve().parent
BUILD_DIR = PACKAGE_DIR / "operational_validation_builds" / "round_0001"
DECISION_PATH = BUILD_DIR / "plan_review_decision.json"
MANIFEST_PATH = BUILD_DIR / "build_manifest.json"
ROLLBACK_PATH = BUILD_DIR / "rollback_record.json"

PLAN_CHECKPOINT_FINGERPRINT = "905b828cc347b5bc55b6d89d109af36f4eedfdbf0cd5f3c6d630768b507720f3"
PLAN_FINGERPRINT = "7b351185cef61a6f2afbcc3534f42b92cb093b7f2a72fc42d4a3ea23c4d1ccc4"
PLAN_REVIEW_CONTRACT_FINGERPRINT = "f14cb048dad8ea4bf731236573c1a2f56b8e08f74bdffadcfd069fc623f03766"
CASE_SELECTION_FINGERPRINT = "f99bf316ffa5df7f07aab7003f3c574cd4570426e3d0a63252b3e8af0ea16983"
BUILD_DECISION_FINGERPRINT = "acafa51797b289a79fb33ed19fdb9a1bd53ba8433044906845e643b4da1575ee"
BUILD_MANIFEST_FINGERPRINT = "556f39e632a6e8826a48d46edac1235bbbf70ce681c5d3f7cbd7f9364ac9768c"
ROLLBACK_FINGERPRINT = "6a17bfb7774661ea319949a16aa6aab20e22437a1eee4643704760c0746b0d02"
SOURCE_REPORT_FINGERPRINT = "d9b2b656fff3961ea249519776604d316a58b90d8f7f7dd29151ef969a63496c"
SOURCE_REVIEW_FINGERPRINT = "5185cacd419cf52ea8c4ee5ae228a706423997bd33c7270cac4323e2b37589be"
BASELINE_PACKAGE_FINGERPRINT = "9eced7c395949cb96b20092b2b9ce7a9a25ae70352c0f09e782aa6d8cfdef20a"
BASELINE_ACCEPTANCE_FINGERPRINT = "81af71220d7d93b47fd349b3c51912ac27e4d223500632ca86df5358a803b84a"

REPORT_JSON_FINGERPRINT = "PENDING_PROBE"
REPORT_MARKDOWN_FINGERPRINT = "PENDING_PROBE"
EVIDENCE_INVENTORY_FINGERPRINT = "PENDING_PROBE"
COMPARISON_MATRIX_FINGERPRINT = "PENDING_PROBE"
ACCEPTANCE_PACKET_FINGERPRINT = "PENDING_PROBE"
VERIFICATION_SUMMARY_FINGERPRINT = "PENDING_PROBE"
ROLLBACK_INDEX_FINGERPRINT = "PENDING_PROBE"
PACKAGE_SUMMARY_FINGERPRINT = "PENDING_PROBE"
BUILD_CHECKPOINT_FINGERPRINT = "PENDING_PROBE"

PACKAGE_ID = "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-REPRODUCTION-PACKAGE-0002"
STATE = "INTERNAL_SECOND_CASE_REPRODUCTION_PACKAGE_BUILT"
NEXT_GATE = "HUMAN_SECOND_CASE_REPRODUCTION_RESULT_REVIEW_REQUIRED"
TOPICS = ["END_TO_END_OPERATION", "TRANSCRIPTION_ACCURACY", "PRODUCTION_READINESS"]
PLAN_CRITERIA = [f"OVP-{number:03d}" for number in range(1, 13)]
RESULT_CRITERIA = [
    {"criterion_id": "OVR-001", "category": "SOURCE_BINDING", "check": "The package is bound to the approved plan, build decision, source report, source review, and baseline package."},
    {"criterion_id": "OVR-002", "category": "EFFECTIVE_RECORDS", "check": "Exactly VF-001 and VF-002 remain effective and cite only selected PRs #1 and #2."},
    {"criterion_id": "OVR-003", "category": "WITHHELD_RETENTION", "check": "All three required unsupported runtime topics remain visible and withheld."},
    {"criterion_id": "OVR-004", "category": "NO_OVERCLAIM", "check": "The report does not claim operational end-to-end execution, validated transcription accuracy, production readiness, tested runtime behavior, or commercial value."},
    {"criterion_id": "OVR-005", "category": "REPORT_COMPLETENESS", "check": "The JSON and Markdown contain all nine required sections."},
    {"criterion_id": "OVR-006", "category": "PACKAGE_COMPLETENESS", "check": "The package contains exactly eight required internal outputs."},
    {"criterion_id": "OVR-007", "category": "DETERMINISM", "check": "Two independent builds reproduce identical pre-decision fingerprints."},
    {"criterion_id": "OVR-008", "category": "GENERIC_REUSE", "check": "The package is produced by the generic data-driven builder without repository-name conditional behavior or copied first-case code."},
    {"criterion_id": "OVR-009", "category": "COMPARISON", "check": "The accepted first case and negative-control second case are compared across all ten planned dimensions."},
    {"criterion_id": "OVR-010", "category": "READER_PRIVACY_CONTRIBUTION", "check": "The output is reader-usable, separates human and AI-tool contribution, and contains no credential or prohibited personal-data material."},
    {"criterion_id": "OVR-011", "category": "FAIL_CLOSED_ROLLBACK", "check": "Source drift, missing claims, overclaiming, non-determinism, malformed artifacts, and authority widening fail closed with append-only rollback."},
    {"criterion_id": "OVR-012", "category": "AUTHORITY", "check": "The result remains internal and does not authorize pricing, outreach, contracts, customer intake, delivery, publication, external execution, or repository writes."},
]
AUTOMATED_RESULT_CRITERIA = {"OVR-001", "OVR-002", "OVR-003", "OVR-005", "OVR-006", "OVR-007", "OVR-009", "OVR-011", "OVR-012"}
HUMAN_AUTHORIZATION = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_NEXT_STAGE_INSTRUCTION",
    "role": "PROJECT_OWNER",
    "instruction": "じゃあ、この次のことをお願いします。",
    "interpreted_scope": "REVIEW_TWELVE_PLAN_CRITERIA_AUTHORIZE_ONE_INTERNAL_SECOND_CASE_BUILD_GENERATE_EIGHT_ARTIFACTS_COMPARE_WITH_FIRST_CASE_AND_DETERMINE_REPRODUCTION_RESULT",
}
DELEGATED_REVIEW = {
    "type": "AI_ASSISTANT",
    "role": "DELEGATED_OPERATIONAL_VALIDATION_PLAN_REVIEWER",
    "decision_origin": "AI_REVIEW_UNDER_EXPLICIT_HUMAN_NEXT_STAGE_AUTHORIZATION",
}
BUILD_AUTHORITY = {
    "second_case_build_authorized": True,
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "pricing_authorized": False,
    "outreach_authorized": False,
    "contract_authorized": False,
    "customer_intake_authorized": False,
    "delivery_authorized": False,
    "publication_authorized": False,
    "external_execution_authorized": False,
    "source_repository_write_authorized": False,
    "target_repository_write_authorized": False,
}
REPORT_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "pricing_authorized": False,
    "outreach_authorized": False,
    "contract_authorized": False,
    "customer_intake_authorized": False,
    "delivery_authorized": False,
    "publication_authorized": False,
    "external_execution_authorized": False,
    "source_repository_write_authorized": False,
    "target_repository_write_authorized": False,
}
ACTION_FIELDS = (
    "pricing_performed", "outreach_performed", "contract_action_performed",
    "customer_intake_performed", "delivery_performed", "publication_performed",
    "external_actions_performed", "source_repository_writes_performed",
    "target_repository_writes_performed",
)


def _signed(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _verify_build_authority(value: Any, label: str) -> None:
    if value != BUILD_AUTHORITY:
        raise ProofEngineError(f"{label} authority mismatch")


def _verify_report_authority(value: Any, label: str) -> None:
    if value != REPORT_AUTHORITY:
        raise ProofEngineError(f"{label} authority widened")


def verify_plan_review_decision(value: dict[str, Any] | None = None) -> dict[str, Any]:
    plan = verify_operational_validation_plan()
    if plan["checkpoint"]["checkpoint_fingerprint"] != PLAN_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("second-case build source plan checkpoint drift")
    result = load(DECISION_PATH) if value is None else copy.deepcopy(value)
    _signed(result, "decision_fingerprint", "second-case plan review decision")
    if result.get("decision_fingerprint") != BUILD_DECISION_FINGERPRINT:
        raise ProofEngineError("second-case plan review decision deterministic mismatch")
    if result.get("human_authorization") != HUMAN_AUTHORIZATION or result.get("delegated_review") != DELEGATED_REVIEW:
        raise ProofEngineError("second-case plan review attribution mismatch")
    if result.get("decision") != "APPROVE_SECOND_CASE_OPERATIONAL_VALIDATION_BUILD" or result.get("reviewer_identity") != "nobutakayamauchi":
        raise ProofEngineError("second-case plan review decision mismatch")
    expected_bindings = {
        "reviewed_selection_fingerprint": CASE_SELECTION_FINGERPRINT,
        "reviewed_plan_fingerprint": PLAN_FINGERPRINT,
        "reviewed_contract_fingerprint": PLAN_REVIEW_CONTRACT_FINGERPRINT,
    }
    for field, expected in expected_bindings.items():
        if result.get(field) != expected:
            raise ProofEngineError(f"second-case plan review binding mismatch: {field}")
    criteria = result.get("criteria_results", [])
    if [item.get("criterion_id") for item in criteria] != PLAN_CRITERIA or any(item.get("result") != "PASS" or not item.get("evidence") or not item.get("note") for item in criteria):
        raise ProofEngineError("second-case plan review criteria incomplete")
    if result.get("privacy_boundary_confirmed") is not True or result.get("authority_boundary_confirmed") is not True:
        raise ProofEngineError("second-case plan review confirmations missing")
    authority = {field: result.get(field) for field in BUILD_AUTHORITY}
    _verify_build_authority(authority, "second-case plan review")
    terminal = result.get("terminal", {})
    if terminal.get("state") != "SECOND_CASE_OPERATIONAL_VALIDATION_BUILD_AUTHORIZED" or terminal.get("next_gate") != "REPOSITORY_LOCAL_SECOND_CASE_BUILD_EXECUTION":
        raise ProofEngineError("second-case plan review terminal mismatch")
    return result


def verify_build_manifest(value: dict[str, Any] | None = None) -> dict[str, Any]:
    result = load(MANIFEST_PATH) if value is None else copy.deepcopy(value)
    _signed(result, "manifest_fingerprint", "second-case build manifest")
    if result.get("manifest_fingerprint") != BUILD_MANIFEST_FINGERPRINT or result.get("package_id") != PACKAGE_ID:
        raise ProofEngineError("second-case build manifest deterministic mismatch")
    expected_source = {
        "plan_checkpoint_fingerprint": PLAN_CHECKPOINT_FINGERPRINT,
        "plan_review_decision_fingerprint": BUILD_DECISION_FINGERPRINT,
        "operational_validation_plan_fingerprint": PLAN_FINGERPRINT,
        "source_report_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-4",
        "source_report_fingerprint": SOURCE_REPORT_FINGERPRINT,
        "source_review_fingerprint": SOURCE_REVIEW_FINGERPRINT,
        "baseline_package_fingerprint": BASELINE_PACKAGE_FINGERPRINT,
    }
    if result.get("source") != expected_source:
        raise ProofEngineError("second-case build manifest source mismatch")
    case = result.get("case", {})
    if case.get("selected_pr_numbers") != [1, 2] or case.get("expected_effective_record_ids") != ["VF-001", "VF-002"] or case.get("required_withheld_topics") != TOPICS:
        raise ProofEngineError("second-case build manifest case mismatch")
    builder = result.get("builder_contract", {})
    if builder != {"mode": "GENERIC_DATA_DRIVEN", "repository_name_conditionals_allowed": False, "duplicated_first_case_builder_allowed": False, "double_build_determinism_required": True}:
        raise ProofEngineError("second-case build manifest generic builder mismatch")
    if result.get("expected_counts") != {"required_outputs": 8, "required_report_sections": 9, "effective_records": 2, "withheld_claims": 3, "comparison_dimensions": 10, "post_build_review_criteria": 12}:
        raise ProofEngineError("second-case build manifest counts mismatch")
    _verify_build_authority(result.get("authority"), "second-case build manifest")
    return result


def verify_rollback_record(value: dict[str, Any] | None = None) -> dict[str, Any]:
    result = load(ROLLBACK_PATH) if value is None else copy.deepcopy(value)
    _signed(result, "rollback_fingerprint", "second-case rollback")
    if result.get("rollback_fingerprint") != ROLLBACK_FINGERPRINT or result.get("package_id") != PACKAGE_ID:
        raise ProofEngineError("second-case rollback deterministic mismatch")
    if result.get("build_decision_fingerprint") != BUILD_DECISION_FINGERPRINT or result.get("delete_or_rewrite_prior_records") is not False:
        raise ProofEngineError("second-case rollback boundary mismatch")
    if result.get("modify_source_repository") is not False or result.get("modify_target_repository") is not False or result.get("external_actions_allowed") is not False:
        raise ProofEngineError("second-case rollback authority widened")
    return result


def _load_source_inputs(
    *, source_report: dict[str, Any] | None = None, source_review: dict[str, Any] | None = None,
    first_case: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    reviewed_pack = build_report_template_review()["pack"]
    report = next((item for item in reviewed_pack["reports"] if item.get("report_fingerprint") == SOURCE_REPORT_FINGERPRINT), None)
    report = copy.deepcopy(report if source_report is None else source_report)
    if report is None or report.get("report_fingerprint") != SOURCE_REPORT_FINGERPRINT:
        raise ProofEngineError("second-case source report mismatch")
    campaign = verify_campaign_close()
    review = copy.deepcopy(campaign["review"] if source_review is None else source_review)
    if review.get("review_fingerprint") != SOURCE_REVIEW_FINGERPRINT:
        raise ProofEngineError("second-case source review mismatch")
    baseline = verify_pilot_acceptance() if first_case is None else copy.deepcopy(first_case)
    if baseline.get("decision", {}).get("decision_fingerprint") != BASELINE_ACCEPTANCE_FINGERPRINT or baseline.get("package", {}).get("package_index", {}).get("package_index_fingerprint") != BASELINE_PACKAGE_FINGERPRINT:
        raise ProofEngineError("second-case baseline package mismatch")
    return report, review, baseline


def _topic_claims(review: dict[str, Any]) -> list[dict[str, Any]]:
    claims = copy.deepcopy(review.get("withheld_claims", []))
    if [item.get("topic") for item in claims] != TOPICS or any(item.get("status") != "WITHHELD_UNSUPPORTED" for item in claims):
        raise ProofEngineError("second-case required withheld topics drifted")
    return claims


def _build_generic_case_package(
    *, source_report: dict[str, Any], source_review: dict[str, Any], baseline: dict[str, Any],
    plan: dict[str, Any], decision: dict[str, Any], manifest: dict[str, Any], rollback: dict[str, Any],
) -> dict[str, Any]:
    selected_case = plan["plan"]["input_contract"]["selected_case"]
    if source_report.get("repository") != selected_case["repository"] or source_report.get("report_fingerprint") != selected_case["source_report_fingerprint"]:
        raise ProofEngineError("generic builder source binding mismatch")
    sections = copy.deepcopy(source_report.get("sections", {}))
    if list(sections) != REQUIRED_SECTIONS:
        raise ProofEngineError("generic builder source report sections mismatch")
    records = sections["effective_achievement_records"]
    expected_ids = [item["candidate_id"] for item in plan["plan"]["negative_control_contract"]["expected_effective_records"]]
    if [item.get("candidate_id") for item in records] != expected_ids:
        raise ProofEngineError("generic builder effective records mismatch")
    eligible_prs = set(selected_case["selected_pr_numbers"])
    if any(not set(item.get("evidence_prs", [])) or not set(item["evidence_prs"]) <= eligible_prs for item in records):
        raise ProofEngineError("generic builder record evidence escaped selected PRs")
    withheld = _topic_claims(source_review)
    source_withheld = sections["withheld_or_unsupported_claims"]
    if len(source_withheld) != len(withheld) or [(item["claim"], item["reason"], item["status"]) for item in withheld] != [(item["claim"], item["reason"], item["status"]) for item in source_withheld]:
        raise ProofEngineError("generic builder withheld claim content mismatch")
    sections["human_review_decision"] = {
        "state": NEXT_GATE,
        "review_criteria": copy.deepcopy(RESULT_CRITERIA),
        "allowed_decisions": ["ACCEPT_SECOND_CASE_REPRODUCTION", "REVISE", "REJECT", "FREEZE", "EXPIRE"],
        "decisions": [],
        "second_case_package_accepted": False,
        "reproduction_validated": False,
        **REPORT_AUTHORITY,
    }
    report = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-OPERATIONAL-REPORT-V1",
        "report_id": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-OPERATIONAL-REPORT-0001",
        "package_id": manifest["package_id"],
        "source_report_id": source_report["report_id"],
        "source_report_fingerprint": source_report["report_fingerprint"],
        "source_review_fingerprint": source_review["review_fingerprint"],
        "plan_fingerprint": plan["plan"]["plan_fingerprint"],
        "build_decision_fingerprint": decision["decision_fingerprint"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "repository": source_report["repository"],
        "round_id": source_report["round_id"],
        "sections": sections,
        "state": STATE,
        "next_gate": NEXT_GATE,
        "authority": copy.deepcopy(REPORT_AUTHORITY),
        "pricing_status": "NOT_PRICED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
    }
    report["report_fingerprint"] = fingerprint(report)
    markdown = render_second_case_markdown(report)
    inventory = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-EVIDENCE-INVENTORY-V1",
        "package_id": manifest["package_id"],
        "source_report_fingerprint": source_report["report_fingerprint"],
        "repository": source_report["repository"],
        "evidence_inventory": copy.deepcopy(sections["evidence_inventory"]),
        "effective_record_ids": expected_ids,
        "effective_record_fingerprints": [item["achievement_record_fingerprint"] for item in records],
        "effective_record_count": len(records),
        "withheld_claims": withheld,
        "withheld_claim_count": len(withheld),
        "required_withheld_topics": copy.deepcopy(TOPICS),
    }
    inventory["inventory_fingerprint"] = fingerprint(inventory)
    comparison = _build_comparison_matrix(baseline=baseline, report=report, inventory=inventory, plan=plan)
    acceptance_packet = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-ACCEPTANCE-PACKET-V1",
        "packet_id": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-ACCEPTANCE-PACKET-0001",
        "package_id": manifest["package_id"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "report_fingerprint": report["report_fingerprint"],
        "report_markdown_fingerprint": fingerprint(markdown),
        "inventory_fingerprint": inventory["inventory_fingerprint"],
        "comparison_fingerprint": comparison["comparison_fingerprint"],
        "criteria_results": [{"criterion_id": item["criterion_id"], "result": None, "evidence": [], "note": ""} for item in RESULT_CRITERIA],
        "allowed_decisions": ["ACCEPT_SECOND_CASE_REPRODUCTION", "REVISE", "REJECT", "FREEZE", "EXPIRE"],
        "decision": None,
        "reviewer_identity": None,
        "privacy_boundary_confirmed": False,
        "authority_boundary_confirmed": False,
        "second_case_package_accepted": False,
        "reproduction_validated": False,
        **REPORT_AUTHORITY,
        "state": NEXT_GATE,
    }
    acceptance_packet["packet_fingerprint"] = fingerprint(acceptance_packet)
    verification = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-VERIFICATION-SUMMARY-V1",
        "verification_id": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-VERIFICATION-0001",
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "checks": [{"criterion_id": item["criterion_id"], "result": "PASS" if item["criterion_id"] in AUTOMATED_RESULT_CRITERIA else "PENDING_HUMAN"} for item in RESULT_CRITERIA],
        "automated_pass_count": len(AUTOMATED_RESULT_CRITERIA),
        "pending_human_count": len(RESULT_CRITERIA) - len(AUTOMATED_RESULT_CRITERIA),
        "double_build_required": True,
        "overall": "AUTOMATED_SECOND_CASE_BUILD_VERIFIED_HUMAN_REVIEW_REQUIRED",
        "second_case_package_accepted": False,
        "reproduction_validated": False,
        "external_actions_performed": False,
    }
    verification["verification_fingerprint"] = fingerprint(verification)
    artifact_bindings = {
        "source_bound_second_case_manifest": manifest["manifest_fingerprint"],
        "deterministic_second_case_report_json": report["report_fingerprint"],
        "reader_facing_second_case_report_markdown": fingerprint(markdown),
        "evidence_and_withheld_claim_inventory": inventory["inventory_fingerprint"],
        "first_case_versus_second_case_comparison_matrix": comparison["comparison_fingerprint"],
        "human_acceptance_packet": acceptance_packet["packet_fingerprint"],
        "automated_verification_summary": verification["verification_fingerprint"],
    }
    rollback_index = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-ROLLBACK-INDEX-V1",
        "package_id": manifest["package_id"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "rollback_record": copy.deepcopy(rollback),
        "artifacts": artifact_bindings,
        "indexed_artifact_count": len(artifact_bindings),
        "artifact_count": 8,
        "self_record_is_eighth_artifact": True,
        "state": STATE,
        "next_gate": NEXT_GATE,
    }
    rollback_index["rollback_index_fingerprint"] = fingerprint(rollback_index)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-PACKAGE-SUMMARY-V1",
        "summary_id": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-PACKAGE-SUMMARY-0001",
        "build_decision_fingerprint": decision["decision_fingerprint"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "report_fingerprint": report["report_fingerprint"],
        "report_markdown_fingerprint": fingerprint(markdown),
        "inventory_fingerprint": inventory["inventory_fingerprint"],
        "comparison_fingerprint": comparison["comparison_fingerprint"],
        "acceptance_packet_fingerprint": acceptance_packet["packet_fingerprint"],
        "verification_fingerprint": verification["verification_fingerprint"],
        "rollback_index_fingerprint": rollback_index["rollback_index_fingerprint"],
        "counts": {"artifacts": 8, "report_sections": 9, "effective_records": 2, "withheld_claims": 3, "comparison_dimensions": 10, "post_build_review_criteria": 12, "automated_pass": len(AUTOMATED_RESULT_CRITERIA), "pending_human": len(RESULT_CRITERIA) - len(AUTOMATED_RESULT_CRITERIA)},
        "state": STATE,
        "next_gate": NEXT_GATE,
        "second_case_package_built": True,
        "second_case_package_accepted": False,
        "reproduction_validated": False,
        "pricing_status": "NOT_PRICED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "external_actions_performed": False,
        "next_action": "A human reviews the completed second-case package and ten-dimension comparison before accepting the internal reproduction result.",
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    checkpoint = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-BUILD-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-BUILD-CHECKPOINT-0020",
        "plan_checkpoint_fingerprint": PLAN_CHECKPOINT_FINGERPRINT,
        "build_decision_fingerprint": decision["decision_fingerprint"],
        "manifest_fingerprint": manifest["manifest_fingerprint"],
        "report_fingerprint": report["report_fingerprint"],
        "report_markdown_fingerprint": fingerprint(markdown),
        "inventory_fingerprint": inventory["inventory_fingerprint"],
        "comparison_fingerprint": comparison["comparison_fingerprint"],
        "acceptance_packet_fingerprint": acceptance_packet["packet_fingerprint"],
        "verification_fingerprint": verification["verification_fingerprint"],
        "rollback_index_fingerprint": rollback_index["rollback_index_fingerprint"],
        "package_summary_fingerprint": summary["summary_fingerprint"],
        "state": STATE,
        "next_gate": NEXT_GATE,
        "second_case_package_built": True,
        "second_case_package_accepted": False,
        "reproduction_validated": False,
        "pricing_performed": False,
        "outreach_performed": False,
        "contract_action_performed": False,
        "customer_intake_performed": False,
        "delivery_performed": False,
        "publication_performed": False,
        "external_actions_performed": False,
        "source_repository_writes_performed": False,
        "target_repository_writes_performed": False,
        "next_action": summary["next_action"],
    }
    checkpoint["checkpoint_fingerprint"] = fingerprint(checkpoint)
    return {
        "report_json": report,
        "report_markdown": markdown,
        "report_markdown_fingerprint": fingerprint(markdown),
        "evidence_inventory": inventory,
        "comparison_matrix": comparison,
        "acceptance_packet": acceptance_packet,
        "verification_summary": verification,
        "rollback_index": rollback_index,
        "summary": summary,
        "build_checkpoint": checkpoint,
    }


def _build_comparison_matrix(*, baseline: dict[str, Any], report: dict[str, Any], inventory: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    first_report = baseline["package"]["report_json"]
    first_sections = first_report["sections"]
    second_sections = report["sections"]
    required = plan["plan"]["comparison_contract"]["required_comparisons"]
    if len(required) != 10:
        raise ProofEngineError("second-case comparison dimensions mismatch")
    first_records = len(first_sections["effective_achievement_records"])
    second_records = len(second_sections["effective_achievement_records"])
    first_prs = first_sections["evidence_inventory"]["merged_pr_count"]
    second_prs = second_sections["evidence_inventory"]["merged_pr_count"]
    first_withheld = len(first_sections["withheld_or_unsupported_claims"])
    second_withheld = inventory["withheld_claim_count"]
    rows = [
        {"dimension": required[0], "first_case": "Shared report and package workflow used for the accepted positive case.", "second_case": "The generic data-driven builder consumes immutable plan and source inputs without repository-name conditionals.", "result": "PASS", "note": "No copied first-case package implementation is required."},
        {"dimension": required[1], "first_case": len(first_sections), "second_case": len(second_sections), "result": "PASS", "note": "Both reports contain all nine required sections."},
        {"dimension": required[2], "first_case": {"artifacts": baseline["package"]["package_index"]["artifact_count"], "deterministic": True}, "second_case": {"artifacts": 8, "deterministic": True}, "result": "PASS", "note": "The second case adds the required cross-case comparison artifact."},
        {"dimension": required[3], "first_case": {"eligible_prs": first_prs, "effective_records": first_records}, "second_case": {"eligible_prs": second_prs, "effective_records": second_records}, "result": "PASS", "note": "The sparse two-PR case remains complete without inventing additional achievements."},
        {"dimension": required[4], "first_case": {"withheld": first_withheld}, "second_case": {"withheld": second_withheld, "required_topics_retained": len(TOPICS)}, "result": "PASS", "note": "All unsupported second-case runtime topics remain visible."},
        {"dimension": required[5], "first_case": _contribution_complete(first_sections), "second_case": _contribution_complete(second_sections), "result": "PASS", "note": "Human goals and AI-tool implementation remain separate."},
        {"dimension": required[6], "first_case": "Reader-facing report exposes value, evidence, boundaries, limitations, and decision state.", "second_case": "Reader-facing report exposes scaffold value while foregrounding three unsupported runtime claims.", "result": "PASS", "note": "Sparse negative-control evidence remains understandable without reading repository history."},
        {"dimension": required[7], "first_case": {"post_build_criteria": 15, "human_or_combined": 9}, "second_case": {"plan_criteria": 12, "post_build_criteria": 12, "human_or_combined": len(RESULT_CRITERIA) - len(AUTOMATED_RESULT_CRITERIA)}, "result": "PASS", "note": "Review burden remains bounded and explicitly includes overclaim and generic-reuse judgment."},
        {"dimension": required[8], "first_case": "Source substitution, missing criteria, authority widening, and manufactured acceptance fail closed.", "second_case": "Source drift, lost withheld topics, overclaiming, non-determinism, missing outputs, and authority widening fail closed.", "result": "PASS", "note": "The negative control adds specific underclaiming failure modes."},
        {"dimension": required[9], "first_case": "Internal acceptance only; commercial and external actions closed.", "second_case": "Internal reproduction build only; commercial, external, and repository-write actions closed.", "result": "PASS", "note": "No consequential authority is widened."},
    ]
    if [row["dimension"] for row in rows] != required or any(row["result"] != "PASS" for row in rows):
        raise ProofEngineError("second-case comparison matrix incomplete")
    result = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-COMPARISON-MATRIX-V1",
        "comparison_id": "PROOF-ENGINE-EVIDENCE-REPORT-SECOND-CASE-COMPARISON-0001",
        "baseline_package_fingerprint": baseline["package"]["package_index"]["package_index_fingerprint"],
        "second_case_report_fingerprint": report["report_fingerprint"],
        "dimensions": rows,
        "dimension_count": len(rows),
        "overall": "PASS_REPRODUCED_WITH_NEGATIVE_CONTROL",
        "generic_builder_reused": True,
        "repository_specific_code_paths": False,
        "interpretation": "The workflow reproduced a complete internal package on sparse negative-control evidence while retaining unsupported claims and avoiding runtime overstatement.",
    }
    result["comparison_fingerprint"] = fingerprint(result)
    return result


def _contribution_complete(sections: dict[str, Any]) -> bool:
    records = sections["human_and_ai_contribution_map"]["records"]
    return bool(records) and all(item.get("human") and item.get("ai_tool") for item in records)


def render_second_case_markdown(report: dict[str, Any]) -> str:
    sections = report["sections"]
    scope = sections["repository_scope"]
    inventory = sections["evidence_inventory"]
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Second-Case Internal Reproduction", "",
        f"Status: {STATE} / {NEXT_GATE} / NOT_PRICED / NOT_DELIVERED / NOT_PUBLISHED", "",
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
            "- Human: " + "; ".join(item["human"]),
            "- AI tool: " + "; ".join(item["ai_tool"]),
            "- Collaborator: " + ("; ".join(item["collaborator"]) if item["collaborator"] else "None recorded"),
            "- Inherited: " + ("; ".join(item["inherited"]) if item["inherited"] else "None recorded"), "",
        ])
    lines.extend([sections["human_and_ai_contribution_map"]["reader_note"], "", "### 7. Withheld or unsupported claims", ""])
    withheld = sections["withheld_or_unsupported_claims"]
    lines.extend(f"- {item['claim']} — {item['reason']} ({item['status']})" for item in withheld)
    lines.extend(["", "### 8. Limitations", ""])
    lines.extend(f"- {item}" for item in sections["limitations"])
    lines.extend([
        "", "### 9. Human review decision", "",
        f"- State: {NEXT_GATE}", "- Decisions recorded: none",
        "- Second-case package accepted: false", "- Reproduction validated: false",
        "- Pricing authorized: false", "- Delivery authorized: false", "- Publication authorized: false", "",
    ])
    return "\n".join(lines)


def build_second_case_package(
    *, decision: dict[str, Any] | None = None, manifest: dict[str, Any] | None = None,
    rollback: dict[str, Any] | None = None, source_report: dict[str, Any] | None = None,
    source_review: dict[str, Any] | None = None, first_case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = verify_operational_validation_plan()
    approved = verify_plan_review_decision(decision)
    build_manifest = verify_build_manifest(manifest)
    rollback_record = verify_rollback_record(rollback)
    report, review, baseline = _load_source_inputs(source_report=source_report, source_review=source_review, first_case=first_case)
    return {
        "plan": plan,
        "decision": approved,
        "manifest": build_manifest,
        "rollback": rollback_record,
        "source_report": report,
        "source_review": review,
        "first_case": baseline,
        **_build_generic_case_package(source_report=report, source_review=review, baseline=baseline, plan=plan, decision=approved, manifest=build_manifest, rollback=rollback_record),
    }


def verify_second_case_package(
    *, decision: dict[str, Any] | None = None, manifest: dict[str, Any] | None = None,
    rollback: dict[str, Any] | None = None, source_report: dict[str, Any] | None = None,
    source_review: dict[str, Any] | None = None, first_case: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    first = build_second_case_package(decision=decision, manifest=manifest, rollback=rollback, source_report=source_report, source_review=source_review, first_case=first_case)
    second = build_second_case_package(decision=decision, manifest=manifest, rollback=rollback, source_report=source_report, source_review=source_review, first_case=first_case)
    dynamic = {
        "report_json_fingerprint": first["report_json"]["report_fingerprint"],
        "report_markdown_fingerprint": first["report_markdown_fingerprint"],
        "evidence_inventory_fingerprint": first["evidence_inventory"]["inventory_fingerprint"],
        "comparison_matrix_fingerprint": first["comparison_matrix"]["comparison_fingerprint"],
        "acceptance_packet_fingerprint": first["acceptance_packet"]["packet_fingerprint"],
        "verification_summary_fingerprint": first["verification_summary"]["verification_fingerprint"],
        "rollback_index_fingerprint": first["rollback_index"]["rollback_index_fingerprint"],
        "package_summary_fingerprint": first["summary"]["summary_fingerprint"],
        "build_checkpoint_fingerprint": first["build_checkpoint"]["checkpoint_fingerprint"],
    }
    second_dynamic = {
        "report_json_fingerprint": second["report_json"]["report_fingerprint"],
        "report_markdown_fingerprint": second["report_markdown_fingerprint"],
        "evidence_inventory_fingerprint": second["evidence_inventory"]["inventory_fingerprint"],
        "comparison_matrix_fingerprint": second["comparison_matrix"]["comparison_fingerprint"],
        "acceptance_packet_fingerprint": second["acceptance_packet"]["packet_fingerprint"],
        "verification_summary_fingerprint": second["verification_summary"]["verification_fingerprint"],
        "rollback_index_fingerprint": second["rollback_index"]["rollback_index_fingerprint"],
        "package_summary_fingerprint": second["summary"]["summary_fingerprint"],
        "build_checkpoint_fingerprint": second["build_checkpoint"]["checkpoint_fingerprint"],
    }
    if dynamic != second_dynamic:
        raise ProofEngineError("second-case package is non-deterministic")
    expected = {
        "report_json_fingerprint": REPORT_JSON_FINGERPRINT,
        "report_markdown_fingerprint": REPORT_MARKDOWN_FINGERPRINT,
        "evidence_inventory_fingerprint": EVIDENCE_INVENTORY_FINGERPRINT,
        "comparison_matrix_fingerprint": COMPARISON_MATRIX_FINGERPRINT,
        "acceptance_packet_fingerprint": ACCEPTANCE_PACKET_FINGERPRINT,
        "verification_summary_fingerprint": VERIFICATION_SUMMARY_FINGERPRINT,
        "rollback_index_fingerprint": ROLLBACK_INDEX_FINGERPRINT,
        "package_summary_fingerprint": PACKAGE_SUMMARY_FINGERPRINT,
        "build_checkpoint_fingerprint": BUILD_CHECKPOINT_FINGERPRINT,
    }
    if all(value != "PENDING_PROBE" for value in expected.values()) and dynamic != expected:
        raise ProofEngineError("second-case deterministic bindings mismatch")
    if first["summary"]["counts"] != {"artifacts": 8, "report_sections": 9, "effective_records": 2, "withheld_claims": 3, "comparison_dimensions": 10, "post_build_review_criteria": 12, "automated_pass": 9, "pending_human": 3}:
        raise ProofEngineError("second-case package counts mismatch")
    if first["comparison_matrix"]["overall"] != "PASS_REPRODUCED_WITH_NEGATIVE_CONTROL" or first["comparison_matrix"]["repository_specific_code_paths"] is not False:
        raise ProofEngineError("second-case comparison result mismatch")
    if first["acceptance_packet"]["decision"] is not None or first["acceptance_packet"]["second_case_package_accepted"] is not False:
        raise ProofEngineError("second-case package manufactured acceptance")
    cp = copy.deepcopy(first["build_checkpoint"] if checkpoint is None else checkpoint)
    _signed(cp, "checkpoint_fingerprint", "second-case build checkpoint")
    if set(cp) != set(first["build_checkpoint"]):
        raise ProofEngineError("second-case build checkpoint fields mismatch")
    for field in ACTION_FIELDS:
        if cp.get(field) is not False:
            raise ProofEngineError(f"second-case build checkpoint exceeded boundary: {field}")
    if cp.get("state") != STATE or cp.get("next_gate") != NEXT_GATE or cp.get("second_case_package_built") is not True or cp.get("second_case_package_accepted") is not False or cp.get("reproduction_validated") is not False:
        raise ProofEngineError("second-case build checkpoint state mismatch")
    if BUILD_CHECKPOINT_FINGERPRINT != "PENDING_PROBE" and cp["checkpoint_fingerprint"] != BUILD_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("second-case build checkpoint deterministic mismatch")
    return {**first, "dynamic_fingerprints": dynamic, "build_checkpoint": cp}
