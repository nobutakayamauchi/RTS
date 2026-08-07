from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_ALLOWED_TIMING = {"NOW", "DEFER", "CLARIFY"}
_ALLOWED_ACTIONS = {"ROUTE_TO_V1", "FREEZE_FOR_LATER", "ASK_HUMAN"}


@dataclass(frozen=True)
class RoutingResult:
    report_path: str
    markdown_path: str
    v1_input_path: str
    idea_id: str
    classification: str
    target_project: str
    target_component: str
    timing: str
    routing_action: str
    confidence: float
    status: str
    human_decision_required: bool
    implementation_executed: bool


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _feature_objects(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else [value]
    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            feature = str(item.get("feature", "")).strip()
            if not feature:
                continue
            record: dict[str, Any] = {"feature": feature}
            decision = item.get("decision")
            if decision in {"KEEP", "SIMPLIFY", "DEFER", "REMOVE", "CLARIFY"}:
                record["decision"] = decision
            reason = str(item.get("reason", "")).strip()
            if reason:
                record["reason"] = reason
            normalized.append(record)
            continue
        feature = str(item).strip()
        if feature:
            normalized.append({"feature": feature, "decision": "KEEP", "reason": "Supplied by V1.1 raw idea context."})
    return normalized


def _reference_objects(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else [value]
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            reference_id = str(item.get("reference_id", "")).strip()
            if not reference_id:
                continue
            record = dict(item)
            record["reference_id"] = reference_id
            normalized.append(record)
            continue
        reference_id = str(item).strip()
        if reference_id:
            normalized.append({"reference_id": reference_id, "reaction": "neutral", "notes": ["Supplied by V1.1 raw idea context."]})
    return normalized


def _stable_idea_id(idea: str, supplied: Any = None) -> str:
    if supplied:
        return str(supplied)
    return "IDEA-" + uuid.uuid5(uuid.NAMESPACE_URL, idea).hex[:12]


def _classify(text: str) -> str:
    value = text.lower()
    if any(term in value for term in ("broken", "bug", "error", "fail", "固ま", "動か", "壊", "不具合", "エラー")):
        return "BUG"
    if any(term in value for term in ("ui", "ux", "design", "layout", "button", "画面", "導線", "デザイン", "ボタン")):
        return "DESIGN"
    if any(term in value for term in ("reference", "screenshot", "スクショ", "参考", "これっぽい")):
        return "REFERENCE"
    if any(term in value for term in ("knowledge", "freezer", "知識", "メモ", "学び")):
        return "KNOWLEDGE"
    if any(term in value for term in ("feature", "add", "want", "欲しい", "追加", "作りたい", "実装")):
        return "FEATURE"
    return "UNKNOWN"


def _project(payload: dict[str, Any], idea: str) -> tuple[str, float]:
    explicit = str(payload.get("project_hint") or payload.get("project_id") or "").strip()
    if explicit:
        return explicit, 0.95
    known = _strings(payload.get("known_projects"))
    lowered = idea.lower()
    for candidate in known:
        if candidate.lower() in lowered:
            return candidate, 0.85
    keyword_map = (
        (("vlog", "video", "動画", "書き出", "保存", "export"), "vlog"),
        (("obsidian", "オブシディアン"), "obsidian"),
        (("rts", "knowledge bridge", "freezer"), "RTS"),
        (("mail", "newsletter", "メルマガ"), "newsletter"),
    )
    for terms, project in keyword_map:
        if any(term in lowered for term in terms):
            return project, 0.75
    return "UNRESOLVED", 0.25


def _component(payload: dict[str, Any], idea: str) -> tuple[str, float]:
    explicit = str(payload.get("component_hint") or "").strip()
    if explicit:
        return explicit, 0.95
    known = _strings(payload.get("known_components"))
    lowered = idea.lower()
    for candidate in known:
        if candidate.lower() in lowered:
            return candidate, 0.85
    maps = (
        (("save", "export", "保存", "書き出"), "save-export"),
        (("upload", "youtube", "アップロード"), "upload"),
        (("ui", "画面", "導線", "button", "ボタン"), "ui"),
        (("debug", "broken", "不具合", "デバッグ"), "debug"),
    )
    for terms, component in maps:
        if any(term in lowered for term in terms):
            return component, 0.75
    return "UNRESOLVED", 0.25


def _timing(payload: dict[str, Any], classification: str, project: str, component: str) -> tuple[str, list[str], list[str]]:
    missing: list[str] = []
    questions: list[str] = []
    if project == "UNRESOLVED":
        missing.append("target_project")
        questions.append("Which existing project should own this idea?")
    if component == "UNRESOLVED":
        missing.append("target_component")
        questions.append("Which component or boundary should this attach to?")
    constraints = _strings(payload.get("constraints"))
    blocker_terms = ("after", "later", "defer", "保留", "後で", "完了後", "安定後")
    idea = str(payload.get("idea", "")).lower()
    if any(term in idea for term in blocker_terms):
        return "DEFER", missing, questions
    if missing or classification == "UNKNOWN":
        if classification == "UNKNOWN":
            missing.append("idea_classification")
            questions.append("Is this primarily a feature, bug, design change, knowledge item, or reference?")
        return "CLARIFY", list(dict.fromkeys(missing)), list(dict.fromkeys(questions))
    if not constraints:
        missing.append("constraints_review")
    return "NOW", missing, questions


def _v1_payload(payload: dict[str, Any], idea_id: str, project: str, component: str, classification: str, questions: list[str]) -> dict[str, Any]:
    title = str(payload.get("title") or f"Routed idea {idea_id}")
    return {
        "schema_version": "1.0",
        "title": title,
        "project_id": None if project == "UNRESOLVED" else project,
        "domain": str(payload.get("domain") or component or "unknown"),
        "role": str(payload.get("role") or "requester"),
        "target_user": str(payload.get("target_user") or "unknown"),
        "feedback": [str(payload["idea"])],
        "goals": _strings(payload.get("goals")),
        "constraints": _strings(payload.get("constraints")),
        "unresolved_questions": questions,
        "references": _reference_objects(payload.get("references")),
        "features": _feature_objects(payload.get("features")),
        "sensory_profile": payload.get("sensory_profile", {}),
        "source": {"type": "idea-router-v1.1", "idea_id": idea_id, "classification": classification},
    }


def route_idea(input_path: str | Path, output_path: str | Path) -> RoutingResult:
    source = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    markdown = output.with_suffix(".md")
    v1_input = output.with_name(output.stem + ".v1-input.json")
    if output.exists() or markdown.exists() or v1_input.exists():
        raise FileExistsError(f"refusing to overwrite routing output: {output}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("idea input must be a JSON object")
    idea = str(payload.get("idea", "")).strip()
    if not idea:
        raise ValueError("idea is required")

    idea_id = _stable_idea_id(idea, payload.get("idea_id"))
    classification = _classify(idea)
    project, project_conf = _project(payload, idea)
    component, component_conf = _component(payload, idea)
    timing, missing, questions = _timing(payload, classification, project, component)
    context_matches = _strings(payload.get("freezer_matches")) + _strings(payload.get("context_matches"))
    if timing == "NOW":
        action = "ROUTE_TO_V1"
    elif timing == "DEFER":
        action = "FREEZE_FOR_LATER"
    else:
        action = "ASK_HUMAN"
    confidence = round(min(project_conf, component_conf, 0.9 if classification != "UNKNOWN" else 0.35), 2)
    v1_payload = _v1_payload(payload, idea_id, project, component, classification, questions)
    report = {
        "schema_version": "1.1",
        "idea_id": idea_id,
        "raw_idea": idea,
        "classification": classification,
        "target_project": project,
        "target_component": component,
        "timing": timing,
        "missing_parts": missing,
        "context_matches": list(dict.fromkeys(context_matches)),
        "routing_action": action,
        "human_questions": questions,
        "confidence": confidence,
        "v1_input": v1_payload,
        "status": "AWAITING_HUMAN_ROUTING_DECISION",
        "human_decision_required": True,
        "implementation_executed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    v1_input.write_text(json.dumps(v1_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(_markdown(report), encoding="utf-8")
    return RoutingResult(
        report_path=str(output), markdown_path=str(markdown), v1_input_path=str(v1_input),
        idea_id=idea_id, classification=classification, target_project=project, target_component=component,
        timing=timing, routing_action=action, confidence=confidence,
        status="AWAITING_HUMAN_ROUTING_DECISION", human_decision_required=True, implementation_executed=False,
    )


def _markdown(report: dict[str, Any]) -> str:
    missing = "\n".join(f"- {item}" for item in report["missing_parts"]) or "- None"
    matches = "\n".join(f"- {item}" for item in report["context_matches"]) or "- None"
    questions = "\n".join(f"- {item}" for item in report["human_questions"]) or "- None"
    return f"""# RTS V1.1 Idea Routing Proposal

- Idea: `{report['idea_id']}`
- Classification: `{report['classification']}`
- Target project: `{report['target_project']}`
- Target component: `{report['target_component']}`
- Timing: `{report['timing']}`
- Action: `{report['routing_action']}`
- Confidence: `{report['confidence']}`
- Status: `{report['status']}`

## Raw idea

{report['raw_idea']}

## Missing parts

{missing}

## Existing context / FREEZER matches

{matches}

## Questions for human routing decision

{questions}

A V1.0-ready payload was generated, but no routing, storage, approval, code modification, repair, or implementation was executed.
"""
