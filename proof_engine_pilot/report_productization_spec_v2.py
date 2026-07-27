from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_productization_review import verify_productization_review
from .report_productization_spec import (
    PRODUCT_SPEC_FINGERPRINT,
    REVIEWED_PACK_FINGERPRINT,
    REVIEWED_TEMPLATE_FINGERPRINT,
    SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
    verify_product_spec_build_contract,
    verify_product_specification,
)

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
SPEC_DIR = PACKAGE_DIR / "productization_specs" / "round_0001"
PRE_BUILD_REVIEW_CONTRACT_PATH = SPEC_DIR / "pre_build_review_contract.json"
POST_BUILD_ACCEPTANCE_CONTRACT_PATH = SPEC_DIR / "acceptance_contract_v2.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_internal_product_spec_checkpoint_0016_r1.json"

OLD_ACCEPTANCE_CONTRACT_FINGERPRINT = "54f4cd704e760e7bc8b7641e6724ad0f9b8d3ac129107fefdfb379bae3f4a831"
PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT = "21b32cdae33b36c44ec289d8aea924918c757b87b309b0658b73d413bb09534d"
POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT = "d8269e54f35946f750bf07a942c0587530cbdb45d9b47f54d15f936ba07755f9"
SUMMARY_FINGERPRINT = "f658fa1728aa930ed1c97f9c1f42ea737cd4ca1754a7c940915354b7111cc62f"
OLD_CHECKPOINT_FINGERPRINT = "a17974e84356ea23a29a957954810710364548637b012bed051e954ba36a4ea2"
EXPECTED_STATE = "HUMAN_PILOT_PACKAGE_BUILD_REVIEW_REQUIRED"
EXPECTED_PRE_BUILD_IDS = [f"BLD-{number:03d}" for number in range(1, 7)]
EXPECTED_ACCEPTANCE_IDS = [f"ACC-{number:03d}" for number in range(1, 16)]

FALSE_AUTHORITY_WITH_BUILD = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "delivery_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "pilot_package_build_authorized": False,
    "pricing_authorized": False,
    "publication_authorized": False,
    "target_repository_write_authorized": False,
}
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "revision_of_checkpoint_fingerprint",
    "source_productization_checkpoint_fingerprint", "product_spec_fingerprint",
    "pre_build_review_contract_fingerprint", "post_build_acceptance_contract_fingerprint",
    "summary_fingerprint", "state", "specification_complete",
    "pre_build_review_contract_complete", "post_build_acceptance_contract_complete",
    "pilot_package_build_authorized", "pricing_performed", "outreach_performed",
    "contract_action_performed", "delivery_performed", "publication_performed",
    "external_actions_performed", "target_repository_writes_performed",
    "next_action", "checkpoint_fingerprint",
}


def _verify_fingerprint(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _verify_false_authority(value: Any, label: str) -> dict[str, bool]:
    if value != FALSE_AUTHORITY_WITH_BUILD:
        raise ProofEngineError(f"{label} authority widened or fields drifted")
    return value


def verify_pre_build_review_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(PRE_BUILD_REVIEW_CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "pre-build review contract")
    if value.get("contract_fingerprint") != PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT:
        raise ProofEngineError("pre-build review contract deterministic mismatch")
    if value.get("schema_version") != "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-PRE-BUILD-REVIEW-CONTRACT-V1":
        raise ProofEngineError("pre-build review contract schema mismatch")
    if value.get("review_stage") != "PRE_BUILD_AUTHORIZATION":
        raise ProofEngineError("pre-build review stage mismatch")
    if value.get("source") != {
        "product_spec_fingerprint": PRODUCT_SPEC_FINGERPRINT,
        "post_build_acceptance_contract_fingerprint": POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT,
        "source_productization_checkpoint_fingerprint": SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
    }:
        raise ProofEngineError("pre-build review source mismatch")
    criteria = value.get("criteria")
    if not isinstance(criteria, list) or [item.get("criterion_id") for item in criteria] != EXPECTED_PRE_BUILD_IDS or any(item.get("required_result") != "PASS" for item in criteria):
        raise ProofEngineError("pre-build review criteria mismatch")
    decision = value.get("decision_contract", {})
    if decision.get("human_decision_required") is not True or decision.get("decisions"):
        raise ProofEngineError("pre-build review decision gate mismatch")
    if decision.get("allowed_decisions") != ["APPROVE_PILOT_PACKAGE_BUILD", "REVISE", "REJECT", "FREEZE"]:
        raise ProofEngineError("pre-build review decisions mismatch")
    _verify_false_authority(value.get("authority"), "pre-build review contract")
    if value.get("terminal") != {
        "state": EXPECTED_STATE,
        "next_action": "A human may authorize one repository-local internal package build without asserting that the unbuilt package already satisfies post-build acceptance criteria.",
    }:
        raise ProofEngineError("pre-build review terminal mismatch")
    return value


def verify_post_build_acceptance_contract(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(POST_BUILD_ACCEPTANCE_CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "post-build acceptance contract")
    if value.get("contract_fingerprint") != POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT:
        raise ProofEngineError("post-build acceptance contract deterministic mismatch")
    if value.get("schema_version") != "PROOF-ENGINE-EVIDENCE-REPORT-ACCEPTANCE-CONTRACT-V2":
        raise ProofEngineError("post-build acceptance contract schema mismatch")
    if value.get("revision_of_contract_fingerprint") != OLD_ACCEPTANCE_CONTRACT_FINGERPRINT:
        raise ProofEngineError("post-build acceptance revision link mismatch")
    if value.get("source") != {
        "product_spec_fingerprint": PRODUCT_SPEC_FINGERPRINT,
        "productization_checkpoint_fingerprint": SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "reviewed_template_fingerprint": REVIEWED_TEMPLATE_FINGERPRINT,
        "reviewed_pack_fingerprint": REVIEWED_PACK_FINGERPRINT,
    }:
        raise ProofEngineError("post-build acceptance source mismatch")
    criteria = value.get("criteria")
    if not isinstance(criteria, list) or [item.get("criterion_id") for item in criteria] != EXPECTED_ACCEPTANCE_IDS or any(item.get("required_result") != "PASS" for item in criteria):
        raise ProofEngineError("post-build acceptance criteria mismatch")
    decision = value.get("decision_contract", {})
    if decision.get("review_stage") != "POST_BUILD_PACKAGE_ACCEPTANCE":
        raise ProofEngineError("post-build acceptance review stage mismatch")
    if decision.get("human_decision_required") is not True or decision.get("decisions"):
        raise ProofEngineError("post-build acceptance decision gate mismatch")
    if decision.get("allowed_decisions") != ["ACCEPT_PILOT_PACKAGE", "REVISE", "REJECT", "REDACT", "EXPIRE", "FREEZE"]:
        raise ProofEngineError("post-build acceptance decisions mismatch")
    _verify_false_authority(value.get("authority"), "post-build acceptance contract")
    if value.get("terminal") != {
        "state": "POST_BUILD_ACCEPTANCE_CONTRACT_READY",
        "next_gate": "HUMAN_PILOT_PACKAGE_ACCEPTANCE_REVIEW_REQUIRED",
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "next_action": "After one internal pilot package is built, a human evaluates the completed artifacts against all fifteen acceptance criteria.",
    }:
        raise ProofEngineError("post-build acceptance terminal mismatch")
    return value


def build_internal_productization_spec_v2(*, build_contract: dict[str, Any] | None = None, specification: dict[str, Any] | None = None, pre_build_contract: dict[str, Any] | None = None, acceptance_contract: dict[str, Any] | None = None) -> dict[str, Any]:
    source = verify_productization_review()
    if source["checkpoint"]["checkpoint_fingerprint"] != SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT:
        raise ProofEngineError("corrected product spec source checkpoint drift")
    verified_build = verify_product_spec_build_contract(build_contract)
    verified_spec = verify_product_specification(specification)
    verified_pre_build = verify_pre_build_review_contract(pre_build_contract)
    verified_acceptance = verify_post_build_acceptance_contract(acceptance_contract)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-SUMMARY-V2",
        "summary_id": "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-SUMMARY-0002",
        "source_productization_checkpoint_fingerprint": SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "product_spec_fingerprint": verified_spec["spec_fingerprint"],
        "pre_build_review_contract_fingerprint": verified_pre_build["contract_fingerprint"],
        "post_build_acceptance_contract_fingerprint": verified_acceptance["contract_fingerprint"],
        "product_name": verified_spec["identity"]["working_name"],
        "delivery_mode": verified_spec["target"]["first_delivery_mode"],
        "counts": {
            "required_sections": len(verified_spec["deliverable_contract"]["required_sections"]),
            "workflow_steps": len(verified_spec["workflow"]),
            "pre_build_review_criteria": len(verified_pre_build["criteria"]),
            "post_build_acceptance_criteria": len(verified_acceptance["criteria"]),
            "commercial_unknowns": len(verified_spec["commercial_unknowns"]),
            "effective_achievement_records_in_source_pack": 16,
            "withheld_claims_in_source_pack": 5,
        },
        "state": EXPECTED_STATE,
        "specification_status": "INTERNAL_PRODUCTIZATION_SPECIFICATION_COMPLETE",
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "pilot_package_build_authorized": False,
        "external_actions_performed": False,
        "next_action": verified_pre_build["terminal"]["next_action"],
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {"source": source, "build_contract": verified_build, "spec": verified_spec, "pre_build": verified_pre_build, "acceptance": verified_acceptance, "summary": summary}


def build_pilot_package_review_template(bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    value = build_internal_productization_spec_v2() if bundle is None else bundle
    return {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-PRE-BUILD-REVIEW-TEMPLATE-V2",
        "review_stage": "PRE_BUILD_AUTHORIZATION",
        "state": EXPECTED_STATE,
        "reviewed_spec_fingerprint": value["spec"]["spec_fingerprint"],
        "reviewed_pre_build_contract_fingerprint": value["pre_build"]["contract_fingerprint"],
        "post_build_acceptance_contract_fingerprint": value["acceptance"]["contract_fingerprint"],
        "criteria_results": [{"criterion_id": item["criterion_id"], "result": None, "evidence": [], "note": ""} for item in value["pre_build"]["criteria"]],
        "post_build_acceptance_results": [],
        "allowed_decisions": copy.deepcopy(value["pre_build"]["decision_contract"]["allowed_decisions"]),
        "decision": None,
        "reviewer_identity": None,
        "selected_case_report_fingerprint": None,
        "privacy_boundary_confirmed": False,
        "rollback_confirmed": False,
        "pilot_package_build_authorized": False,
        "pricing_authorized": False,
        "outreach_authorized": False,
        "contract_authorized": False,
        "delivery_authorized": False,
        "publication_authorized": False,
    }


def render_internal_productization_markdown(bundle: dict[str, Any] | None = None) -> str:
    value = build_internal_productization_spec_v2() if bundle is None else bundle
    spec, pre_build, acceptance = value["spec"], value["pre_build"], value["acceptance"]
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Corrected Internal Product Specification", "",
        "Status: INTERNAL_PRODUCTIZATION_SPECIFICATION_COMPLETE / HUMAN_PILOT_PACKAGE_BUILD_REVIEW_REQUIRED", "",
        "The pre-build authorization review is separated from the post-build package acceptance review.", "",
        "## Product", "", f"- Name: {spec['identity']['working_name']}",
        f"- First delivery mode: {spec['target']['first_delivery_mode']}", f"- Primary user: {spec['target']['primary_user']}", "",
        "## Pre-build authorization criteria", "",
    ]
    lines.extend(f"- {item['criterion_id']} / {item['category']}: {item['check']}" for item in pre_build["criteria"])
    lines.extend(["", "These six criteria decide only whether one internal repository-local package may be built.", "They do not assert that an unbuilt package passes the fifteen post-build acceptance criteria.", "", "## Post-build acceptance criteria", ""])
    lines.extend(f"- {item['criterion_id']} / {item['category']}: {item['check']} ({item['verification']})" for item in acceptance["criteria"])
    lines.extend(["", "## Authority boundary", "", "- Pilot package build authorized: false", "- Package acceptance authorized: false", "- Pricing authorized: false", "- Outreach authorized: false", "- Contract authorized: false", "- Delivery authorized: false", "- Publication authorized: false", "- External execution authorized: false", "- Automatic approval authorized: false", "", "## Next human gate", "", pre_build["terminal"]["next_action"], ""])
    return "\n".join(lines)


def verify_internal_productization_spec_v2(*, build_contract: dict[str, Any] | None = None, specification: dict[str, Any] | None = None, pre_build_contract: dict[str, Any] | None = None, acceptance_contract: dict[str, Any] | None = None, checkpoint: dict[str, Any] | None = None) -> dict[str, Any]:
    bundle = build_internal_productization_spec_v2(build_contract=build_contract, specification=specification, pre_build_contract=pre_build_contract, acceptance_contract=acceptance_contract)
    summary = bundle["summary"]
    _verify_fingerprint(summary, "summary_fingerprint", "corrected internal product specification summary")
    if summary["summary_fingerprint"] != SUMMARY_FINGERPRINT:
        raise ProofEngineError("corrected internal product summary deterministic mismatch")
    if summary["counts"] != {"required_sections":9,"workflow_steps":8,"pre_build_review_criteria":6,"post_build_acceptance_criteria":15,"commercial_unknowns":7,"effective_achievement_records_in_source_pack":16,"withheld_claims_in_source_pack":5}:
        raise ProofEngineError("corrected internal product counts mismatch")
    if (summary["state"], summary["pilot_package_build_authorized"], summary["external_actions_performed"]) != (EXPECTED_STATE, False, False):
        raise ProofEngineError("corrected internal product boundary widened")
    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("corrected product spec checkpoint fields mismatch")
    _verify_fingerprint(cp, "checkpoint_fingerprint", "corrected product spec checkpoint")
    expected = {
        "schema_version":"PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-CHECKPOINT-V2",
        "checkpoint_id":"PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-CHECKPOINT-0016-R1",
        "revision_of_checkpoint_fingerprint":OLD_CHECKPOINT_FINGERPRINT,
        "source_productization_checkpoint_fingerprint":SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "product_spec_fingerprint":PRODUCT_SPEC_FINGERPRINT,
        "pre_build_review_contract_fingerprint":PRE_BUILD_REVIEW_CONTRACT_FINGERPRINT,
        "post_build_acceptance_contract_fingerprint":POST_BUILD_ACCEPTANCE_CONTRACT_FINGERPRINT,
        "summary_fingerprint":SUMMARY_FINGERPRINT,
        "state":EXPECTED_STATE,
        "specification_complete":True,
        "pre_build_review_contract_complete":True,
        "post_build_acceptance_contract_complete":True,
        "pilot_package_build_authorized":False,
        "next_action":summary["next_action"],
    }
    for field, expected_value in expected.items():
        if cp[field] != expected_value:
            raise ProofEngineError(f"corrected product spec checkpoint mismatch: {field}")
    for field in ("pricing_performed","outreach_performed","contract_action_performed","delivery_performed","publication_performed","external_actions_performed","target_repository_writes_performed"):
        if cp[field] is not False:
            raise ProofEngineError(f"corrected product spec checkpoint exceeded boundary: {field}")
    review_template = build_pilot_package_review_template(bundle)
    if [item["criterion_id"] for item in review_template["criteria_results"]] != EXPECTED_PRE_BUILD_IDS:
        raise ProofEngineError("pre-build review template criteria mismatch")
    if review_template["post_build_acceptance_results"]:
        raise ProofEngineError("pre-build review manufactured package acceptance results")
    if review_template["decision"] is not None:
        raise ProofEngineError("pre-build review template manufactured a decision")
    markdown = render_internal_productization_markdown(bundle)
    return {**bundle, "checkpoint": cp, "review_template": review_template, "markdown": markdown, "markdown_fingerprint": fingerprint(markdown)}


verify_internal_productization_spec = verify_internal_productization_spec_v2
build_internal_productization_spec = build_internal_productization_spec_v2
