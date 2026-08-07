from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contract import (
    CONTRACT_SCHEMA_VERSION,
    raise_for_contract,
    validate_input_contract,
    validate_output_contract,
)


_ALLOWED_REACTIONS = {"like", "dislike", "neutral", "confusing"}
_ALLOWED_DECISIONS = {"KEEP", "SIMPLIFY", "DEFER", "REMOVE", "CLARIFY"}


@dataclass(frozen=True)
class ReferenceDecision:
    reference_id: str
    reaction: str
    adopted: tuple[str, ...]
    rejected: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class FeatureDecision:
    feature: str
    decision: str
    reason: str


@dataclass(frozen=True)
class PlannedNode:
    id: str
    type: str
    label: str
    status: str


@dataclass(frozen=True)
class PlannedEdge:
    from_id: str
    to_id: str
    type: str
    reason: str


@dataclass(frozen=True)
class PlannedStructure:
    nodes: tuple[PlannedNode, ...]
    edges: tuple[PlannedEdge, ...]


@dataclass(frozen=True)
class TranslationBrief:
    schema_version: str
    request_id: str
    project_id: str
    title: str
    domain: str
    role: str
    target_user: str
    inferred_goals: tuple[str, ...]
    design_constraints: tuple[str, ...]
    feature_decisions: tuple[FeatureDecision, ...]
    sensory_profile: dict[str, float]
    reference_ledger: tuple[ReferenceDecision, ...]
    unresolved_questions: tuple[str, ...]
    missing_parts: tuple[str, ...]
    planned_structure: PlannedStructure
    human_decision_required: bool
    status: str


def _as_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _stable_id(prefix: str, supplied: Any, seed: str) -> str:
    value = str(supplied or "").strip()
    if value:
        return value
    digest = uuid.uuid5(uuid.NAMESPACE_URL, seed).hex[:12]
    return f"{prefix}-{digest}"


def _bounded_profile(value: Any) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("sensory_profile must be an object")
    result: dict[str, float] = {}
    for key, raw in value.items():
        number = float(raw)
        result[str(key)] = max(-1.0, min(1.0, number))
    return dict(sorted(result.items()))


def _feedback_constraints(feedback: list[str]) -> tuple[list[str], list[str]]:
    constraints: list[str] = []
    goals: list[str] = []
    joined = "\n".join(feedback).lower()

    if any(term in joined for term in ("complex", "complicated", "複雑", "ごちゃ", "多すぎ")):
        goals.append("Reduce cognitive load without hiding the primary action.")
        constraints.extend(
            (
                "Limit simultaneously visible choices.",
                "Keep advanced options outside the primary path.",
                "Prefer a shallow navigation path for frequent actions.",
            )
        )
    if any(term in joined for term in ("one tap", "one-tap", "1 tap", "一発", "ワンタップ", "すぐアクセス")):
        goals.append("Reach a frequent or urgent action with minimal navigation.")
        constraints.extend(
            (
                "Identify the exact high-frequency target before assigning permanent navigation space.",
                "Compare fixed navigation, shortcut, recent-item, and contextual-action options.",
            )
        )
    if any(term in joined for term in ("unclear", "意味がわから", "分からん", "わからないボタン", "confusing button")):
        goals.append("Make controls understandable before interaction.")
        constraints.extend(
            (
                "Do not rely on an ambiguous icon without a discoverable label.",
                "Every primary control must expose its destination or effect.",
            )
        )
    return goals, constraints


def _feature_decisions(features: list[dict[str, Any]]) -> tuple[FeatureDecision, ...]:
    results: list[FeatureDecision] = []
    for item in features:
        feature = str(item.get("feature", "")).strip()
        if not feature:
            raise ValueError("feature decision requires feature")
        decision = str(item.get("decision", "CLARIFY")).upper()
        if decision not in _ALLOWED_DECISIONS:
            raise ValueError(f"unsupported feature decision: {decision}")
        reason = str(item.get("reason", "Human discussion required.")).strip()
        results.append(FeatureDecision(feature, decision, reason))
    return tuple(results)


def _reference_ledger(references: list[dict[str, Any]]) -> tuple[ReferenceDecision, ...]:
    results: list[ReferenceDecision] = []
    for item in references:
        reference_id = str(item.get("reference_id", "")).strip()
        if not reference_id:
            raise ValueError("reference requires reference_id")
        reaction = str(item.get("reaction", "neutral")).lower()
        if reaction not in _ALLOWED_REACTIONS:
            raise ValueError(f"unsupported reference reaction: {reaction}")
        results.append(
            ReferenceDecision(
                reference_id=reference_id,
                reaction=reaction,
                adopted=tuple(_as_strings(item.get("adopted"))),
                rejected=tuple(_as_strings(item.get("rejected"))),
                notes=tuple(_as_strings(item.get("notes"))),
            )
        )
    return tuple(results)


def _missing_parts(
    goals: list[str],
    features: tuple[FeatureDecision, ...],
    references: tuple[ReferenceDecision, ...],
    unresolved: list[str],
) -> tuple[str, ...]:
    missing: list[str] = []
    if not goals:
        missing.append("primary_outcome")
    if not features:
        missing.append("feature_scope")
    if references and not any(item.adopted or item.rejected for item in references):
        missing.append("reference_breakdown")
    if unresolved:
        missing.append("human_decisions")
    return tuple(dict.fromkeys(missing))


def _planned_structure(
    request_id: str,
    goals: list[str],
    features: tuple[FeatureDecision, ...],
    references: tuple[ReferenceDecision, ...],
    missing_parts: tuple[str, ...],
) -> PlannedStructure:
    nodes: list[PlannedNode] = [PlannedNode(request_id, "request", "Translated request", "planned")]
    edges: list[PlannedEdge] = []

    for index, goal in enumerate(goals, start=1):
        node_id = f"{request_id}:goal:{index}"
        nodes.append(PlannedNode(node_id, "goal", goal, "planned"))
        edges.append(PlannedEdge(request_id, node_id, "clarifies", "Goal inferred from user input."))

    for index, feature in enumerate(features, start=1):
        node_id = f"{request_id}:feature:{index}"
        status = "planned" if feature.decision in {"KEEP", "SIMPLIFY"} else "deferred"
        nodes.append(PlannedNode(node_id, "feature", feature.feature, status))
        edges.append(PlannedEdge(request_id, node_id, "implements", feature.reason))

    for index, reference in enumerate(references, start=1):
        node_id = f"{request_id}:reference:{index}"
        nodes.append(PlannedNode(node_id, "reference", reference.reference_id, "evidence"))
        edges.append(PlannedEdge(request_id, node_id, "references", f"Reaction: {reference.reaction}"))

    for index, part in enumerate(missing_parts, start=1):
        node_id = f"{request_id}:missing:{index}"
        nodes.append(PlannedNode(node_id, "missing_part", part, "blocking"))
        edges.append(PlannedEdge(node_id, request_id, "blocks", "Required before final approval."))

    approval_id = f"{request_id}:approval"
    nodes.append(PlannedNode(approval_id, "approval", "Human approval", "waiting"))
    edges.append(PlannedEdge(request_id, approval_id, "requires_approval", "No implementation may begin automatically."))
    return PlannedStructure(tuple(nodes), tuple(edges))


def _wire_payload(brief: TranslationBrief) -> dict[str, Any]:
    payload = asdict(brief)
    payload["planned_structure"]["edges"] = [
        {"from": item["from_id"], "to": item["to_id"], "type": item["type"], "reason": item["reason"]}
        for item in payload["planned_structure"]["edges"]
    ]
    return payload


def translate_intent(input_path: str | Path, output_path: str | Path) -> TranslationBrief:
    source = Path(input_path)
    output = Path(output_path)
    markdown = output.with_suffix(".md")
    if output.exists() or markdown.exists():
        raise FileExistsError(f"refusing to overwrite translation brief: {output}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("translation input must be a JSON object")
    raise_for_contract(validate_input_contract(payload))

    title = str(payload.get("title", "Untitled design translation")).strip()
    project_id = _stable_id("PRJ", payload.get("project_id"), title + ":project")
    request_id = _stable_id("REQ", payload.get("request_id"), project_id + ":" + title)

    feedback = _as_strings(payload.get("feedback"))
    inferred_goals, constraints = _feedback_constraints(feedback)
    inferred_goals.extend(_as_strings(payload.get("goals")))
    constraints.extend(_as_strings(payload.get("constraints")))

    references = _reference_ledger(list(payload.get("references", [])))
    if references and not any(item.adopted or item.rejected or item.notes for item in references):
        constraints.append("Reference reactions need concrete adopted or rejected elements before implementation.")

    unresolved = _as_strings(payload.get("unresolved_questions"))
    if not inferred_goals:
        unresolved.append("What outcome should the design optimize first?")
    if any(item.reaction == "confusing" and not item.notes for item in references):
        unresolved.append("Which part of each confusing reference causes the confusion?")

    feature_decisions = _feature_decisions(list(payload.get("features", [])))
    unique_goals = list(dict.fromkeys(inferred_goals))
    unique_constraints = list(dict.fromkeys(constraints))
    unique_unresolved = list(dict.fromkeys(unresolved))
    missing_parts = _missing_parts(unique_goals, feature_decisions, references, unique_unresolved)
    planned = _planned_structure(request_id, unique_goals, feature_decisions, references, missing_parts)

    brief = TranslationBrief(
        schema_version=CONTRACT_SCHEMA_VERSION,
        request_id=request_id,
        project_id=project_id,
        title=title,
        domain=str(payload.get("domain", "unknown")).strip(),
        role=str(payload.get("role", "unknown")).strip(),
        target_user=str(payload.get("target_user", "unknown")).strip(),
        inferred_goals=tuple(unique_goals),
        design_constraints=tuple(unique_constraints),
        feature_decisions=feature_decisions,
        sensory_profile=_bounded_profile(payload.get("sensory_profile")),
        reference_ledger=references,
        unresolved_questions=tuple(unique_unresolved),
        missing_parts=missing_parts,
        planned_structure=planned,
        human_decision_required=True,
        status="AWAITING_HUMAN_DECISION",
    )

    wire = _wire_payload(brief)
    raise_for_contract(validate_output_contract(wire))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(wire, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(_markdown(brief), encoding="utf-8")
    return brief


def _markdown(brief: TranslationBrief) -> str:
    goals = "\n".join(f"- {item}" for item in brief.inferred_goals) or "- None yet"
    constraints = "\n".join(f"- {item}" for item in brief.design_constraints) or "- None yet"
    features = "\n".join(
        f"- **{item.decision} — {item.feature}**: {item.reason}" for item in brief.feature_decisions
    ) or "- None supplied"
    sensory = "\n".join(f"- {key}: {value:+.2f}" for key, value in brief.sensory_profile.items()) or "- None supplied"
    references = "\n".join(
        f"- **{item.reference_id} / {item.reaction}** — adopt: {', '.join(item.adopted) or 'none'}; "
        f"reject: {', '.join(item.rejected) or 'none'}; notes: {', '.join(item.notes) or 'none'}"
        for item in brief.reference_ledger
    ) or "- None supplied"
    questions = "\n".join(f"- {item}" for item in brief.unresolved_questions) or "- None"
    missing = "\n".join(f"- {item}" for item in brief.missing_parts) or "- None detected"
    nodes = "\n".join(f"- `{item.type}` {item.label} ({item.status})" for item in brief.planned_structure.nodes)
    return f"""# Design & Function Translation Brief

## Contract

- Schema: `{brief.schema_version}`
- Request: `{brief.request_id}`
- Project: `{brief.project_id}`
- Status: `{brief.status}`

## Context

- Title: {brief.title}
- Domain: {brief.domain}
- Role: {brief.role}
- Target user: {brief.target_user}

## Inferred goals

{goals}

## Design constraints

{constraints}

## Feature decisions

{features}

## Sensory profile

{sensory}

## Reference adoption ledger

{references}

## Missing parts

{missing}

## Planned structure

{nodes}

## Questions for human discussion

{questions}

No design approval or implementation was executed.
"""
