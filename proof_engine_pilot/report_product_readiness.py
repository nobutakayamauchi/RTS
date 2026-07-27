from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .report_operational_validation_result import verify_operational_reproduction_result

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "product_readiness" / "round_0001"
INSTRUCTION_PATH = ROUND_DIR / "instruction_record.json"
CONTRACT_PATH = ROUND_DIR / "assessment_contract.json"
ASSESSMENT_PATH = ROUND_DIR / "assessment.json"
PLAN_PATH = ROUND_DIR / "hardening_plan.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_product_readiness_checkpoint_0022.json"

SOURCE_EVALUATION_FP = "dd23947b37961651a8a9e26051696fc0e1266cd312eaaab3ff5fef8da409b762"
SOURCE_ACCEPTANCE_FP = "fa5b8e84c23b4e5244cd5d8c32f5a63bd081aabcad355a8efa60ebb757c075c8"
SOURCE_CHECKPOINT_FP = "3c47a8f325558f444c283f2cbea8d61f258470c91ec3c8ad9cd6e23028bc366c"
INSTRUCTION_FP = "0d74468999f288c2ad245f2d4412c5f785f483d4199a082743ca158b9af855e0"
CONTRACT_FP = "a6e3a826aad11f1aa0e598fd6dd400284732445400e994fc6e586ffecef799d3"
ASSESSMENT_FP = "b99b46f1b4544a08232f0f86b4b9b7ea55ef37e4f2b074480c6cb088af40746c"
PLAN_FP = "d3d96476fe82c127d453ce875fad5d4630f2e9e8c1e5b82d9122981bea421a72"
SUMMARY_FP = "8f56d24569d6e25c6d5df09fc67cc3c2c09f737804c630799dc5f91010268a39"
CHECKPOINT_FP = "d101cb26621ebae7a7189d2b48b6bcce873f895d42459b6efcf44e12ca805225"
STATE = "INTERNAL_PRODUCT_READINESS_ASSESSED"
NEXT_GATE = "HUMAN_BOUNDED_HARDENING_EXECUTION_REVIEW_REQUIRED"
DECISION = "READY_FOR_BOUNDED_INTERNAL_HARDENING"

AUTHORITY_FALSE_FIELDS = {
    "pricing_authorized", "outreach_authorized", "contract_authorized",
    "customer_intake_authorized", "delivery_authorized", "publication_authorized",
    "external_execution_authorized", "source_repository_write_authorized",
    "target_repository_write_authorized",
}


def _signed(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _load_signed(path: Path, field: str, expected: str, label: str) -> dict[str, Any]:
    value = load(path)
    _signed(value, field, label)
    if value.get(field) != expected:
        raise ProofEngineError(f"{label} deterministic mismatch")
    return value


def verify_instruction_record(value: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        value = _load_signed(INSTRUCTION_PATH, "record_fingerprint", INSTRUCTION_FP, "instruction record")
    else:
        value = copy.deepcopy(value)
        _signed(value, "record_fingerprint", "instruction record")
        if value.get("record_fingerprint") != INSTRUCTION_FP:
            raise ProofEngineError("instruction record deterministic mismatch")
    if value.get("raw_input_retained_in_operator_surfaces") is not False:
        raise ProofEngineError("raw user input leaked into operator surfaces")
    policy = value.get("normalization_policy", {})
    if policy.get("preserve_intent") is not True or policy.get("do_not_quote_obvious_input_errors_in_readmes_or_pr_bodies") is not True:
        raise ProofEngineError("instruction normalization policy weakened")
    normalized = value.get("normalized_instruction", "")
    if not normalized or "\n" in normalized:
        raise ProofEngineError("normalized instruction is missing or malformed")
    return value


def verify_assessment_contract(value: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        value = _load_signed(CONTRACT_PATH, "contract_fingerprint", CONTRACT_FP, "readiness contract")
    else:
        value = copy.deepcopy(value)
        _signed(value, "contract_fingerprint", "readiness contract")
        if value.get("contract_fingerprint") != CONTRACT_FP:
            raise ProofEngineError("readiness contract deterministic mismatch")
    if sum(item.get("weight", 0) for item in value.get("dimensions", [])) != 100:
        raise ProofEngineError("readiness contract weights do not total 100")
    if [item.get("id") for item in value.get("dimensions", [])] != [f"PRD-{i:02d}" for i in range(1, 11)]:
        raise ProofEngineError("readiness dimensions mismatch")
    authority = value.get("authority", {})
    closed = AUTHORITY_FALSE_FIELDS | {"automatic_approval_authorized", "automatic_rewrite_authorized", "bounded_internal_hardening_authorized"}
    if any(authority.get(field) is not False for field in closed):
        raise ProofEngineError("readiness contract authority widened")
    return value


def verify_assessment(value: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        value = _load_signed(ASSESSMENT_PATH, "assessment_fingerprint", ASSESSMENT_FP, "readiness assessment")
    else:
        value = copy.deepcopy(value)
        _signed(value, "assessment_fingerprint", "readiness assessment")
        if value.get("assessment_fingerprint") != ASSESSMENT_FP:
            raise ProofEngineError("readiness assessment deterministic mismatch")
    results = value.get("dimension_results", [])
    if [item.get("id") for item in results] != [f"PRD-{i:02d}" for i in range(1, 11)]:
        raise ProofEngineError("readiness assessment dimensions mismatch")
    if sum(item.get("score", 0) for item in results) != 82 or value.get("weighted_score") != 82:
        raise ProofEngineError("readiness score mismatch")
    if value.get("decision") != DECISION or value.get("customer_pilot_ready") is not False or value.get("production_service_ready") is not False:
        raise ProofEngineError("readiness decision or boundary mismatch")
    estimates = value.get("completion_estimates", {})
    if estimates.get("overall_rts", {}).get("percent") != 72 or estimates.get("short_term_target", {}).get("percent") != 92:
        raise ProofEngineError("completion estimate mismatch")
    if sum(item["score"] for item in estimates["overall_rts"]["basis"]) != 72:
        raise ProofEngineError("overall RTS completion basis mismatch")
    if sum(item["score"] for item in estimates["short_term_target"]["basis"]) != 92:
        raise ProofEngineError("short-term completion basis mismatch")
    terminal = value.get("terminal", {})
    if terminal.get("state") != STATE or terminal.get("next_gate") != NEXT_GATE:
        raise ProofEngineError("readiness terminal mismatch")
    return value


def verify_hardening_plan(value: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        value = _load_signed(PLAN_PATH, "plan_fingerprint", PLAN_FP, "hardening plan")
    else:
        value = copy.deepcopy(value)
        _signed(value, "plan_fingerprint", "hardening plan")
        if value.get("plan_fingerprint") != PLAN_FP:
            raise ProofEngineError("hardening plan deterministic mismatch")
    items = value.get("work_items", [])
    if [item.get("work_id") for item in items] != [f"HARD-{i:03d}" for i in range(1, 6)]:
        raise ProofEngineError("hardening work items mismatch")
    if items[0].get("status") != "COMPLETED_IN_THIS_STAGE" or any(item.get("status") != "PLANNED" for item in items[1:]):
        raise ProofEngineError("hardening work status mismatch")
    if value.get("execution_order") != ["HARD-002", "HARD-003", "HARD-004", "HARD-005"] or value.get("wip_limit") != 1:
        raise ProofEngineError("hardening execution contract mismatch")
    authority = value.get("authority", {})
    if any(item is not False for item in authority.values()):
        raise ProofEngineError("hardening plan authority widened")
    return value


def build_product_readiness_summary(*, instruction: dict[str, Any] | None = None, contract: dict[str, Any] | None = None, assessment: dict[str, Any] | None = None, plan: dict[str, Any] | None = None) -> dict[str, Any]:
    source = verify_operational_reproduction_result()
    if source["evaluation"]["evaluation_fingerprint"] != SOURCE_EVALUATION_FP:
        raise ProofEngineError("source operational reproduction evaluation drift")
    if source["decision"]["decision_fingerprint"] != SOURCE_ACCEPTANCE_FP:
        raise ProofEngineError("source operational reproduction acceptance drift")
    if source["checkpoint"]["checkpoint_fingerprint"] != SOURCE_CHECKPOINT_FP:
        raise ProofEngineError("source operational reproduction checkpoint drift")
    instruction = verify_instruction_record(instruction)
    contract = verify_assessment_contract(contract)
    assessment = verify_assessment(assessment)
    plan = verify_hardening_plan(plan)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCT-READINESS-SUMMARY-V1",
        "summary_id": "PROOF-ENGINE-EVIDENCE-REPORT-PRODUCT-READINESS-SUMMARY-0001",
        "source_operational_reproduction_checkpoint_fingerprint": SOURCE_CHECKPOINT_FP,
        "instruction_record_fingerprint": instruction["record_fingerprint"],
        "assessment_contract_fingerprint": contract["contract_fingerprint"],
        "assessment_fingerprint": assessment["assessment_fingerprint"],
        "hardening_plan_fingerprint": plan["plan_fingerprint"],
        "completion": {"overall_rts_percent": 72, "short_term_internal_product_candidate_percent": 92, "product_readiness_score": 82},
        "decision": DECISION,
        "state": STATE,
        "next_gate": NEXT_GATE,
        "counts": {"readiness_dimensions": 10, "dimensions_pass": 4, "dimensions_partial": 5, "dimensions_not_started": 1, "risks": 5, "hardening_work_items": 5, "hardening_items_completed": 1, "hardening_items_planned": 4},
        "customer_pilot_ready": False,
        "production_service_ready": False,
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "customer_intake_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
        "external_actions_performed": False,
        "next_action": "A human reviews and authorizes the bounded internal hardening plan beginning with the operator runbook and intake contract.",
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {"source": source, "instruction": instruction, "contract": contract, "assessment": assessment, "plan": plan, "summary": summary}


def verify_product_readiness(*, instruction: dict[str, Any] | None = None, contract: dict[str, Any] | None = None, assessment: dict[str, Any] | None = None, plan: dict[str, Any] | None = None, checkpoint: dict[str, Any] | None = None) -> dict[str, Any]:
    bundle = build_product_readiness_summary(instruction=instruction, contract=contract, assessment=assessment, plan=plan)
    summary = bundle["summary"]
    _signed(summary, "summary_fingerprint", "readiness summary")
    if summary["summary_fingerprint"] != SUMMARY_FP:
        raise ProofEngineError("readiness summary deterministic mismatch")
    if checkpoint is None:
        cp = _load_signed(CHECKPOINT_PATH, "checkpoint_fingerprint", CHECKPOINT_FP, "readiness checkpoint")
    else:
        cp = copy.deepcopy(checkpoint)
        _signed(cp, "checkpoint_fingerprint", "readiness checkpoint")
        if cp.get("checkpoint_fingerprint") != CHECKPOINT_FP:
            raise ProofEngineError("readiness checkpoint deterministic mismatch")
    expected = {
        "source_operational_reproduction_checkpoint_fingerprint": SOURCE_CHECKPOINT_FP,
        "instruction_record_fingerprint": INSTRUCTION_FP,
        "assessment_contract_fingerprint": CONTRACT_FP,
        "assessment_fingerprint": ASSESSMENT_FP,
        "hardening_plan_fingerprint": PLAN_FP,
        "summary_fingerprint": SUMMARY_FP,
        "state": STATE,
        "next_gate": NEXT_GATE,
        "overall_rts_completion_percent": 72,
        "short_term_completion_percent": 92,
        "product_readiness_score": 82,
        "bounded_internal_hardening_authorized": False,
        "customer_pilot_authorized": False,
    }
    for field, wanted in expected.items():
        if cp.get(field) != wanted:
            raise ProofEngineError(f"readiness checkpoint mismatch: {field}")
    for field in ("pricing_performed", "outreach_performed", "contract_action_performed", "customer_intake_performed", "delivery_performed", "publication_performed", "external_actions_performed", "source_repository_writes_performed", "target_repository_writes_performed"):
        if cp.get(field) is not False:
            raise ProofEngineError(f"readiness checkpoint exceeded boundary: {field}")
    return {**bundle, "checkpoint": cp}


def render_product_readiness_markdown(bundle: dict[str, Any] | None = None) -> str:
    bundle = verify_product_readiness() if bundle is None else bundle
    assessment = bundle["assessment"]
    lines = ["# Evidence Report Product Readiness Assessment", "", f"State: {STATE}", f"Decision: {DECISION}", "", "## Completion", "", "- RTS overall planning estimate: 72%", "- Short-term internal product-candidate completion: 92%", "- Product-readiness score: 82/100", "", "## Readiness dimensions", ""]
    for item in assessment["dimension_results"]:
        lines.append(f"- {item['id']} {item['result']}: {item['score']}/{item['maximum']}")
    lines.extend(["", "## Boundary", "", "- Customer pilot ready: false", "- Production service ready: false", "- Pricing, outreach, contracting, intake, delivery, and publication remain closed.", "", "## Next gate", "", NEXT_GATE, ""])
    return "\n".join(lines)
