from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_productization_review import verify_productization_review
from .report_template import REQUIRED_SECTIONS

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
SPEC_DIR = PACKAGE_DIR / "productization_specs" / "round_0001"
BUILD_CONTRACT_PATH = SPEC_DIR / "build_contract.json"
PRODUCT_SPEC_PATH = SPEC_DIR / "product_specification.json"
ACCEPTANCE_CONTRACT_PATH = SPEC_DIR / "acceptance_contract.json"
CHECKPOINT_PATH = (
    ROOT
    / "pilot_runs"
    / "reconnect_pilot_p3"
    / "evidence_report_internal_product_spec_checkpoint_0016.json"
)

SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT = (
    "5ec1888f85ca802c023a1fce9c68c69c089a6085b5770b011f25139e97d03dd0"
)
SOURCE_PRODUCTIZATION_DECISION_FINGERPRINT = (
    "010f5a2d39e712b181ed227fe62cdb61680db890898a43994543833e3c27efd9"
)
REVIEWED_TEMPLATE_FINGERPRINT = (
    "579d086788e636317cd61392fc3af97de468ff27c9ba478e962a973bd91ad4f6"
)
REVIEWED_PACK_FINGERPRINT = (
    "c95360f6ef1376914261eac574757ceb99f7f25c998b7be5752436200375f1bb"
)
REVIEWED_REPORT_FINGERPRINTS = {
    "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-2":
        "a644d21ccf98cbdadf810c2e5294776d22376995a69c5abd76b29e4066e864dc",
    "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-3":
        "48ef70f2a24842851fbfd2c19e30b360835a1a5248181090a91694dbd9ac395e",
    "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-4":
        "d9b2b656fff3961ea249519776604d316a58b90d8f7f7dd29151ef969a63496c",
}
BUILD_CONTRACT_FINGERPRINT = (
    "deeb524430c9cc905c55e31fc0321da1bedd665dc0d55e0cf459913622122f26"
)
PRODUCT_SPEC_FINGERPRINT = (
    "2c5132b29b68bfcf3bc9dd9b509cc3176f9ebf828aaa33a8bee3fadd9d817e71"
)
ACCEPTANCE_CONTRACT_FINGERPRINT = (
    "54f4cd704e760e7bc8b7641e6724ad0f9b8d3ac129107fefdfb379bae3f4a831"
)
SUMMARY_FINGERPRINT = (
    "fbf53edb5244a1a126b85ba229e8ac93165510b1625c69cdf7a61856c12efb33"
)
EXPECTED_STATE = "HUMAN_PILOT_PACKAGE_BUILD_REVIEW_REQUIRED"
EXPECTED_HUMAN_AUTHORIZATION = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_ACTION_INSTRUCTION",
    "role": "PROJECT_OWNER",
    "instruction": "動きを行う。",
}
FALSE_AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "delivery_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "pricing_authorized": False,
    "publication_authorized": False,
    "target_repository_write_authorized": False,
}
REQUIRED_RECORD_FIELDS = [
    "candidate_id",
    "reader_summary",
    "record_kind",
    "value_interpretation",
    "evidence_strength",
    "evidence_prs",
    "evidence_boundary",
    "contribution_map",
    "lineage",
]
EXPECTED_CRITERION_IDS = [f"ACC-{number:03d}" for number in range(1, 16)]
CHECKPOINT_FIELDS = {
    "schema_version",
    "checkpoint_id",
    "source_productization_checkpoint_fingerprint",
    "product_spec_fingerprint",
    "acceptance_contract_fingerprint",
    "summary_fingerprint",
    "state",
    "specification_complete",
    "acceptance_contract_complete",
    "pilot_package_build_authorized",
    "pricing_performed",
    "outreach_performed",
    "contract_action_performed",
    "delivery_performed",
    "publication_performed",
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


def _verify_false_authority(
    value: Any,
    *,
    label: str,
    include_pilot_build: bool = False,
) -> dict[str, bool]:
    expected = copy.deepcopy(FALSE_AUTHORITY)
    if include_pilot_build:
        expected["pilot_package_build_authorized"] = False
    if value != expected:
        raise ProofEngineError(f"{label} authority widened or fields drifted")
    return value


def verify_product_spec_build_contract(
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = load(BUILD_CONTRACT_PATH) if contract is None else copy.deepcopy(contract)
    _verify_fingerprint(value, "contract_fingerprint", "product spec build contract")
    if value.get("contract_fingerprint") != BUILD_CONTRACT_FINGERPRINT:
        raise ProofEngineError("product spec build contract deterministic fingerprint mismatch")
    if value.get("schema_version") != (
        "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCT-SPEC-BUILD-CONTRACT-V1"
    ):
        raise ProofEngineError("product spec build contract schema mismatch")
    if value.get("contract_id") != (
        "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCT-SPEC-BUILD-CONTRACT-0001"
    ):
        raise ProofEngineError("product spec build contract identity mismatch")
    if value.get("human_authorization") != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("product spec build is not bound to the action instruction")
    if value.get("source") != {
        "productization_checkpoint_fingerprint":
            SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "productization_decision_fingerprint":
            SOURCE_PRODUCTIZATION_DECISION_FINGERPRINT,
        "reviewed_template_fingerprint": REVIEWED_TEMPLATE_FINGERPRINT,
        "reviewed_pack_fingerprint": REVIEWED_PACK_FINGERPRINT,
        "reviewed_report_fingerprints": REVIEWED_REPORT_FINGERPRINTS,
    }:
        raise ProofEngineError("product spec build source mismatch")
    if value.get("scope") != (
        "INTERNAL_PRODUCTIZATION_SPECIFICATION_AND_ACCEPTANCE_CONTRACT"
    ):
        raise ProofEngineError("product spec build scope widened")
    _verify_false_authority(value.get("authority"), label="product spec build contract")
    if value.get("terminal") != {
        "state": EXPECTED_STATE,
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
    }:
        raise ProofEngineError("product spec build terminal boundary mismatch")
    return value


def verify_product_specification(
    specification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = (
        load(PRODUCT_SPEC_PATH)
        if specification is None
        else copy.deepcopy(specification)
    )
    _verify_fingerprint(value, "spec_fingerprint", "internal product specification")
    if value.get("spec_fingerprint") != PRODUCT_SPEC_FINGERPRINT:
        raise ProofEngineError("internal product specification deterministic mismatch")
    if value.get("schema_version") != (
        "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-V1"
    ):
        raise ProofEngineError("internal product specification schema mismatch")
    source = value.get("source", {})
    if source != {
        "productization_checkpoint_fingerprint":
            SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "productization_decision_fingerprint":
            SOURCE_PRODUCTIZATION_DECISION_FINGERPRINT,
        "reviewed_template_fingerprint": REVIEWED_TEMPLATE_FINGERPRINT,
        "reviewed_pack_fingerprint": REVIEWED_PACK_FINGERPRINT,
        "reviewed_report_fingerprints": REVIEWED_REPORT_FINGERPRINTS,
        "effective_achievement_record_count": 16,
        "withheld_claim_count": 5,
        "build_contract_fingerprint": BUILD_CONTRACT_FINGERPRINT,
    }:
        raise ProofEngineError("internal product specification source mismatch")
    if value.get("human_authorization") != EXPECTED_HUMAN_AUTHORIZATION:
        raise ProofEngineError("internal product specification authorization mismatch")
    deliverable = value.get("deliverable_contract", {})
    if deliverable.get("required_sections") != REQUIRED_SECTIONS:
        raise ProofEngineError("internal product required sections mismatch")
    if deliverable.get("required_record_fields") != REQUIRED_RECORD_FIELDS:
        raise ProofEngineError("internal product record contract mismatch")
    workflow = value.get("workflow")
    if (
        not isinstance(workflow, list)
        or [item.get("step") for item in workflow] != list(range(1, 9))
        or [item.get("name") for item in workflow] != [
            "SOURCE_BOUNDARY_CONFIRMATION",
            "EVIDENCE_ELIGIBILITY_VERIFICATION",
            "ACHIEVEMENT_RECORD_ASSEMBLY",
            "CONTRIBUTION_SEPARATION",
            "WITHHELD_CLAIM_RETENTION",
            "NINE_SECTION_REPORT_RENDERING",
            "FACTUALITY_AND_PRIVACY_REVIEW",
            "DELIVERY_RELEASE_DECISION",
        ]
    ):
        raise ProofEngineError("internal product workflow mismatch")
    if value.get("target", {}).get("first_delivery_mode") != (
        "OPERATOR_ASSISTED_SINGLE_CASE"
    ):
        raise ProofEngineError("internal product first delivery mode mismatch")
    if value.get("target", {}).get("pricing_status") != "UNDECIDED":
        raise ProofEngineError("internal product pricing decision manufactured")
    _verify_false_authority(value.get("authority"), label="internal product specification")
    if value.get("terminal") != {
        "state": "INTERNAL_PRODUCTIZATION_SPECIFICATION_COMPLETE",
        "next_gate": EXPECTED_STATE,
        "next_action": "Review this specification and acceptance contract before authorizing a single-case internal pilot package build.",
    }:
        raise ProofEngineError("internal product specification terminal mismatch")
    return value


def verify_acceptance_contract(
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = (
        load(ACCEPTANCE_CONTRACT_PATH)
        if contract is None
        else copy.deepcopy(contract)
    )
    _verify_fingerprint(value, "contract_fingerprint", "acceptance contract")
    if value.get("contract_fingerprint") != ACCEPTANCE_CONTRACT_FINGERPRINT:
        raise ProofEngineError("acceptance contract deterministic mismatch")
    if value.get("schema_version") != (
        "PROOF-ENGINE-EVIDENCE-REPORT-ACCEPTANCE-CONTRACT-V1"
    ):
        raise ProofEngineError("acceptance contract schema mismatch")
    if value.get("source") != {
        "product_spec_fingerprint": PRODUCT_SPEC_FINGERPRINT,
        "productization_checkpoint_fingerprint":
            SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "reviewed_template_fingerprint": REVIEWED_TEMPLATE_FINGERPRINT,
        "reviewed_pack_fingerprint": REVIEWED_PACK_FINGERPRINT,
    }:
        raise ProofEngineError("acceptance contract source mismatch")
    criteria = value.get("criteria")
    if (
        not isinstance(criteria, list)
        or [item.get("criterion_id") for item in criteria]
        != EXPECTED_CRITERION_IDS
        or any(item.get("required_result") != "PASS" for item in criteria)
    ):
        raise ProofEngineError("acceptance criteria mismatch")
    decision = value.get("decision_contract", {})
    if decision.get("human_decision_required") is not True:
        raise ProofEngineError("acceptance contract weakened human decision gate")
    if decision.get("decisions"):
        raise ProofEngineError("acceptance contract manufactured a decision")
    if decision.get("allowed_decisions") != [
        "APPROVE_PILOT_PACKAGE_BUILD",
        "REVISE",
        "REJECT",
        "REDACT",
        "EXPIRE",
        "FREEZE",
    ]:
        raise ProofEngineError("acceptance contract decisions mismatch")
    _verify_false_authority(
        value.get("authority"),
        label="acceptance contract",
        include_pilot_build=True,
    )
    terminal = value.get("terminal", {})
    if terminal != {
        "state": EXPECTED_STATE,
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "next_action": "A human reviews the internal product specification and acceptance contract and decides whether to authorize one single-case internal pilot package build.",
    }:
        raise ProofEngineError("acceptance contract terminal boundary mismatch")
    return value


def build_internal_productization_spec(
    *,
    build_contract: dict[str, Any] | None = None,
    specification: dict[str, Any] | None = None,
    acceptance_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = verify_productization_review()
    if source["checkpoint"]["checkpoint_fingerprint"] != (
        SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT
    ):
        raise ProofEngineError("internal product spec source checkpoint drift")
    if source["decision"]["decision_fingerprint"] != (
        SOURCE_PRODUCTIZATION_DECISION_FINGERPRINT
    ):
        raise ProofEngineError("internal product spec source decision drift")
    verified_build = verify_product_spec_build_contract(build_contract)
    verified_spec = verify_product_specification(specification)
    verified_acceptance = verify_acceptance_contract(acceptance_contract)
    summary = {
        "schema_version":
            "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-SUMMARY-V1",
        "summary_id":
            "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-SUMMARY-0001",
        "source_productization_checkpoint_fingerprint":
            SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "product_spec_fingerprint": verified_spec["spec_fingerprint"],
        "acceptance_contract_fingerprint":
            verified_acceptance["contract_fingerprint"],
        "product_name": verified_spec["identity"]["working_name"],
        "delivery_mode": verified_spec["target"]["first_delivery_mode"],
        "counts": {
            "required_sections":
                len(verified_spec["deliverable_contract"]["required_sections"]),
            "workflow_steps": len(verified_spec["workflow"]),
            "acceptance_criteria": len(verified_acceptance["criteria"]),
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
        "next_action": verified_acceptance["terminal"]["next_action"],
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {
        "source": source,
        "build_contract": verified_build,
        "spec": verified_spec,
        "acceptance": verified_acceptance,
        "summary": summary,
    }


def build_pilot_package_review_template(
    bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = build_internal_productization_spec() if bundle is None else bundle
    return {
        "schema_version":
            "PROOF-ENGINE-EVIDENCE-REPORT-PILOT-PACKAGE-REVIEW-TEMPLATE-V1",
        "state": EXPECTED_STATE,
        "reviewed_spec_fingerprint": value["spec"]["spec_fingerprint"],
        "reviewed_acceptance_contract_fingerprint":
            value["acceptance"]["contract_fingerprint"],
        "criteria_results": [
            {
                "criterion_id": item["criterion_id"],
                "result": None,
                "evidence": [],
                "note": "",
            }
            for item in value["acceptance"]["criteria"]
        ],
        "allowed_decisions":
            copy.deepcopy(value["acceptance"]["decision_contract"]["allowed_decisions"]),
        "decision": None,
        "reviewer_identity": None,
        "privacy_confirmed": False,
        "authority_boundary_confirmed": False,
        "pilot_package_build_authorized": False,
        "pricing_authorized": False,
        "outreach_authorized": False,
        "contract_authorized": False,
        "delivery_authorized": False,
        "publication_authorized": False,
    }


def render_internal_productization_markdown(
    bundle: dict[str, Any] | None = None,
) -> str:
    value = build_internal_productization_spec() if bundle is None else bundle
    spec = value["spec"]
    acceptance = value["acceptance"]
    lines = [
        "# Evidence-Backed Achievement Discovery Report — Internal Product Specification",
        "",
        "Status: INTERNAL_PRODUCTIZATION_SPECIFICATION_COMPLETE / HUMAN_PILOT_PACKAGE_BUILD_REVIEW_REQUIRED",
        "",
        "## Product",
        "",
        f"- Name: {spec['identity']['working_name']}",
        f"- Product family: {spec['identity']['product_family']}",
        f"- First delivery mode: {spec['target']['first_delivery_mode']}",
        f"- Primary user: {spec['target']['primary_user']}",
        f"- Primary job: {spec['target']['primary_job']}",
        "",
        "## Fixed input boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in spec["input_contract"]["required"])
    lines.extend(["", "## Workflow", ""])
    lines.extend(
        f"{item['step']}. {item['name']} — human gate: "
        f"{str(item['human_gate']).lower()}"
        for item in spec["workflow"]
    )
    lines.extend(["", "## Deliverable", ""])
    lines.extend(
        f"- Section: {item}"
        for item in spec["deliverable_contract"]["required_sections"]
    )
    lines.extend(["", "## Acceptance contract", ""])
    lines.extend(
        f"- {item['criterion_id']} / {item['category']}: {item['check']} "
        f"({item['verification']})"
        for item in acceptance["criteria"]
    )
    lines.extend(["", "## Commercial unknowns", ""])
    lines.extend(f"- {item}" for item in spec["commercial_unknowns"])
    lines.extend([
        "",
        "## Authority boundary",
        "",
        "- Pilot package build authorized: false",
        "- Pricing authorized: false",
        "- Outreach authorized: false",
        "- Contract authorized: false",
        "- Delivery authorized: false",
        "- Publication authorized: false",
        "- External execution authorized: false",
        "- Automatic approval authorized: false",
        "- Automatic rewriting authorized: false",
        "",
        "## Next human gate",
        "",
        acceptance["terminal"]["next_action"],
        "",
    ])
    return "\n".join(lines)


def verify_internal_productization_spec(
    *,
    build_contract: dict[str, Any] | None = None,
    specification: dict[str, Any] | None = None,
    acceptance_contract: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_internal_productization_spec(
        build_contract=build_contract,
        specification=specification,
        acceptance_contract=acceptance_contract,
    )
    summary = bundle["summary"]
    _verify_fingerprint(
        summary,
        "summary_fingerprint",
        "internal product specification summary",
    )
    if summary["summary_fingerprint"] != SUMMARY_FINGERPRINT:
        raise ProofEngineError("internal product summary deterministic mismatch")
    if summary["counts"] != {
        "required_sections": 9,
        "workflow_steps": 8,
        "acceptance_criteria": 15,
        "commercial_unknowns": 7,
        "effective_achievement_records_in_source_pack": 16,
        "withheld_claims_in_source_pack": 5,
    }:
        raise ProofEngineError("internal product specification counts mismatch")
    if (
        summary["state"],
        summary["pricing_status"],
        summary["outreach_status"],
        summary["contract_status"],
        summary["delivery_status"],
        summary["publication_status"],
        summary["pilot_package_build_authorized"],
        summary["external_actions_performed"],
    ) != (
        EXPECTED_STATE,
        "NOT_PRICED",
        "NOT_STARTED",
        "NOT_STARTED",
        "NOT_DELIVERED",
        "NOT_PUBLISHED",
        False,
        False,
    ):
        raise ProofEngineError("internal product specification boundary widened")

    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("internal product spec checkpoint fields mismatch")
    _verify_fingerprint(
        cp,
        "checkpoint_fingerprint",
        "internal product specification checkpoint",
    )
    expected = {
        "schema_version":
            "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-CHECKPOINT-V1",
        "checkpoint_id":
            "PROOF-ENGINE-EVIDENCE-REPORT-INTERNAL-PRODUCT-SPEC-CHECKPOINT-0016",
        "source_productization_checkpoint_fingerprint":
            SOURCE_PRODUCTIZATION_CHECKPOINT_FINGERPRINT,
        "product_spec_fingerprint": PRODUCT_SPEC_FINGERPRINT,
        "acceptance_contract_fingerprint": ACCEPTANCE_CONTRACT_FINGERPRINT,
        "summary_fingerprint": SUMMARY_FINGERPRINT,
        "state": EXPECTED_STATE,
        "specification_complete": True,
        "acceptance_contract_complete": True,
        "pilot_package_build_authorized": False,
        "next_action": summary["next_action"],
    }
    for field, expected_value in expected.items():
        if cp[field] != expected_value:
            raise ProofEngineError(f"internal product spec checkpoint mismatch: {field}")
    for field in (
        "pricing_performed",
        "outreach_performed",
        "contract_action_performed",
        "delivery_performed",
        "publication_performed",
        "external_actions_performed",
        "target_repository_writes_performed",
    ):
        if cp[field] is not False:
            raise ProofEngineError(
                f"internal product spec checkpoint exceeded boundary: {field}"
            )
    review_template = build_pilot_package_review_template(bundle)
    if review_template["decision"] is not None:
        raise ProofEngineError("pilot package review template manufactured a decision")
    markdown = render_internal_productization_markdown(bundle)
    return {
        **bundle,
        "checkpoint": cp,
        "review_template": review_template,
        "markdown": markdown,
        "markdown_fingerprint": fingerprint(markdown),
    }
