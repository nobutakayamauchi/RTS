from __future__ import annotations

import base64
import copy
import json
import zlib
from pathlib import Path
from typing import Any

from .core import ProofEngineError, fingerprint, load

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
ROUND_DIR = PACKAGE_DIR / "product_readiness" / "round_0006"
STATUS_PATH = ROOT / "docs" / "status" / "RTS_CURRENT_POSITION_PILOT_PLAN.json"
CHECKPOINT_PATH = ROOT / "pilot_runs" / "reconnect_pilot_p3" / "evidence_report_customer_pilot_plan_checkpoint_0027.json"

BUNDLE_PATH = ROUND_DIR / "pilot_plan_bundle.b64"

PATHS = {
    "status": STATUS_PATH,
    "checkpoint": CHECKPOINT_PATH,
}

EXPECTED = {
    "contract": "aa509f46c8b6d6655a6f0da03eb130f3aaed88ae5aacdae62ad2add3b5e65ee0",
    "eligibility": "642bc404284972f0bada4e9a5126a1dc054cb114d26814f71e8611fbe1abd8f9",
    "boundary": "1a847ed62f860006820981f3f21bd52b0d23c8b01649858c92341dd29f79f3fc",
    "scorecard": "ab9706454911ff4daa1d3e22adff1eb1f04d165d3b7d0e899acc61ac37aeaf8e",
    "incident": "79e462b38950cd7ec0790d930fc0c4f7279b703bf7c29468b4f8143bc919ed8e",
    "score_hold": "1b1f156d66b13da701fe44b1c6ffa2d1651a4508237d9f54a8938eafa49f8879",
    "review": "de09265d7323a4c2321797a3b040f362bf44b89005c46a7fd9ddcef99d5dc871",
    "completion": "f1850340dd257b51903c2f8820f9a81b99c5873c67b93542573df10470142f8b",
    "status": "629a96de6d70b240aba3c04b5e838465621844902fa476eabd598d596dbaefee",
    "checkpoint": "b526cbfc833989d6f7d15e27b59f93896fe9b9aaa013f39bcaaa7998d0aa1718",
    "bundle": "5ceacb4d4798b31aa08bec544b56b016b8c84588ee7373e7318872cf67f61f6a"
}


CLOSED_AUTHORITY_FIELDS = {
    "customer_intake_authorized",
    "customer_pilot_execution_authorized",
    "participant_contact_authorized",
    "outreach_authorized",
    "pricing_authorized",
    "contract_authorized",
    "delivery_authorized",
    "publication_authorized",
    "external_execution_authorized",
    "source_repository_write_authorized",
    "target_repository_write_authorized",
}


def verify_bundle(value: dict[str, Any] | None = None) -> dict[str, Any]:
    if value is None:
        try:
            value = json.loads(zlib.decompress(base64.b64decode(BUNDLE_PATH.read_text(encoding="utf-8"))).decode("utf-8"))
        except (OSError, ValueError, zlib.error, json.JSONDecodeError) as exc:
            raise ProofEngineError("invalid pilot plan bundle") from exc
    value = copy.deepcopy(value)
    material = copy.deepcopy(value)
    actual = material.pop("bundle_fingerprint", None)
    if actual != EXPECTED["bundle"] or actual != fingerprint(material):
        raise ProofEngineError("bundle fingerprint mismatch")
    expected_keys = {"contract", "eligibility", "boundary", "scorecard", "incident", "score_hold", "review", "completion"}
    if value.get("logical_artifact_count") != 8 or set(value.get("artifacts", {})) != expected_keys:
        raise ProofEngineError("bundle shape mismatch")
    return value


def _signed(
    key: str,
    field: str,
    value: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if value is None:
        if key in ("status", "checkpoint"):
            value = load(PATHS[key])
        else:
            value = verify_bundle()["artifacts"][key]
    else:
        value = copy.deepcopy(value)
    material = copy.deepcopy(value)
    actual = material.pop(field, None)
    if actual != EXPECTED[key] or actual != fingerprint(material):
        raise ProofEngineError(f"{key} fingerprint mismatch")
    return value


def _closed(authority: dict[str, Any], label: str) -> None:
    if not CLOSED_AUTHORITY_FIELDS.issubset(authority):
        raise ProofEngineError(f"{label} authority fields missing")
    if any(authority[field] is not False for field in CLOSED_AUTHORITY_FIELDS):
        raise ProofEngineError(f"{label} authority widened")


def verify_contract(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("contract", "contract_fingerprint", value)
    if value.get("stage") != "PLAN_AND_REVIEW_ONLY":
        raise ProofEngineError("planning stage widened")
    shape = value.get("pilot_shape", {})
    required_shape = {
        "wip_limit": 1,
        "participant_limit": 1,
        "repository_limit": 1,
        "cycle_limit": 1,
        "source_visibility": "PUBLIC_ONLY",
        "source_mode": "READ_ONLY_FIXED_COMMIT_AND_MERGED_PR_METADATA",
        "operation_mode": "OPERATOR_ASSISTED",
        "commercial_consideration_authorized": False,
        "automatic_publication": False,
        "automatic_delivery": False,
    }
    if shape != required_shape:
        raise ProofEngineError("pilot shape mismatch")
    if len(value.get("planned_human_gates", [])) != 5 or len(value.get("planned_outputs", [])) != 7:
        raise ProofEngineError("pilot contract shape mismatch")
    if value.get("raw_user_input_included") is not False:
        raise ProofEngineError("raw instruction exposed")
    authority = value.get("authority", {})
    if authority.get("bounded_internal_pilot_planning_authorized") is not True:
        raise ProofEngineError("planning authority missing")
    _closed(authority, "contract")
    return value


def verify_eligibility(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("eligibility", "eligibility_fingerprint", value)
    if value.get("plan_contract_fingerprint") != EXPECTED["contract"]:
        raise ProofEngineError("eligibility binding mismatch")
    profile = value.get("required_profile", {})
    if profile.get("repository_visibility") != "PUBLIC":
        raise ProofEngineError("private repository eligibility")
    if profile.get("consent") != "EXPLICIT_WRITTEN_CONSENT_REQUIRED_BEFORE_ANY_EXECUTION":
        raise ProofEngineError("consent requirement weakened")
    checks = value.get("required_intake_checks", [])
    if [item.get("check_id") for item in checks] != [f"INT-{number:03d}" for number in range(1, 7)]:
        raise ProofEngineError("intake checklist mismatch")
    if value.get("automatic_acceptance") is not False or value.get("real_participant_selected") is not False:
        raise ProofEngineError("participant acceptance manufactured")
    _closed(value.get("authority", {}), "eligibility")
    return value


def verify_data_boundary(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("boundary", "boundary_fingerprint", value)
    if value.get("plan_contract_fingerprint") != EXPECTED["contract"]:
        raise ProofEngineError("data boundary binding mismatch")
    allowed = value.get("allowed_planned_inputs", [])
    if len(allowed) != 5 or any("private" in item.lower() for item in allowed):
        raise ProofEngineError("data input boundary widened")
    prohibited = value.get("prohibited_inputs", [])
    required_fragments = ("private repositories", "credentials", "customer", "medical", "confidential", "unknown-origin")
    if not all(any(fragment in item.lower() for item in prohibited) for fragment in required_fragments):
        raise ProofEngineError("prohibited input coverage mismatch")
    routing = value.get("routing_policy", {})
    expected_routing = {
        "credential_or_secret": "STOP",
        "high_risk_identifier": "EXCLUDE",
        "maskable_personal_data": "MASK_AND_REQUIRE_HUMAN_REVIEW",
        "private_or_confidential_source": "REJECT",
        "clean_public_source": "ELIGIBLE_FOR_LATER_HUMAN_INTAKE_REVIEW",
    }
    if routing != expected_routing:
        raise ProofEngineError("data routing mismatch")
    retention = value.get("retention_policy", {})
    if retention.get("raw_prohibited_payload_retained") is not False:
        raise ProofEngineError("raw prohibited payload retained")
    _closed(value.get("authority", {}), "data boundary")
    return value


def verify_scorecard(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("scorecard", "scorecard_fingerprint", value)
    if value.get("plan_contract_fingerprint") != EXPECTED["contract"]:
        raise ProofEngineError("scorecard binding mismatch")
    successes = value.get("success_criteria", [])
    failures = value.get("failure_conditions", [])
    if [item.get("criterion_id") for item in successes] != [f"PIL-S-{number:03d}" for number in range(1, 9)]:
        raise ProofEngineError("success criteria mismatch")
    if any(item.get("required") is not True for item in successes):
        raise ProofEngineError("required success criterion weakened")
    if [item.get("condition_id") for item in failures] != [f"PIL-F-{number:03d}" for number in range(1, 8)]:
        raise ProofEngineError("failure conditions mismatch")
    if value.get("scoring_rule") != "ALL_REQUIRED_SUCCESS_CRITERIA_MUST_PASS_AND_NO_FAILURE_CONDITION_MAY_REMAIN_OPEN":
        raise ProofEngineError("scorecard rule weakened")
    if value.get("partial_success_prohibited") is not True:
        raise ProofEngineError("partial pilot success allowed")
    _closed(value.get("authority", {}), "scorecard")
    return value


def verify_incident_runbook(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("incident", "runbook_fingerprint", value)
    if value.get("plan_contract_fingerprint") != EXPECTED["contract"]:
        raise ProofEngineError("incident binding mismatch")
    steps = value.get("response_steps", [])
    if [item.get("order") for item in steps] != list(range(1, 7)):
        raise ProofEngineError("incident response order mismatch")
    if value.get("no_raw_payload_in_incident_log") is not True:
        raise ProofEngineError("incident raw payload allowed")
    if value.get("automatic_resume") is not False:
        raise ProofEngineError("automatic resume widened")
    if [item.get("level") for item in value.get("severity_levels", [])] != ["P0", "P1", "P2"]:
        raise ProofEngineError("severity levels mismatch")
    _closed(value.get("authority", {}), "incident runbook")
    return value


def verify_score_hold(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("score_hold", "decision_fingerprint", value)
    if value.get("plan_contract_fingerprint") != EXPECTED["contract"]:
        raise ProofEngineError("score hold binding mismatch")
    if (
        value.get("previous_product_readiness_score"),
        value.get("current_product_readiness_score"),
        value.get("score_change"),
    ) != (93, 93, 0):
        raise ProofEngineError("readiness score inflated")
    if value.get("overall_rts_planning_estimate_percent") != 77:
        raise ProofEngineError("overall planning estimate mismatch")
    required_not_supported = {
        "CUSTOMER_PILOT_EXECUTION_AUTHORIZED",
        "CUSTOMER_VALUE_VALIDATED",
        "PRICING_VALIDATED",
        "DELIVERY_ACCEPTED",
        "COMMERCIAL_EFFECTIVENESS",
        "PRODUCTION_SERVICE_READY",
    }
    if set(value.get("not_supported", [])) != required_not_supported:
        raise ProofEngineError("unsupported claims mismatch")
    _closed(value.get("authority", {}), "score hold")
    return value


def verify_plan_review(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("review", "review_fingerprint", value)
    expected_sources = {
        "plan_contract_fingerprint": EXPECTED["contract"],
        "eligibility_fingerprint": EXPECTED["eligibility"],
        "data_boundary_fingerprint": EXPECTED["boundary"],
        "scorecard_fingerprint": EXPECTED["scorecard"],
        "incident_runbook_fingerprint": EXPECTED["incident"],
        "readiness_score_hold_fingerprint": EXPECTED["score_hold"],
    }
    if value.get("sources") != expected_sources:
        raise ProofEngineError("plan review source binding mismatch")
    criteria = value.get("criteria_results", [])
    if [item.get("criterion_id") for item in criteria] != [f"PPR-{number:03d}" for number in range(1, 16)]:
        raise ProofEngineError("plan review criteria mismatch")
    if any(item.get("result") != "PASS" or not item.get("evidence") for item in criteria):
        raise ProofEngineError("plan review failed")
    if value.get("decision") != "ACCEPT_BOUNDED_CUSTOMER_PILOT_PLAN_FOR_SEPARATE_EXECUTION_AUTHORIZATION_REVIEW":
        raise ProofEngineError("plan review decision mismatch")
    performed = (
        "real_participant_selected",
        "participant_contact_performed",
        "customer_intake_performed",
        "customer_pilot_performed",
        "external_human_review_performed",
    )
    if any(value.get(field) is not False for field in performed):
        raise ProofEngineError("pilot activity manufactured")
    authority = value.get("authority", {})
    if authority.get("bounded_internal_pilot_plan_review_authorized") is not True:
        raise ProofEngineError("plan review authority missing")
    _closed(authority, "plan review")
    return value


def verify_completion(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("completion", "completion_fingerprint", value)
    if value.get("state") != "INTERNAL_BOUNDED_CUSTOMER_PILOT_PLAN_REVIEW_COMPLETE":
        raise ProofEngineError("planning completion state mismatch")
    if value.get("next_gate") != "HUMAN_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_REQUIRED":
        raise ProofEngineError("planning next gate mismatch")
    if value.get("execution_status") != "NOT_AUTHORIZED" or value.get("participant_status") != "NOT_SELECTED":
        raise ProofEngineError("execution or participant status widened")
    position = value.get("current_position", {})
    if (
        position.get("rts_overall_planning_estimate_percent"),
        position.get("short_term_internal_hardening_percent"),
        position.get("product_readiness_score"),
        position.get("current_step"),
    ) != (77, 100, 93, "CUSTOMER-PILOT-EXECUTION-AUTHORIZATION"):
        raise ProofEngineError("completion position mismatch")
    expected_outputs = {
        "plan_contract_fingerprint": EXPECTED["contract"],
        "eligibility_fingerprint": EXPECTED["eligibility"],
        "data_boundary_fingerprint": EXPECTED["boundary"],
        "scorecard_fingerprint": EXPECTED["scorecard"],
        "incident_runbook_fingerprint": EXPECTED["incident"],
        "readiness_score_hold_fingerprint": EXPECTED["score_hold"],
        "plan_review_fingerprint": EXPECTED["review"],
    }
    if value.get("outputs") != expected_outputs:
        raise ProofEngineError("completion outputs mismatch")
    authority = value.get("authority", {})
    if authority.get("bounded_internal_pilot_planning_complete") is not True:
        raise ProofEngineError("planning completion authority missing")
    _closed(authority, "completion")
    return value


def verify_progress(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("status", "map_fingerprint", value)
    axes = value.get("final_shape", {}).get("axes", [])
    if sum(item.get("score", -1) for item in axes) != 77 or sum(item.get("maximum", -1) for item in axes) != 100:
        raise ProofEngineError("progress axes mismatch")
    position = value.get("current_position", {})
    if (
        position.get("rts_overall_planning_estimate_percent"),
        position.get("short_term_internal_hardening_percent"),
        position.get("product_readiness_score"),
        position.get("current_state"),
        position.get("current_step"),
    ) != (
        77,
        100,
        93,
        "INTERNAL_BOUNDED_CUSTOMER_PILOT_PLAN_REVIEW_COMPLETE",
        "CUSTOMER-PILOT-EXECUTION-AUTHORIZATION",
    ):
        raise ProofEngineError("current position mismatch")
    if position.get("pilot_plan_complete") is not True:
        raise ProofEngineError("pilot plan incomplete")
    if position.get("pilot_execution_authorized") is not False or position.get("real_participant_selected") is not False:
        raise ProofEngineError("pilot execution or participant manufactured")
    _closed(value.get("authority", {}), "progress")
    return value


def verify_checkpoint(value: dict[str, Any] | None = None) -> dict[str, Any]:
    value = _signed("checkpoint", "checkpoint_fingerprint", value)
    bindings = {
        "plan_contract_fingerprint": "contract",
        "eligibility_fingerprint": "eligibility",
        "data_boundary_fingerprint": "boundary",
        "scorecard_fingerprint": "scorecard",
        "incident_runbook_fingerprint": "incident",
        "readiness_score_hold_fingerprint": "score_hold",
        "plan_review_fingerprint": "review",
        "planning_completion_fingerprint": "completion",
        "progress_map_fingerprint": "status",
    }
    if any(value.get(field) != EXPECTED[key] for field, key in bindings.items()):
        raise ProofEngineError("checkpoint binding mismatch")
    if (
        value.get("state"),
        value.get("next_gate"),
        value.get("rts_overall_planning_estimate_percent"),
        value.get("short_term_internal_hardening_percent"),
        value.get("product_readiness_score"),
    ) != (
        "INTERNAL_BOUNDED_CUSTOMER_PILOT_PLAN_REVIEW_COMPLETE",
        "HUMAN_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_REQUIRED",
        77,
        100,
        93,
    ):
        raise ProofEngineError("checkpoint state mismatch")
    performed = [field for field in value if field.endswith("_performed")]
    if any(value[field] is not False for field in performed):
        raise ProofEngineError("checkpoint external action performed")
    return value


def verify_customer_pilot_plan_stage() -> dict[str, Any]:
    result = {
        "bundle": verify_bundle(),
        "contract": verify_contract(),
        "eligibility": verify_eligibility(),
        "boundary": verify_data_boundary(),
        "scorecard": verify_scorecard(),
        "incident": verify_incident_runbook(),
        "score_hold": verify_score_hold(),
        "review": verify_plan_review(),
        "completion": verify_completion(),
        "progress": verify_progress(),
        "checkpoint": verify_checkpoint(),
    }
    result["summary"] = {
        "state": "INTERNAL_BOUNDED_CUSTOMER_PILOT_PLAN_REVIEW_COMPLETE",
        "next_gate": "HUMAN_BOUNDED_CUSTOMER_PILOT_EXECUTION_AUTHORIZATION_REQUIRED",
        "rts_overall_planning_estimate_percent": 77,
        "short_term_internal_hardening_percent": 100,
        "product_readiness_score": 93,
        "product_readiness_score_change": 0,
        "participant_limit": 1,
        "repository_limit": 1,
        "cycle_limit": 1,
        "public_repository_only": True,
        "real_participant_selected": False,
        "participant_contact_performed": False,
        "customer_intake_performed": False,
        "customer_pilot_performed": False,
        "customer_pilot_execution_authorized": False,
        "pricing_authorized": False,
        "outreach_authorized": False,
        "contract_authorized": False,
        "delivery_authorized": False,
        "publication_authorized": False,
    }
    return result
