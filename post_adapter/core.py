from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Callable


class PostAdapterError(ValueError):
    """Raised when source material is unsafe or incomplete for adaptation."""


REQUIRED_FIELDS = (
    "project_name",
    "update_type",
    "summary",
    "facts",
    "source_refs",
    "audience",
    "call_to_action",
)

REVIEW_STATES = {"DRAFT", "REVIEW_REQUIRED", "APPROVED_FOR_COPY", "REJECTED"}

Renderer = Callable[[dict], str]
_ADAPTERS: dict[str, Renderer] = {}


def _nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PostAdapterError(f"{field} must be a non-empty string")
    return value.strip()


def _source_index(source_refs: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for raw in source_refs:
        if not isinstance(raw, dict):
            raise PostAdapterError("source_refs entries must be objects")
        source_id = _nonempty_text(raw.get("id"), "source_refs[].id")
        if source_id in index:
            raise PostAdapterError(f"duplicate source ref: {source_id}")
        index[source_id] = deepcopy(raw)
    return index


def normalize_source(source: dict) -> dict:
    """Validate and normalize one development/update source record.

    Verified public claims are accepted only when they bind to a declared source
    reference. Everything else is retained as a warning and excluded from the
    publish-ready fact list.
    """
    if not isinstance(source, dict):
        raise PostAdapterError("source must be an object")

    missing = [field for field in REQUIRED_FIELDS if field not in source]
    if missing:
        raise PostAdapterError(f"missing required fields: {', '.join(missing)}")

    normalized = deepcopy(source)
    for field in ("project_name", "update_type", "summary", "audience", "call_to_action"):
        normalized[field] = _nonempty_text(normalized[field], field)

    facts = normalized["facts"]
    refs = normalized["source_refs"]
    if not isinstance(facts, list) or not facts:
        raise PostAdapterError("facts must be a non-empty list")
    if not isinstance(refs, list) or not refs:
        raise PostAdapterError("source_refs must be a non-empty list")

    source_index = _source_index(refs)
    verified_facts: list[dict] = []
    warnings: list[str] = []

    for position, raw_fact in enumerate(facts, start=1):
        if not isinstance(raw_fact, dict):
            raise PostAdapterError("facts entries must be objects")
        claim = _nonempty_text(raw_fact.get("claim"), "facts[].claim")
        status = _nonempty_text(raw_fact.get("status", "UNVERIFIED"), "facts[].status").upper()
        source_ref = raw_fact.get("source_ref")

        if status == "VERIFIED" and isinstance(source_ref, str) and source_ref in source_index:
            verified_facts.append(
                {
                    "claim": claim,
                    "source_ref": source_ref,
                    "status": "VERIFIED",
                }
            )
        else:
            reason = "unverified claim"
            if status == "VERIFIED" and source_ref not in source_index:
                reason = "verified claim has no declared source binding"
            warnings.append(f"fact {position}: {reason}: {claim}")

    if not verified_facts:
        raise PostAdapterError("no publishable facts remain after evidence binding")

    normalized["verified_facts"] = verified_facts
    normalized["warnings"] = warnings
    normalized["review_state"] = "REVIEW_REQUIRED" if warnings else "DRAFT"
    return normalized


def _fact_lines(source: dict, prefix: str = "- ") -> str:
    return "\n".join(f"{prefix}{fact['claim']}" for fact in source["verified_facts"])


def _evidence_lines(source: dict) -> str:
    return "\n".join(
        f"- {fact['source_ref']}: {fact['claim']}" for fact in source["verified_facts"]
    )


def _warning_block(source: dict) -> str:
    if not source["warnings"]:
        return ""
    return "\n\nHuman review warnings:\n" + "\n".join(
        f"- {warning}" for warning in source["warnings"]
    )


def render_x(source: dict) -> str:
    body = [
        f"{source['project_name']}: {source['summary']}",
        "",
        _fact_lines(source, "• "),
        "",
        source["call_to_action"],
    ]
    return "\n".join(body).strip() + _warning_block(source) + "\n"


def render_note(source: dict) -> str:
    title = f"{source['project_name']} — {source['update_type']} update"
    parts = [
        f"# {title}",
        "",
        f"対象: {source['audience']}",
        "",
        source["summary"],
        "",
        "## 今回確認できたこと",
        "",
        _fact_lines(source),
        "",
        "## 根拠",
        "",
        _evidence_lines(source),
    ]
    limits = source.get("known_limits") or []
    if limits:
        parts.extend(["", "## 現時点の制約", "", *[f"- {item}" for item in limits]])
    parts.extend(["", "## 次のアクション", "", source["call_to_action"]])
    return "\n".join(parts).strip() + _warning_block(source) + "\n"


def render_github(source: dict) -> str:
    parts = [
        f"## {source['project_name']} — {source['update_type']}",
        "",
        f"**Summary:** {source['summary']}",
        "",
        "### Verified changes",
        "",
        _fact_lines(source),
        "",
        "### Evidence",
        "",
        _evidence_lines(source),
        "",
        f"**Next:** {source['call_to_action']}",
    ]
    return "\n".join(parts).strip() + _warning_block(source) + "\n"


def render_instagram(source: dict) -> str:
    hook = f"{source['project_name']}、今回ここが進みました。"
    parts = [
        hook,
        "",
        source["summary"],
        "",
        _fact_lines(source, "✓ "),
        "",
        source["call_to_action"],
    ]
    media_refs = source.get("media_refs") or []
    if media_refs:
        parts.extend(
            [
                "",
                "Carousel / Reel outline:",
                *[f"- Scene {index}: {item}" for index, item in enumerate(media_refs, start=1)],
                "",
                "Alt-text draft: 開発更新の内容と確認済み結果を示す画像・画面。公開前に実画像に合わせて修正する。",
            ]
        )
    return "\n".join(parts).strip() + _warning_block(source) + "\n"


def register_adapter(name: str, renderer: Renderer) -> None:
    clean_name = _nonempty_text(name, "adapter name").lower()
    if not callable(renderer):
        raise PostAdapterError("renderer must be callable")
    _ADAPTERS[clean_name] = renderer


def _default_adapters() -> None:
    if _ADAPTERS:
        return
    register_adapter("x", render_x)
    register_adapter("note", render_note)
    register_adapter("github", render_github)
    register_adapter("instagram", render_instagram)


def build_bundle(
    source: dict,
    *,
    generated_at: str | None = None,
    review_state: str | None = None,
) -> dict:
    """Build an in-memory v0 post bundle without publishing anywhere."""
    _default_adapters()
    normalized = normalize_source(source)

    if review_state is None:
        review_state = normalized["review_state"]
    review_state = _nonempty_text(review_state, "review_state").upper()
    if review_state not in REVIEW_STATES:
        raise PostAdapterError(f"invalid review_state: {review_state}")
    if review_state == "APPROVED_FOR_COPY" and normalized["warnings"]:
        raise PostAdapterError("cannot approve bundle while evidence warnings remain")

    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    fingerprint_input = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    bundle_id = "PA-" + hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()[:16].upper()

    outputs = {name: renderer(normalized) for name, renderer in _ADAPTERS.items()}
    manifest = {
        "schema_version": "0.1",
        "bundle_id": bundle_id,
        "project_name": normalized["project_name"],
        "generated_at": generated_at,
        "channels": list(outputs),
        "source_refs": [item["id"] for item in normalized["source_refs"]],
        "verification_warnings": normalized["warnings"],
        "human_review_state": review_state,
        "external_publication_performed": False,
    }
    source_summary = (
        f"# {normalized['project_name']} source summary\n\n"
        f"{normalized['summary']}\n\n"
        "## Verified facts\n\n"
        f"{_fact_lines(normalized)}\n\n"
        "## Evidence bindings\n\n"
        f"{_evidence_lines(normalized)}\n"
    )
    return {
        "manifest": manifest,
        "source_summary": source_summary,
        "outputs": outputs,
        "normalized_source": normalized,
    }
