from __future__ import annotations

from .base import (
    Any,
    datetime,
    timedelta,
    AUTHORITY_KINDS,
    AUTHORITY_STATES,
    ASSERTION_STATES,
    CURRENT_SOURCE_REQUIRED_PIN_CLASSES,
    DOCUMENT_STATES,
    PIN_CLASSES,
    EventStateError,
    _index,
    _parse_time,
    _require_dict,
    _require_list,
    _require_str,
    _source_is_current,
    _source_supports_verified_claim,
)
def _validate_authorities(case: dict[str, Any]) -> dict[str, str]:
    authorities = _require_dict(case.get("authorities", {}), "authorities")
    normalized: dict[str, str] = {}
    for kind in AUTHORITY_KINDS:
        state = authorities.get(kind, "UNKNOWN")
        if state not in AUTHORITY_STATES:
            raise EventStateError(f"authority {kind} has unsupported state: {state}")
        normalized[kind] = state
    for key in authorities:
        if key not in AUTHORITY_KINDS:
            raise EventStateError(f"unsupported authority kind: {key}")
    return normalized


def _validate_decisions(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisions = _require_list(case.get("decisions", []), "decisions")
    idx = _index(decisions, "decision_id", "decisions")
    for decision_id, decision in idx.items():
        _require_str(decision.get("result"), f"decision {decision_id}.result")
        status = _require_str(decision.get("status"), f"decision {decision_id}.status")
        if status not in ASSERTION_STATES:
            raise EventStateError(f"decision {decision_id} has unsupported status: {status}")
        _require_str(decision.get("actor_tool"), f"decision {decision_id}.actor_tool")
        _parse_time(decision.get("time"), f"decision {decision_id}.time")
        _require_str(decision.get("reason"), f"decision {decision_id}.reason")
        refs = _require_list(decision.get("input_refs", []), f"decision {decision_id}.input_refs")
        if not all(isinstance(v, str) and v for v in refs):
            raise EventStateError(f"decision {decision_id}.input_refs must contain non-empty strings")
        supersedes = decision.get("supersedes")
        if supersedes is not None:
            if supersedes == decision_id or supersedes not in idx:
                raise EventStateError(f"decision {decision_id} supersedes unknown/self decision: {supersedes}")
            if _parse_time(idx[supersedes]["time"], f"decision {supersedes}.time") >= _parse_time(
                decision["time"], f"decision {decision_id}.time"
            ):
                raise EventStateError(f"decision {decision_id} must occur after superseded decision")
    return idx


def _validate_actions(
    case: dict[str, Any],
    source_idx: dict[str, dict[str, Any]],
    fact_idx: dict[str, dict[str, Any]],
    authorities: dict[str, str],
    evaluated_at: datetime,
) -> dict[str, dict[str, Any]]:
    actions = _require_list(case.get("actions", []), "actions")
    idx = _index(actions, "action_id", "actions")
    for action_id, action in idx.items():
        pin = _require_str(action.get("pin_class"), f"action {action_id}.pin_class")
        if pin not in PIN_CLASSES:
            raise EventStateError(f"action {action_id} has unsupported pin_class: {pin}")
        assertion = _require_str(action.get("assertion_state"), f"action {action_id}.assertion_state")
        if assertion not in ASSERTION_STATES:
            raise EventStateError(f"action {action_id} has unsupported assertion_state: {assertion}")
        _require_str(action.get("reason"), f"action {action_id}.reason")
        _require_str(action.get("next_action"), f"action {action_id}.next_action")
        source_refs = _require_list(action.get("source_refs", []), f"action {action_id}.source_refs")
        if not all(isinstance(v, str) and v for v in source_refs):
            raise EventStateError(f"action {action_id}.source_refs must contain non-empty strings")
        missing = [ref for ref in source_refs if ref not in source_idx]
        if missing:
            raise EventStateError(f"action {action_id} references unknown source(s): {', '.join(missing)}")
        authority_required = action.get("authority_required")
        if authority_required is not None:
            if authority_required not in AUTHORITY_KINDS:
                raise EventStateError(f"action {action_id} has unsupported authority_required")
            # Lack of authority is a visible state, not a structural error.
            action["authority_state"] = authorities[authority_required]
        if action.get("deadline") is not None:
            _parse_time(action["deadline"], f"action {action_id}.deadline")

        required_fact_refs = _require_list(action.get("required_fact_refs", []), f"action {action_id}.required_fact_refs")
        if not all(isinstance(v, str) and v for v in required_fact_refs):
            raise EventStateError(f"action {action_id}.required_fact_refs must contain non-empty strings")
        if any(ref not in fact_idx for ref in required_fact_refs):
            raise EventStateError(f"action {action_id} references unknown required fact")
        if assertion == "VERIFIED" and any(fact_idx[ref]["status"] != "CONFIRMED" for ref in required_fact_refs):
            raise EventStateError(f"action {action_id} cannot be VERIFIED with unconfirmed applicability fact")

        if pin in CURRENT_SOURCE_REQUIRED_PIN_CLASSES and assertion == "VERIFIED":
            supporting = [source_idx[ref] for ref in source_refs]
            if not any(_source_supports_verified_claim(src, evaluated_at) for src in supporting):
                raise EventStateError(
                    f"action {action_id} cannot be VERIFIED legal/deadline pin without current official source and observed artifact digest"
                )
        notification = action.get("notification")
        if notification is not None:
            note = _require_dict(notification, f"action {action_id}.notification")
            disclosure = _require_str(note.get("disclosure"), f"action {action_id}.notification.disclosure")
            if disclosure not in {"MINIMAL", "PROTECTED_VIEW_ONLY", "EXPLICIT_SENSITIVE_ALLOWED"}:
                raise EventStateError(f"action {action_id} has unsupported notification disclosure")
            if disclosure != "EXPLICIT_SENSITIVE_ALLOWED" and note.get("contains_sensitive_detail") is True:
                raise EventStateError(f"action {action_id} leaks sensitive detail to external notification")
    return idx


def _validate_documents(
    case: dict[str, Any],
    source_idx: dict[str, dict[str, Any]],
    fact_idx: dict[str, dict[str, Any]],
    evidence_idx: dict[str, dict[str, Any]],
    authorities: dict[str, str],
    evaluated_at: datetime,
) -> dict[str, dict[str, Any]]:
    documents = _require_list(case.get("documents", []), "documents")
    idx = _index(documents, "document_id", "documents")
    for document_id, doc in idx.items():
        state = _require_str(doc.get("state"), f"document {document_id}.state")
        if state not in DOCUMENT_STATES:
            raise EventStateError(f"document {document_id} has unsupported state: {state}")
        source_ref = doc.get("official_source_ref")
        if source_ref is not None and source_ref not in source_idx:
            raise EventStateError(f"document {document_id} references unknown source: {source_ref}")
        required_facts = _require_list(doc.get("required_fact_refs", []), f"document {document_id}.required_fact_refs")
        required_evidence = _require_list(
            doc.get("required_evidence_refs", []), f"document {document_id}.required_evidence_refs"
        )
        if any(ref not in fact_idx for ref in required_facts):
            raise EventStateError(f"document {document_id} references unknown required fact")
        if any(ref not in evidence_idx for ref in required_evidence):
            raise EventStateError(f"document {document_id} references unknown required evidence")
        if state in {"DOCUMENT_READY_DRAFT", "USER_REVIEW_REQUIRED", "SUBMISSION_AUTHORIZED", "SUBMITTED", "RECEIPT", "OUTCOME_OBSERVED"}:
            if source_ref is None:
                raise EventStateError(f"document {document_id} ready-state requires official_source_ref")
            source = source_idx[source_ref]
            if not _source_supports_verified_claim(source, evaluated_at):
                raise EventStateError(f"document {document_id} ready-state requires current official source and observed artifact digest")
            if any(fact_idx[ref]["status"] != "CONFIRMED" for ref in required_facts):
                raise EventStateError(f"document {document_id} ready-state has unconfirmed required fact")
            if any(evidence_idx[ref]["status"] not in {"PRESERVED_VERIFIED", "PRESERVED_UNVERIFIED"} for ref in required_evidence):
                raise EventStateError(f"document {document_id} ready-state has missing required evidence")
        if state in {"SUBMISSION_AUTHORIZED", "SUBMITTED", "RECEIPT", "OUTCOME_OBSERVED"} and authorities["submit"] != "AUTHORIZED":
            raise EventStateError(f"document {document_id} submission state requires explicit submit authority")
    return idx


def _watch_report(
    case: dict[str, Any],
    evaluated_at: datetime,
    source_idx: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    watches = _require_list(case.get("watches", []), "watches")
    idx = _index(watches, "watch_id", "watches")
    report: list[dict[str, Any]] = []
    for watch_id, watch in idx.items():
        last = _parse_time(watch.get("last_successful_check"), f"watch {watch_id}.last_successful_check")
        threshold = watch.get("staleness_threshold_seconds")
        if not isinstance(threshold, int) or threshold <= 0:
            raise EventStateError(f"watch {watch_id}.staleness_threshold_seconds must be positive integer")
        next_expected_raw = watch.get("next_expected_check")
        next_expected = _parse_time(next_expected_raw, f"watch {watch_id}.next_expected_check") if next_expected_raw else None
        source_set = _require_list(watch.get("source_set", []), f"watch {watch_id}.source_set")
        if not source_set or not all(isinstance(v, str) and v for v in source_set):
            raise EventStateError(f"watch {watch_id}.source_set must contain references")
        missing_sources = [ref for ref in source_set if ref not in source_idx]
        if missing_sources:
            raise EventStateError(f"watch {watch_id} references unknown source(s): {', '.join(missing_sources)}")
        delivery = _require_str(
            watch.get("notification_delivery_state", "UNKNOWN"),
            f"watch {watch_id}.notification_delivery_state",
        )
        if delivery not in {"DELIVERED", "FAILED", "PENDING", "NOT_REQUIRED", "UNKNOWN"}:
            raise EventStateError(f"watch {watch_id} has unsupported notification_delivery_state")
        stale = evaluated_at > last + timedelta(seconds=threshold)
        missed = next_expected is not None and evaluated_at > next_expected and last < next_expected
        failure = watch.get("failure_state")
        degraded = stale or missed or (isinstance(failure, str) and failure not in {"NONE", "NOT_APPLICABLE"}) or delivery == "FAILED"
        report.append(
            {
                "watch_id": watch_id,
                "status": "WATCH_DEGRADED" if degraded else "CURRENT",
                "last_successful_check": watch["last_successful_check"],
                "next_expected_check": next_expected_raw,
                "notification_delivery_state": delivery,
            }
        )
    return sorted(report, key=lambda v: v["watch_id"])


