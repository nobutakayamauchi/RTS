from __future__ import annotations

import difflib
import hashlib
import json
import re
from collections import defaultdict
from typing import Any, Iterable

from model_behavior_adaptation.core import CONFIG_VALUES


class TransitionError(ValueError):
    pass


SCHEMA_VERSION = "transition-evidence-bundle/v1"
SOURCE_TYPES = {
    "README",
    "RELEASE_NOTES",
    "API_DOCS",
    "MIGRATION_GUIDE",
    "MODEL_CARD",
    "TOOL_DOCS",
    "LIMITS_DOCS",
    "SDK_SCHEMA",
    "DEPRECATION_NOTE",
    "OTHER_OFFICIAL",
}
TRUST_LEVELS = {"OFFICIAL", "UNOFFICIAL"}
CLAIM_KINDS = {
    "CONTRACT",
    "CAPABILITY",
    "LIMIT",
    "DEPRECATION",
    "MARKETING",
    "PRICING",
    "PERFORMANCE",
}
CONTRACT_AREAS = {
    "model_identity",
    "context",
    "instructions",
    "reasoning",
    "tools",
    "state",
    "memory_cache",
    "response_schema",
    "streaming",
    "sandbox",
    "delegation",
    "errors_retries",
    "limits",
    "auth_permissions",
    "pricing_usage",
    "other",
}
SEVERITY_RANK = {"S0": 0, "S1": 1, "S2": 2, "S3": 3}
AUTHORITY_NONE = {
    "execution_authority": "NONE",
    "profile_application_authority": "NONE",
    "promotion_authority": "NONE",
}
FORBIDDEN_FIELDS = {
    "chain_of_thought",
    "hidden_reasoning",
    "reasoning_text",
    "scratchpad",
}
MAX_SOURCES = 32
MAX_CLAIMS_PER_SOURCE = 128
MAX_SOURCE_CHARS = 250_000
MAX_TOTAL_CLAIMS = 512
MAX_PROBES = 8

TOPOLOGY_KEYS = {
    "execution_model",
    "runtime_topology",
    "agent_loop",
    "planner_model",
    "tool_loop_owner",
    "tool_execution_model",
    "delegation_model",
    "subagent_model",
    "state_model",
    "conversation_state_model",
    "sandbox_model",
    "memory_model",
}

AREA_TO_F_DIMENSIONS = {
    "context": ["context_mode"],
    "instructions": ["instruction_density"],
    "reasoning": ["reasoning_tier"],
    "tools": ["tool_strategy", "autonomy"],
    "state": ["autonomy", "context_mode"],
    "memory_cache": ["recall_mode"],
    "sandbox": ["tool_strategy", "autonomy"],
    "delegation": ["autonomy", "tool_strategy"],
    "errors_retries": ["tool_strategy"],
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalized_text(text: str) -> str:
    return " ".join(text.split())


def _claim_key(claim: dict[str, Any]) -> tuple[str, str]:
    return claim["area"], claim["key"]


def _claim_value_fingerprint(claim: dict[str, Any]) -> str:
    return _canonical({"kind": claim["kind"], "value": claim["value"]})


def _validate_no_forbidden_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        forbidden = sorted(FORBIDDEN_FIELDS & set(value))
        if forbidden:
            raise TransitionError(f"{path} contains forbidden hidden-reasoning fields: {forbidden}")
        for key, child in value.items():
            _validate_no_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_fields(child, f"{path}[{index}]")


def validate_claim(claim: dict[str, Any], content: str) -> None:
    if not isinstance(claim, dict):
        raise TransitionError("claim must be an object")
    required = {"claim_id", "area", "key", "kind", "value", "anchor"}
    missing = sorted(required - set(claim))
    if missing:
        raise TransitionError(f"claim missing fields: {missing}")
    for field in ("claim_id", "key", "anchor"):
        if not isinstance(claim[field], str) or not claim[field]:
            raise TransitionError(f"claim.{field} must be a non-empty string")
    if claim["area"] not in CONTRACT_AREAS:
        raise TransitionError(f"unsupported claim area: {claim['area']!r}")
    if claim["kind"] not in CLAIM_KINDS:
        raise TransitionError(f"unsupported claim kind: {claim['kind']!r}")
    if len(claim["anchor"]) > 2000:
        raise TransitionError("claim.anchor exceeds 2000 characters")
    if claim["anchor"] not in content:
        raise TransitionError(f"claim anchor not found in source content: {claim['claim_id']}")
    try:
        _canonical(claim["value"])
    except (TypeError, ValueError) as exc:
        raise TransitionError("claim.value must be JSON-compatible") from exc
    _validate_no_forbidden_fields(claim, "claim")


def validate_source(source: dict[str, Any]) -> None:
    if not isinstance(source, dict):
        raise TransitionError("source must be an object")
    required = {
        "source_id",
        "document_id",
        "source_type",
        "trust",
        "url",
        "ref",
        "content",
        "content_sha256",
        "claims",
    }
    missing = sorted(required - set(source))
    if missing:
        raise TransitionError(f"source missing fields: {missing}")
    for field in ("source_id", "document_id", "url", "ref"):
        if not isinstance(source[field], str) or not source[field]:
            raise TransitionError(f"source.{field} must be a non-empty string")
    if source["source_type"] not in SOURCE_TYPES:
        raise TransitionError(f"unsupported source_type: {source['source_type']!r}")
    if source["trust"] not in TRUST_LEVELS:
        raise TransitionError(f"unsupported source trust: {source['trust']!r}")
    content = source["content"]
    if not isinstance(content, str) or not content:
        raise TransitionError("source.content must be non-empty text")
    if len(content) > MAX_SOURCE_CHARS:
        raise TransitionError(f"source.content exceeds {MAX_SOURCE_CHARS} characters")
    digest = source["content_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise TransitionError("source.content_sha256 must be lowercase SHA-256 hex")
    if _sha256_text(content) != digest:
        raise TransitionError(f"source digest mismatch: {source['source_id']}")
    claims = source["claims"]
    if not isinstance(claims, list):
        raise TransitionError("source.claims must be a list")
    if len(claims) > MAX_CLAIMS_PER_SOURCE:
        raise TransitionError(f"source.claims exceeds {MAX_CLAIMS_PER_SOURCE}")
    seen_claim_ids: set[str] = set()
    for claim in claims:
        validate_claim(claim, content)
        claim_id = claim["claim_id"]
        if claim_id in seen_claim_ids:
            raise TransitionError(f"duplicate claim_id within source: {claim_id}")
        seen_claim_ids.add(claim_id)
    _validate_no_forbidden_fields(source, "source")


def validate_bundle(bundle: dict[str, Any]) -> None:
    if not isinstance(bundle, dict):
        raise TransitionError("bundle must be an object")
    required = {
        "schema_version",
        "provider",
        "product_surface",
        "generation",
        "captured_at",
        "sources",
    }
    missing = sorted(required - set(bundle))
    if missing:
        raise TransitionError(f"bundle missing fields: {missing}")
    if bundle["schema_version"] != SCHEMA_VERSION:
        raise TransitionError(f"schema_version must be {SCHEMA_VERSION!r}")
    for field in ("provider", "product_surface", "generation", "captured_at"):
        if not isinstance(bundle[field], str) or not bundle[field]:
            raise TransitionError(f"bundle.{field} must be a non-empty string")
    sources = bundle["sources"]
    if not isinstance(sources, list) or not sources:
        raise TransitionError("bundle.sources must be a non-empty list")
    if len(sources) > MAX_SOURCES:
        raise TransitionError(f"bundle.sources exceeds {MAX_SOURCES}")
    seen_source_ids: set[str] = set()
    seen_document_ids: set[str] = set()
    total_claims = 0
    for source in sources:
        validate_source(source)
        if source["source_id"] in seen_source_ids:
            raise TransitionError(f"duplicate source_id: {source['source_id']}")
        if source["document_id"] in seen_document_ids:
            raise TransitionError(f"duplicate document_id: {source['document_id']}")
        seen_source_ids.add(source["source_id"])
        seen_document_ids.add(source["document_id"])
        total_claims += len(source["claims"])
    if total_claims > MAX_TOTAL_CLAIMS:
        raise TransitionError(f"bundle total claims exceeds {MAX_TOTAL_CLAIMS}")
    _validate_no_forbidden_fields(bundle, "bundle")


def _official_claim_index(bundle: dict[str, Any]) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for source in bundle["sources"]:
        if source["trust"] != "OFFICIAL":
            continue
        for claim in source["claims"]:
            grouped[_claim_key(claim)].append({
                "claim": claim,
                "source_id": source["source_id"],
                "document_id": source["document_id"],
                "url": source["url"],
                "ref": source["ref"],
            })
    conflicts: list[dict[str, Any]] = []
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for key, entries in sorted(grouped.items()):
        values = {_claim_value_fingerprint(entry["claim"]) for entry in entries}
        if len(values) > 1:
            conflicts.append({
                "area": key[0],
                "key": key[1],
                "source_ids": sorted(entry["source_id"] for entry in entries),
                "reason": "CONFLICTING_OFFICIAL_CLAIMS",
            })
            continue
        representative = entries[0]["claim"]
        index[key] = {
            "area": representative["area"],
            "key": representative["key"],
            "kind": representative["kind"],
            "value": representative["value"],
            "behavior_status": "UNVERIFIED",
            "evidence": [
                {
                    "source_id": entry["source_id"],
                    "document_id": entry["document_id"],
                    "url": entry["url"],
                    "ref": entry["ref"],
                    "claim_id": entry["claim"]["claim_id"],
                }
                for entry in entries
            ],
        }
    return index, conflicts


def _severity_for_delta(old: dict[str, Any] | None, new: dict[str, Any] | None) -> tuple[str, str]:
    claim = new or old
    assert claim is not None
    area = claim["area"]
    kind = claim["kind"]
    key = claim["key"]

    if kind == "MARKETING":
        return "S0", "MARKETING_OR_WORDING_ONLY"
    if kind in {"PRICING", "PERFORMANCE"} or area == "pricing_usage":
        return "S1", "OPERATING_COST_OR_PERFORMANCE_TUNING"
    if kind == "LIMIT" or area == "limits":
        return "S1", "BOUND_OR_LIMIT_CHANGED"
    if area == "model_identity":
        return "S1", "MODEL_IDENTITY_OR_NAMING_CHANGED"
    if key in TOPOLOGY_KEYS and area in {"tools", "state", "memory_cache", "sandbox", "delegation"}:
        return "S3", "OBSERVABLE_EXECUTION_CONTRACT_TOPOLOGY_CHANGED"
    if area in {"state", "delegation", "sandbox", "memory_cache", "tools"}:
        return "S2", "AGENT_OR_TOOL_BEHAVIOR_CONTRACT_CHANGED"
    if area in {
        "context",
        "instructions",
        "reasoning",
        "response_schema",
        "streaming",
        "errors_retries",
        "auth_permissions",
    }:
        return "S2", "BEHAVIORAL_OR_INTERFACE_CONTRACT_CHANGED"
    if kind == "DEPRECATION":
        return "S2", "DEPRECATED_CONTRACT_SURFACE"
    return "S1", "MATERIAL_DOCUMENTED_CONTRACT_CHANGE"


def _max_severity(deltas: Iterable[dict[str, Any]]) -> str:
    result = "S0"
    for delta in deltas:
        if SEVERITY_RANK[delta["severity"]] > SEVERITY_RANK[result]:
            result = delta["severity"]
    return result


def _remove_mapped_anchors(content: str, anchors: Iterable[str]) -> str:
    residual = _normalized_text(content)
    normalized_anchors = sorted(
        {_normalized_text(anchor) for anchor in anchors if _normalized_text(anchor)},
        key=len,
        reverse=True,
    )
    for anchor in normalized_anchors:
        residual = residual.replace(anchor, " ")
    return _normalized_text(residual)


def _document_text_change_review(old_bundle: dict[str, Any], new_bundle: dict[str, Any], claim_delta_keys: set[tuple[str, str]]) -> list[dict[str, Any]]:
    old_docs = {source["document_id"]: source for source in old_bundle["sources"] if source["trust"] == "OFFICIAL"}
    new_docs = {source["document_id"]: source for source in new_bundle["sources"] if source["trust"] == "OFFICIAL"}
    issues: list[dict[str, Any]] = []
    for document_id in sorted(set(old_docs) & set(new_docs)):
        old = old_docs[document_id]
        new = new_docs[document_id]
        if old["content_sha256"] == new["content_sha256"]:
            continue
        if _normalized_text(old["content"]) == _normalized_text(new["content"]):
            continue
        old_anchors = [
            claim["anchor"] for claim in old["claims"]
            if _claim_key(claim) in claim_delta_keys
        ]
        new_anchors = [
            claim["anchor"] for claim in new["claims"]
            if _claim_key(claim) in claim_delta_keys
        ]
        old_residual = _remove_mapped_anchors(old["content"], old_anchors)
        new_residual = _remove_mapped_anchors(new["content"], new_anchors)
        if old_residual != new_residual:
            ratio = difflib.SequenceMatcher(None, old_residual, new_residual).ratio()
            issues.append({
                "document_id": document_id,
                "old_source_id": old["source_id"],
                "new_source_id": new["source_id"],
                "reason": "OFFICIAL_TEXT_CHANGE_HAS_UNMAPPED_RESIDUAL",
                "residual_similarity_ratio": round(ratio, 6),
                "old_residual_sha256": _sha256_text(old_residual),
                "new_residual_sha256": _sha256_text(new_residual),
            })
    for document_id in sorted(set(new_docs) - set(old_docs)):
        new = new_docs[document_id]
        if not new["claims"]:
            issues.append({
                "document_id": document_id,
                "new_source_id": new["source_id"],
                "reason": "NEW_OFFICIAL_DOCUMENT_HAS_NO_NORMALIZED_CLAIMS",
            })
    for document_id in sorted(set(old_docs) - set(new_docs)):
        old = old_docs[document_id]
        if not old["claims"]:
            issues.append({
                "document_id": document_id,
                "old_source_id": old["source_id"],
                "reason": "REMOVED_OFFICIAL_DOCUMENT_HAS_NO_NORMALIZED_CLAIMS",
            })
    return issues


def _probe_requirements(severity: str, deltas: list[dict[str, Any]], review_required: bool) -> dict[str, Any]:
    dimensions: list[str] = []
    unmapped_areas: list[str] = []
    changed_areas = []
    for delta in deltas:
        if delta["severity"] == "S0":
            continue
        area = delta["area"]
        if area not in changed_areas:
            changed_areas.append(area)
        mapped = AREA_TO_F_DIMENSIONS.get(area, [])
        if not mapped and area not in unmapped_areas:
            unmapped_areas.append(area)
        for dimension in mapped:
            if dimension not in CONFIG_VALUES:
                raise TransitionError(f"H mapped unknown F dimension: {dimension}")
            if dimension not in dimensions:
                dimensions.append(dimension)
    if severity == "S3":
        for dimension in CONFIG_VALUES:
            if dimension not in dimensions:
                dimensions.append(dimension)
    cap_by_severity = {"S0": 1, "S1": 3, "S2": 6, "S3": 8}
    max_probe_count = min(MAX_PROBES, cap_by_severity[severity])
    if review_required:
        execution_recommendation = "HOLD_FOR_REVIEW"
    elif severity == "S0":
        execution_recommendation = "MINIMAL_REVALIDATION"
    elif severity == "S1":
        execution_recommendation = "TUNING_REVALIDATION"
    elif severity == "S2":
        execution_recommendation = "TARGETED_REPROFILE"
    else:
        execution_recommendation = "EXPANDED_CONSERVATIVE_REPROFILE"
    return {
        "preferred_f_dimensions": dimensions[: len(CONFIG_VALUES)],
        "max_probe_count": max_probe_count,
        "changed_contract_areas": changed_areas,
        "unmapped_contract_areas": unmapped_areas,
        "execution_recommendation": execution_recommendation,
        "execution_authority": "NONE",
    }


def _profile_disposition(severity: str, review_required: bool) -> dict[str, Any]:
    if review_required:
        return {
            "old_profile_evidence": "PRESERVE_HISTORICAL",
            "old_operating_assumptions": "HOLD_REUSE_PENDING_REVIEW",
            "direct_application": "BLOCKED",
            "recommended_mode": "CONSERVATIVE",
        }
    if severity == "S0":
        return {
            "old_profile_evidence": "PRESERVE_HISTORICAL",
            "old_operating_assumptions": "PRIOR_ONLY",
            "direct_application": "BLOCKED_UNTIL_F_REVALIDATION",
            "recommended_mode": "MINIMAL_REVALIDATION",
        }
    if severity == "S1":
        return {
            "old_profile_evidence": "PRESERVE_HISTORICAL",
            "old_operating_assumptions": "PRIOR_ONLY",
            "direct_application": "BLOCKED_UNTIL_F_REVALIDATION",
            "recommended_mode": "TUNING_REVALIDATION",
        }
    if severity == "S2":
        return {
            "old_profile_evidence": "PRESERVE_HISTORICAL",
            "old_operating_assumptions": "HYPOTHESIS_ONLY",
            "direct_application": "BLOCKED",
            "recommended_mode": "CONSERVATIVE_TARGETED_REPROFILE",
        }
    return {
        "old_profile_evidence": "PRESERVE_HISTORICAL",
        "old_operating_assumptions": "QUARANTINE_FOR_DIRECT_REUSE",
        "direct_application": "BLOCKED",
        "recommended_mode": "CONSERVATIVE_EXPANDED_REPROFILE",
    }


def compare_bundles(old_bundle: dict[str, Any], new_bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(old_bundle)
    validate_bundle(new_bundle)
    if old_bundle["provider"] != new_bundle["provider"]:
        raise TransitionError("provider mismatch between bundles")
    if old_bundle["product_surface"] != new_bundle["product_surface"]:
        raise TransitionError("product_surface mismatch between bundles")
    if old_bundle["generation"] == new_bundle["generation"]:
        raise TransitionError("old/new generation must differ")

    old_index, old_conflicts = _official_claim_index(old_bundle)
    new_index, new_conflicts = _official_claim_index(new_bundle)
    conflicts = old_conflicts + new_conflicts

    deltas: list[dict[str, Any]] = []
    for key in sorted(set(old_index) | set(new_index)):
        old = old_index.get(key)
        new = new_index.get(key)
        if old is not None and new is not None and _canonical({"kind": old["kind"], "value": old["value"]}) == _canonical({"kind": new["kind"], "value": new["value"]}):
            continue
        severity, reason = _severity_for_delta(old, new)
        deltas.append({
            "area": key[0],
            "key": key[1],
            "change": "ADDED" if old is None else "REMOVED" if new is None else "CHANGED",
            "old": old,
            "new": new,
            "severity": severity,
            "reason": reason,
            "behavior_status": "UNVERIFIED",
        })

    claim_delta_keys = {(delta["area"], delta["key"]) for delta in deltas}
    unmapped_text_changes = _document_text_change_review(old_bundle, new_bundle, claim_delta_keys)
    review_required = bool(conflicts or unmapped_text_changes)
    severity = _max_severity(deltas)
    if review_required and severity == "S0":
        transition_state = "REVIEW_REQUIRED"
    elif review_required:
        transition_state = "REVIEW_REQUIRED"
    else:
        transition_state = "CLASSIFIED"

    return {
        "schema_version": "model-transition-report/v1",
        "provider": old_bundle["provider"],
        "product_surface": old_bundle["product_surface"],
        "old_generation": old_bundle["generation"],
        "new_generation": new_bundle["generation"],
        "transition_state": transition_state,
        "severity": severity,
        "severity_meaning": {
            "S0": "NO_MATERIAL_EXTERNAL_CONTRACT_CHANGE",
            "S1": "TUNING_LIMIT_OR_COST_CHANGE",
            "S2": "BEHAVIOR_OR_INTERFACE_CONTRACT_CHANGE",
            "S3": "OBSERVABLE_EXECUTION_CONTRACT_SHIFT",
        }[severity],
        "architecture_claim": "OBSERVABLE_EXECUTION_CONTRACT_ONLY",
        "hidden_architecture_claim": "NONE",
        "documentation_behavior_status": "UNVERIFIED",
        "deltas": deltas,
        "conflicts": conflicts,
        "unmapped_text_changes": unmapped_text_changes,
        "profile_disposition": _profile_disposition(severity, review_required),
        "probe_requirements": _probe_requirements(severity, deltas, review_required),
        "authority": dict(AUTHORITY_NONE),
    }
