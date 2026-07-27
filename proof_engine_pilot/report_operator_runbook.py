from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "product_readiness" / "round_0002"
POLICY_PATH = ROUND_DIR / "instruction_provenance_policy.json"
INSTRUCTION_PATH = ROUND_DIR / "instruction_record.json"
INTAKE_PATH = ROUND_DIR / "intake_contract.json"
RUNBOOK_PATH = ROUND_DIR / "operator_runbook.json"
ESCALATION_PATH = ROUND_DIR / "support_escalation_matrix.json"
RESULT_PATH = ROUND_DIR / "hardening_execution_result.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_operator_runbook_checkpoint_0023.json"

POLICY_FINGERPRINT = "75ebe8d863f9b729fa9d9cc975aa677e00934d2fdd2fbdf40d58098dabf4d313"
INSTRUCTION_FINGERPRINT = "0d8b9a7cf21ea7914c912080318574e348703ab879eeea5cc2732bb0b91b9380"
INTAKE_FINGERPRINT = "f51409e709a4ae0ef339127d253c3bfef72120ef804acbf5a6de5b67592df25b"
RUNBOOK_FINGERPRINT = "4df55e60578a9e068206a9e8433129c08149c38f1862f0729498ecad17d27c14"
ESCALATION_FINGERPRINT = "1f56c512573aacf4d2e13c8d45816ee19f984ee6b6ac12a8e20b7e016867b396"
RESULT_FINGERPRINT = "6aeb9b36bdfb8eb36edecfe6eac700b1d0e8d64d5d215280c3db7d8adb1e8202"
CHECKPOINT_FINGERPRINT = "2043d8f919b6fd1e66efd777d072efb2fb917310d24132e5adc3d4a461494d52"

FALSE_AUTHORITY_FIELDS = {
    "contract_authorized",
    "customer_intake_authorized",
    "customer_pilot_authorized",
    "delivery_authorized",
    "external_execution_authorized",
    "outreach_authorized",
    "pricing_authorized",
    "publication_authorized",
    "source_repository_write_authorized",
    "target_repository_write_authorized",
}


def _verify_fingerprint(value: dict[str, Any], field: str, expected: str, label: str) -> dict[str, Any]:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != expected or actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return value


def _require_false_authority(authority: dict[str, Any], fields: set[str], label: str) -> None:
    if not fields.issubset(authority):
        raise ProofEngineError(f"{label} authority fields missing")
    if any(authority[field] is not False for field in fields):
        raise ProofEngineError(f"{label} authority widened")


def verify_instruction_provenance_policy(value: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = _verify_fingerprint(value or load(POLICY_PATH), "policy_fingerprint", POLICY_FINGERPRINT, "instruction policy")
    demo = policy.get("demonstration_policy", {})
    if demo.get("rough_input_robustness_may_be_reported") is not True:
        raise ProofEngineError("rough-input evidence was discarded")
    if demo.get("verbatim_user_example_required") is not False:
        raise ProofEngineError("verbatim user example required")
    if policy.get("record_layers", {}).get("restricted_raw_log", {}).get("enabled") is not False:
        raise ProofEngineError("raw log enabled")
    _require_false_authority(
        policy.get("authority", {}),
        {"automatic_approval_authorized", "automatic_rewrite_authorized", "publication_authorized", "raw_log_retention_authorized", "scope_widening_authorized"},
        "instruction policy",
    )
    return policy


def verify_instruction_record(value: dict[str, Any] | None = None) -> dict[str, Any]:
    record = _verify_fingerprint(value or load(INSTRUCTION_PATH), "record_fingerprint", INSTRUCTION_FINGERPRINT, "instruction record")
    if record.get("raw_text_retained") is not False or record.get("scope_widened") is not False:
        raise ProofEngineError("instruction record boundary widened")
    raw_fingerprint = record.get("raw_input_fingerprint")
    if not isinstance(raw_fingerprint, str) or len(raw_fingerprint) != 64:
        raise ProofEngineError("raw input fingerprint invalid")
    scope_material = {"normalized_instruction": record.get("normalized_instruction"), "interpreted_scope": record.get("interpreted_scope")}
    if record.get("scope_fingerprint") != fingerprint(scope_material):
        raise ProofEngineError("instruction scope fingerprint mismatch")
    actions = record.get("normalization_actions", [])
    if not any(isinstance(action, str) and "rough-input robustness insight" in action for action in actions):
        raise ProofEngineError("rough-input insight missing")
    return record


def verify_intake_contract(value: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = _verify_fingerprint(value or load(INTAKE_PATH), "contract_fingerprint", INTAKE_FINGERPRINT, "intake contract")
    required = {item.get("field") for item in contract.get("required_inputs", [])}
    expected = {"source_repository", "source_ref", "analysis_objective", "normalized_instruction", "raw_input_fingerprint", "allowed_claim_classes", "excluded_or_withheld_topics"}
    if required != expected:
        raise ProofEngineError("intake fields mismatch")
    rejection_codes = {item.get("code") for item in contract.get("rejection_conditions", [])}
    if rejection_codes != {"REJECT_PRIVATE_SOURCE", "REJECT_SECRET_OR_CREDENTIAL", "REJECT_CUSTOMER_OR_PERSONAL_PAYLOAD", "REJECT_AMBIGUOUS_AUTHORITY", "REJECT_UNBOUNDED_OBJECTIVE", "REJECT_UNRESOLVED_SCOPE"}:
        raise ProofEngineError("intake rejection policy mismatch")
    _require_false_authority(contract.get("authority", {}), FALSE_AUTHORITY_FIELDS - {"delivery_authorized", "outreach_authorized"}, "intake contract")
    return contract


def verify_operator_runbook(value: dict[str, Any] | None = None) -> dict[str, Any]:
    runbook = _verify_fingerprint(value or load(RUNBOOK_PATH), "runbook_fingerprint", RUNBOOK_FINGERPRINT, "operator runbook")
    phases = runbook.get("phases", [])
    if [item.get("phase_id") for item in phases] != [f"OP-0{i}" for i in range(1, 8)]:
        raise ProofEngineError("runbook phase order mismatch")
    if runbook.get("wip_limit") != 1:
        raise ProofEngineError("runbook WIP widened")
    gates = {item.get("human_gate") for item in phases}
    if not {"SCOPE_CONFIRMATION_REQUIRED", "INTAKE_ACCEPTANCE_REQUIRED", "BUILD_AUTHORIZATION_REQUIRED", "PACKAGE_ACCEPTANCE_REQUIRED", "FINAL_INTERNAL_DECISION_REQUIRED"}.issubset(gates):
        raise ProofEngineError("runbook human gates missing")
    _require_false_authority(runbook.get("authority", {}), FALSE_AUTHORITY_FIELDS, "operator runbook")
    return runbook


def verify_support_escalation(value: dict[str, Any] | None = None) -> dict[str, Any]:
    matrix = _verify_fingerprint(value or load(ESCALATION_PATH), "matrix_fingerprint", ESCALATION_FINGERPRINT, "escalation matrix")
    if [item.get("level") for item in matrix.get("levels", [])] != ["L0_OPERATOR", "L1_PROJECT_OWNER", "L2_SECURITY_PRIVACY_REVIEW", "L3_SEPARATE_GOVERNANCE_DECISION"]:
        raise ProofEngineError("escalation levels mismatch")
    if any(matrix.get("authority", {}).values()):
        raise ProofEngineError("escalation authority widened")
    return matrix


def verify_hardening_result(value: dict[str, Any] | None = None) -> dict[str, Any]:
    result = _verify_fingerprint(value or load(RESULT_PATH), "result_fingerprint", RESULT_FINGERPRINT, "hardening result")
    if result.get("state") != "INTERNAL_OPERATOR_RUNBOOK_AND_INTAKE_CONTRACT_COMPLETE":
        raise ProofEngineError("hardening state mismatch")
    if result.get("next_gate") != "HUMAN_INDEPENDENT_READER_REVIEW_PLAN_REQUIRED":
        raise ProofEngineError("hardening gate mismatch")
    if result.get("completed_work_item", {}).get("work_id") != "HARD-002":
        raise ProofEngineError("wrong hardening work item")
    if [item.get("result") for item in result.get("completed_work_item", {}).get("acceptance_results", [])] != ["PASS"] * 5:
        raise ProofEngineError("HARD-002 acceptance failed")
    progress = result.get("completion_update", {})
    if progress.get("rts_overall_planning_estimate_percent") != 73 or progress.get("short_term_internal_product_candidate_percent") != 95 or progress.get("product_readiness_score_unchanged") != 82:
        raise ProofEngineError("completion update mismatch")
    authority = result.get("authority", {})
    if authority.get("bounded_internal_runbook_authorized") is not True:
        raise ProofEngineError("internal runbook not authorized")
    _require_false_authority(authority, FALSE_AUTHORITY_FIELDS, "hardening result")
    return result


def verify_checkpoint(value: dict[str, Any] | None = None) -> dict[str, Any]:
    checkpoint = _verify_fingerprint(value or load(CHECKPOINT_PATH), "checkpoint_fingerprint", CHECKPOINT_FINGERPRINT, "operator checkpoint")
    if checkpoint.get("hardening_execution_result_fingerprint") != RESULT_FINGERPRINT:
        raise ProofEngineError("checkpoint result binding mismatch")
    performed_fields = [field for field in checkpoint if field.endswith("_performed")]
    if any(checkpoint[field] is not False for field in performed_fields):
        raise ProofEngineError("checkpoint external action performed")
    if checkpoint.get("state") != "INTERNAL_OPERATOR_RUNBOOK_AND_INTAKE_CONTRACT_COMPLETE":
        raise ProofEngineError("checkpoint state mismatch")
    return checkpoint


def verify_operator_runbook_stage() -> dict[str, Any]:
    policy = verify_instruction_provenance_policy()
    instruction = verify_instruction_record()
    intake = verify_intake_contract()
    runbook = verify_operator_runbook()
    escalation = verify_support_escalation()
    result = verify_hardening_result()
    checkpoint = verify_checkpoint()
    outputs = result["completed_work_item"]["outputs"]
    expected_outputs = {
        "instruction_provenance_policy_fingerprint": policy["policy_fingerprint"],
        "instruction_record_fingerprint": instruction["record_fingerprint"],
        "intake_contract_fingerprint": intake["contract_fingerprint"],
        "operator_runbook_fingerprint": runbook["runbook_fingerprint"],
        "support_escalation_matrix_fingerprint": escalation["matrix_fingerprint"],
    }
    if outputs != expected_outputs:
        raise ProofEngineError("HARD-002 output bindings mismatch")
    return {
        "policy": policy,
        "instruction": instruction,
        "intake_contract": intake,
        "operator_runbook": runbook,
        "support_escalation": escalation,
        "result": result,
        "checkpoint": checkpoint,
        "summary": {
            "state": result["state"],
            "next_gate": result["next_gate"],
            "rts_overall_planning_estimate_percent": 73,
            "short_term_internal_product_candidate_percent": 95,
            "product_readiness_score": 82,
            "runbook_phases": len(runbook["phases"]),
            "intake_required_fields": len(intake["required_inputs"]),
            "intake_rejection_conditions": len(intake["rejection_conditions"]),
            "escalation_levels": len(escalation["levels"]),
            "rough_input_robustness_preserved": True,
            "verbatim_raw_instruction_required": False,
            "remaining_work_items": result["remaining_work_items"],
        },
    }
