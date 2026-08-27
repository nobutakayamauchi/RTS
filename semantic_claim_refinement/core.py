from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from model_transition_intelligence.core import validate_bundle
from official_docs_intake.core import (
    AUTHORITY_NONE,
    _chunk_blocks,
    _sha256_text,
    report_fingerprint,
    verify_intake_report,
)


class RefinementError(ValueError):
    pass


REPORT_SCHEMA_VERSION = "semantic-claim-refinement-report/v1"
METHOD = "CONTROLLED_SEMANTIC_ALIAS_V1"
MAX_ADDED_CLAIMS = 128
MAX_RULES = 32
NEGATION_OR_EXCEPTION_RE = re.compile(
    r"\b(?:no|not|never|without|cannot|can't|does not|doesn't|do not|don't|except|unless|unsupported|unavailable)\b|\bonly when\b|\bnot available\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SemanticRule:
    rule_id: str
    area: str
    key: str
    kind: str
    semantic_value: dict[str, Any]
    patterns: tuple[str, ...]


DEFAULT_RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        "tools.parallel_calls.v1",
        "tools",
        "parallel_tool_calls",
        "CAPABILITY",
        {"support": "DOCUMENTED", "mode": "PARALLEL_TOOL_CALLS"},
        (
            r"\b(?:multiple|several|more than one)\s+(?:tools?|functions?)\b.{0,80}\b(?:parallel|concurrent|concurrently|simultaneous|simultaneously)\b",
            r"\b(?:parallel|concurrent|concurrently)\b.{0,80}\b(?:tools?|functions?)\b",
        ),
    ),
    SemanticRule(
        "state.background_execution.v1",
        "state",
        "background_execution",
        "CAPABILITY",
        {"support": "DOCUMENTED", "mode": "BACKGROUND_EXECUTION"},
        (
            r"\b(?:background mode|background execution|continue running in the background)\b",
            r"\b(?:continue|keeps? running).{0,100}\b(?:disconnect|disconnected|connection closes?)\b",
        ),
    ),
    SemanticRule(
        "state.persistence.v1",
        "state",
        "state_persistence",
        "CONTRACT",
        {"persistence": "DOCUMENTED_ACROSS_TURNS"},
        (
            r"\b(?:retain|retains|preserve|preserves|persist|persists)\b.{0,100}\b(?:across turns|between turns|between requests|across requests)\b",
        ),
    ),
    SemanticRule(
        "tools.automatic_selection.v1",
        "tools",
        "automatic_tool_selection",
        "CAPABILITY",
        {"support": "DOCUMENTED", "mode": "AUTOMATIC_SELECTION"},
        (
            r"\b(?:selects?|chooses?)\b.{0,60}\btools?\b.{0,60}\bautomatically\b",
            r"\bautomatically\b.{0,60}\b(?:selects?|chooses?)\b.{0,60}\btools?\b",
        ),
    ),
    SemanticRule(
        "delegation.coordinated_agents.v1",
        "delegation",
        "coordinated_agents",
        "CAPABILITY",
        {"support": "DOCUMENTED", "mode": "COORDINATED_AGENTS"},
        (
            r"\b(?:coordinates?|coordinated|coordinate)\b.{0,80}\bagents?\b",
            r"\bagent workers?\b",
        ),
    ),
    SemanticRule(
        "response.schema_conformance.v1",
        "response_schema",
        "schema_conformance",
        "CONTRACT",
        {"support": "DOCUMENTED", "mode": "SCHEMA_CONFORMANCE"},
        (
            r"\bresponses?\b.{0,80}\b(?:conform|conforms|constrained)\b.{0,80}\bschema\b",
            r"\bschema[- ]constrained\b",
        ),
    ),
    SemanticRule(
        "sandbox.isolated_environment.v1",
        "sandbox",
        "isolated_execution_environment",
        "CONTRACT",
        {"support": "DOCUMENTED", "mode": "ISOLATED_EXECUTION_ENVIRONMENT"},
        (
            r"\bisolated (?:execution )?environment\b",
            r"\bexecution environment\b.{0,60}\bisolated\b",
        ),
    ),
    SemanticRule(
        "limits.concurrent_requests.v1",
        "limits",
        "concurrent_requests",
        "LIMIT",
        {"dimension": "CONCURRENT_REQUESTS", "limit": "DOCUMENTED"},
        (
            r"\b(?:concurrent|simultaneous) requests?\b",
        ),
    ),
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _semantic_matches(anchor: str, rules: tuple[SemanticRule, ...]) -> list[SemanticRule]:
    matches: list[SemanticRule] = []
    for rule in rules:
        if any(re.search(pattern, anchor, re.IGNORECASE) for pattern in rule.patterns):
            matches.append(rule)
    return matches


def _claim_for(rule: SemanticRule, anchor: str) -> dict[str, Any]:
    digest = _sha256_text(anchor)
    return {
        "claim_id": "j_" + _sha256_text(f"{rule.rule_id}|{anchor}")[:20],
        "area": rule.area,
        "key": rule.key,
        "kind": rule.kind,
        "value": copy.deepcopy(rule.semantic_value),
        "anchor": anchor,
        "extraction_method": METHOD,
        "refinement_rule_id": rule.rule_id,
        "input_anchor_sha256": digest,
        "behavior_status": "UNVERIFIED",
    }


def refine_intake_report(
    intake_report: dict[str, Any],
    *,
    rules: tuple[SemanticRule, ...] = DEFAULT_RULES,
) -> dict[str, Any]:
    verify_intake_report(intake_report)
    if not isinstance(rules, tuple) or not rules or len(rules) > MAX_RULES:
        raise RefinementError(f"rules must be a non-empty tuple capped at {MAX_RULES}")
    if len({rule.rule_id for rule in rules}) != len(rules):
        raise RefinementError("duplicate semantic rule_id")

    input_fp = report_fingerprint(intake_report)
    bundle = intake_report.get("bundle")
    if bundle is None:
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "FAILED",
            "input_report_fingerprint": input_fp,
            "bundle": None,
            "audit": {"reason": "INPUT_BUNDLE_MISSING", "resolved_count": 0, "remaining_ambiguous_count": 0},
            "docs_claim_status": "UNVERIFIED",
            "hidden_architecture_claim": "NONE",
            **AUTHORITY_NONE,
        }

    refined_bundle = copy.deepcopy(bundle)
    audits_by_source = {
        row["source_id"]: row
        for row in intake_report["audit"].get("documents", [])
        if isinstance(row, dict) and row.get("source_id")
    }
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    added_total = 0
    upstream_truncated = False

    for source in refined_bundle["sources"]:
        doc_audit = audits_by_source.get(source["source_id"], {})
        extraction = doc_audit.get("extraction", {})
        ambiguous = extraction.get("ambiguous", [])
        upstream_truncated = upstream_truncated or bool(extraction.get("ambiguous_findings_truncated"))
        if not ambiguous:
            continue

        chunks_by_hash: dict[str, str] = {}
        for anchor in _chunk_blocks(source["content"]):
            chunks_by_hash.setdefault(_sha256_text(anchor), anchor)
        existing = {(claim["area"], claim["key"], claim["anchor"]) for claim in source["claims"]}

        for finding in ambiguous:
            anchor_hash = finding.get("anchor_sha256")
            anchor = chunks_by_hash.get(anchor_hash)
            if not anchor:
                unresolved.append({"source_id": source["source_id"], "anchor_sha256": anchor_hash, "reason": "ANCHOR_NOT_RECOVERED"})
                continue
            matches = _semantic_matches(anchor, rules)
            if matches and NEGATION_OR_EXCEPTION_RE.search(anchor):
                unresolved.append({
                    "source_id": source["source_id"],
                    "anchor_sha256": anchor_hash,
                    "preview": anchor[:240],
                    "reason": "NEGATION_OR_EXCEPTION",
                    "candidate_count": len(matches),
                    "candidate_rule_ids": [rule.rule_id for rule in matches],
                })
                continue
            if not matches:
                unresolved.append({"source_id": source["source_id"], "anchor_sha256": anchor_hash, "preview": anchor[:240], "reason": "NO_ONTOLOGY_MATCH"})
                continue
            if len(matches) != 1:
                unresolved.append({
                    "source_id": source["source_id"],
                    "anchor_sha256": anchor_hash,
                    "preview": anchor[:240],
                    "reason": "MULTIPLE_ONTOLOGY_MATCHES",
                    "candidate_count": len(matches),
                    "candidate_rule_ids": [rule.rule_id for rule in matches],
                })
                continue

            rule = matches[0]
            claim = _claim_for(rule, anchor)
            fingerprint = (claim["area"], claim["key"], claim["anchor"])
            if fingerprint not in existing:
                if added_total >= MAX_ADDED_CLAIMS:
                    unresolved.append({"source_id": source["source_id"], "anchor_sha256": anchor_hash, "preview": anchor[:240], "reason": "ADDED_CLAIM_CAP_REACHED"})
                    continue
                source["claims"].append(claim)
                existing.add(fingerprint)
                added_total += 1
            resolved.append({
                "source_id": source["source_id"],
                "anchor_sha256": anchor_hash,
                "rule_id": rule.rule_id,
                "claim_id": claim["claim_id"],
                "candidate_count": len(matches),
            })

    validate_bundle(refined_bundle)
    fetch_failures = intake_report["audit"].get("fetch_failures", [])
    status = "READY_FOR_H" if not unresolved and not upstream_truncated and not fetch_failures else "REVIEW_REQUIRED"
    original_ambiguous = int(intake_report["audit"].get("ambiguous_block_count", 0))
    remaining = len(unresolved) + (1 if upstream_truncated else 0)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "input_report_fingerprint": input_fp,
        "provider": intake_report["provider"],
        "product_surface": intake_report["product_surface"],
        "generation": intake_report["generation"],
        "bundle": refined_bundle,
        "audit": {
            "method": METHOD,
            "original_ambiguous_count": original_ambiguous,
            "resolved_count": len(resolved),
            "added_claim_count": added_total,
            "remaining_ambiguous_count": remaining,
            "upstream_ambiguous_findings_truncated": upstream_truncated,
            "fetch_failure_count": len(fetch_failures),
            "resolved": resolved,
            "unresolved": unresolved,
            "review_reduction_is_not_correctness_evidence": True,
        },
        "docs_claim_status": "UNVERIFIED",
        "hidden_architecture_claim": "NONE",
        **AUTHORITY_NONE,
    }
    verify_refinement_report(report, intake_report=intake_report)
    return report


def verify_refinement_report(report: dict[str, Any], *, intake_report: dict[str, Any] | None = None) -> None:
    if not isinstance(report, dict):
        raise RefinementError("report must be an object")
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise RefinementError("invalid refinement report schema")
    if report.get("status") not in {"READY_FOR_H", "REVIEW_REQUIRED", "FAILED"}:
        raise RefinementError("invalid refinement status")
    for key, value in AUTHORITY_NONE.items():
        if report.get(key) != value:
            raise RefinementError(f"authority boundary violated: {key}")
    if report.get("docs_claim_status") != "UNVERIFIED":
        raise RefinementError("docs claims must remain UNVERIFIED")
    if report.get("hidden_architecture_claim") != "NONE":
        raise RefinementError("hidden architecture claim is forbidden")
    fp = report.get("input_report_fingerprint")
    if not isinstance(fp, str) or not re.fullmatch(r"[0-9a-f]{64}", fp):
        raise RefinementError("input_report_fingerprint must be SHA-256 hex")
    if intake_report is not None:
        verify_intake_report(intake_report)
        if report_fingerprint(intake_report) != fp:
            raise RefinementError("input report fingerprint mismatch")
    bundle = report.get("bundle")
    if bundle is not None:
        validate_bundle(bundle)
        for source in bundle["sources"]:
            for claim in source["claims"]:
                if claim.get("extraction_method") == METHOD:
                    if claim.get("anchor") not in source["content"]:
                        raise RefinementError("refined claim anchor not present in source")
                    if claim.get("behavior_status") != "UNVERIFIED":
                        raise RefinementError("refined claim became verified behavior")
                    if claim.get("input_anchor_sha256") != _sha256_text(claim["anchor"]):
                        raise RefinementError("refined claim anchor digest mismatch")
    audit = report.get("audit")
    if not isinstance(audit, dict):
        raise RefinementError("refinement audit missing")
    if report["status"] == "READY_FOR_H":
        if bundle is None:
            raise RefinementError("READY_FOR_H requires bundle")
        if audit.get("remaining_ambiguous_count") != 0:
            raise RefinementError("READY_FOR_H cannot retain ambiguity")
        if audit.get("upstream_ambiguous_findings_truncated"):
            raise RefinementError("READY_FOR_H forbidden when upstream ambiguity was truncated")
        if audit.get("fetch_failure_count"):
            raise RefinementError("READY_FOR_H cannot retain fetch failures")


def refinement_fingerprint(report: dict[str, Any]) -> str:
    verify_refinement_report(report)
    return hashlib.sha256(_canonical(report).encode("utf-8")).hexdigest()
