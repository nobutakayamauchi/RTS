from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load

P = Path(__file__).resolve().parent
R = P.parent
D = P / "product_readiness" / "round_0007"
PATH = {
    "contract": D / "execution_authorization_contract.json",
    "scorecard": D / "candidate_selection_scorecard.json",
    "outreach": D / "outreach_message_template.json",
    "consent": D / "consent_and_intake_form.json",
    "source": D / "source_freeze_form.json",
    "preflight": D / "preflight_checklist.json",
    "withdrawal": D / "withdrawal_incident_protocol.json",
    "decision": D / "authorization_decision.json",
    "status": R / "docs/status/RTS_CURRENT_POSITION_PILOT_EXECUTION_AUTH.json",
    "checkpoint": R / "pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_execution_auth_checkpoint_0028.json",
    "prior_status": R / "docs/status/RTS_CURRENT_POSITION_PILOT_PLAN.json",
    "prior_checkpoint": R / "pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_plan_checkpoint_0027.json",
}
FP = {'contract': '969e77a4518fe9059ad20208d648f797cb59ea1a29cf2a6b44a387c12d21ad09', 'scorecard': 'bd156451e3ef05f0c13b77ee4e6d2e84dec5383d94100f2061887c0271814f9a', 'outreach': 'ffd966240ad007c2842198b65686db381e760e436b0d2852bea760015056e88a', 'consent': '4fc471c6dce13c07814ff8c467dab3f43dbe8f87a9155169242605e37776d160', 'source': 'b29eb8400cee2470aa436860720195e94b010fa7a49536093d5397bf71b4c979', 'preflight': '0655c91770c0fd1503b5ac90dd06041ff9411c0803ea60180c3db49f5850f305', 'withdrawal': 'ee850e0371c5ff6d7edf347c11969ae658a2927a3d3d826bca6b2f920c0f32de', 'decision': '1d5ec5aeb148a3a51a88fcef01ed97cac51a8a460e315a1a4be571140f2b524e', 'status': '468fbb778b4c7d271f80e082e2afbd5ec7d2daca595e1c7a020951c70249b76e', 'checkpoint': '0fb836f70ca37d58f9b22f8cd21d487014c6eadfd2fdb16d746a29c3856a0627'}
CLOSED = {
    "participant_contact_authorized", "customer_intake_authorized",
    "customer_pilot_execution_authorized", "pricing_authorized",
    "outreach_authorized", "contract_authorized", "delivery_authorized",
    "publication_authorized", "external_execution_authorized",
    "source_repository_write_authorized", "target_repository_write_authorized",
}
PRIOR_STATUS_FP = "629a96de6d70b240aba3c04b5e838465621844902fa476eabd598d596dbaefee"
PRIOR_CHECKPOINT_FP = "b526cbfc833989d6f7d15e27b59f93896fe9b9aaa013f39bcaaa7998d0aa1718"


def _signed(key: str, value: dict[str, Any] | None, field: str) -> dict[str, Any]:
    v = load(PATH[key]) if value is None else copy.deepcopy(value)
    material = copy.deepcopy(v)
    actual = material.pop(field, None)
    if actual != FP[key] or fingerprint(material) != actual:
        raise ProofEngineError(f"{key} fingerprint mismatch")
    return v


def _closed(authority: dict[str, Any]) -> None:
    if not CLOSED.issubset(authority) or any(authority[name] is not False for name in CLOSED):
        raise ProofEngineError("external authority widened")


def verify_prior_plan_history() -> dict[str, str]:
    status = load(PATH["prior_status"])
    status_material = copy.deepcopy(status)
    status_actual = status_material.pop("map_fingerprint", None)
    if status_actual != PRIOR_STATUS_FP or fingerprint(status_material) != status_actual:
        raise ProofEngineError("prior pilot plan status changed")
    checkpoint = load(PATH["prior_checkpoint"])
    checkpoint_material = copy.deepcopy(checkpoint)
    checkpoint_actual = checkpoint_material.pop("checkpoint_fingerprint", None)
    if checkpoint_actual != PRIOR_CHECKPOINT_FP or fingerprint(checkpoint_material) != checkpoint_actual:
        raise ProofEngineError("prior pilot plan checkpoint changed")
    return {"prior_status": status_actual, "prior_checkpoint": checkpoint_actual}


def verify_contract(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("contract", value, "contract_fingerprint")
    source = v["source"]
    if source["pilot_plan_checkpoint_fingerprint"] != PRIOR_CHECKPOINT_FP:
        raise ProofEngineError("prior plan binding mismatch")
    if source["pilot_plan_state"] != "INTERNAL_BOUNDED_CUSTOMER_PILOT_PLAN_REVIEW_COMPLETE":
        raise ProofEngineError("prior plan state mismatch")
    if source["raw_instruction_retained"] is not False or len(source["raw_instruction_sha256"]) != 64:
        raise ProofEngineError("instruction provenance mismatch")
    if v["scope"] != {
        "participant_limit": 1, "public_repository_limit": 1, "pilot_cycle_limit": 1,
        "wip_limit": 1, "compensation_jpy": 0, "operator_assisted": True,
    }:
        raise ProofEngineError("scope widened")
    authorized = v["authorized_now"]
    if authorized != {
        "internal_candidate_discovery": True, "internal_candidate_scoring": True,
        "template_preparation": True, "named_candidate_contact": False,
        "customer_intake": False, "pilot_execution": False,
    }:
        raise ProofEngineError("authorization contract mismatch")
    acceptance = v["acceptance"]
    if tuple(acceptance[k] for k in (
        "artifact_count", "review_criterion_count", "focused_test_count_minimum",
        "named_candidate_count_required", "participant_contact_events_required",
        "customer_intake_events_required", "pilot_execution_events_required",
        "product_readiness_score_required", "rts_overall_planning_estimate_percent_required",
    )) != (8, 16, 20, 0, 0, 0, 0, 93, 78):
        raise ProofEngineError("acceptance contract mismatch")
    if v["authority"].get("internal_candidate_selection_preparation_authorized") is not True:
        raise ProofEngineError("internal preparation authority missing")
    _closed(v["authority"])
    return v


def verify_scorecard(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("scorecard", value, "scorecard_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("scorecard contract binding mismatch")
    if (v["candidate_count"], v["candidate_records"], v["selection_status"]) != (
        0, [], "NO_NAMED_CANDIDATE_SELECTED"
    ):
        raise ProofEngineError("candidate silently selected")
    if v["threshold"] != {
        "minimum_score": 80, "all_hard_gates_required": True, "ties_require_human_review": True
    }:
        raise ProofEngineError("candidate threshold weakened")
    if [x["id"] for x in v["hard_gates"]] != [f"CG-{i:02d}" for i in range(1, 9)]:
        raise ProofEngineError("hard gate set mismatch")
    if sum(x["maximum"] for x in v["weighted_criteria"]) != 100 or len(v["weighted_criteria"]) != 7:
        raise ProofEngineError("weighted score mismatch")
    if len(v["disqualifiers"]) != 8:
        raise ProofEngineError("disqualifier set mismatch")
    _closed(v["authority"])
    return v


def verify_outreach(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("outreach", value, "template_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("outreach contract binding mismatch")
    if v["send_status"] != "NOT_SENT" or v["named_recipient"] is not None:
        raise ProofEngineError("outreach already targeted or sent")
    body = v["body"]
    required = ["公開GitHubリポジトリ1件", "無償", "非公開コード", "返信だけでは分析を開始しません", "途中でいつでも撤回"]
    if any(text not in body for text in required):
        raise ProofEngineError("outreach disclosure missing")
    if len(v["required_disclosures"]) != 7 or len(v["prohibited_claims"]) != 6:
        raise ProofEngineError("outreach boundary mismatch")
    _closed(v["authority"])
    return v


def verify_consent(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("consent", value, "form_fingerprint")
    if v["contract_fingerprint"] != FP["contract"] or v["status"] != "BLANK_TEMPLATE_NOT_EXECUTED":
        raise ProofEngineError("consent form state mismatch")
    if v["submission_count"] != 0 or len(v["participant_fields"]) != 5 or len(v["required_confirmations"]) != 8:
        raise ProofEngineError("consent form was executed or weakened")
    rules = v["consent_validity"]
    if tuple(rules[k] for k in (
        "all_confirmations_required", "typed_name_required",
        "consent_timestamp_required", "repository_and_commit_must_match_source_freeze",
    )) != (True, True, True, True):
        raise ProofEngineError("consent validity weakened")
    if rules["blank_or_ambiguous_value"] != "REJECT_INTAKE":
        raise ProofEngineError("ambiguous consent allowed")
    if not any("reply" in text.lower() and "not consent" in text.lower() for text in v["required_confirmations"]):
        raise ProofEngineError("reply-only consent guard missing")
    _closed(v["authority"])
    return v


def verify_source_freeze(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("source", value, "form_fingerprint")
    if v["contract_fingerprint"] != FP["contract"] or v["status"] != "BLANK_TEMPLATE_NOT_EXECUTED":
        raise ProofEngineError("source freeze state mismatch")
    if v["source_freeze_count"] != 0 or len(v["required_fields"]) != 9:
        raise ProofEngineError("source already fixed or fields missing")
    fields = {x["field"]: x["constraint"] for x in v["required_fields"]}
    if fields.get("repository_visibility") != "PUBLIC" or fields.get("fixed_commit_sha") != "40 lowercase hexadecimal characters":
        raise ProofEngineError("public immutable source boundary weakened")
    if len(v["automatic_rejections"]) != 6:
        raise ProofEngineError("source rejection policy mismatch")
    _closed(v["authority"])
    return v


def verify_preflight(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("preflight", value, "checklist_fingerprint")
    if v["contract_fingerprint"] != FP["contract"] or v["status"] != "BLANK_TEMPLATE_NOT_EXECUTED":
        raise ProofEngineError("preflight state mismatch")
    if v["all_checks_required"] is not True or v["partial_pass_allowed"] is not False:
        raise ProofEngineError("partial preflight allowed")
    checks = v["checks"]
    if [x["id"] for x in checks] != [f"PF-{i:02d}" for i in range(1, 17)]:
        raise ProofEngineError("preflight check set mismatch")
    phases = [x["phase"] for x in checks]
    if {phase: phases.count(phase) for phase in set(phases)} != {
        "PRE_CONTACT": 3, "PRE_INTAKE": 2, "PRE_BUILD": 5, "PRE_RELEASE": 4, "PRE_CLOSE": 2
    }:
        raise ProofEngineError("preflight phase distribution mismatch")
    if v["completed_check_count"] != 0:
        raise ProofEngineError("preflight falsely completed")
    _closed(v["authority"])
    return v


def verify_withdrawal(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("withdrawal", value, "protocol_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("withdrawal contract binding mismatch")
    if len(v["stop_triggers"]) != 9 or len(v["immediate_actions"]) != 5:
        raise ProofEngineError("stop protocol weakened")
    if (v["incident_count"], v["withdrawal_count"]) != (0, 0):
        raise ProofEngineError("unrecorded real incident or withdrawal")
    effect = v["withdrawal_effect"]
    if (effect["future_processing"], effect["participant_release"], effect["publication"]) != (
        "STOP", "PROHIBITED", "PROHIBITED"
    ):
        raise ProofEngineError("withdrawal effect weakened")
    if "new explicit human authorization" not in effect["restart"]:
        raise ProofEngineError("restart authority weakened")
    _closed(v["authority"])
    return v


def verify_decision(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("decision", value, "decision_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("decision contract binding mismatch")
    expected = {
        "candidate_selection_scorecard": FP["scorecard"], "outreach_message_template": FP["outreach"],
        "consent_and_intake_form": FP["consent"], "source_freeze_form": FP["source"],
        "preflight_checklist": FP["preflight"], "withdrawal_incident_protocol": FP["withdrawal"],
    }
    if v["artifact_fingerprints"] != expected:
        raise ProofEngineError("decision artifact binding mismatch")
    criteria = v["criteria_results"]
    if [x["criterion_id"] for x in criteria] != [f"EA-{i:03d}" for i in range(1, 17)]:
        raise ProofEngineError("decision criteria mismatch")
    if v["criterion_count"] != 16 or any(x["result"] != "PASS" for x in criteria):
        raise ProofEngineError("authorization review failed")
    if (v["decision"], v["state"], v["next_gate"]) != (
        "AUTHORIZE_INTERNAL_CANDIDATE_SELECTION_PREPARATION_ONLY",
        "INTERNAL_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_PACKET_COMPLETE",
        "HUMAN_NAMED_PARTICIPANT_CONTACT_AUTHORIZATION_REQUIRED",
    ):
        raise ProofEngineError("authorization terminal mismatch")
    if (v["product_readiness_score"], v["product_readiness_score_change"], v["rts_overall_planning_estimate_percent"]) != (93, 0, 78):
        raise ProofEngineError("progress or score mismatch")
    if any(v[name] is not False for name in (
        "external_evidence_created", "real_participant_selected", "external_contact_performed",
        "customer_intake_performed", "pilot_execution_performed",
    )):
        raise ProofEngineError("external action manufactured")
    if v["authority"].get("internal_candidate_selection_preparation_authorized") is not True:
        raise ProofEngineError("internal preparation decision missing")
    _closed(v["authority"])
    return v


def verify_progress(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("status", value, "map_fingerprint")
    axes = v["final_shape"]["axes"]
    current = v["current_position"]
    if (sum(x["score"] for x in axes), sum(x["maximum"] for x in axes)) != (78, 100):
        raise ProofEngineError("progress map mismatch")
    if (current["current_state"], current["next_gate"]) != (
        "INTERNAL_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_PACKET_COMPLETE",
        "HUMAN_NAMED_PARTICIPANT_CONTACT_AUTHORIZATION_REQUIRED",
    ):
        raise ProofEngineError("current position state mismatch")
    if tuple(current[k] for k in (
        "rts_overall_planning_estimate_percent", "short_term_internal_hardening_percent",
        "product_readiness_score", "product_readiness_score_change",
    )) != (78, 100, 93, 0):
        raise ProofEngineError("current position values mismatch")
    if current["internal_candidate_selection_preparation_authorized"] is not True:
        raise ProofEngineError("internal preparation not authorized")
    if any(current[k] is not False for k in (
        "real_participant_selected", "participant_contact_authorized",
        "customer_intake_authorized", "pilot_execution_authorized",
    )):
        raise ProofEngineError("external position widened")
    _closed(v["authority"])
    return v


def verify_checkpoint(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("checkpoint", value, "checkpoint_fingerprint")
    bindings = {
        "execution_authorization_contract_fingerprint": "contract",
        "candidate_selection_scorecard_fingerprint": "scorecard",
        "outreach_message_template_fingerprint": "outreach",
        "consent_and_intake_form_fingerprint": "consent",
        "source_freeze_form_fingerprint": "source",
        "preflight_checklist_fingerprint": "preflight",
        "withdrawal_incident_protocol_fingerprint": "withdrawal",
        "authorization_decision_fingerprint": "decision",
        "progress_map_fingerprint": "status",
    }
    if any(v[field] != FP[key] for field, key in bindings.items()):
        raise ProofEngineError("checkpoint binding mismatch")
    if tuple(v[k] for k in (
        "rts_overall_planning_estimate_percent", "short_term_internal_hardening_percent",
        "product_readiness_score",
    )) != (78, 100, 93):
        raise ProofEngineError("checkpoint values mismatch")
    performed = [k for k in v if k.endswith("_performed")]
    if any(v[k] is not False for k in performed):
        raise ProofEngineError("checkpoint external action")
    return v


def verify_customer_pilot_execution_authorization_stage() -> dict[str, Any]:
    prior = verify_prior_plan_history()
    result = {
        "prior": prior,
        "contract": verify_contract(),
        "scorecard": verify_scorecard(),
        "outreach": verify_outreach(),
        "consent": verify_consent(),
        "source": verify_source_freeze(),
        "preflight": verify_preflight(),
        "withdrawal": verify_withdrawal(),
        "decision": verify_decision(),
        "progress": verify_progress(),
        "checkpoint": verify_checkpoint(),
    }
    result["summary"] = {
        "state": "INTERNAL_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_PACKET_COMPLETE",
        "next_gate": "HUMAN_NAMED_PARTICIPANT_CONTACT_AUTHORIZATION_REQUIRED",
        "rts_overall_planning_estimate_percent": 78,
        "short_term_internal_hardening_percent": 100,
        "product_readiness_score": 93,
        "product_readiness_score_change": 0,
        "logical_artifact_count": 8,
        "review_criterion_count": 16,
        "preflight_check_count": 16,
        "candidate_count": 0,
        "internal_candidate_selection_preparation_authorized": True,
        "participant_contact_authorized": False,
        "customer_intake_authorized": False,
        "pilot_execution_authorized": False,
        "external_actions_performed": False,
    }
    return result
