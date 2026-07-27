from __future__ import annotations

import copy
import inspect
from pathlib import Path
from typing import Any

from .core import ProofEngineError, canonical_json, fingerprint, load
from . import report_operational_validation_build as _build_impl
from .report_operational_validation_build_v2 import (
    ACCEPTANCE_PACKET_FINGERPRINT,
    BUILD_CHECKPOINT_FINGERPRINT,
    COMPARISON_MATRIX_FINGERPRINT,
    EVIDENCE_INVENTORY_FINGERPRINT,
    PACKAGE_SUMMARY_FINGERPRINT,
    REPORT_JSON_FINGERPRINT,
    REPORT_MARKDOWN_FINGERPRINT,
    RESULT_CRITERIA,
    ROLLBACK_INDEX_FINGERPRINT,
    TOPICS,
    VERIFICATION_SUMMARY_FINGERPRINT,
    verify_second_case_package,
)

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
BUILD_DIR = PACKAGE_DIR / "operational_validation_builds" / "round_0001"
ACCEPTANCE_PATH = BUILD_DIR / "acceptance_decision.json"
EVALUATION_PATH = BUILD_DIR / "evaluation.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_operational_reproduction_checkpoint_0021.json"

PLAN_CHECKPOINT_FINGERPRINT = "905b828cc347b5bc55b6d89d109af36f4eedfdbf0cd5f3c6d630768b507720f3"
BUILD_DECISION_FINGERPRINT = "acafa51797b289a79fb33ed19fdb9a1bd53ba8433044906845e643b4da1575ee"
BUILD_MANIFEST_FINGERPRINT = "556f39e632a6e8826a48d46edac1235bbbf70ce681c5d3f7cbd7f9364ac9768c"
BASELINE_PACKAGE_FINGERPRINT = "9eced7c395949cb96b20092b2b9ce7a9a25ae70352c0f09e782aa6d8cfdef20a"
ACCEPTANCE_DECISION_FINGERPRINT = "fa5b8e84c23b4e5244cd5d8c32f5a63bd081aabcad355a8efa60ebb757c075c8"
EVALUATION_FINGERPRINT = "dd23947b37961651a8a9e26051696fc0e1266cd312eaaab3ff5fef8da409b762"
CHECKPOINT_FINGERPRINT = "3c47a8f325558f444c283f2cbea8d61f258470c91ec3c8ad9cd6e23028bc366c"
FINAL_STATE = "INTERNAL_TWO_CASE_OPERATIONAL_REPRODUCTION_VALIDATED"
FINAL_GATE = "HUMAN_PRODUCT_READINESS_REVIEW_REQUIRED"
FINAL_ACTION = "Review the two-case internal result and decide whether to open a bounded product-readiness assessment; stop before pricing, outreach, contracts, customer intake, delivery, or publication."
CRITERIA_IDS = [f"OVR-{number:03d}" for number in range(1, 13)]
HYPOTHESIS_IDS = [f"OV-H{number:02d}" for number in range(1, 6)]
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
    "role": "DELEGATED_SECOND_CASE_REPRODUCTION_REVIEWER",
    "decision_origin": "AI_POST_BUILD_REVIEW_UNDER_EXPLICIT_HUMAN_NEXT_STAGE_AUTHORIZATION",
}
FALSE_AUTHORITY_FIELDS = (
    "automatic_approval_authorized", "automatic_rewrite_authorized", "pricing_authorized",
    "outreach_authorized", "contract_authorized", "customer_intake_authorized",
    "delivery_authorized", "publication_authorized", "external_execution_authorized",
    "source_repository_write_authorized", "target_repository_write_authorized",
)
ACTION_FIELDS = (
    "pricing_performed", "outreach_performed", "contract_action_performed",
    "customer_intake_performed", "delivery_performed", "publication_performed",
    "external_actions_performed", "source_repository_writes_performed",
    "target_repository_writes_performed",
)
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "plan_checkpoint_fingerprint",
    "build_checkpoint_fingerprint", "acceptance_decision_fingerprint",
    "evaluation_fingerprint", "comparison_fingerprint",
    "second_case_package_summary_fingerprint", "state", "next_gate",
    "second_case_package_built", "second_case_package_accepted",
    "reproduction_validated", *ACTION_FIELDS, "next_action", "checkpoint_fingerprint",
}


def _signed(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _closed_authority(value: dict[str, Any], label: str) -> None:
    for field in FALSE_AUTHORITY_FIELDS:
        if value.get(field) is not False:
            raise ProofEngineError(f"{label} authority widened: {field}")


def _verify_completed_package(package: dict[str, Any]) -> None:
    report = package["report_json"]
    sections = report["sections"]
    if [item.get("candidate_id") for item in sections["effective_achievement_records"]] != ["VF-001", "VF-002"]:
        raise ProofEngineError("accepted second-case records mismatch")
    if [item.get("topic") for item in package["evidence_inventory"]["withheld_claims"]] != TOPICS:
        raise ProofEngineError("accepted second-case withheld topics mismatch")
    if any(item.get("status") != "WITHHELD_UNSUPPORTED" for item in package["evidence_inventory"]["withheld_claims"]):
        raise ProofEngineError("accepted second-case withheld status mismatch")
    comparison = package["comparison_matrix"]
    if comparison.get("overall") != "PASS_REPRODUCED_WITH_NEGATIVE_CONTROL" or comparison.get("dimension_count") != 10:
        raise ProofEngineError("accepted second-case comparison mismatch")
    if comparison.get("generic_builder_reused") is not True or comparison.get("repository_specific_code_paths") is not False:
        raise ProofEngineError("accepted second-case generic reuse mismatch")
    generic_source = inspect.getsource(_build_impl._build_generic_case_package)
    if "nobutakayamauchi/rts-video-flow" in generic_source or "nobutakayamauchi/seminar-compass" in generic_source:
        raise ProofEngineError("generic second-case builder contains repository-specific literal")
    contribution = sections["human_and_ai_contribution_map"]["records"]
    if not contribution or any(not item.get("human") or not item.get("ai_tool") for item in contribution):
        raise ProofEngineError("accepted second-case contribution separation incomplete")
    review_text = (canonical_json(report) + "\n" + package["report_markdown"]).lower()
    secret_markers = ("ghp_", "github_pat_", "akia", "begin private key", '"password":', '"secret":', '"access_token":')
    if any(marker in review_text for marker in secret_markers):
        raise ProofEngineError("accepted second-case package contains credential-like material")
    prohibited_positive_phrases = (
        "end-to-end workflow is operational", "japanese transcription accuracy is established",
        "the repository is production ready", "automated tests prove runtime behavior",
        "external user value or commercial effectiveness is established",
    )
    if any(phrase in review_text for phrase in prohibited_positive_phrases):
        raise ProofEngineError("accepted second-case package contains prohibited positive claim")
    markdown_markers = tuple(f"### {number}." for number in range(1, 10)) + (
        "WITHHELD_UNSUPPORTED", "Evidence boundary:", "Human and AI contribution map",
    )
    if any(marker not in package["report_markdown"] for marker in markdown_markers):
        raise ProofEngineError("accepted second-case reader report incomplete")
    _closed_authority(report["authority"], "accepted second-case report")
    checkpoint = package["build_checkpoint"]
    for field in ACTION_FIELDS:
        if checkpoint.get(field) is not False:
            raise ProofEngineError(f"accepted second-case build exceeded boundary: {field}")


def verify_reproduction_acceptance_decision(
    value: dict[str, Any] | None = None, *, package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verified_package = verify_second_case_package() if package is None else copy.deepcopy(package)
    _verify_completed_package(verified_package)
    result = load(ACCEPTANCE_PATH) if value is None else copy.deepcopy(value)
    _signed(result, "decision_fingerprint", "second-case reproduction acceptance")
    if result.get("decision_fingerprint") != ACCEPTANCE_DECISION_FINGERPRINT:
        raise ProofEngineError("second-case reproduction acceptance deterministic mismatch")
    if result.get("human_authorization") != HUMAN_AUTHORIZATION or result.get("delegated_review") != DELEGATED_REVIEW:
        raise ProofEngineError("second-case reproduction acceptance attribution mismatch")
    if result.get("decision") != "ACCEPT_SECOND_CASE_REPRODUCTION" or result.get("reviewer_identity") != "nobutakayamauchi":
        raise ProofEngineError("second-case reproduction acceptance decision mismatch")
    if result.get("acceptance_scope") != "INTERNAL_TWO_CASE_REPRODUCTION_ONLY":
        raise ProofEngineError("second-case reproduction acceptance scope widened")
    expected_bindings = {
        "reviewed_plan_review_decision_fingerprint": BUILD_DECISION_FINGERPRINT,
        "reviewed_manifest_fingerprint": BUILD_MANIFEST_FINGERPRINT,
        "reviewed_report_fingerprint": REPORT_JSON_FINGERPRINT,
        "reviewed_report_markdown_fingerprint": REPORT_MARKDOWN_FINGERPRINT,
        "reviewed_inventory_fingerprint": EVIDENCE_INVENTORY_FINGERPRINT,
        "reviewed_comparison_fingerprint": COMPARISON_MATRIX_FINGERPRINT,
        "reviewed_acceptance_packet_fingerprint": ACCEPTANCE_PACKET_FINGERPRINT,
        "reviewed_verification_fingerprint": VERIFICATION_SUMMARY_FINGERPRINT,
        "reviewed_rollback_index_fingerprint": ROLLBACK_INDEX_FINGERPRINT,
        "reviewed_package_summary_fingerprint": PACKAGE_SUMMARY_FINGERPRINT,
        "reviewed_build_checkpoint_fingerprint": BUILD_CHECKPOINT_FINGERPRINT,
    }
    for field, expected in expected_bindings.items():
        if result.get(field) != expected:
            raise ProofEngineError(f"second-case reproduction acceptance binding mismatch: {field}")
    criteria = result.get("criteria_results", [])
    if [item.get("criterion_id") for item in criteria] != CRITERIA_IDS or any(item.get("result") != "PASS" or not item.get("evidence") or not item.get("note") for item in criteria):
        raise ProofEngineError("second-case reproduction acceptance criteria incomplete")
    if result.get("privacy_boundary_confirmed") is not True or result.get("authority_boundary_confirmed") is not True:
        raise ProofEngineError("second-case reproduction acceptance confirmations missing")
    if result.get("generic_reuse_confirmed") is not True or result.get("withheld_claim_retention_confirmed") is not True:
        raise ProofEngineError("second-case reproduction acceptance validation confirmations missing")
    if result.get("second_case_package_accepted") is not True or result.get("reproduction_validated") is not True:
        raise ProofEngineError("second-case reproduction result not accepted")
    _closed_authority(result, "second-case reproduction acceptance")
    if result.get("terminal") != {
        "state": FINAL_STATE,
        "next_gate": FINAL_GATE,
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "next_action": FINAL_ACTION,
    }:
        raise ProofEngineError("second-case reproduction acceptance terminal mismatch")
    return result


def verify_reproduction_evaluation(
    value: dict[str, Any] | None = None, *, package: dict[str, Any] | None = None,
    decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verified_package = verify_second_case_package() if package is None else copy.deepcopy(package)
    accepted = verify_reproduction_acceptance_decision(decision, package=verified_package)
    result = load(EVALUATION_PATH) if value is None else copy.deepcopy(value)
    _signed(result, "evaluation_fingerprint", "two-case reproduction evaluation")
    if result.get("evaluation_fingerprint") != EVALUATION_FINGERPRINT:
        raise ProofEngineError("two-case reproduction evaluation deterministic mismatch")
    expected_bindings = {
        "acceptance_decision_fingerprint": accepted["decision_fingerprint"],
        "build_checkpoint_fingerprint": BUILD_CHECKPOINT_FINGERPRINT,
        "baseline_package_fingerprint": BASELINE_PACKAGE_FINGERPRINT,
        "second_case_package_summary_fingerprint": PACKAGE_SUMMARY_FINGERPRINT,
        "comparison_fingerprint": COMPARISON_MATRIX_FINGERPRINT,
    }
    for field, expected in expected_bindings.items():
        if result.get(field) != expected:
            raise ProofEngineError(f"two-case reproduction evaluation binding mismatch: {field}")
    expected_counts = {
        "cases": 2, "criteria": 12, "criteria_passed": 12,
        "validation_hypotheses": 5, "hypotheses_passed": 5,
        "comparison_dimensions": 10, "comparison_dimensions_passed": 10,
        "second_case_artifacts": 8, "second_case_records": 2,
        "second_case_withheld_claims": 3,
    }
    if result.get("counts") != expected_counts:
        raise ProofEngineError("two-case reproduction evaluation counts mismatch")
    hypotheses = result.get("hypothesis_results", [])
    if [item.get("hypothesis_id") for item in hypotheses] != HYPOTHESIS_IDS or any(item.get("result") != "PASS" or not item.get("note") for item in hypotheses):
        raise ProofEngineError("two-case reproduction hypotheses incomplete")
    if result.get("comparison_result") != "PASS_REPRODUCED_WITH_NEGATIVE_CONTROL" or result.get("reproduction_result") != "PASS":
        raise ProofEngineError("two-case reproduction evaluation result mismatch")
    if result.get("supported_conclusion") != "BOUNDED_INTERNAL_TWO_CASE_OPERATIONAL_REPRODUCTION" or result.get("product_readiness_interpretation") != "INTERNAL_REPRODUCTION_VALIDATED_NOT_COMMERCIAL_READINESS":
        raise ProofEngineError("two-case reproduction conclusion widened")
    if result.get("state") != FINAL_STATE or result.get("next_gate") != FINAL_GATE or result.get("next_action") != FINAL_ACTION:
        raise ProofEngineError("two-case reproduction evaluation terminal mismatch")
    if result.get("external_actions_performed") is not False or any(result.get(field) != expected for field, expected in {
        "pricing_status": "NOT_PRICED", "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED", "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
    }.items()):
        raise ProofEngineError("two-case reproduction evaluation exceeded boundary")
    return result


def render_reproduction_result_markdown(
    package: dict[str, Any], decision: dict[str, Any], evaluation: dict[str, Any],
) -> str:
    lines = [
        "# Evidence Report — Two-Case Internal Operational Reproduction Result", "",
        f"Status: {FINAL_STATE} / {FINAL_GATE}", "", "## Result", "",
        f"- Decision: {decision['decision']}",
        f"- Reproduction result: {evaluation['reproduction_result']}",
        f"- Comparison result: {evaluation['comparison_result']}",
        f"- Supported conclusion: {evaluation['supported_conclusion']}",
        f"- Product-readiness interpretation: {evaluation['product_readiness_interpretation']}", "",
        "## Second-case package", "",
        "- Repository: `nobutakayamauchi/rts-video-flow`",
        f"- Artifacts: {evaluation['counts']['second_case_artifacts']}",
        f"- Effective records: {evaluation['counts']['second_case_records']}",
        f"- Withheld claims: {evaluation['counts']['second_case_withheld_claims']}",
        f"- Report fingerprint: `{REPORT_JSON_FINGERPRINT}`",
        f"- Comparison fingerprint: `{COMPARISON_MATRIX_FINGERPRINT}`", "",
        "## Validation", "",
    ]
    lines.extend(f"- {item['hypothesis_id']}: {item['result']} — {item['note']}" for item in evaluation["hypothesis_results"])
    lines.extend(["", "## Not proven", ""])
    lines.extend(f"- {item}" for item in evaluation["not_proven"])
    lines.extend([
        "", "## Authority boundary", "",
        "- Pricing performed: false", "- Outreach performed: false",
        "- Contract action performed: false", "- Customer intake performed: false",
        "- Delivery performed: false", "- Publication performed: false",
        "- External execution performed: false", "- Source or target repository writes performed: false",
        "", "## Next human gate", "", FINAL_ACTION, "",
    ])
    return "\n".join(lines)


def verify_operational_reproduction_result(
    *, package: dict[str, Any] | None = None, acceptance: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None, checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    verified_package = verify_second_case_package() if package is None else copy.deepcopy(package)
    decision = verify_reproduction_acceptance_decision(acceptance, package=verified_package)
    evaluated = verify_reproduction_evaluation(evaluation, package=verified_package, decision=decision)
    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("two-case reproduction checkpoint fields mismatch")
    _signed(cp, "checkpoint_fingerprint", "two-case reproduction checkpoint")
    expected = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-OPERATIONAL-REPRODUCTION-CHECKPOINT-V1",
        "checkpoint_id": "PROOF-ENGINE-EVIDENCE-REPORT-OPERATIONAL-REPRODUCTION-CHECKPOINT-0021",
        "plan_checkpoint_fingerprint": PLAN_CHECKPOINT_FINGERPRINT,
        "build_checkpoint_fingerprint": BUILD_CHECKPOINT_FINGERPRINT,
        "acceptance_decision_fingerprint": ACCEPTANCE_DECISION_FINGERPRINT,
        "evaluation_fingerprint": EVALUATION_FINGERPRINT,
        "comparison_fingerprint": COMPARISON_MATRIX_FINGERPRINT,
        "second_case_package_summary_fingerprint": PACKAGE_SUMMARY_FINGERPRINT,
        "state": FINAL_STATE,
        "next_gate": FINAL_GATE,
        "second_case_package_built": True,
        "second_case_package_accepted": True,
        "reproduction_validated": True,
        "next_action": FINAL_ACTION,
    }
    for field, wanted in expected.items():
        if cp.get(field) != wanted:
            raise ProofEngineError(f"two-case reproduction checkpoint mismatch: {field}")
    for field in ACTION_FIELDS:
        if cp.get(field) is not False:
            raise ProofEngineError(f"two-case reproduction checkpoint exceeded boundary: {field}")
    if cp["checkpoint_fingerprint"] != CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("two-case reproduction checkpoint deterministic mismatch")
    markdown = render_reproduction_result_markdown(verified_package, decision, evaluated)
    return {
        "package": verified_package,
        "decision": decision,
        "evaluation": evaluated,
        "checkpoint": cp,
        "markdown": markdown,
        "markdown_fingerprint": fingerprint(markdown),
    }
