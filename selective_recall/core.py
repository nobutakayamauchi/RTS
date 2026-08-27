"""Deterministic, non-authorizing selective recall and memory lifecycle validation.

This module is intentionally repository-local and read-only. It does not own raw
memory bodies, execute tools, call providers, mutate lifecycle records, or grant
execution/promotion authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


REGISTRY_SCHEMA_VERSION = 1
OUTPUT_SCHEMA_VERSION = 1
NO_AUTHORITY = "NONE"

LIFECYCLE_STATES = frozenset(
    {
        "RAW",
        "ACTIVE_CANDIDATE",
        "VERIFICATION_PENDING",
        "REPEATED",
        "PROMOTION_READY",
        "CANONICAL",
        "FOLDED",
        "SUPERSEDED",
        "ARCHIVED",
        "QUARANTINED",
    }
)

DEFAULT_RECALL_ELIGIBLE_STATES = frozenset(
    {
        "ACTIVE_CANDIDATE",
        "VERIFICATION_PENDING",
        "REPEATED",
        "PROMOTION_READY",
        "CANONICAL",
    }
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "RAW": frozenset({"ACTIVE_CANDIDATE", "QUARANTINED", "ARCHIVED"}),
    "ACTIVE_CANDIDATE": frozenset({"VERIFICATION_PENDING", "QUARANTINED", "ARCHIVED"}),
    "VERIFICATION_PENDING": frozenset(
        {"REPEATED", "ACTIVE_CANDIDATE", "QUARANTINED", "ARCHIVED"}
    ),
    "REPEATED": frozenset(
        {"PROMOTION_READY", "ACTIVE_CANDIDATE", "QUARANTINED", "ARCHIVED"}
    ),
    "PROMOTION_READY": frozenset({"CANONICAL", "REPEATED", "QUARANTINED", "ARCHIVED"}),
    "CANONICAL": frozenset({"FOLDED", "SUPERSEDED", "QUARANTINED"}),
    "FOLDED": frozenset({"SUPERSEDED", "ARCHIVED"}),
    "SUPERSEDED": frozenset({"ARCHIVED"}),
    "QUARANTINED": frozenset({"RAW", "ARCHIVED"}),
    "ARCHIVED": frozenset(),
}

REGISTRY_FIELDS = {
    "schema_version",
    "execution_authority",
    "promotion_authority",
    "records",
}
RECORD_FIELDS = {
    "memory_id",
    "source_path",
    "source_git_blob_sha",
    "lifecycle_state",
    "event_triggers",
    "scope_tags",
    "as_of",
    "superseded_by",
    "evidence_refs",
}
REQUEST_FIELDS = {
    "event",
    "scope_tags",
    "current_context_sufficient",
    "explicit_recall",
    "max_results",
}


class RecallValidationError(ValueError):
    """Raised when recall/lifecycle input fails closed validation."""


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    source_path: str
    source_git_blob_sha: str
    lifecycle_state: str
    event_triggers: tuple[str, ...]
    scope_tags: tuple[str, ...]
    as_of: str
    superseded_by: str | None
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RecallRequest:
    event: str
    scope_tags: tuple[str, ...]
    current_context_sufficient: bool
    explicit_recall: bool
    max_results: int


@dataclass(frozen=True)
class RecallAnchor:
    memory_id: str
    source_path: str
    lifecycle_state: str
    as_of: str
    event_triggers: tuple[str, ...]
    scope_tags: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    freshness: str


@dataclass(frozen=True)
class ExcludedRecord:
    memory_id: str
    reason: str


def _exact_fields(value: Any, expected: set[str], *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RecallValidationError(f"{field} must be an object")
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        raise RecallValidationError(f"{field} missing fields: {', '.join(missing)}")
    if extra:
        raise RecallValidationError(f"{field} unknown fields: {', '.join(extra)}")
    return value


def _required_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecallValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _string_tuple(value: Any, *, field: str, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise RecallValidationError(f"{field} must be a list of non-empty strings")
    normalized = tuple(dict.fromkeys(entry.strip() for entry in value))
    if not allow_empty and not normalized:
        raise RecallValidationError(f"{field} must not be empty")
    return normalized


def _validate_as_of(value: Any) -> str:
    text = _required_string(value, field="as_of")
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecallValidationError("as_of must be an ISO-8601 date-time") from exc
    return text


def _validate_blob_sha(value: Any) -> str:
    text = _required_string(value, field="source_git_blob_sha")
    if len(text) != 40 or any(char not in "0123456789abcdef" for char in text):
        raise RecallValidationError("source_git_blob_sha must be a lowercase 40-char Git SHA-1")
    return text


def _resolve_repo_path(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise RecallValidationError(f"absolute source path forbidden: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / rel).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise RecallValidationError(f"source path escapes repository root: {relative}")
    return resolved


def git_blob_sha_bytes(data: bytes) -> str:
    """Return the Git blob object SHA-1 for exact bytes.

    This is used only as a deterministic freshness/version identity. It is not a
    cryptographic security claim.
    """

    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def git_blob_sha_path(path: Path) -> str:
    return git_blob_sha_bytes(path.read_bytes())


def _parse_record(raw: Any, *, index: int) -> MemoryRecord:
    value = _exact_fields(raw, RECORD_FIELDS, field=f"records[{index}]")
    memory_id = _required_string(value["memory_id"], field=f"records[{index}].memory_id")
    source_path = _required_string(value["source_path"], field=f"records[{index}].source_path")
    lifecycle_state = _required_string(
        value["lifecycle_state"], field=f"records[{index}].lifecycle_state"
    )
    if lifecycle_state not in LIFECYCLE_STATES:
        raise RecallValidationError(
            f"records[{index}].lifecycle_state must be one of {sorted(LIFECYCLE_STATES)}"
        )
    triggers = _string_tuple(
        value["event_triggers"], field=f"records[{index}].event_triggers", allow_empty=False
    )
    scope_tags = _string_tuple(value["scope_tags"], field=f"records[{index}].scope_tags")
    evidence_refs = _string_tuple(
        value["evidence_refs"], field=f"records[{index}].evidence_refs", allow_empty=False
    )
    superseded_by = value["superseded_by"]
    if superseded_by is not None:
        superseded_by = _required_string(
            superseded_by, field=f"records[{index}].superseded_by"
        )
    if lifecycle_state == "SUPERSEDED" and superseded_by is None:
        raise RecallValidationError(
            f"records[{index}]: SUPERSEDED requires superseded_by"
        )
    return MemoryRecord(
        memory_id=memory_id,
        source_path=source_path,
        source_git_blob_sha=_validate_blob_sha(value["source_git_blob_sha"]),
        lifecycle_state=lifecycle_state,
        event_triggers=triggers,
        scope_tags=scope_tags,
        as_of=_validate_as_of(value["as_of"]),
        superseded_by=superseded_by,
        evidence_refs=evidence_refs,
    )


def load_registry(root: Path, registry_path: str | Path = "memory/recall_registry.json") -> list[MemoryRecord]:
    registry_rel = str(registry_path)
    path = _resolve_repo_path(root, registry_rel)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RecallValidationError(f"missing recall registry: {registry_rel}") from exc
    except json.JSONDecodeError as exc:
        raise RecallValidationError(f"invalid recall registry JSON: {exc}") from exc

    value = _exact_fields(raw, REGISTRY_FIELDS, field="registry")
    if value["schema_version"] != REGISTRY_SCHEMA_VERSION:
        raise RecallValidationError(
            f"registry.schema_version must equal {REGISTRY_SCHEMA_VERSION}"
        )
    if value["execution_authority"] != NO_AUTHORITY:
        raise RecallValidationError("registry.execution_authority must be NONE")
    if value["promotion_authority"] != NO_AUTHORITY:
        raise RecallValidationError("registry.promotion_authority must be NONE")
    if not isinstance(value["records"], list):
        raise RecallValidationError("registry.records must be a list")

    records = [_parse_record(record, index=i) for i, record in enumerate(value["records"])]
    ids = [record.memory_id for record in records]
    if len(ids) != len(set(ids)):
        raise RecallValidationError("registry contains duplicate memory_id values")

    # Structural path/source validation is strict. Freshness mismatch is handled
    # per record so one stale memory cannot hide otherwise valid current memories.
    for record in records:
        source = _resolve_repo_path(root, record.source_path)
        if not source.is_file():
            raise RecallValidationError(f"memory source is missing or not a file: {record.source_path}")
    return records


def record_freshness(root: Path, record: MemoryRecord) -> str:
    source = _resolve_repo_path(root, record.source_path)
    if not source.is_file():
        return "MISSING"
    return "CURRENT" if git_blob_sha_path(source) == record.source_git_blob_sha else "STALE"


def verify_registry(
    root: Path,
    registry_path: str | Path = "memory/recall_registry.json",
    *,
    require_current: bool = True,
) -> dict[str, Any]:
    records = load_registry(root, registry_path)
    statuses = [
        {
            "memory_id": record.memory_id,
            "source_path": record.source_path,
            "lifecycle_state": record.lifecycle_state,
            "freshness": record_freshness(root, record),
        }
        for record in records
    ]
    stale = [entry for entry in statuses if entry["freshness"] != "CURRENT"]
    if require_current and stale:
        details = ", ".join(f"{entry['memory_id']}={entry['freshness']}" for entry in stale)
        raise RecallValidationError(f"recall registry has non-current sources: {details}")
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "record_count": len(records),
        "all_sources_current": not stale,
        "records": statuses,
        "execution_authority": NO_AUTHORITY,
        "promotion_authority": NO_AUTHORITY,
    }


def parse_request(raw: Any) -> RecallRequest:
    value = _exact_fields(raw, REQUEST_FIELDS, field="recall request")
    event = value["event"]
    if not isinstance(event, str):
        raise RecallValidationError("recall request.event must be a string")
    event = event.strip()
    scope_tags = _string_tuple(value["scope_tags"], field="recall request.scope_tags")
    if not isinstance(value["current_context_sufficient"], bool):
        raise RecallValidationError("current_context_sufficient must be boolean")
    if not isinstance(value["explicit_recall"], bool):
        raise RecallValidationError("explicit_recall must be boolean")
    max_results = value["max_results"]
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 20:
        raise RecallValidationError("max_results must be an integer between 1 and 20")
    return RecallRequest(
        event=event,
        scope_tags=scope_tags,
        current_context_sufficient=value["current_context_sufficient"],
        explicit_recall=value["explicit_recall"],
        max_results=max_results,
    )


def _base_output(decision: str, reason: str, *, request: RecallRequest) -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "recall_decision": decision,
        "reason": reason,
        "request": {
            "event": request.event,
            "scope_tags": list(request.scope_tags),
            "current_context_sufficient": request.current_context_sufficient,
            "explicit_recall": request.explicit_recall,
            "max_results": request.max_results,
        },
        "selected_anchors": [],
        "excluded_count": 0,
        "exclusion_counts": {},
        "execution_authority": NO_AUTHORITY,
        "promotion_authority": NO_AUTHORITY,
    }


def route_recall(
    root: Path,
    request: RecallRequest | dict[str, Any],
    registry_path: str | Path = "memory/recall_registry.json",
) -> dict[str, Any]:
    """Select the smallest relevant current memory anchors.

    The fast paths intentionally run before registry loading, so a tiny task with
    sufficient current context does not pay a full-history/registry validation
    cost merely to decide that recall is unnecessary.
    """

    req = request if isinstance(request, RecallRequest) else parse_request(request)

    if req.current_context_sufficient and not req.explicit_recall:
        return _base_output("NO_RECALL", "CURRENT_CONTEXT_SUFFICIENT", request=req)
    if not req.event:
        return _base_output("NO_RECALL", "INSUFFICIENT_SIGNAL", request=req)

    records = load_registry(root, registry_path)
    exclusion_counts: dict[str, int] = {}
    candidates: list[tuple[int, MemoryRecord]] = []
    requested_scopes = set(req.scope_tags)

    def exclude(reason: str) -> None:
        exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1

    for record in records:
        # Cheap registry metadata gates run before source-body freshness I/O.
        # This keeps unrelated strata cold as the memory corpus grows.
        if record.lifecycle_state not in DEFAULT_RECALL_ELIGIBLE_STATES:
            exclude("LIFECYCLE_INELIGIBLE")
            continue
        if record.superseded_by is not None:
            exclude("SUPERSEDED")
            continue
        if req.event not in record.event_triggers:
            exclude("EVENT_MISMATCH")
            continue
        record_scopes = set(record.scope_tags)
        overlap = requested_scopes & record_scopes
        if requested_scopes and not overlap:
            exclude("SCOPE_MISMATCH")
            continue

        freshness = record_freshness(root, record)
        if freshness != "CURRENT":
            exclude(freshness)
            continue

        # Event match is mandatory. Scope overlap only refines ranking. Stable
        # memory_id ordering resolves ties deterministically.
        score = 100 + len(overlap)
        candidates.append((score, record))

    candidates.sort(key=lambda entry: (-entry[0], entry[1].memory_id))
    selected_records = [record for _, record in candidates[: req.max_results]]

    output = _base_output(
        "RECALL" if selected_records else "NO_RECALL",
        "MATCHED_RELEVANT_ANCHOR" if selected_records else "NO_ELIGIBLE_MATCH",
        request=req,
    )
    output["selected_anchors"] = [
        asdict(
            RecallAnchor(
                memory_id=record.memory_id,
                source_path=record.source_path,
                lifecycle_state=record.lifecycle_state,
                as_of=record.as_of,
                event_triggers=record.event_triggers,
                scope_tags=record.scope_tags,
                evidence_refs=record.evidence_refs,
                freshness="CURRENT",
            )
        )
        for record in selected_records
    ]
    output["excluded_count"] = sum(exclusion_counts.values())
    output["exclusion_counts"] = dict(sorted(exclusion_counts.items()))
    return output


def validate_transition(from_state: str, to_state: str) -> dict[str, Any]:
    source = _required_string(from_state, field="from_state")
    target = _required_string(to_state, field="to_state")
    if source not in LIFECYCLE_STATES:
        raise RecallValidationError(f"invalid from_state: {source}")
    if target not in LIFECYCLE_STATES:
        raise RecallValidationError(f"invalid to_state: {target}")
    if target not in ALLOWED_TRANSITIONS[source]:
        raise RecallValidationError(f"lifecycle transition not allowed: {source} -> {target}")
    return {
        "valid": True,
        "from_state": source,
        "to_state": target,
        "applied": False,
        "application_authority": NO_AUTHORITY,
        "execution_authority": NO_AUTHORITY,
        "promotion_authority": NO_AUTHORITY,
    }


def lifecycle_states() -> Iterable[str]:
    return sorted(LIFECYCLE_STATES)
