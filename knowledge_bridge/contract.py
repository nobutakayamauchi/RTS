from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CONTRACT_SCHEMA_VERSION = "1.0"
_ALLOWED_STATUSES = {"AWAITING_HUMAN_DECISION"}
_ALLOWED_FEATURE_DECISIONS = {"KEEP", "SIMPLIFY", "DEFER", "REMOVE", "CLARIFY"}
_ALLOWED_NODE_TYPES = {"request", "goal", "feature", "reference", "missing_part", "implementation_target", "approval"}
_ALLOWED_EDGE_TYPES = {"clarifies", "implements", "depends_on", "inserts_into", "references", "blocks", "requires_approval"}


@dataclass(frozen=True)
class ContractError:
    path: str
    message: str


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_input_contract(payload: dict[str, Any]) -> tuple[ContractError, ...]:
    errors: list[ContractError] = []
    version = payload.get("schema_version", CONTRACT_SCHEMA_VERSION)
    if version != CONTRACT_SCHEMA_VERSION:
        errors.append(ContractError("schema_version", f"unsupported schema version: {version}"))

    for key in ("request_id", "project_id"):
        value = payload.get(key)
        if value is not None and not _is_non_empty_string(value):
            errors.append(ContractError(key, "must be a non-empty string when supplied"))

    for key in ("feedback", "goals", "constraints", "unresolved_questions"):
        value = payload.get(key)
        if value is not None and not isinstance(value, (str, list, tuple)):
            errors.append(ContractError(key, "must be a string or list of strings"))

    references = payload.get("references", [])
    if not isinstance(references, list):
        errors.append(ContractError("references", "must be an array"))
    else:
        for index, item in enumerate(references):
            if not isinstance(item, dict):
                errors.append(ContractError(f"references[{index}]", "must be an object"))
            elif not _is_non_empty_string(item.get("reference_id")):
                errors.append(ContractError(f"references[{index}].reference_id", "is required"))

    features = payload.get("features", [])
    if not isinstance(features, list):
        errors.append(ContractError("features", "must be an array"))
    else:
        for index, item in enumerate(features):
            if not isinstance(item, dict):
                errors.append(ContractError(f"features[{index}]", "must be an object"))
                continue
            if not _is_non_empty_string(item.get("feature")):
                errors.append(ContractError(f"features[{index}].feature", "is required"))
            decision = str(item.get("decision", "CLARIFY")).upper()
            if decision not in _ALLOWED_FEATURE_DECISIONS:
                errors.append(ContractError(f"features[{index}].decision", f"unsupported decision: {decision}"))

    sensory = payload.get("sensory_profile")
    if sensory is not None and not isinstance(sensory, dict):
        errors.append(ContractError("sensory_profile", "must be an object"))

    return tuple(errors)


def validate_output_contract(payload: dict[str, Any]) -> tuple[ContractError, ...]:
    errors: list[ContractError] = []
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        errors.append(ContractError("schema_version", "must equal 1.0"))
    for key in ("request_id", "project_id", "title", "status"):
        if not _is_non_empty_string(payload.get(key)):
            errors.append(ContractError(key, "must be a non-empty string"))
    if payload.get("status") not in _ALLOWED_STATUSES:
        errors.append(ContractError("status", "must remain at the human decision gate"))
    if payload.get("human_decision_required") is not True:
        errors.append(ContractError("human_decision_required", "must be true"))

    for key in ("inferred_goals", "design_constraints", "unresolved_questions", "missing_parts"):
        if not isinstance(payload.get(key), list):
            errors.append(ContractError(key, "must be an array"))

    planned = payload.get("planned_structure")
    if not isinstance(planned, dict):
        errors.append(ContractError("planned_structure", "must be an object"))
    else:
        nodes = planned.get("nodes", [])
        edges = planned.get("edges", [])
        if not isinstance(nodes, list):
            errors.append(ContractError("planned_structure.nodes", "must be an array"))
        else:
            ids: set[str] = set()
            for index, node in enumerate(nodes):
                if not isinstance(node, dict):
                    errors.append(ContractError(f"planned_structure.nodes[{index}]", "must be an object"))
                    continue
                node_id = node.get("id")
                if not _is_non_empty_string(node_id):
                    errors.append(ContractError(f"planned_structure.nodes[{index}].id", "is required"))
                elif node_id in ids:
                    errors.append(ContractError(f"planned_structure.nodes[{index}].id", "must be unique"))
                else:
                    ids.add(node_id)
                if node.get("type") not in _ALLOWED_NODE_TYPES:
                    errors.append(ContractError(f"planned_structure.nodes[{index}].type", "unsupported node type"))
        if not isinstance(edges, list):
            errors.append(ContractError("planned_structure.edges", "must be an array"))
        else:
            for index, edge in enumerate(edges):
                if not isinstance(edge, dict):
                    errors.append(ContractError(f"planned_structure.edges[{index}]", "must be an object"))
                    continue
                if edge.get("type") not in _ALLOWED_EDGE_TYPES:
                    errors.append(ContractError(f"planned_structure.edges[{index}].type", "unsupported edge type"))
                for endpoint in ("from", "to"):
                    if not _is_non_empty_string(edge.get(endpoint)):
                        errors.append(ContractError(f"planned_structure.edges[{index}].{endpoint}", "is required"))
    return tuple(errors)


def raise_for_contract(errors: tuple[ContractError, ...]) -> None:
    if errors:
        rendered = "; ".join(f"{item.path}: {item.message}" for item in errors)
        raise ValueError(f"contract validation failed: {rendered}")
