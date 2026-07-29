from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load

P = Path(__file__).resolve().parent
R = P.parent
D = P / "product_readiness" / "round_0009"

PATH = {
    "contract": D / "selection_and_contact_authorization_contract.json",
    "selection": D / "named_candidate_selection.json",
    "route": D / "public_contact_route_review.json",
    "message": D / "personalized_outreach_message.json",
    "preflight": D / "one_time_send_preflight.json",
    "response": D / "response_handling_protocol.json",
    "score_hold": D / "readiness_score_hold.json",
    "completion": D / "named_candidate_contact_packet_completion.json",
    "status": R / "docs/status/RTS_CURRENT_POSITION_NAMED_CANDIDATE_CONTACT_PACKET.json",
    "checkpoint": R / "pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_named_candidate_contact_packet_checkpoint_0030.json",
    "prior_completion": P / "product_readiness" / "round_0008/candidate_shortlist_completion.json",
    "prior_status": R / "docs/status/RTS_CURRENT_POSITION_CANDIDATE_SHORTLIST.json",
    "prior_checkpoint": R / "pilot_runs/reconnect_pilot_p3/evidence_report_customer_pilot_candidate_shortlist_checkpoint_0029.json",
}

FP = {
    "contract": "3f71633c06e7325958f716f66965cd277146e0c1190482365ee052972988a057",
    "selection": "84826d5caab1db7c37c244a7d00751f9e1b63d451d6d5a9bc5ff436d8f117e27",
    "route": "6e6d6d3e64e727f536860f15fd6745d30468e1d877277c79d5d8647d0bda3d98",
    "message": "b3342d54593eec798601f5a338996567ec8c79e90edc67d92dc073ed695b4729",
    "preflight": "aa0176da6c414238e570a828747eee4bae7e14dc7ff574b55e2b4e48221d2510",
    "response": "5e9c932f30ee6f1f74996be87b1a2357adf9ce75fb29bbbf75c80bd5d901a898",
    "score_hold": "66be286d2cc39b3bfc4c7f8ce081ab9a41c44deea29d3495cb32e0397b24815e",
    "completion": "4b721f6dadcf318809de7a64950deb58e1e5a556414194606a30f5508e4a2d31",
    "status": "1e83fe35d1c93b8d1bb75de379423142937b26896408966ef391106eca45d624",
    "checkpoint": "f2c9eb691f785853190bd7e66b5413792f652efb814530944e32d978ecd151a4",
}

PRIOR = {
    "completion": "4bc4c3cb4bcf121e21887c150363035074680ebdd356d4640d412ab01790a853",
    "status": "963cdcbff1c70c3c432135021fd67f0386e417571a2aaff7c9ec74d04a09042d",
    "checkpoint": "42212a185a492ebc92c15a9fd90abc4e22fea0c90cae794560ef275365400861",
}

CLOSED = {
    "contract_authorized",
    "customer_intake_authorized",
    "customer_pilot_execution_authorized",
    "delivery_authorized",
    "external_execution_authorized",
    "outreach_authorized",
    "participant_contact_authorized",
    "pricing_authorized",
    "publication_authorized",
    "source_repository_write_authorized",
    "target_repository_write_authorized",
}

INTERNAL_TRUE = {
    "internal_contact_packet_preparation_authorized",
    "internal_named_contact_candidate_selection_authorized",
}


def _signed(key: str, value: dict[str, Any] | None, field: str) -> dict[str, Any]:
    v = load(PATH[key]) if value is None else copy.deepcopy(value)
    material = copy.deepcopy(v)
    actual = material.pop(field, None)
    if actual != FP[key] or fingerprint(material) != actual:
        raise ProofEngineError(f"{key} fingerprint mismatch")
    return v


def _closed(authority: dict[str, Any]) -> None:
    if not CLOSED.issubset(authority):
        raise ProofEngineError("closed authority field missing")
    if any(authority[name] is not False for name in CLOSED):
        raise ProofEngineError("external authority widened")
    if not INTERNAL_TRUE.issubset(authority):
        raise ProofEngineError("internal authority field missing")
    if any(authority[name] is not True for name in INTERNAL_TRUE):
        raise ProofEngineError("internal preparation authority missing")


def _prior_signed(
    key: str,
    value: dict[str, Any] | None,
    field: str,
    expected: str,
) -> dict[str, Any]:
    v = load(PATH[key]) if value is None else copy.deepcopy(value)
    material = copy.deepcopy(v)
    actual = material.pop(field, None)
    if actual != expected or fingerprint(material) != actual:
        raise ProofEngineError(f"{key} changed")
    return v


def verify_prior_shortlist_history(
    completion: dict[str, Any] | None = None,
    status: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, str]:
    c = _prior_signed("prior_completion", completion, "completion_fingerprint", PRIOR["completion"])
    s = _prior_signed("prior_status", status, "map_fingerprint", PRIOR["status"])
    k = _prior_signed("prior_checkpoint", checkpoint, "checkpoint_fingerprint", PRIOR["checkpoint"])
    if c["state"] != "INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE":
        raise ProofEngineError("prior shortlist state mismatch")
    if s["current_position"]["next_gate"] != "HUMAN_RECOMMENDED_CANDIDATE_SELECTION_AND_CONTACT_AUTHORIZATION_REQUIRED":
        raise ProofEngineError("prior shortlist next gate mismatch")
    if k["selected_count"] != 0 or k["participant_contact_performed"] is not False:
        raise ProofEngineError("prior shortlist external action drift")
    return {"completion": PRIOR["completion"], "status": PRIOR["status"], "checkpoint": PRIOR["checkpoint"]}


def verify_contract(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("contract", value, "contract_fingerprint")
    source = v["source"]
    if source != {
        "normalized_instruction": "Complete the named-candidate selection and contact-authorization packet while showing overall and stage progress, but do not send any external message.",
        "prior_candidate_shortlist_checkpoint_fingerprint": PRIOR["checkpoint"],
        "prior_candidate_shortlist_completion_fingerprint": PRIOR["completion"],
        "prior_candidate_shortlist_status_fingerprint": PRIOR["status"],
        "prior_state": "INTERNAL_PUBLIC_CANDIDATE_SHORTLIST_COMPLETE",
        "raw_instruction_retained": False,
        "raw_instruction_sha256": "e0d913688f8af37a6814304035c309625ccefffb3631fc4bf9ffe4f05bdcef1c",
    }:
        raise ProofEngineError("instruction or prior-history binding mismatch")
    if v["scope"] != {
        "compensation_jpy": 0,
        "fixed_commit_limit": 1,
        "follow_up_limit": 0,
        "named_contact_candidate_limit": 1,
        "operator_assisted": True,
        "outbound_message_limit": 0,
        "pilot_participant_limit": 0,
        "public_contact_route_observation_limit": 2,
        "public_issue_or_pull_request_contact_allowed": False,
        "public_repository_limit": 1,
    }:
        raise ProofEngineError("contact packet scope widened")
    if v["authorized_now"] != {
        "customer_intake": False,
        "internal_contact_route_review": True,
        "internal_named_contact_candidate_selection": True,
        "one_time_send_preflight_preparation": True,
        "participant_contact": False,
        "personalized_message_preparation": True,
        "pilot_execution": False,
    }:
        raise ProofEngineError("contact packet authority mismatch")
    acceptance = v["acceptance"]
    if tuple(acceptance[k] for k in (
        "artifact_count",
        "customer_intake_events_required",
        "focused_test_count_minimum",
        "named_contact_candidate_count_required",
        "participant_contact_events_required",
        "pilot_execution_events_required",
        "pilot_participant_count_required",
        "product_readiness_score_required",
        "review_criterion_count",
        "rts_overall_planning_estimate_percent_required",
    )) != (8, 0, 28, 1, 0, 0, 0, 93, 18, 80):
        raise ProofEngineError("contact packet acceptance mismatch")
    _closed(v["authority"])
    return v


def verify_selection(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("selection", value, "selection_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("selection contract binding mismatch")
    identity = v["candidate_public_identity"]
    if identity != {
        "fixed_commit_sha": "333eb6ce4f193852f4d9fe5412e8636929b6bb4e",
        "github_login": "jbexta",
        "prior_rank": 1,
        "public_readme_blob_sha": "ecf562df63252d4376446cc882d3d5598f668f06",
        "public_score": 86,
        "repository": "jbexta/AgentPilot",
        "repository_visibility": "PUBLIC",
    }:
        raise ProofEngineError("selected contact candidate changed")
    if (
        v["selected_contact_candidate_count"],
        v["selected_repository"],
        v["selection_status"],
    ) != (
        1,
        "jbexta/AgentPilot",
        "SELECTED_FOR_ONE_TIME_CONTACT_AUTHORIZATION_REVIEW",
    ):
        raise ProofEngineError("named contact candidate selection mismatch")
    if v["pilot_participant_count"] != 0 or v["pilot_participant_selected"] is not False:
        raise ProofEngineError("contact candidate silently became participant")
    if v["pending_human_gates"] != [
        "CONTACT_ACCOUNT_IDENTITY_VERIFICATION",
        "CONTACT_ROUTE_ACCEPTABILITY_VERIFICATION",
        "REPOSITORY_AUTHORITY_CONFIRMATION",
        "WRITTEN_VOLUNTARY_CONSENT",
    ]:
        raise ProofEngineError("pending human gate set weakened")
    if len(v["decision_basis"]) != 5:
        raise ProofEngineError("selection evidence basis mismatch")
    _closed(v["authority"])
    return v


def verify_route(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("route", value, "route_review_fingerprint")
    if v["contract_fingerprint"] != FP["contract"] or v["candidate_selection_fingerprint"] != FP["selection"]:
        raise ProofEngineError("route binding mismatch")
    if v["fixed_public_evidence"] != {
        "fixed_commit_sha": "333eb6ce4f193852f4d9fe5412e8636929b6bb4e",
        "readme_blob_sha": "ecf562df63252d4376446cc882d3d5598f668f06",
        "readme_line_range": [20, 24],
        "repository": "jbexta/AgentPilot",
    }:
        raise ProofEngineError("route evidence boundary changed")
    routes = v["observed_routes"]
    if len(routes) != 2 or v["route_count"] != 2:
        raise ProofEngineError("route count mismatch")
    if [(x["platform"], x["priority"], x["public_identifier"]) for x in routes] != [
        ("X", 1, "AgentPilotAI"),
        ("DISCORD", 2, "1169291612816420896"),
    ]:
        raise ProofEngineError("public route set changed")
    if any(x["identity_verification_status"] != "PENDING_HUMAN_VERIFICATION" for x in routes):
        raise ProofEngineError("contact identity falsely verified")
    if any(x["acceptability_status"] != "PENDING_HUMAN_VERIFICATION" for x in routes):
        raise ProofEngineError("contact acceptability falsely verified")
    if v["preferred_route"] != {
        "platform": "X",
        "recipient_account": None,
        "route_type": "DIRECT_MESSAGE_IF_AVAILABLE",
        "status": "PREFERRED_PENDING_HUMAN_VERIFICATION",
    }:
        raise ProofEngineError("preferred route prematurely finalized")
    required_prohibited = {
        "PUBLIC_GITHUB_ISSUE_WITHOUT_EXPLICIT_INVITATION",
        "PUBLIC_GITHUB_PULL_REQUEST",
        "UNVERIFIED_EMAIL_ADDRESS",
        "SCRAPED_PRIVATE_CONTACT_INFORMATION",
        "MULTI_CHANNEL_BLAST",
    }
    if set(v["prohibited_routes"]) != required_prohibited:
        raise ProofEngineError("prohibited route boundary weakened")
    if v["send_target_populated"] is not False:
        raise ProofEngineError("send target silently populated")
    _closed(v["authority"])
    return v


def verify_message(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("message", value, "message_fingerprint")
    if (
        v["contract_fingerprint"] != FP["contract"]
        or v["candidate_selection_fingerprint"] != FP["selection"]
        or v["route_review_fingerprint"] != FP["route"]
    ):
        raise ProofEngineError("message artifact binding mismatch")
    if (v["send_status"], v["send_event_count"], v["named_recipient"]) != ("NOT_SENT", 0, None):
        raise ProofEngineError("message was targeted or sent")
    if v["message_language"] != "en" or v["personalized_repository"] != "jbexta/AgentPilot":
        raise ProofEngineError("message personalization mismatch")
    body = v["body"]
    required = [
        "one public GitHub repository",
        "free of charge",
        "No analysis would begin",
        "private unless you separately approve sharing",
        "decline or withdraw at any time",
        "Would you be open to receiving the one-page scope?",
    ]
    if any(text not in body for text in required):
        raise ProofEngineError("message disclosure missing")
    if len(v["disclosures"]) != 9 or len(v["prohibited_claims"]) != 6:
        raise ProofEngineError("message boundary mismatch")
    if "reply is not consent and does not start analysis" not in v["disclosures"]:
        raise ProofEngineError("reply-only consent guard missing")
    _closed(v["authority"])
    return v


def verify_preflight(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("preflight", value, "preflight_fingerprint")
    if (
        v["contract_fingerprint"] != FP["contract"]
        or v["candidate_selection_fingerprint"] != FP["selection"]
        or v["message_fingerprint"] != FP["message"]
    ):
        raise ProofEngineError("send preflight binding mismatch")
    if v["status"] != "BLANK_NOT_EXECUTED" or v["completed_check_count"] != 0:
        raise ProofEngineError("send preflight falsely executed")
    if v["all_checks_required"] is not True or v["partial_pass_allowed"] is not False:
        raise ProofEngineError("partial send preflight allowed")
    if v["outbound_message_limit"] != 0 or v["follow_up_limit"] != 0:
        raise ProofEngineError("send or follow-up authority widened")
    checks = v["checks"]
    if [x["id"] for x in checks] != [f"OS-{i:02d}" for i in range(1, 19)]:
        raise ProofEngineError("send preflight check set mismatch")
    if any(x["phase"] != "PRE_SEND" or x["status"] != "PENDING" for x in checks):
        raise ProofEngineError("send preflight silently advanced")
    _closed(v["authority"])
    return v


def verify_response(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("response", value, "response_protocol_fingerprint")
    if v["contract_fingerprint"] != FP["contract"] or v["message_fingerprint"] != FP["message"]:
        raise ProofEngineError("response protocol binding mismatch")
    if (
        v["automatic_customer_intake"] is not False
        or v["automatic_pilot_start"] is not False
        or v["raw_prohibited_payload_retention"] is not False
        or v["response_event_count"] != 0
    ):
        raise ProofEngineError("response processing authority widened")
    policy = v["no_response_policy"]
    if policy != {
        "days_until_close": 14,
        "follow_up_count": 0,
        "result": "CLOSE_WITHOUT_CONTACT_RETRY",
    }:
        raise ProofEngineError("no-response policy weakened")
    classes = {x["class"]: x for x in v["response_classes"]}
    if set(classes) != {
        "POSITIVE_INTEREST",
        "NEGATIVE_OR_DECLINE",
        "AMBIGUOUS",
        "NO_RESPONSE",
        "UNSOLICITED_SECRET_OR_PRIVATE_DATA",
    }:
        raise ProofEngineError("response class set mismatch")
    if any(x["creates_consent"] is not False for x in classes.values()):
        raise ProofEngineError("response silently creates consent")
    if classes["NEGATIVE_OR_DECLINE"]["action"] != "STOP_AND_CLOSE":
        raise ProofEngineError("decline does not stop")
    if "DO_NOT_INTAKE_OR_ANALYZE" not in classes["AMBIGUOUS"]["action"]:
        raise ProofEngineError("ambiguous response allowed intake")
    if "WITHOUT_FOLLOW_UP" not in classes["NO_RESPONSE"]["action"]:
        raise ProofEngineError("no-response follow-up allowed")
    if "EXCLUDE_RAW_PAYLOAD" not in classes["UNSOLICITED_SECRET_OR_PRIVATE_DATA"]["action"]:
        raise ProofEngineError("prohibited raw payload retention allowed")
    _closed(v["authority"])
    return v


def verify_score_hold(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("score_hold", value, "score_hold_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("score hold contract binding mismatch")
    if v["current_score"] != 93 or v["score_change"] != 0:
        raise ProofEngineError("product readiness score inflated")
    evidence_fields = [
        "commercial_effectiveness_evidence_added",
        "customer_value_evidence_added",
        "delivery_acceptance_evidence_added",
        "external_human_usability_evidence_added",
        "pricing_evidence_added",
    ]
    if any(v[name] is not False for name in evidence_fields):
        raise ProofEngineError("external evidence manufactured")
    _closed(v["authority"])
    return v


def verify_completion(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("completion", value, "completion_fingerprint")
    if v["contract_fingerprint"] != FP["contract"]:
        raise ProofEngineError("completion contract binding mismatch")
    expected = {
        "candidate_selection": FP["selection"],
        "contact_route_review": FP["route"],
        "one_time_send_preflight": FP["preflight"],
        "personalized_outreach_message": FP["message"],
        "response_handling_protocol": FP["response"],
        "score_hold": FP["score_hold"],
    }
    if v["artifact_fingerprints"] != expected:
        raise ProofEngineError("completion artifact binding mismatch")
    if [x["criterion_id"] for x in v["acceptance_results"]] != [f"NCC-{i:02d}" for i in range(1, 13)]:
        raise ProofEngineError("completion criterion set mismatch")
    if any(x["result"] != "PASS" for x in v["acceptance_results"]):
        raise ProofEngineError("contact packet completion includes non-pass criterion")
    if (
        v["state"],
        v["next_gate"],
        v["named_contact_candidate_count"],
        v["pilot_participant_count"],
        v["message_send_event_count"],
        v["customer_intake_event_count"],
        v["pilot_execution_event_count"],
        v["response_event_count"],
        v["product_readiness_score"],
        v["rts_overall_planning_estimate_percent"],
        v["selected_repository"],
    ) != (
        "INTERNAL_NAMED_CANDIDATE_SELECTION_AND_CONTACT_PACKET_COMPLETE",
        "HUMAN_ONE_TIME_OUTREACH_SEND_AUTHORIZATION_REQUIRED",
        1,
        0,
        0,
        0,
        0,
        0,
        93,
        80,
        "jbexta/AgentPilot",
    ):
        raise ProofEngineError("contact packet completion state mismatch")
    _closed(v["authority"])
    return v


def verify_progress(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("status", value, "map_fingerprint")
    position = v["current_position"]
    if (
        position["current_state"],
        position["current_step"],
        position["next_gate"],
        position["rts_overall_planning_estimate_percent"],
        position["short_term_internal_hardening_percent"],
        position["product_readiness_score"],
    ) != (
        "INTERNAL_NAMED_CANDIDATE_SELECTION_AND_CONTACT_PACKET_COMPLETE",
        "ONE-TIME-OUTREACH-SEND-AUTHORIZATION",
        "HUMAN_ONE_TIME_OUTREACH_SEND_AUTHORIZATION_REQUIRED",
        80,
        100,
        93,
    ):
        raise ProofEngineError("current position mismatch")
    if (
        position["contact_packet_complete"] is not True
        or position["named_contact_candidate_selected"] is not True
        or position["recommended_candidate_repository"] != "jbexta/AgentPilot"
        or position["pilot_participant_selected"] is not False
        or position["message_send_event_count"] != 0
        or position["participant_contact_authorized"] is not False
        or position["participant_contact_performed"] is not False
        or position["customer_intake_authorized"] is not False
        or position["pilot_execution_authorized"] is not False
    ):
        raise ProofEngineError("current position authority or count drift")
    axes = v["final_shape"]["axes"]
    if sum(x["score"] for x in axes) != 80 or axes[-1] != {
        "axis": "PRODUCT_AND_SERVICE_OPERATING_LAYER",
        "maximum": 25,
        "score": 21,
        "state": "IN_PROGRESS",
    }:
        raise ProofEngineError("planning axis estimate drift")
    if v["final_shape"]["target_percent"] != 100:
        raise ProofEngineError("final target changed")
    _closed(v["authority"])
    return v


def verify_checkpoint(value: dict[str, Any] | None = None) -> dict[str, Any]:
    v = _signed("checkpoint", value, "checkpoint_fingerprint")
    expected_bindings = {
        "candidate_selection_fingerprint": FP["selection"],
        "completion_fingerprint": FP["completion"],
        "contact_route_review_fingerprint": FP["route"],
        "contract_fingerprint": FP["contract"],
        "message_fingerprint": FP["message"],
        "one_time_send_preflight_fingerprint": FP["preflight"],
        "prior_candidate_shortlist_checkpoint_fingerprint": PRIOR["checkpoint"],
        "prior_candidate_shortlist_completion_fingerprint": PRIOR["completion"],
        "prior_candidate_shortlist_status_fingerprint": PRIOR["status"],
        "progress_map_fingerprint": FP["status"],
        "response_handling_protocol_fingerprint": FP["response"],
        "score_hold_fingerprint": FP["score_hold"],
    }
    if any(v[name] != expected for name, expected in expected_bindings.items()):
        raise ProofEngineError("checkpoint artifact binding mismatch")
    false_actions = [
        "contract_action_performed",
        "customer_intake_performed",
        "delivery_performed",
        "external_execution_performed",
        "message_send_performed",
        "participant_contact_performed",
        "pilot_execution_performed",
        "pricing_performed",
        "publication_performed",
        "source_or_target_repository_writes_performed",
    ]
    if any(v[name] is not False for name in false_actions):
        raise ProofEngineError("checkpoint records external action")
    if (
        v["state"],
        v["next_gate"],
        v["named_contact_candidate_count"],
        v["pilot_participant_count"],
        v["response_event_count"],
        v["product_readiness_score"],
        v["rts_overall_planning_estimate_percent"],
        v["short_term_internal_hardening_percent"],
    ) != (
        "INTERNAL_NAMED_CANDIDATE_SELECTION_AND_CONTACT_PACKET_COMPLETE",
        "HUMAN_ONE_TIME_OUTREACH_SEND_AUTHORIZATION_REQUIRED",
        1,
        0,
        0,
        93,
        80,
        100,
    ):
        raise ProofEngineError("checkpoint state mismatch")
    return v


def verify_all() -> dict[str, Any]:
    verify_prior_shortlist_history()
    contract = verify_contract()
    selection = verify_selection()
    route = verify_route()
    message = verify_message()
    preflight = verify_preflight()
    response = verify_response()
    score_hold = verify_score_hold()
    completion = verify_completion()
    progress = verify_progress()
    checkpoint = verify_checkpoint()
    return {
        "contract": contract,
        "selection": selection,
        "route": route,
        "message": message,
        "preflight": preflight,
        "response": response,
        "score_hold": score_hold,
        "completion": completion,
        "progress": progress,
        "checkpoint": checkpoint,
    }


def summary() -> dict[str, Any]:
    values = verify_all()
    position = values["progress"]["current_position"]
    return {
        "state": position["current_state"],
        "next_gate": position["next_gate"],
        "rts_overall_planning_estimate_percent": position["rts_overall_planning_estimate_percent"],
        "short_term_internal_hardening_percent": position["short_term_internal_hardening_percent"],
        "product_readiness_score": position["product_readiness_score"],
        "product_readiness_score_change": values["score_hold"]["score_change"],
        "named_contact_candidate_count": values["completion"]["named_contact_candidate_count"],
        "selected_repository": values["selection"]["selected_repository"],
        "public_score": values["selection"]["candidate_public_identity"]["public_score"],
        "pilot_participant_count": values["completion"]["pilot_participant_count"],
        "preferred_route_status": values["route"]["preferred_route"]["status"],
        "named_recipient": values["message"]["named_recipient"],
        "message_send_event_count": values["message"]["send_event_count"],
        "response_event_count": values["response"]["response_event_count"],
        "participant_contact_authorized": values["contract"]["authority"]["participant_contact_authorized"],
        "customer_intake_authorized": values["contract"]["authority"]["customer_intake_authorized"],
        "pilot_execution_authorized": values["contract"]["authority"]["customer_pilot_execution_authorized"],
        "external_actions_performed": any([
            values["checkpoint"]["message_send_performed"],
            values["checkpoint"]["participant_contact_performed"],
            values["checkpoint"]["customer_intake_performed"],
            values["checkpoint"]["pilot_execution_performed"],
            values["checkpoint"]["external_execution_performed"],
        ]),
    }
