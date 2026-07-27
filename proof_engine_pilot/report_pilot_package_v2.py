from __future__ import annotations

import copy
from typing import Any

from . import report_pilot_package as base
from .core import ProofEngineError, load
from .report_template import REQUIRED_SECTIONS
from .report_template_review import verify_report_template_review

BUILD_DECISION_FINGERPRINT = "992d33bf450a0fad5fce8548c0da71dcf86380691e732ba8d89130af265b5b7d"
CASE_INTAKE_FINGERPRINT = "d16beab6d22251459839a6038f6174bc1f3e3d24ee7d600e34a3fb7906c40ce0"
ROLLBACK_FINGERPRINT = "9bb6c0505a6eb39aa0f03ff15077b230576d99e87359c7423d9875f752583cc2"
MANIFEST_FINGERPRINT = "e30a88388bfeae449e753df624d6b699404a687bae06fec54d619ab73dd5af2e"
REPORT_JSON_FINGERPRINT = "60c4760c446f90277a4db49e99cedbbc51ef5d1889c3c458cdf0e624bf22bc41"
REPORT_MARKDOWN_FINGERPRINT = "5130e58f79d271a6d6172acf853273f206ec0882dd9a16c599b1651f4dda7c5e"
EVIDENCE_INVENTORY_FINGERPRINT = "4ee9f727bbc20627dbe18221b43445defff169b285b3514db5e8f5da999ca1d1"
ACCEPTANCE_PACKET_FINGERPRINT = "f1a4e4024d831f4fa22ccd12a70244c87641fba2fe4e0ab29914b3aa96d71895"
VERIFICATION_SUMMARY_FINGERPRINT = "d751596c9ff0d70b8bd07536be09191dd3cb274e24e7c6ec1885df3f3c135a42"
PACKAGE_INDEX_FINGERPRINT = "9eced7c395949cb96b20092b2b9ce7a9a25ae70352c0f09e782aa6d8cfdef20a"
SUMMARY_FINGERPRINT = "cf3a8b61ac3c75d065c0bab2b163381ecbfcd778abc3780949e0977e0b5c7c9f"
CHECKPOINT_FINGERPRINT = "64906aceb1c40a363438696709ee02ba658d278bfb2ee45112c201f10f569a70"
CANONICAL_REPOSITORY = "nobutakayamauchi/seminar-compass"

base.BUILD_DECISION_FINGERPRINT = BUILD_DECISION_FINGERPRINT
base.CASE_INTAKE_FINGERPRINT = CASE_INTAKE_FINGERPRINT
base.ROLLBACK_FINGERPRINT = ROLLBACK_FINGERPRINT
base.MANIFEST_FINGERPRINT = MANIFEST_FINGERPRINT
base.REPORT_JSON_FINGERPRINT = REPORT_JSON_FINGERPRINT
base.REPORT_MARKDOWN_FINGERPRINT = REPORT_MARKDOWN_FINGERPRINT
base.EVIDENCE_INVENTORY_FINGERPRINT = EVIDENCE_INVENTORY_FINGERPRINT
base.ACCEPTANCE_PACKET_FINGERPRINT = ACCEPTANCE_PACKET_FINGERPRINT
base.VERIFICATION_SUMMARY_FINGERPRINT = VERIFICATION_SUMMARY_FINGERPRINT
base.PACKAGE_INDEX_FINGERPRINT = PACKAGE_INDEX_FINGERPRINT
base.SUMMARY_FINGERPRINT = SUMMARY_FINGERPRINT
base.CHECKPOINT_FINGERPRINT = CHECKPOINT_FINGERPRINT


def verify_build_decision(decision: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(base.BUILD_DECISION_PATH) if decision is None else copy.deepcopy(decision)
    base._verify_fingerprint(value, "decision_fingerprint", "pilot package build decision")
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
    if value.get("reviewed_spec_checkpoint_fingerprint") != base.CORRECTED_SPEC_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("pilot package build spec checkpoint mismatch")
    if value.get("reviewed_spec_fingerprint") != base.PRODUCT_SPEC_FINGERPRINT:
        raise ProofEngineError("pilot package build spec mismatch")
    if value.get("reviewed_pre_build_contract_fingerprint") != base.PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT:
        raise ProofEngineError("pilot package build pre-build contract mismatch")
    if value.get("post_build_acceptance_contract_fingerprint") != base.POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT:
        raise ProofEngineError("pilot package build acceptance contract mismatch")
    results = value.get("criteria_results")
    if not isinstance(results, list) or [item.get("criterion_id") for item in results] != base.EXPECTED_BUILD_CRITERIA or any(item.get("result") != "PASS" for item in results):
        raise ProofEngineError("pilot package build criteria mismatch")
    if value.get("selected_case") != {
        "repository": CANONICAL_REPOSITORY,
        "snapshot_binding": "VERIFIED_SOURCE_REPORT_FINGERPRINT",
        "source_mode": "READ_ONLY_SNAPSHOT",
        "source_report_fingerprint": base.SOURCE_REPORT_FINGERPRINT,
        "source_report_id": base.SOURCE_REPORT_ID,
        "visibility": "PUBLIC",
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
    value = load(base.CASE_INTAKE_PATH) if intake is None else copy.deepcopy(intake)
    base._verify_fingerprint(value, "intake_fingerprint", "pilot case intake")
    if value.get("intake_fingerprint") != CASE_INTAKE_FINGERPRINT:
        raise ProofEngineError("pilot case intake deterministic mismatch")
    if value.get("build_decision_fingerprint") != BUILD_DECISION_FINGERPRINT:
        raise ProofEngineError("pilot case intake decision mismatch")
    if value.get("source") != {
        "report_fingerprint": base.SOURCE_REPORT_FINGERPRINT,
        "report_id": base.SOURCE_REPORT_ID,
        "repository": CANONICAL_REPOSITORY,
        "snapshot_binding": "DERIVE_AND_VERIFY_FROM_SOURCE_REPORT",
        "source_mode": "READ_ONLY_SNAPSHOT",
        "visibility": "PUBLIC",
    }:
        raise ProofEngineError("pilot case intake source mismatch")
    if value.get("subject") != {"display_name": CANONICAL_REPOSITORY, "personal_identity_required": False, "type": "PROJECT"}:
        raise ProofEngineError("pilot case intake subject mismatch")
    if value.get("operator", {}).get("wip_limit") != 1 or value.get("operator", {}).get("mode") != "OPERATOR_ASSISTED_SINGLE_CASE":
        raise ProofEngineError("pilot case intake operator boundary mismatch")
    if value.get("privacy") != {
        "credentials_allowed": False, "private_payload_allowed": False,
        "source_visibility_required": "PUBLIC", "third_party_personal_data_allowed": False,
    }:
        raise ProofEngineError("pilot case intake privacy widened")
    if len(value.get("required_outputs", [])) != 7:
        raise ProofEngineError("pilot case intake output contract mismatch")
    return value


def source_report() -> dict[str, Any]:
    bundle = verify_report_template_review()
    report = next((item for item in bundle["pack"]["reports"] if item["report_id"] == base.SOURCE_REPORT_ID), None)
    if report is None or report.get("report_fingerprint") != base.SOURCE_REPORT_FINGERPRINT:
        raise ProofEngineError("pilot package source report mismatch")
    if report.get("repository") != CANONICAL_REPOSITORY or list(report.get("sections", {})) != REQUIRED_SECTIONS:
        raise ProofEngineError("pilot package source report scope mismatch")
    if len(report["sections"]["effective_achievement_records"]) != 6 or report["sections"]["withheld_or_unsupported_claims"]:
        raise ProofEngineError("pilot package source report counts mismatch")
    return copy.deepcopy(report)


base.verify_build_decision = verify_build_decision
base.verify_case_intake = verify_case_intake
base._source_report = source_report

build_pilot_package = base.build_pilot_package
verify_pilot_package = base.verify_pilot_package
render_report_markdown = base.render_report_markdown
verify_package_manifest = base.verify_package_manifest
verify_rollback_record = base.verify_rollback_record
