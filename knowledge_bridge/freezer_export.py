from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .challenge import challenge_record
from .route import route_record


@dataclass(frozen=True)
class FreezerExportResult:
    knowledge_id: str
    draft_path: str
    review_path: str
    item_id: str
    build_authority: str
    schema_compatible: bool


_REQUIRED_METADATA = (
    "original_problem",
    "why_it_matters",
    "trigger_conditions",
    "negative_triggers",
    "dependencies",
    "estimated_hours",
    "human_review",
)


def _load_record(root: Path, knowledge_id: str) -> dict[str, Any]:
    path = root / "normalized" / f"{knowledge_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"knowledge record not found: {knowledge_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _freezer_type(record: dict[str, Any]) -> str:
    metadata = record.get("frontmatter", {})
    explicit = str(metadata.get("freezer_type", "")).lower()
    allowed = {"feature", "research", "product", "architecture", "process", "risk"}
    if explicit in allowed:
        return explicit
    mapping = {
        "spec": "architecture",
        "decision": "process",
        "test": "process",
        "pattern": "research",
        "problem": "risk",
        "project_context": "product",
        "idea": "feature",
    }
    return mapping.get(str(record.get("knowledge_type", "idea")), "feature")


def _item_id(knowledge_id: str) -> str:
    number = int(hashlib.sha256(knowledge_id.encode("utf-8")).hexdigest()[:10], 16) % 1_000_000
    return f"RTS-FRZ-{number:06d}"


def _hours(value: Any) -> dict[str, float]:
    if isinstance(value, dict):
        minimum = float(value.get("minimum", value.get("min", 0)))
        maximum = float(value.get("maximum", value.get("max", minimum)))
    elif isinstance(value, (int, float)):
        minimum = maximum = float(value)
    elif isinstance(value, list) and len(value) == 2:
        minimum, maximum = float(value[0]), float(value[1])
    else:
        raise ValueError("estimated_hours must be a number, [minimum, maximum], or object")
    if minimum < 0 or maximum < minimum:
        raise ValueError("estimated_hours must satisfy 0 <= minimum <= maximum")
    return {"minimum": minimum, "maximum": maximum}


def _priority(record: dict[str, Any]) -> dict[str, float]:
    metadata = record.get("frontmatter", {})
    supplied = metadata.get("priority", {}) if isinstance(metadata.get("priority"), dict) else {}
    confidence = max(0.0, min(5.0, float(record.get("confidence", 0)) * 5.0))
    defaults = {
        "impact": 2.5,
        "urgency": 2.0,
        "strategic_fit": 3.0,
        "readiness": 3.0,
        "revenue_value": 0.0,
        "dependency_value": 2.0,
        "risk_reduction": 2.0,
        "confidence": confidence,
        "effort": 2.5,
        "uncertainty": max(0.0, 5.0 - confidence),
    }
    for key in defaults:
        if key in supplied:
            defaults[key] = max(0.0, min(5.0, float(supplied[key])))
    return defaults


def _validate_contract(item: dict[str, Any]) -> None:
    required = {
        "item_id", "version", "title", "type", "status", "summary",
        "original_problem", "why_it_matters", "reason_frozen", "preserved_value",
        "priority", "trigger_conditions", "negative_triggers", "dependencies",
        "source_refs", "possible_destinations", "estimated_hours", "tags",
        "build_authority", "recall_mode", "created_at", "updated_at",
    }
    missing = sorted(required - set(item))
    if missing:
        raise ValueError("FREEZER schema fields missing: " + ", ".join(missing))
    if item["build_authority"] != "NOT_APPROVED":
        raise ValueError("bridge exports must force build_authority=NOT_APPROVED")
    if item["status"] not in {"CAPTURED", "NORMALIZED", "SCORED", "READY"}:
        raise ValueError("bridge may only export a non-selected FREEZER draft status")
    if not str(item["item_id"]).startswith("RTS-FRZ-") or len(item["item_id"]) != 14:
        raise ValueError("invalid FREEZER item_id")
    if not item["original_problem"] or not item["why_it_matters"]:
        raise ValueError("original_problem and why_it_matters are required")
    if not isinstance(item["trigger_conditions"], list) or not isinstance(item["negative_triggers"], list):
        raise ValueError("trigger fields must be arrays")


def export_freezer_draft(
    state_root: str | Path,
    knowledge_id: str,
    output_path: str | Path,
) -> FreezerExportResult:
    root = Path(state_root)
    record = _load_record(root, knowledge_id)
    metadata = record.get("frontmatter", {})

    route = route_record(root, knowledge_id)
    if route.destination != "freezer":
        raise PermissionError(f"record is routed to {route.destination}, not freezer")
    challenge = challenge_record(root, knowledge_id)
    if not challenge.promotion_ready:
        raise PermissionError("record has not passed the Devil's Advocate gate")
    if record.get("sensitivity") in {"personal", "restricted"}:
        raise PermissionError("sensitive records cannot be exported to FREEZER")

    missing = [key for key in _REQUIRED_METADATA if not metadata.get(key)]
    if missing:
        raise ValueError("FREEZER export metadata missing: " + ", ".join(missing))
    if str(metadata.get("human_review", "")).lower() not in {"required", "confirmed", "true"} and metadata.get("human_review") is not True:
        raise ValueError("human_review must be explicitly required or confirmed")

    now = datetime.now(timezone.utc).isoformat()
    item_id = _item_id(knowledge_id)
    item = {
        "item_id": item_id,
        "version": 1,
        "title": str(record.get("title") or knowledge_id),
        "type": _freezer_type(record),
        "status": "CAPTURED",
        "summary": str(metadata.get("summary") or record.get("source_excerpt") or record.get("body", "")).strip(),
        "original_problem": str(metadata["original_problem"]).strip(),
        "why_it_matters": str(metadata["why_it_matters"]).strip(),
        "reason_frozen": "",
        "preserved_value": _as_list(metadata.get("preserved_value") or metadata.get("acceptance_criteria")),
        "priority": _priority(record),
        "trigger_conditions": _as_list(metadata["trigger_conditions"]),
        "negative_triggers": _as_list(metadata["negative_triggers"]),
        "dependencies": _as_list(metadata["dependencies"]),
        "source_refs": [
            f"knowledge:{knowledge_id}",
            f"capture:{record.get('capture_id')}",
            f"source:{record.get('source_path')}",
            f"sha256:{record.get('source_hash')}",
            f"challenge:{knowledge_id}:promotion_ready=true",
        ],
        "possible_destinations": _as_list(metadata.get("possible_destinations") or [record.get("project_id") or "RTS"]),
        "estimated_hours": _hours(metadata["estimated_hours"]),
        "tags": sorted(set(_as_list(record.get("tags")) + ["knowledge-bridge", "human-review-required"])),
        "build_authority": "NOT_APPROVED",
        "recall_mode": str(metadata.get("recall_mode", "MANUAL")).upper(),
        "supersedes": metadata.get("supersedes"),
        "created_at": now,
        "updated_at": now,
    }
    _validate_contract(item)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing FREEZER draft: {output}")
    output.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review = {
        "knowledge_id": knowledge_id,
        "item_id": item_id,
        "automatic_freezer_add_invoked": False,
        "automatic_approval_possible": False,
        "human_review": metadata["human_review"],
        "route": asdict(route),
        "challenge": asdict(challenge),
        "source_hash": record.get("source_hash"),
        "draft_path": str(output),
    }
    review_path = output.with_suffix(output.suffix + ".review.json")
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return FreezerExportResult(
        knowledge_id=knowledge_id,
        draft_path=str(output),
        review_path=str(review_path),
        item_id=item_id,
        build_authority="NOT_APPROVED",
        schema_compatible=True,
    )
