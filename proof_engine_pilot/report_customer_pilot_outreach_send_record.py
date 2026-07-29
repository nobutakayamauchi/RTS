from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "product_readiness" / "round_0010"
CONTRACT_PATH = ROUND_DIR / "outreach_send_record_contract.json"
EVENT_PATH = ROUND_DIR / "human_attested_send_event.json"
PRIVACY_PATH = ROUND_DIR / "privacy_minimization_record.json"
WINDOW_PATH = ROUND_DIR / "response_wait_window.json"
SCORE_PATH = ROUND_DIR / "readiness_score_hold.json"
COMPLETION_PATH = ROUND_DIR / "outreach_waiting_completion.json"
POSITION_PATH = ROOT / "docs" / "status" / "RTS_CURRENT_POSITION_OUTREACH_WAITING.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_customer_pilot_outreach_waiting_checkpoint_0031.json"
PRIOR_COMPLETION_PATH = PACKAGE_DIR / "product_readiness" / "round_0009" / "named_candidate_contact_packet_completion.json"
PRIOR_POSITION_PATH = ROOT / "docs" / "status" / "RTS_CURRENT_POSITION_NAMED_CANDIDATE_CONTACT_PACKET.json"
PRIOR_CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_customer_pilot_named_candidate_contact_packet_checkpoint_0030.json"

EXPECTED_AUTHORITY = {
    "additional_outreach_authorized": False,
    "analysis_authorized": False,
    "contract_authorized": False,
    "customer_intake_authorized": False,
    "customer_pilot_execution_authorized": False,
    "delivery_authorized": False,
    "external_execution_authorized": False,
    "follow_up_authorized": False,
    "historical_one_time_outreach_human_authorized": True,
    "internal_outreach_recording_authorized": True,
    "pricing_authorized": False,
    "publication_authorized": False,
    "source_repository_write_authorized": False,
    "target_repository_write_authorized": False,
}


class OutreachRecordError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise OutreachRecordError(f"invalid or missing JSON: {path}") from exc
    if not isinstance(value, dict):
        raise OutreachRecordError("JSON root must be an object")
    return value


def verify_fingerprint(value: dict, field: str, label: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != fingerprint(material):
        raise OutreachRecordError(f"{label} fingerprint mismatch")
    return actual


def verify_prior_history() -> dict:
    completion = load(PRIOR_COMPLETION_PATH)
    position = load(PRIOR_POSITION_PATH)
    checkpoint = load(PRIOR_CHECKPOINT_PATH)
    if completion.get("completion_fingerprint") != "4b721f6dadcf318809de7a64950deb58e1e5a556414194606a30f5508e4a2d31":
        raise OutreachRecordError("prior completion drift")
    if position.get("map_fingerprint") != "1e83fe35d1c93b8d1bb75de379423142937b26896408966ef391106eca45d624":
        raise OutreachRecordError("prior position drift")
    if checkpoint.get("checkpoint_fingerprint") != "f2c9eb691f785853190bd7e66b5413792f652efb814530944e32d978ecd151a4":
        raise OutreachRecordError("prior checkpoint drift")
    return {"completion": completion, "position": position, "checkpoint": checkpoint}


def verify_contract(value: dict | None = None) -> dict:
    value = load(CONTRACT_PATH) if value is None else value
    verify_fingerprint(value, "contract_fingerprint", "contract")
    if value.get("schema_version") != "RTS-CUSTOMER-PILOT-OUTREACH-SEND-RECORD-CONTRACT-V1":
        raise OutreachRecordError("contract schema mismatch")
    if value.get("selected_repository") != "jbexta/AgentPilot":
        raise OutreachRecordError("candidate repository drift")
    if value.get("authority") != EXPECTED_AUTHORITY:
        raise OutreachRecordError("contract authority widened")
    allowed = value.get("allowed_record", {})
    expected = {
        "route": "DISCORD_DM",
        "recipient_public_handle": "jbexta",
        "send_event_count": 1,
        "evidence_class": "HUMAN_ATTESTED",
        "message_body_storage": False,
        "exact_payload_match_claim": False,
    }
    if allowed != expected:
        raise OutreachRecordError("allowed record boundary mismatch")
    if len(value.get("required_stops", [])) != 5:
        raise OutreachRecordError("required stops mismatch")
    return value


def verify_event(value: dict | None = None, contract: dict | None = None) -> dict:
    value = load(EVENT_PATH) if value is None else value
    contract = verify_contract() if contract is None else contract
    verify_fingerprint(value, "event_fingerprint", "event")
    if value.get("contract_fingerprint") != contract["contract_fingerprint"]:
        raise OutreachRecordError("event contract mismatch")
    expected = {
        "candidate_repository": "jbexta/AgentPilot",
        "route": "DISCORD_DM",
        "recipient_public_handle": "jbexta",
        "event_date_local": "2026-07-29",
        "event_time_local": None,
        "event_time_precision": "DATE_ONLY",
        "send_event_count": 1,
        "follow_up_event_count": 0,
        "response_event_count": 0,
        "response_status": "NOT_REPORTED_AT_RECORD_TIME",
        "historical_one_time_authorization_consumed": True,
        "additional_outreach_authorized": False,
        "participant_contact_performed": True,
        "pilot_participant_selected": False,
        "customer_intake_performed": False,
        "analysis_performed": False,
        "publication_performed": False,
        "target_repository_write_performed": False,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise OutreachRecordError(f"event boundary mismatch: {key}")
    evidence = value.get("evidence", {})
    if evidence != {
        "class": "HUMAN_ATTESTED",
        "source": "USER_REPORT_IN_CURRENT_CONVERSATION",
        "independent_delivery_receipt_available": False,
        "message_body_stored": False,
        "message_exactly_verified": False,
        "screenshot_stored": False,
    }:
        raise OutreachRecordError("event evidence overclaimed")
    return value


def verify_privacy(value: dict | None = None, event: dict | None = None, contract: dict | None = None) -> dict:
    value = load(PRIVACY_PATH) if value is None else value
    contract = verify_contract() if contract is None else contract
    event = verify_event(contract=contract) if event is None else event
    verify_fingerprint(value, "privacy_fingerprint", "privacy")
    if value.get("contract_fingerprint") != contract["contract_fingerprint"] or value.get("event_fingerprint") != event["event_fingerprint"]:
        raise OutreachRecordError("privacy linkage mismatch")
    if value.get("raw_private_payload_retained") is not False or value.get("contact_graph_expansion_performed") is not False:
        raise OutreachRecordError("private payload retained")
    excluded = set(value.get("excluded_fields", []))
    required = {
        "private message body",
        "Discord message identifier",
        "Discord server identifier",
        "screenshot",
        "device metadata",
    }
    if not required <= excluded or value.get("result") != "PASS_MINIMUM_NECESSARY_RECORD":
        raise OutreachRecordError("privacy exclusions incomplete")
    return value


def verify_window(value: dict | None = None, event: dict | None = None, contract: dict | None = None) -> dict:
    value = load(WINDOW_PATH) if value is None else value
    contract = verify_contract() if contract is None else contract
    event = verify_event(contract=contract) if event is None else event
    verify_fingerprint(value, "window_fingerprint", "wait window")
    if value.get("contract_fingerprint") != contract["contract_fingerprint"] or value.get("event_fingerprint") != event["event_fingerprint"]:
        raise OutreachRecordError("window linkage mismatch")
    expected = {
        "duration_days": 14,
        "reminder_created": True,
        "discord_content_monitoring_available": False,
        "instant_reply_detection_available": False,
        "follow_up_authorized": False,
        "follow_up_limit": 0,
        "no_response_action": "CLOSE_WITHOUT_FOLLOW_UP",
        "current_state": "WAITING_FOR_HUMAN_REPORTED_RESPONSE_OR_WINDOW_EXPIRY",
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise OutreachRecordError(f"wait boundary mismatch: {key}")
    return value


def verify_score(value: dict | None = None, event: dict | None = None, contract: dict | None = None) -> dict:
    value = load(SCORE_PATH) if value is None else value
    contract = verify_contract() if contract is None else contract
    event = verify_event(contract=contract) if event is None else event
    verify_fingerprint(value, "score_hold_fingerprint", "score hold")
    if value.get("contract_fingerprint") != contract["contract_fingerprint"] or value.get("event_fingerprint") != event["event_fingerprint"]:
        raise OutreachRecordError("score linkage mismatch")
    if value.get("prior_product_readiness_score") != 93 or value.get("current_product_readiness_score") != 93 or value.get("score_change") != 0:
        raise OutreachRecordError("product readiness inflated")
    return value


def verify_completion(
    value: dict | None = None,
    *,
    contract: dict | None = None,
    event: dict | None = None,
    privacy: dict | None = None,
    window: dict | None = None,
    score: dict | None = None,
) -> dict:
    value = load(COMPLETION_PATH) if value is None else value
    contract = verify_contract() if contract is None else contract
    event = verify_event(contract=contract) if event is None else event
    privacy = verify_privacy(event=event, contract=contract) if privacy is None else privacy
    window = verify_window(event=event, contract=contract) if window is None else window
    score = verify_score(event=event, contract=contract) if score is None else score
    verify_fingerprint(value, "completion_fingerprint", "completion")
    if value.get("state") != "HUMAN_ATTESTED_ONE_TIME_OUTREACH_RECORDED" or value.get("next_gate") != "HUMAN_RESPONSE_EVENT_OR_NO_RESPONSE_WINDOW_EXPIRY_REQUIRED":
        raise OutreachRecordError("completion state mismatch")
    expected_links = {
        "send_event": event["event_fingerprint"],
        "privacy_minimization": privacy["privacy_fingerprint"],
        "response_wait_window": window["window_fingerprint"],
        "score_hold": score["score_hold_fingerprint"],
    }
    if value.get("artifact_fingerprints") != expected_links or value.get("authority") != EXPECTED_AUTHORITY:
        raise OutreachRecordError("completion linkage or authority mismatch")
    expected_counts = {
        "message_send_event_count": 1,
        "follow_up_event_count": 0,
        "response_event_count": 0,
        "pilot_participant_count": 0,
        "customer_intake_event_count": 0,
        "pilot_execution_event_count": 0,
        "product_readiness_score": 93,
        "rts_overall_planning_estimate_percent": 81,
        "short_term_internal_hardening_percent": 100,
    }
    for key, expected_value in expected_counts.items():
        if value.get(key) != expected_value:
            raise OutreachRecordError(f"completion count mismatch: {key}")
    if len(value.get("acceptance_results", [])) != 10 or any(item.get("result") != "PASS" for item in value["acceptance_results"]):
        raise OutreachRecordError("completion acceptance mismatch")
    return value


def verify_position(value: dict | None = None, completion: dict | None = None) -> dict:
    value = load(POSITION_PATH) if value is None else value
    completion = verify_completion() if completion is None else completion
    verify_fingerprint(value, "map_fingerprint", "position")
    if value.get("authority") != EXPECTED_AUTHORITY:
        raise OutreachRecordError("position authority mismatch")
    current = value.get("current_position", {})
    expected = {
        "current_state": completion["state"],
        "next_gate": completion["next_gate"],
        "rts_overall_planning_estimate_percent": 81,
        "product_readiness_score": 93,
        "message_send_event_count": 1,
        "follow_up_event_count": 0,
        "response_event_count": 0,
        "response_status": "NOT_REPORTED_AT_RECORD_TIME",
        "pilot_participant_selected": False,
        "customer_intake_authorized": False,
        "analysis_authorized": False,
        "pilot_execution_authorized": False,
    }
    for key, expected_value in expected.items():
        if current.get(key) != expected_value:
            raise OutreachRecordError(f"position mismatch: {key}")
    axes = value.get("final_shape", {}).get("axes", [])
    if sum(item.get("score", -999) for item in axes) != 81:
        raise OutreachRecordError("position score mismatch")
    return value


def verify_checkpoint(
    value: dict | None = None,
    *,
    completion: dict | None = None,
    position: dict | None = None,
    contract: dict | None = None,
    event: dict | None = None,
    privacy: dict | None = None,
    window: dict | None = None,
    score: dict | None = None,
) -> dict:
    value = load(CHECKPOINT_PATH) if value is None else value
    contract = verify_contract() if contract is None else contract
    event = verify_event(contract=contract) if event is None else event
    privacy = verify_privacy(event=event, contract=contract) if privacy is None else privacy
    window = verify_window(event=event, contract=contract) if window is None else window
    score = verify_score(event=event, contract=contract) if score is None else score
    completion = verify_completion(contract=contract, event=event, privacy=privacy, window=window, score=score) if completion is None else completion
    position = verify_position(completion=completion) if position is None else position
    verify_fingerprint(value, "checkpoint_fingerprint", "checkpoint")
    links = {
        "contract_fingerprint": contract["contract_fingerprint"],
        "event_fingerprint": event["event_fingerprint"],
        "privacy_fingerprint": privacy["privacy_fingerprint"],
        "window_fingerprint": window["window_fingerprint"],
        "score_hold_fingerprint": score["score_hold_fingerprint"],
        "completion_fingerprint": completion["completion_fingerprint"],
        "progress_map_fingerprint": position["map_fingerprint"],
    }
    for key, expected_value in links.items():
        if value.get(key) != expected_value:
            raise OutreachRecordError(f"checkpoint linkage mismatch: {key}")
    expected = {
        "message_send_performed": True,
        "message_send_event_count": 1,
        "follow_up_performed": False,
        "response_event_count": 0,
        "customer_intake_performed": False,
        "analysis_performed": False,
        "pilot_execution_performed": False,
        "pricing_performed": False,
        "contract_action_performed": False,
        "delivery_performed": False,
        "publication_performed": False,
        "external_execution_performed": False,
        "source_or_target_repository_writes_performed": False,
        "product_readiness_score": 93,
        "rts_overall_planning_estimate_percent": 81,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise OutreachRecordError(f"checkpoint boundary mismatch: {key}")
    return value


def verify_all() -> dict:
    verify_prior_history()
    contract = verify_contract()
    event = verify_event(contract=contract)
    privacy = verify_privacy(event=event, contract=contract)
    window = verify_window(event=event, contract=contract)
    score = verify_score(event=event, contract=contract)
    completion = verify_completion(contract=contract, event=event, privacy=privacy, window=window, score=score)
    position = verify_position(completion=completion)
    checkpoint = verify_checkpoint(
        completion=completion,
        position=position,
        contract=contract,
        event=event,
        privacy=privacy,
        window=window,
        score=score,
    )
    return {
        "state": completion["state"],
        "next_gate": completion["next_gate"],
        "rts_overall_planning_estimate_percent": 81,
        "short_term_internal_hardening_percent": 100,
        "product_readiness_score": 93,
        "message_send_event_count": 1,
        "follow_up_event_count": 0,
        "response_event_count": 0,
        "response_status": "NOT_REPORTED_AT_RECORD_TIME",
        "discord_content_monitoring_available": False,
        "pilot_participant_count": 0,
        "customer_intake_event_count": 0,
        "pilot_execution_event_count": 0,
        "checkpoint_fingerprint": checkpoint["checkpoint_fingerprint"],
    }
