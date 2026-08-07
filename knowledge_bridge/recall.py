from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EVENTS = {
    "SPEC_DRAFTED",
    "DEVILS_ADVOCATE",
    "ASSET_SEARCH",
    "FREEZER_INTAKE",
    "PREFLIGHT",
    "UI_BOOTSTRAP",
    "BUG_REPORTED",
    "RELEASE_GATE",
    "RESUME_WORK",
}

_EVENT_TYPES = {
    "SPEC_DRAFTED": {"decision", "spec", "problem", "pattern"},
    "DEVILS_ADVOCATE": {"decision", "spec", "problem", "evidence"},
    "ASSET_SEARCH": {"pattern", "decision", "spec", "test"},
    "FREEZER_INTAKE": {"decision", "spec", "problem"},
    "PREFLIGHT": {"decision", "spec", "test", "evidence"},
    "UI_BOOTSTRAP": {"decision", "spec", "test", "problem", "pattern"},
    "BUG_REPORTED": {"problem", "test", "evidence", "decision"},
    "RELEASE_GATE": {"test", "evidence", "decision", "spec"},
    "RESUME_WORK": {"project_context", "decision", "problem", "spec"},
}


@dataclass(frozen=True)
class RecallItem:
    knowledge_id: str
    title: str
    score: float
    reasons: tuple[str, ...]
    source_path: str


def recall_event(state_root: str | Path, event: str, project_id: str | None = None, threshold: float = 0.45) -> tuple[RecallItem, ...]:
    event = event.upper()
    if event not in SUPPORTED_EVENTS:
        raise ValueError(f"unsupported recall event: {event}")
    root = Path(state_root)
    folder = root / "normalized"
    if not folder.exists():
        return ()

    allowed = _EVENT_TYPES[event]
    items: list[RecallItem] = []
    for path in sorted(folder.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("sensitivity") in {"personal", "restricted"}:
            continue
        score = 0.0
        reasons: list[str] = []
        kind = record.get("knowledge_type")
        if kind in allowed:
            score += 0.45
            reasons.append(f"event_type_match:{kind}")
        if project_id and record.get("project_id") == project_id:
            score += 0.35
            reasons.append("same_project")
        status = record.get("status")
        if status in {"challenged", "approved", "frozen"}:
            score += 0.1
            reasons.append(f"governed_status:{status}")
        if float(record.get("confidence", 0.0)) >= 0.7:
            score += 0.1
            reasons.append("high_confidence")
        if score < threshold:
            continue
        items.append(RecallItem(
            knowledge_id=record["knowledge_id"],
            title=record.get("title", ""),
            score=round(min(score, 1.0), 3),
            reasons=tuple(reasons),
            source_path=record.get("source_path", ""),
        ))
    items.sort(key=lambda item: (-item.score, item.knowledge_id))
    return tuple(items)
