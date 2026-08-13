#!/usr/bin/env python3
"""Thin Event Assist state binder for 新RTS（仮称）.

This module deliberately does not retrieve law, schedule notifications, store evidence,
perform cryptography, or submit anything. It binds externally produced observations into
one small machine-checkable state and derives only mechanical gap/authority/watch results.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

SCHEMA = "new-rts-event-case/v0"
REPORT_SCHEMA = "new-rts-event-case-report/v0"
IMPLEMENTATION_ID = "thin-rts-event-state-binder/v0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EVENT_TRUTH_STATES = {"CONFIRMED", "OBSERVED", "DISPUTED", "UNKNOWN"}
FACT_STATES = {"CONFIRMED", "OBSERVED", "CONFLICT", "UNKNOWN"}
SOURCE_CLASSES = {
    "OFFICIAL_PRIMARY",
    "OFFICIAL_LOCAL",
    "OFFICIAL_PROCEDURE_PORTAL",
    "PROFESSIONAL_INSTRUCTION",
    "COMMON_PRACTICAL_FAILURE",
    "LOCAL_OR_PROVIDER_SPECIFIC",
    "NEWS_SIGNAL",
    "UNVERIFIED_CANDIDATE",
    "USER_CONFIRMED_INPUT",
}
SOURCE_STATES = {"CURRENT_OBSERVED", "STALE", "CONFLICT", "UNVERIFIED_SIGNAL", "UNKNOWN"}
EVIDENCE_STATES = {
    "PRESERVED_VERIFIED",
    "PRESERVED_UNVERIFIED",
    "PARTIAL",
    "MISSING_RECOVERABLE",
    "MISSING_IRRECOVERABLE",
    "BLOCKED_AUTHORITY",
    "BLOCKED_TECHNICAL",
    "NOT_APPLICABLE",
    "UNKNOWN",
}
TRIAGE_STATES = {"PRESERVE_HIGH", "PRESERVE_REVIEW", "IGNORE_LOW", "BLOCKED", "UNKNOWN"}
AUTHORITY_STATES = {"AUTHORIZED", "BLOCKED", "UNKNOWN", "NOT_APPLICABLE"}
AUTHORITY_KINDS = {"observe", "collect", "access", "transform", "disclose", "submit", "promote"}
PIN_CLASSES = {
    "ACTION_REQUIRED",
    "DEADLINE_SOON",
    "POSSIBLY_ELIGIBLE",
    "CLAIM_MAY_BE_MISSING",
    "NOTICE_MAY_BE_REQUIRED",
    "EVIDENCE_GAP",
    "DOCUMENT_GAP",
    "CAPTURE_WINDOW_CLOSING",
    "LAW_OR_PROGRAM_CHANGED",
    "WATCH_DEGRADED",
    "OFFICIAL_CONFIRMATION_REQUIRED",
    "PROFESSIONAL_REVIEW_RECOMMENDED",
    "UNKNOWN",
}
ASSERTION_STATES = {"CANDIDATE", "VERIFIED", "CONFLICT", "UNKNOWN"}
DOCUMENT_STATES = {
    "IDENTIFIED",
    "ELIGIBILITY_UNCONFIRMED",
    "ELIGIBILITY_CONFIRMED",
    "DOCUMENT_READY_DRAFT",
    "USER_REVIEW_REQUIRED",
    "SUBMISSION_AUTHORIZED",
    "SUBMITTED",
    "RECEIPT",
    "OUTCOME_OBSERVED",
}
LEGAL_PIN_CLASSES = {
    "POSSIBLY_ELIGIBLE",
    "CLAIM_MAY_BE_MISSING",
    "NOTICE_MAY_BE_REQUIRED",
    "LAW_OR_PROGRAM_CHANGED",
}
CURRENT_SOURCE_REQUIRED_PIN_CLASSES = LEGAL_PIN_CLASSES | {"DEADLINE_SOON"}
GAP_STATES = {
    "PARTIAL",
    "MISSING_RECOVERABLE",
    "MISSING_IRRECOVERABLE",
    "BLOCKED_AUTHORITY",
    "BLOCKED_TECHNICAL",
    "UNKNOWN",
}


class EventStateError(RuntimeError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EventStateError(f"{name} must be an object")
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise EventStateError(f"{name} must be a list")
    return value


def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventStateError(f"{name} must be a non-empty string")
    return value


def _parse_time(value: str, name: str) -> datetime:
    raw = _require_str(value, name)
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise EventStateError(f"{name} must be ISO-8601") from exc
    if dt.tzinfo is None:
        raise EventStateError(f"{name} must include timezone")
    return dt.astimezone(timezone.utc)


def _index(items: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for idx, item in enumerate(items):
        obj = _require_dict(item, f"{label}[{idx}]")
        ident = _require_str(obj.get(key), f"{label}[{idx}].{key}")
        if ident in out:
            raise EventStateError(f"duplicate {label} id: {ident}")
        out[ident] = obj
    return out


def _validate_sources(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = _require_list(case.get("sources", []), "sources")
    idx = _index(sources, "source_id", "sources")
    for source_id, src in idx.items():
        cls = _require_str(src.get("source_class"), f"source {source_id}.source_class")
        if cls not in SOURCE_CLASSES:
            raise EventStateError(f"source {source_id} has unsupported source_class: {cls}")
        state = _require_str(src.get("status"), f"source {source_id}.status")
        if state not in SOURCE_STATES:
            raise EventStateError(f"source {source_id} has unsupported status: {state}")
        _require_str(src.get("reference"), f"source {source_id}.reference")
        retrieved = _parse_time(src.get("retrieved_at"), f"source {source_id}.retrieved_at")
        stale_after = src.get("stale_after")
        if stale_after is not None:
            stale_at = _parse_time(stale_after, f"source {source_id}.stale_after")
            if stale_at < retrieved:
                raise EventStateError(f"source {source_id}.stale_after precedes retrieval")
        observed_ref = src.get("observed_artifact_ref")
        observed_digest = src.get("observed_sha256")
        if (observed_ref is None) != (observed_digest is None):
            raise EventStateError(f"source {source_id} observed artifact reference/digest must be bound together")
        if observed_ref is not None:
            _require_str(observed_ref, f"source {source_id}.observed_artifact_ref")
            if not isinstance(observed_digest, str) or not SHA256_RE.fullmatch(observed_digest):
                raise EventStateError(f"source {source_id}.observed_sha256 must be lowercase SHA-256")
    return idx


def _source_is_current(src: dict[str, Any], evaluated_at: datetime) -> bool:
    if src.get("status") != "CURRENT_OBSERVED":
        return False
    stale_after = src.get("stale_after")
    if stale_after is not None and evaluated_at > _parse_time(stale_after, f"source {src.get('source_id')}.stale_after"):
        return False
    return True


def _source_supports_verified_claim(src: dict[str, Any], evaluated_at: datetime) -> bool:
    return (
        src.get("source_class") in {"OFFICIAL_PRIMARY", "OFFICIAL_LOCAL", "OFFICIAL_PROCEDURE_PORTAL"}
        and _source_is_current(src, evaluated_at)
        and isinstance(src.get("observed_artifact_ref"), str)
        and bool(src.get("observed_artifact_ref"))
        and isinstance(src.get("observed_sha256"), str)
        and SHA256_RE.fullmatch(src["observed_sha256"]) is not None
    )


def _validate_facts(case: dict[str, Any], source_idx: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    facts = _require_list(case.get("facts", []), "facts")
    idx = _index(facts, "fact_id", "facts")
    for fact_id, fact in idx.items():
        _require_str(fact.get("name"), f"fact {fact_id}.name")
        state = _require_str(fact.get("status"), f"fact {fact_id}.status")
        if state not in FACT_STATES:
            raise EventStateError(f"fact {fact_id} has unsupported status: {state}")
        source_ref = fact.get("source_ref")
        if state == "CONFIRMED" and source_ref is None:
            raise EventStateError(f"fact {fact_id} CONFIRMED requires source_ref provenance")
        if source_ref is not None and source_ref not in source_idx:
            raise EventStateError(f"fact {fact_id} references unknown source: {source_ref}")
        if fact.get("observed_at") is not None:
            _parse_time(fact["observed_at"], f"fact {fact_id}.observed_at")
    return idx


def _validate_evidence(case: dict[str, Any], source_idx: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    evidence = _require_list(case.get("evidence", []), "evidence")
    idx = _index(evidence, "evidence_id", "evidence")
    for evidence_id, ev in idx.items():
        _require_str(ev.get("evidence_class"), f"evidence {evidence_id}.evidence_class")
        state = _require_str(ev.get("status"), f"evidence {evidence_id}.status")
        if state not in EVIDENCE_STATES:
            raise EventStateError(f"evidence {evidence_id} has unsupported status: {state}")
        triage = _require_str(ev.get("triage"), f"evidence {evidence_id}.triage")
        if triage not in TRIAGE_STATES:
            raise EventStateError(f"evidence {evidence_id} has unsupported triage: {triage}")
        source_ref = ev.get("source_ref")
        if source_ref is not None and source_ref not in source_idx:
            raise EventStateError(f"evidence {evidence_id} references unknown source: {source_ref}")
        authority_state = _require_str(ev.get("collection_authority"), f"evidence {evidence_id}.collection_authority")
        if authority_state not in AUTHORITY_STATES:
            raise EventStateError(f"evidence {evidence_id} has unsupported collection_authority")
        if state == "PRESERVED_VERIFIED":
            _require_str(ev.get("preservation_ref"), f"evidence {evidence_id}.preservation_ref")
            integrity = _require_str(ev.get("integrity_state"), f"evidence {evidence_id}.integrity_state")
            if integrity != "CONTENT_INTEGRITY_PASS":
                raise EventStateError(
                    f"evidence {evidence_id} cannot be PRESERVED_VERIFIED without CONTENT_INTEGRITY_PASS"
                )
        if state == "BLOCKED_AUTHORITY" and authority_state == "AUTHORIZED":
            raise EventStateError(f"evidence {evidence_id} BLOCKED_AUTHORITY conflicts with AUTHORIZED")
    return idx


