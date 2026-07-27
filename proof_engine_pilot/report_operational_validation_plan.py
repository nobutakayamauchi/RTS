from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load
from .cross_repo_campaign_close import verify_campaign_close
from .report_pilot_acceptance import verify_pilot_acceptance
from .report_template import REQUIRED_SECTIONS

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
PLAN_DIR = PACKAGE_DIR / "operational_validation_plans" / "round_0001"
SELECTION_PATH = PLAN_DIR / "case_selection.json"
PLAN_PATH = PLAN_DIR / "plan.json"
REVIEW_PATH = PLAN_DIR / "plan_review_contract.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_operational_validation_plan_checkpoint_0019.json"

FIRST_DECISION = "81af71220d7d93b47fd349b3c51912ac27e4d223500632ca86df5358a803b84a"
FIRST_CHECKPOINT = "c127b8e718a056671a8fbb1d9776e505e23cd416cd680bdeed0821f47f205611"
ROUND4_CONTRACT = "4b14c0b0186286eb53b21f28d5b631a236eb81c85519f9907d096398288139e1"
ROUND4_REPORT = "d9b2b656fff3961ea249519776604d316a58b90d8f7f7dd29151ef969a63496c"
SELECTION_FP = "f99bf316ffa5df7f07aab7003f3c574cd4570426e3d0a63252b3e8af0ea16983"
PLAN_FP = "7b351185cef61a6f2afbcc3534f42b92cb093b7f2a72fc42d4a3ea23c4d1ccc4"
REVIEW_FP = "f14cb048dad8ea4bf731236573c1a2f56b8e08f74bdffadcfd069fc623f03766"
SUMMARY_FP = "4b39093819c6e948b0d59c32dc0ac03b24a5bbfe885408e65951dee2d294fc0d"
CHECKPOINT_FP = "905b828cc347b5bc55b6d89d109af36f4eedfdbf0cd5f3c6d630768b507720f3"
STATE = "INTERNAL_OPERATIONAL_VALIDATION_PLAN_COMPLETE"
NEXT_GATE = "HUMAN_SECOND_CASE_OPERATIONAL_VALIDATION_BUILD_REVIEW_REQUIRED"
NEXT_ACTION = "A human reviews the selected negative-control case, operational plan, and twelve plan criteria before authorizing one internal second-case build."
TOPICS = ["END_TO_END_OPERATION", "TRANSCRIPTION_ACCURACY", "PRODUCTION_READINESS"]
CRITERIA = [f"OVP-{i:03d}" for i in range(1, 13)]
WORKFLOW = [
    "PLAN_AND_AUTHORITY_VERIFICATION",
    "SOURCE_BOUNDARY_RECONSTRUCTION",
    "GENERIC_CASE_ADAPTER_VALIDATION",
    "EVIDENCE_AND_WITHHELD_CLAIM_ASSEMBLY",
    "NINE_SECTION_REPORT_GENERATION",
    "EIGHT_ARTIFACT_PACKAGE_GENERATION",
    "DOUBLE_BUILD_DETERMINISM_CHECK",
    "FIRST_CASE_COMPARISON",
    "FACTUALITY_PRIVACY_AND_USABILITY_REVIEW",
    "SECOND_CASE_ACCEPTANCE_DECISION",
]
AUTHORITY = {
    "automatic_approval_authorized": False,
    "automatic_rewrite_authorized": False,
    "contract_authorized": False,
    "customer_intake_authorized": False,
    "delivery_authorized": False,
    "external_execution_authorized": False,
    "outreach_authorized": False,
    "pricing_authorized": False,
    "publication_authorized": False,
    "second_case_build_authorized": False,
    "target_repository_write_authorized": False,
}
HUMAN = {
    "type": "HUMAN",
    "identity": "nobutakayamauchi",
    "identity_source": "CURRENT_CHAT_EXPLICIT_HIGHEST_VALUE_REPRODUCTION_INSTRUCTION",
    "role": "PROJECT_OWNER",
    "instruction": "じゃあ、えっと最後の一文で、小人め候補の中から、検証価値の高い意見から、内容再現テストを進めてください。",
    "interpreted_scope": "SELECT_HIGHEST_VALIDATION_VALUE_APPROVED_CANDIDATE_AND_DEFINE_ONE_INTERNAL_OPERATIONAL_REPRODUCTION_PLAN",
}
CHECKPOINT_FIELDS = {
    "schema_version", "checkpoint_id", "source_first_case_acceptance_checkpoint_fingerprint",
    "source_round_four_review_contract_fingerprint", "case_selection_fingerprint",
    "operational_validation_plan_fingerprint", "plan_review_contract_fingerprint",
    "summary_fingerprint", "state", "next_gate", "selected_repository", "plan_complete",
    "plan_reviewed", "second_case_build_authorized", "pricing_performed",
    "outreach_performed", "contract_action_performed", "delivery_performed",
    "publication_performed", "customer_intake_performed", "external_actions_performed",
    "target_repository_writes_performed", "source_repository_writes_performed",
    "next_action", "checkpoint_fingerprint",
}


def _signed(value: dict[str, Any], field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise ProofEngineError(f"{label} fingerprint mismatch")
    return actual


def _closed(value: Any, label: str) -> None:
    if value != AUTHORITY:
        raise ProofEngineError(f"{label} authority widened or fields drifted")


def verify_case_selection(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(SELECTION_PATH) if value is None else copy.deepcopy(value)
    _signed(value, "selection_fingerprint", "case selection")
    if value.get("selection_fingerprint") != SELECTION_FP or value.get("human_authorization") != HUMAN:
        raise ProofEngineError("case selection identity or authorization mismatch")
    candidates = value.get("candidates_considered", [])
    if [item.get("repository") for item in candidates] != [
        "nobutakayamauchi/seminar-compass",
        "nobutakayamauchi/RTS-minicompany",
        "nobutakayamauchi/rts-video-flow",
    ]:
        raise ProofEngineError("case selection comparison mismatch")
    selected = value.get("selected_case", {})
    expected = {
        "repository": "nobutakayamauchi/rts-video-flow",
        "visibility": "PUBLIC",
        "default_branch": "main",
        "source_mode": "READ_ONLY_SNAPSHOT",
        "source_report_id": "PROOF-ENGINE-EVIDENCE-REPORT-DEMO-ROUND-4",
        "source_report_fingerprint": ROUND4_REPORT,
        "source_round_id": "ROUND-4",
        "source_round_fingerprint": "d4aa4b703124349227a8eac83923bf12c9a553ea125e9654f6d8f97fd87b43d3",
        "source_round_review_contract_fingerprint": ROUND4_CONTRACT,
        "readme_blob_sha": "bf1dc0f75da08202c2a07dced5d0885b43fac5b5",
        "selected_pr_numbers": [1, 2],
        "approved_candidate_ids": ["VF-001", "VF-002"],
        "required_withheld_topics": TOPICS,
        "expected_achievement_record_count": 2,
        "expected_withheld_claim_count": 3,
    }
    if selected != expected or value.get("decision") != "SELECT_RTS_VIDEO_FLOW_FOR_INTERNAL_OPERATIONAL_REPRODUCTION_PLAN":
        raise ProofEngineError("selected case mismatch")
    if len(value.get("selection_rationale", [])) != 4:
        raise ProofEngineError("selection rationale incomplete")
    _closed(value.get("authority"), "case selection")
    return value


def verify_plan_document(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(PLAN_PATH) if value is None else copy.deepcopy(value)
    _signed(value, "plan_fingerprint", "operational plan")
    if value.get("plan_fingerprint") != PLAN_FP or value.get("human_authorization") != HUMAN:
        raise ProofEngineError("operational plan identity or authorization mismatch")
    if value.get("source") != {
        "case_selection_fingerprint": SELECTION_FP,
        "accepted_first_case_decision_fingerprint": FIRST_DECISION,
        "accepted_first_case_checkpoint_fingerprint": FIRST_CHECKPOINT,
        "selected_case_report_fingerprint": ROUND4_REPORT,
        "selected_case_review_contract_fingerprint": ROUND4_CONTRACT,
    }:
        raise ProofEngineError("operational plan source mismatch")
    identity = value.get("identity", {})
    if identity.get("case") != "nobutakayamauchi/rts-video-flow" or identity.get("case_role") != "NEGATIVE_CONTROL" or identity.get("wip_limit") != 1 or identity.get("status") != "PLAN_ONLY":
        raise ProofEngineError("operational plan identity mismatch")
    execution = value.get("execution_contract", {})
    workflow = execution.get("workflow", [])
    if [item.get("step") for item in workflow] != list(range(1, 11)) or [item.get("name") for item in workflow] != WORKFLOW:
        raise ProofEngineError("operational plan workflow mismatch")
    if execution.get("required_report_sections") != REQUIRED_SECTIONS or len(execution.get("required_outputs", [])) != 8:
        raise ProofEngineError("operational plan deliverable mismatch")
    if "generic data-driven" not in execution.get("implementation_rule", "") or "not conditional code paths" not in execution.get("implementation_rule", ""):
        raise ProofEngineError("generic execution requirement missing")
    negative = value.get("negative_control_contract", {})
    if [item.get("candidate_id") for item in negative.get("expected_effective_records", [])] != ["VF-001", "VF-002"] or negative.get("required_withheld_topics") != TOPICS or negative.get("silent_withheld_claim_deletion_allowed") is not False:
        raise ProofEngineError("negative-control contract mismatch")
    comparison = value.get("comparison_contract", {})
    if len(comparison.get("required_comparisons", [])) != 10 or comparison.get("second_case_expected", {}).get("withheld_claims") != 3:
        raise ProofEngineError("comparison contract mismatch")
    if len(value.get("validation_hypotheses", [])) != 5 or len(value.get("failure_and_rollback", {}).get("fail_closed_conditions", [])) != 12:
        raise ProofEngineError("plan hypothesis or fail-closed contract mismatch")
    _closed(value.get("authority"), "operational plan")
    terminal = value.get("terminal", {})
    if terminal.get("state") != STATE or terminal.get("next_gate") != NEXT_GATE or any(terminal.get(k) != v for k, v in {
        "pricing_status": "NOT_PRICED",
        "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED",
        "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED",
    }.items()):
        raise ProofEngineError("operational plan terminal mismatch")
    return value


def verify_plan_review_contract(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load(REVIEW_PATH) if value is None else copy.deepcopy(value)
    _signed(value, "contract_fingerprint", "plan review contract")
    if value.get("contract_fingerprint") != REVIEW_FP:
        raise ProofEngineError("plan review contract deterministic mismatch")
    if value.get("source") != {
        "accepted_first_case_decision_fingerprint": FIRST_DECISION,
        "case_selection_fingerprint": SELECTION_FP,
        "operational_validation_plan_fingerprint": PLAN_FP,
        "selected_case_report_fingerprint": ROUND4_REPORT,
    }:
        raise ProofEngineError("plan review source mismatch")
    criteria = value.get("criteria", [])
    if [item.get("criterion_id") for item in criteria] != CRITERIA or any(item.get("required_result") != "PASS" for item in criteria):
        raise ProofEngineError("plan review criteria mismatch")
    decision = value.get("decision_contract", {})
    if decision.get("decisions") != [] or decision.get("allowed_decisions") != [
        "APPROVE_SECOND_CASE_OPERATIONAL_VALIDATION_BUILD", "REVISE", "REJECT", "FREEZE", "EXPIRE"
    ]:
        raise ProofEngineError("plan review decision contract mismatch")
    if value.get("completion_rule") != {
        "all_criteria_must_pass": True,
        "any_failure_blocks_build_authorization": True,
        "human_decision_required": True,
        "partial_approval_allowed": False,
    }:
        raise ProofEngineError("plan review completion rule mismatch")
    _closed(value.get("authority"), "plan review contract")
    return value


def build_operational_validation_plan(
    *, selection: dict[str, Any] | None = None, plan: dict[str, Any] | None = None,
    review_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    first = verify_pilot_acceptance()
    if first["decision"]["decision_fingerprint"] != FIRST_DECISION or first["checkpoint"]["checkpoint_fingerprint"] != FIRST_CHECKPOINT:
        raise ProofEngineError("first-case acceptance source drift")
    campaign = verify_campaign_close()
    review = campaign["review"]
    if campaign["contract"]["contract_fingerprint"] != ROUND4_CONTRACT or review["source"]["repository"] != "nobutakayamauchi/rts-video-flow" or review["counts"]["effective_approved"] != 2 or review["counts"]["withheld_claims"] != 3 or [item["topic"] for item in review["withheld_claims"]] != TOPICS:
        raise ProofEngineError("Round 4 negative-control source drift")
    selected = verify_case_selection(selection)
    verified_plan = verify_plan_document(plan)
    contract = verify_plan_review_contract(review_contract)
    summary = {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-OPERATIONAL-VALIDATION-PLAN-SUMMARY-V1",
        "summary_id": "PROOF-ENGINE-EVIDENCE-REPORT-OPERATIONAL-VALIDATION-PLAN-SUMMARY-0001",
        "source_first_case_acceptance_decision_fingerprint": FIRST_DECISION,
        "source_first_case_acceptance_checkpoint_fingerprint": FIRST_CHECKPOINT,
        "source_round_four_review_contract_fingerprint": ROUND4_CONTRACT,
        "case_selection_fingerprint": selected["selection_fingerprint"],
        "operational_validation_plan_fingerprint": verified_plan["plan_fingerprint"],
        "plan_review_contract_fingerprint": contract["contract_fingerprint"],
        "selected_repository": "nobutakayamauchi/rts-video-flow",
        "selected_validation_role": "FROZEN_UNTESTED_SCAFFOLD_NEGATIVE_CONTROL",
        "counts": {
            "candidates_considered": 3, "public_candidates": 2, "selected_cases": 1,
            "workflow_steps": 10, "validation_hypotheses": 5, "plan_review_criteria": 12,
            "required_report_sections": 9, "required_outputs": 8,
            "expected_effective_records": 2, "required_withheld_topics": 3,
            "comparison_dimensions": 10,
        },
        "state": STATE, "next_gate": NEXT_GATE, "second_case_build_authorized": False,
        "pricing_status": "NOT_PRICED", "outreach_status": "NOT_STARTED",
        "contract_status": "NOT_STARTED", "delivery_status": "NOT_DELIVERED",
        "publication_status": "NOT_PUBLISHED", "external_actions_performed": False,
        "next_action": NEXT_ACTION,
    }
    summary["summary_fingerprint"] = fingerprint(summary)
    return {"first_case": first, "campaign": campaign, "selection": selected, "plan": verified_plan, "review_contract": contract, "summary": summary}


def build_plan_review_template(bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    bundle = build_operational_validation_plan() if bundle is None else bundle
    return {
        "schema_version": "PROOF-ENGINE-EVIDENCE-REPORT-OPERATIONAL-VALIDATION-PLAN-REVIEW-TEMPLATE-V1",
        "state": NEXT_GATE,
        "reviewed_selection_fingerprint": bundle["selection"]["selection_fingerprint"],
        "reviewed_plan_fingerprint": bundle["plan"]["plan_fingerprint"],
        "reviewed_contract_fingerprint": bundle["review_contract"]["contract_fingerprint"],
        "criteria_results": [{"criterion_id": item["criterion_id"], "result": None, "evidence": [], "note": ""} for item in bundle["review_contract"]["criteria"]],
        "allowed_decisions": copy.deepcopy(bundle["review_contract"]["decision_contract"]["allowed_decisions"]),
        "decision": None, "reviewer_identity": None, "privacy_boundary_confirmed": False,
        "authority_boundary_confirmed": False, "second_case_build_authorized": False,
        "pricing_authorized": False, "outreach_authorized": False, "contract_authorized": False,
        "delivery_authorized": False, "publication_authorized": False,
    }


def render_operational_validation_plan_markdown(bundle: dict[str, Any] | None = None) -> str:
    bundle = build_operational_validation_plan() if bundle is None else bundle
    plan = bundle["plan"]
    lines = [
        "# Evidence Report — Second-Case Internal Operational Validation Plan", "",
        f"Status: {STATE} / {NEXT_GATE}", "", "## Selected case", "",
        "- Repository: `nobutakayamauchi/rts-video-flow`",
        "- Role: frozen untested scaffold negative control",
        "- Source mode: read-only snapshot", "- Selected PRs: #1 and #2",
        "- Expected effective records: 2", "- Required withheld topics: 3", "",
        "## Why this case", "",
    ]
    lines.extend(f"- {item}" for item in bundle["selection"]["selection_rationale"])
    lines.extend(["", "## Workflow", ""])
    lines.extend(f"{item['step']}. {item['name']} — human gate: {str(item['human_gate']).lower()}" for item in plan["execution_contract"]["workflow"])
    lines.extend(["", "## Required outputs", ""])
    lines.extend(f"- {item}" for item in plan["execution_contract"]["required_outputs"])
    lines.extend(["", "## Negative-control boundary", ""])
    lines.extend(f"- Must retain withheld topic: {item}" for item in TOPICS)
    lines.extend([
        "- End-to-end operation may not be claimed.",
        "- Japanese transcription accuracy may not be claimed.",
        "- Production readiness may not be claimed.", "",
        "## Authority boundary", "",
        "- Second-case build authorized: false", "- Pricing authorized: false",
        "- Outreach authorized: false", "- Contract authorized: false",
        "- Delivery authorized: false", "- Publication authorized: false",
        "- External execution authorized: false", "- Customer intake authorized: false",
        "- Source or target repository writes authorized: false", "",
        "## Next human gate", "", NEXT_ACTION, "",
    ])
    return "\n".join(lines)


def verify_operational_validation_plan(
    *, selection: dict[str, Any] | None = None, plan: dict[str, Any] | None = None,
    review_contract: dict[str, Any] | None = None, checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle = build_operational_validation_plan(selection=selection, plan=plan, review_contract=review_contract)
    summary = bundle["summary"]
    _signed(summary, "summary_fingerprint", "plan summary")
    if summary["summary_fingerprint"] != SUMMARY_FP:
        raise ProofEngineError("plan summary deterministic mismatch")
    cp = load(CHECKPOINT_PATH) if checkpoint is None else copy.deepcopy(checkpoint)
    if set(cp) != CHECKPOINT_FIELDS:
        raise ProofEngineError("plan checkpoint fields mismatch")
    _signed(cp, "checkpoint_fingerprint", "plan checkpoint")
    expected = {
        "source_first_case_acceptance_checkpoint_fingerprint": FIRST_CHECKPOINT,
        "source_round_four_review_contract_fingerprint": ROUND4_CONTRACT,
        "case_selection_fingerprint": SELECTION_FP,
        "operational_validation_plan_fingerprint": PLAN_FP,
        "plan_review_contract_fingerprint": REVIEW_FP,
        "summary_fingerprint": SUMMARY_FP, "state": STATE, "next_gate": NEXT_GATE,
        "selected_repository": "nobutakayamauchi/rts-video-flow", "plan_complete": True,
        "plan_reviewed": False, "second_case_build_authorized": False, "next_action": NEXT_ACTION,
    }
    for field, wanted in expected.items():
        if cp.get(field) != wanted:
            raise ProofEngineError(f"plan checkpoint mismatch: {field}")
    for field in (
        "pricing_performed", "outreach_performed", "contract_action_performed",
        "delivery_performed", "publication_performed", "customer_intake_performed",
        "external_actions_performed", "target_repository_writes_performed",
        "source_repository_writes_performed",
    ):
        if cp.get(field) is not False:
            raise ProofEngineError(f"plan checkpoint exceeded boundary: {field}")
    if cp["checkpoint_fingerprint"] != CHECKPOINT_FP:
        raise ProofEngineError("plan checkpoint deterministic mismatch")
    template = build_plan_review_template(bundle)
    if template["decision"] is not None or template["second_case_build_authorized"] is not False:
        raise ProofEngineError("plan review template manufactured authority")
    markdown = render_operational_validation_plan_markdown(bundle)
    return {**bundle, "checkpoint": cp, "review_template": template, "markdown": markdown, "markdown_fingerprint": fingerprint(markdown)}
