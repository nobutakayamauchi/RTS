from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "product_readiness" / "round_0003"
STATUS_PATH = ROOT / "docs" / "status" / "RTS_FINAL_SHAPE_AND_CURRENT_POSITION.json"
PROTOCOL_PATH = ROUND_DIR / "reader_review_protocol.json"
PACKET_V1_PATH = ROUND_DIR / "reader_packet_v1.json"
REVIEW_V1_PATH = ROUND_DIR / "reader_review_v1.json"
CONFUSION_PATH = ROUND_DIR / "confusion_log.json"
PACKET_V2_PATH = ROUND_DIR / "reader_packet_v2.json"
REVIEW_V2_PATH = ROUND_DIR / "reader_review_v2.json"
RESULT_PATH = ROUND_DIR / "hardening_execution_result.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_reader_usability_checkpoint_0024.json"

EXPECTED = {
    "progress": "3580adbae13e3651b979da85b5df58efd69543945ff975274e38cc181eb569f7",
    "protocol": "b2915b5cdacbac84373eb02f097f243d4e5513fe2a454c61f11678a30b5631f6",
    "packet_v1": "25a8d821d29e6969a5e803817518d158793d5ec0f2d12cf42b8745744cd8c2df",
    "review_v1": "2d853acf70c4a5816365e047bc0de730d67475afcf64839c53c467934620011e",
    "confusion": "10a75b6c210efed103b59963e4fa67a704563452b3cc49a9ad213b0c3b8567a2",
    "packet_v2": "cda00bd68291227841655f77f46946b068aa4f28810c87a3fd2d6d200da359b7",
    "review_v2": "bbc90723e8b04c02e4b40630beebdd8877e523db15fa6f204cc252a2d8466914",
    "result": "69f6face6ff2fcf3ff27f55aeb2f9964621259db060f5381a26fdfa0005a85fc",
    "checkpoint": "23d926fb0e77bb1df8c69922992cc4a30d9c58f0295ca3c185a124d871d152c6",
}

FALSE_AUTHORITY_FIELDS = {
    "customer_pilot_authorized",
    "customer_intake_authorized",
    "pricing_authorized",
    "outreach_authorized",
    "contract_authorized",
    "delivery_authorized",
    "publication_authorized",
    "external_execution_authorized",
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


def verify_progress_map(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(STATUS_PATH), "map_fingerprint", EXPECTED["progress"], "progress map")
    axes = value.get("final_shape", {}).get("axes", [])
    if sum(item.get("score", -1) for item in axes) != 74 or sum(item.get("maximum", -1) for item in axes) != 100:
        raise ProofEngineError("overall progress mismatch")
    current = value.get("current_position", {})
    if current.get("short_term_completion_percent") != 97 or current.get("current_step") != "HARD-004":
        raise ProofEngineError("current position mismatch")
    if current.get("completed") != ["HARD-001", "HARD-002", "HARD-003"]:
        raise ProofEngineError("completed hardening order mismatch")
    _require_false_authority(value.get("authority", {}), FALSE_AUTHORITY_FIELDS, "progress map")
    return value


def verify_protocol(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(PROTOCOL_PATH), "protocol_fingerprint", EXPECTED["protocol"], "reader protocol")
    if value.get("review_mode") != "ROLE_SEPARATED_DELEGATED_BLIND_READER_DRY_RUN":
        raise ProofEngineError("review mode widened")
    if len(value.get("reader_roles", [])) != 3 or len(value.get("questions", [])) != 6:
        raise ProofEngineError("reader protocol shape mismatch")
    if value.get("authority", {}).get("external_human_claim_authorized") is not False:
        raise ProofEngineError("external-human claim widened")
    return value


def verify_packet_v1(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(PACKET_V1_PATH), "packet_fingerprint", EXPECTED["packet_v1"], "reader packet v1")
    if len(value.get("case_summaries", [])) != 2:
        raise ProofEngineError("reader packet case count mismatch")
    second = value["case_summaries"][1]
    if second.get("withheld") != ["END_TO_END_OPERATION", "TRANSCRIPTION_ACCURACY", "PRODUCTION_READINESS"]:
        raise ProofEngineError("reader packet withheld topics mismatch")
    return value


def verify_review_v1(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(REVIEW_V1_PATH), "review_fingerprint", EXPECTED["review_v1"], "reader review v1")
    if value.get("packet_fingerprint") != EXPECTED["packet_v1"]:
        raise ProofEngineError("review v1 packet binding mismatch")
    confusions = [item for reader in value.get("reader_results", []) for item in reader.get("material_confusions", [])]
    if {item.get("confusion_id") for item in confusions} != {"C-01", "C-02", "C-03", "C-04"}:
        raise ProofEngineError("review v1 confusion set mismatch")
    if value.get("external_human_review_performed") is not False:
        raise ProofEngineError("external review manufactured")
    return value


def verify_confusion_log(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(CONFUSION_PATH), "log_fingerprint", EXPECTED["confusion"], "confusion log")
    if value.get("source_review_fingerprint") != EXPECTED["review_v1"]:
        raise ProofEngineError("confusion log binding mismatch")
    if [item.get("confusion_id") for item in value.get("entries", [])] != ["C-01", "C-02", "C-03", "C-04"]:
        raise ProofEngineError("confusion log order mismatch")
    if value.get("raw_user_input_included") is not False:
        raise ProofEngineError("raw user input exposed")
    return value


def verify_packet_v2(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(PACKET_V2_PATH), "packet_fingerprint", EXPECTED["packet_v2"], "reader packet v2")
    if value.get("supersedes_packet_fingerprint") != EXPECTED["packet_v1"]:
        raise ProofEngineError("packet v2 append-only binding mismatch")
    if value.get("revision_log_fingerprint") != EXPECTED["confusion"]:
        raise ProofEngineError("packet v2 revision binding mismatch")
    status = value.get("plain_language_status", {})
    if len(status.get("verified_now", [])) != 4 or len(status.get("not_verified", [])) != 5:
        raise ProofEngineError("packet v2 status shape mismatch")
    if value.get("external_human_validation_claimed") is not False:
        raise ProofEngineError("external-human validation manufactured")
    return value


def verify_review_v2(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(REVIEW_V2_PATH), "review_fingerprint", EXPECTED["review_v2"], "reader review v2")
    if value.get("packet_fingerprint") != EXPECTED["packet_v2"] or value.get("supersedes_review_fingerprint") != EXPECTED["review_v1"]:
        raise ProofEngineError("review v2 append-only binding mismatch")
    readers = value.get("reader_results", [])
    if len(readers) != 3:
        raise ProofEngineError("review v2 reader count mismatch")
    for reader in readers:
        if reader.get("correct_answers") != 6 or reader.get("total_questions") != 6:
            raise ProofEngineError("reader comprehension failed")
        if reader.get("verified_vs_withheld_distinguished") is not True or reader.get("commercial_inference_rejected") is not True:
            raise ProofEngineError("reader boundary comprehension failed")
        if reader.get("material_confusions") != [] or reader.get("result") != "PASS":
            raise ProofEngineError("reader v2 material confusion remains")
    if value.get("external_human_review_performed") is not False:
        raise ProofEngineError("external review manufactured")
    return value


def verify_result(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(RESULT_PATH), "result_fingerprint", EXPECTED["result"], "hardening result")
    completed = value.get("completed_work_item", {})
    if completed.get("work_id") != "HARD-003" or completed.get("result") != "PASS_INTERNAL":
        raise ProofEngineError("HARD-003 result mismatch")
    if value.get("state") != "INTERNAL_ROLE_SEPARATED_READER_USABILITY_VALIDATED":
        raise ProofEngineError("HARD-003 state mismatch")
    if value.get("next_gate") != "HUMAN_THIRD_CASE_GENERALIZATION_PLAN_REQUIRED":
        raise ProofEngineError("HARD-003 next gate mismatch")
    progress = value.get("completion_update", {})
    if progress.get("rts_overall_planning_estimate_percent") != 74 or progress.get("short_term_internal_product_candidate_percent") != 97:
        raise ProofEngineError("HARD-003 completion mismatch")
    authority = value.get("authority", {})
    if authority.get("bounded_internal_reader_review_authorized") is not True:
        raise ProofEngineError("bounded reader review authority missing")
    _require_false_authority(authority, FALSE_AUTHORITY_FIELDS, "hardening result")
    if authority.get("external_human_validation_claim_authorized") is not False:
        raise ProofEngineError("external-human claim widened")
    return value


def verify_checkpoint(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _verify_fingerprint(value or load(CHECKPOINT_PATH), "checkpoint_fingerprint", EXPECTED["checkpoint"], "reader checkpoint")
    if value.get("hardening_execution_result_fingerprint") != EXPECTED["result"]:
        raise ProofEngineError("checkpoint result binding mismatch")
    if value.get("progress_map_fingerprint") != EXPECTED["progress"] or value.get("reader_review_v2_fingerprint") != EXPECTED["review_v2"]:
        raise ProofEngineError("checkpoint output binding mismatch")
    performed = [field for field in value if field.endswith("_performed")]
    if any(value[field] is not False for field in performed):
        raise ProofEngineError("checkpoint external action performed")
    return value


def verify_reader_usability_stage() -> dict[str, Any]:
    progress = verify_progress_map()
    protocol = verify_protocol()
    packet_v1 = verify_packet_v1()
    review_v1 = verify_review_v1()
    confusion = verify_confusion_log()
    packet_v2 = verify_packet_v2()
    review_v2 = verify_review_v2()
    result = verify_result()
    checkpoint = verify_checkpoint()
    outputs = result["completed_work_item"]["outputs"]
    expected_outputs = {
        "progress_map_fingerprint": EXPECTED["progress"],
        "review_protocol_fingerprint": EXPECTED["protocol"],
        "reader_packet_v1_fingerprint": EXPECTED["packet_v1"],
        "reader_review_v1_fingerprint": EXPECTED["review_v1"],
        "confusion_log_fingerprint": EXPECTED["confusion"],
        "reader_packet_v2_fingerprint": EXPECTED["packet_v2"],
        "reader_review_v2_fingerprint": EXPECTED["review_v2"],
    }
    if outputs != expected_outputs:
        raise ProofEngineError("HARD-003 output bindings mismatch")
    return {
        "progress": progress,
        "protocol": protocol,
        "packet_v1": packet_v1,
        "review_v1": review_v1,
        "confusion": confusion,
        "packet_v2": packet_v2,
        "review_v2": review_v2,
        "result": result,
        "checkpoint": checkpoint,
        "summary": {
            "state": result["state"],
            "next_gate": result["next_gate"],
            "rts_overall_planning_estimate_percent": 74,
            "short_term_internal_product_candidate_percent": 97,
            "product_readiness_baseline_score": 82,
            "current_step": "HARD-004",
            "reader_roles": 3,
            "questions_per_reader": 6,
            "version_1_material_confusions": 4,
            "version_2_material_confusions": 0,
            "external_human_review_performed": False,
            "remaining_work_items": ["HARD-004", "HARD-005"],
        },
    }
