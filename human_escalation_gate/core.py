from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from official_docs_intake.core import AUTHORITY_NONE
from review_necessity_triage import triage_fingerprint, verify_triage_report


class HumanEscalationError(ValueError):
    pass


REPORT_SCHEMA_VERSION = "human-escalation-gate-report/v1"
ALLOWED_DISPOSITIONS = {
    "AI_CONTINUE",
    "AI_RESOLVE",
    "WAIT_SAFE_DEFER",
    "HUMAN_CANDIDATE",
    "HUMAN_NOW",
    "REVIEW_BLOCKED",
}
ALLOWED_EVIDENCE_OUTCOMES = {
    "OBSERVED",
    "REFUTED",
    "INCONCLUSIVE",
    "NON_DISCRIMINATING",
}
EXHAUSTION_SEARCH_ROUTE = "SEARCH_FOR_NEW_DISCRIMINATING_ROUTE"
MAX_EVIDENCE = 2048


_ESCAPE_ROUTE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "MEASURE_CLASSIFIER_LATENCY_OVERHEAD",
        (r"classifiers?", r"(?:longer|latency|seconds?|paused|synchronously)"),
    ),
    (
        "ADAPT_OR_VERIFY_API_CONTRACT",
        (r"safety_identifier",),
    ),
    (
        "VERIFY_REASONING_CONTEXT_FIELD",
        (r"reasoning\.context",),
    ),
    (
        "VERIFY_STATE_CONTINUATION_CONTRACT",
        (r"previous_response_id",),
    ),
    (
        "REPLICATE_DOCUMENTED_BENCHMARK",
        (r"(?:eval|evaluation|benchmark)", r"\b\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?%"),
    ),
    (
        "ADD_OR_VERIFY_CONTEXT_TELEMETRY",
        (r"track context",),
    ),
    (
        "PROBE_LONG_SESSION_CONTEXT_GROWTH",
        (r"long sessions?", r"(?:prompt|tool|context|content)"),
    ),
    (
        "APPLY_CONSERVATIVE_AUTHORITY_POLICY_AND_REVALIDATE",
        (r"level of action", r"authoriz"),
    ),
    (
        "RECALIBRATE_LIMIT_OR_BUDGET",
        (r"(?:billed|billing|token rates?|pricing|price|cost)",),
    ),
    (
        "FETCH_REFERENCED_OFFICIAL_DOC_CONTEXT",
        (r"learn more", r"https?://|\[[^\]]+\]\("),
    ),
    (
        "FETCH_ADJACENT_OFFICIAL_DOC_CONTEXT",
        (r"\bwhen:\s*$",),
    ),
    (
        "PROBE_STRUCTURED_OUTPUT_GUIDANCE",
        (r"output schema", r"(?:emit|produce|return)"),
    ),
    (
        "MAP_ENGINE_IDENTITY_CATALOG",
        (r"legacy models?", r"(?:still available|available|model)"),
    ),
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _matches_all(text: str, patterns: Iterable[str]) -> bool:
    return all(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def recover_escape_routes(anchor: str) -> list[str]:
    """Bounded second-pass escape-route search over the exact K0 anchor.

    These are verification/evidence-acquisition routes, not claims that the
    documentation is true and not execution authorization.
    """

    routes: list[str] = []
    for route_id, patterns in _ESCAPE_ROUTE_RULES:
        if _matches_all(anchor, patterns):
            routes.append(route_id)
    return list(dict.fromkeys(routes))


def _k0_routes(record: dict[str, Any]) -> list[str]:
    routes = list(record.get("da", {}).get("problem_solving_paths", []))
    routes += list(record.get("counter_da", {}).get("problem_solving_paths", []))
    return list(dict.fromkeys(str(route) for route in routes if str(route)))


def _is_material(record: dict[str, Any]) -> bool:
    da = record["da"]
    counter = record["counter_da"]
    max_importance = max(
        int(da.get("human_review_importance", 0)),
        int(counter.get("human_review_importance", 0)),
    )
    return bool(
        record.get("classification") == "HUMAN_NOW"
        or int(da.get("impact", 0)) >= 4
        or int(da.get("causal_reach", 0)) >= 4
        or int(counter.get("human_review_importance", 0)) >= 4
        or (
            int(record.get("perspective_gap", 0)) >= 2
            and max_importance >= 3
        )
    )


def _normalize_mapping(value: Any, *, name: str) -> dict[int, dict[str, Any]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise HumanEscalationError(f"{name} must be an object keyed by finding index")
    result: dict[int, dict[str, Any]] = {}
    for raw_key, row in value.items():
        try:
            key = int(raw_key)
        except (TypeError, ValueError) as exc:
            raise HumanEscalationError(f"{name} key must be an integer finding index") from exc
        if not isinstance(row, dict):
            raise HumanEscalationError(f"{name}[{key}] must be an object")
        result[key] = row
    return result


def _validate_evidence_row(row: dict[str, Any], *, finding_count: int) -> None:
    required = {
        "evidence_id",
        "finding_index",
        "route_id",
        "probe_fingerprint",
        "evidence_distinction",
        "outcome",
        "learned_facts",
        "closed_routes",
        "opened_routes",
    }
    missing = sorted(required - row.keys())
    extra = sorted(row.keys() - required)
    if missing:
        raise HumanEscalationError(f"verification evidence missing fields: {missing}")
    if extra:
        raise HumanEscalationError(f"verification evidence unknown fields: {extra}")
    if not isinstance(row["evidence_id"], str) or not row["evidence_id"].strip():
        raise HumanEscalationError("evidence_id is required")
    index = row["finding_index"]
    if not isinstance(index, int) or index < 0 or index >= finding_count:
        raise HumanEscalationError("verification evidence finding_index is invalid")
    if not isinstance(row["route_id"], str) or not row["route_id"].strip():
        raise HumanEscalationError("verification evidence route_id is required")
    fp = row["probe_fingerprint"]
    if not isinstance(fp, str) or not re.fullmatch(r"[0-9a-f]{64}", fp):
        raise HumanEscalationError("probe_fingerprint must be SHA-256 hex")
    if not isinstance(row["evidence_distinction"], str) or not row["evidence_distinction"].strip():
        raise HumanEscalationError("evidence_distinction is required")
    if row["outcome"] not in ALLOWED_EVIDENCE_OUTCOMES:
        raise HumanEscalationError("invalid verification evidence outcome")
    for field in ("learned_facts", "closed_routes", "opened_routes"):
        values = row[field]
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise HumanEscalationError(f"verification evidence {field} must be a non-empty-string list")
    if not row["learned_facts"] and not row["closed_routes"] and not row["opened_routes"]:
        raise HumanEscalationError("verification evidence must change the knowledge state")


def _validate_decision(row: dict[str, Any], *, evidence_ids: set[str]) -> None:
    if set(row) != {"decision", "evidence_ids"}:
        raise HumanEscalationError("decision requires only decision and evidence_ids")
    if not isinstance(row["decision"], str) or not row["decision"].strip():
        raise HumanEscalationError("decision text is required")
    ids = row["evidence_ids"]
    if not isinstance(ids, list) or any(not isinstance(x, str) or x not in evidence_ids for x in ids):
        raise HumanEscalationError("decision evidence_ids must reference verification evidence")
    if not ids:
        raise HumanEscalationError("decision requires supporting evidence")


def _validate_safe_defer(row: dict[str, Any], *, evidence_ids: set[str]) -> None:
    if set(row) != {"trigger", "rationale", "evidence_ids"}:
        raise HumanEscalationError("safe defer requires trigger, rationale and evidence_ids")
    if not isinstance(row["trigger"], str) or not row["trigger"].strip():
        raise HumanEscalationError("safe defer trigger is required")
    if not isinstance(row["rationale"], str) or not row["rationale"].strip():
        raise HumanEscalationError("safe defer rationale is required")
    ids = row["evidence_ids"]
    if not isinstance(ids, list) or any(not isinstance(x, str) or x not in evidence_ids for x in ids):
        raise HumanEscalationError("safe defer evidence_ids must reference verification evidence")


def _default_safe_defer(record: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("classification") not in {"HUMAN_LATER", "DEFER_LOW_VALUE"}:
        return None
    return {
        "trigger": "SOURCE_OR_ENGINE_IDENTITY_CHANGE",
        "rationale": "K0 found no immediate material dead-end; recheck when the source or engine identity changes.",
        "evidence_ids": [],
    }


def evaluate_escalation_report(
    triage_report: dict[str, Any],
    *,
    verification_evidence: list[dict[str, Any]] | None = None,
    decisions: dict[int | str, dict[str, Any]] | None = None,
    safe_defers: dict[int | str, dict[str, Any]] | None = None,
    human_choices: dict[int | str, str] | None = None,
) -> dict[str, Any]:
    verify_triage_report(triage_report)
    records = triage_report["records"]
    evidence = list(verification_evidence or [])
    if len(evidence) > MAX_EVIDENCE:
        raise HumanEscalationError(f"verification evidence exceeds cap {MAX_EVIDENCE}")
    decision_map = _normalize_mapping(decisions, name="decisions")
    defer_map = _normalize_mapping(safe_defers, name="safe_defers")
    choice_map_raw = human_choices or {}
    if not isinstance(choice_map_raw, dict):
        raise HumanEscalationError("human_choices must be an object keyed by finding index")
    choice_map: dict[int, str] = {}
    for raw_key, value in choice_map_raw.items():
        try:
            key = int(raw_key)
        except (TypeError, ValueError) as exc:
            raise HumanEscalationError("human_choices key must be an integer finding index") from exc
        if not isinstance(value, str) or not value.strip():
            raise HumanEscalationError("human choice must be a non-empty string")
        choice_map[key] = value

    seen_evidence_ids: set[str] = set()
    seen_probe_fingerprints: set[str] = set()
    evidence_by_index: dict[int, list[dict[str, Any]]] = {}
    for row in evidence:
        if not isinstance(row, dict):
            raise HumanEscalationError("verification evidence row must be an object")
        _validate_evidence_row(row, finding_count=len(records))
        if row["evidence_id"] in seen_evidence_ids:
            raise HumanEscalationError("duplicate evidence_id")
        if row["probe_fingerprint"] in seen_probe_fingerprints:
            raise HumanEscalationError("equivalent/replayed probe fingerprint is forbidden")
        seen_evidence_ids.add(row["evidence_id"])
        seen_probe_fingerprints.add(row["probe_fingerprint"])
        evidence_by_index.setdefault(row["finding_index"], []).append(row)

    output_records: list[dict[str, Any]] = []
    counts = {key: 0 for key in sorted(ALLOWED_DISPOSITIONS)}
    for index, k0 in enumerate(records):
        if k0.get("classification") == "REVIEW_BLOCKED":
            disposition = "REVIEW_BLOCKED"
            output = {
                "finding_index": index,
                "source_id": k0["source_id"],
                "anchor_sha256": k0["anchor_sha256"],
                "anchor": k0["anchor"],
                "k0_classification": k0["classification"],
                "material_effect": _is_material(k0),
                "initial_routes": [],
                "recovered_escape_routes": [],
                "residual_routes": [],
                "verification_evidence_ids": [],
                "learned_facts": [],
                "decision": None,
                "safe_defer": None,
                "disposition": disposition,
                "reason_codes": ["UPSTREAM_REVIEW_BLOCKED"],
                "human_handoff": None,
                "semantic_correctness_decided": False,
                "evidence_drop_authority": "NONE",
            }
            output_records.append(output)
            counts[disposition] += 1
            continue

        initial_routes = list(dict.fromkeys(_k0_routes(k0) + recover_escape_routes(k0["anchor"])))
        active_routes = list(initial_routes)
        learned_facts: list[str] = []
        evidence_ids_for_finding: set[str] = set()
        exhaustion_search_observed = False
        for row in evidence_by_index.get(index, []):
            evidence_ids_for_finding.add(row["evidence_id"])
            learned_facts.extend(row["learned_facts"])
            route_id = row["route_id"]
            if route_id == EXHAUSTION_SEARCH_ROUTE:
                if row["opened_routes"]:
                    active_routes.extend(row["opened_routes"])
                elif not active_routes and row["outcome"] in {"OBSERVED", "REFUTED", "NON_DISCRIMINATING"}:
                    # A no-new-route search only proves exhaustion after all
                    # previously known routes have already been closed and their
                    # evidence has been folded into the current knowledge state.
                    exhaustion_search_observed = True
            else:
                if route_id not in active_routes and route_id not in row["opened_routes"]:
                    raise HumanEscalationError(
                        f"finding {index}: evidence route {route_id!r} was not an active or newly opened route"
                    )
            closeable_routes = set(active_routes) | set(row["opened_routes"])
            unknown_closures = [closed for closed in row["closed_routes"] if closed not in closeable_routes]
            if unknown_closures:
                raise HumanEscalationError(
                    f"finding {index}: cannot close routes that were never active: {unknown_closures}"
                )
            for closed in row["closed_routes"]:
                active_routes = [route for route in active_routes if route != closed]
            for opened in row["opened_routes"]:
                if opened not in active_routes:
                    active_routes.append(opened)
        active_routes = list(dict.fromkeys(active_routes))
        learned_facts = list(dict.fromkeys(learned_facts))

        decision = decision_map.get(index)
        if decision is not None:
            _validate_decision(decision, evidence_ids=evidence_ids_for_finding)
        safe_defer = defer_map.get(index)
        if safe_defer is not None:
            _validate_safe_defer(safe_defer, evidence_ids=evidence_ids_for_finding)
        elif not active_routes:
            safe_defer = _default_safe_defer(k0)

        material = _is_material(k0)
        human_choice = choice_map.get(index)
        if decision is not None:
            disposition = "AI_RESOLVE"
            reasons = ["DEFENSIBLE_EVIDENCE_BACKED_DECISION_EXISTS"]
        elif active_routes:
            disposition = "AI_CONTINUE"
            reasons = ["DISCRIMINATING_AI_SIDE_ROUTE_REMAINS"]
        elif safe_defer is not None:
            disposition = "WAIT_SAFE_DEFER"
            reasons = ["BOUNDED_SAFE_RECHECK_EXISTS"]
        elif not material:
            disposition = "WAIT_SAFE_DEFER"
            reasons = ["NO_MATERIAL_HUMAN_DECISION_REQUIRED"]
            safe_defer = {
                "trigger": "MATERIALITY_OR_SOURCE_CHANGE",
                "rationale": "Residual ambiguity is not material enough to justify immediate human attention.",
                "evidence_ids": sorted(evidence_ids_for_finding),
            }
        elif exhaustion_search_observed and human_choice:
            disposition = "HUMAN_NOW"
            reasons = ["KNOWLEDGE_INTEGRATED_AI_EXHAUSTION", "MATERIAL_RESIDUAL_HUMAN_CHOICE"]
        else:
            disposition = "HUMAN_CANDIDATE"
            reasons = ["MATERIAL_DEAD_END_NOT_YET_PROVEN_EXHAUSTED"]

        handoff = None
        if disposition == "HUMAN_NOW":
            handoff = {
                "tested_routes": sorted({row["route_id"] for row in evidence_by_index.get(index, [])}),
                "learned_facts": learned_facts,
                "residual_ambiguity": k0["anchor"],
                "why_ai_has_no_next_route": "All known routes are closed and a bounded search found no new discriminating route.",
                "material_human_choice": human_choice,
            }

        output = {
            "finding_index": index,
            "source_id": k0["source_id"],
            "anchor_sha256": k0["anchor_sha256"],
            "anchor": k0["anchor"],
            "k0_classification": k0["classification"],
            "material_effect": material,
            "initial_routes": initial_routes,
            "recovered_escape_routes": recover_escape_routes(k0["anchor"]),
            "residual_routes": active_routes,
            "verification_evidence_ids": sorted(evidence_ids_for_finding),
            "learned_facts": learned_facts,
            "decision": decision,
            "safe_defer": safe_defer,
            "disposition": disposition,
            "reason_codes": reasons,
            "human_handoff": handoff,
            "semantic_correctness_decided": False,
            "evidence_drop_authority": "NONE",
        }
        output_records.append(output)
        counts[disposition] += 1

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "input_triage_fingerprint": triage_fingerprint(triage_report),
        "input_record_count": len(records),
        "records": output_records,
        "audit": {
            "disposition_counts": counts,
            "attempt_count_is_exhaustion": False,
            "knowledge_integration_required": True,
            "human_now_requires_materiality": True,
            "human_now_requires_no_remaining_route": True,
            "human_now_requires_exhaustion_search": True,
            "human_now_requires_explicit_human_choice": True,
            "automatic_evidence_drop_enabled": False,
        },
        "docs_claim_status": "UNVERIFIED",
        "hidden_architecture_claim": "NONE",
        **AUTHORITY_NONE,
    }
    verify_escalation_report(report, triage_report=triage_report)
    return report


def verify_escalation_report(
    report: dict[str, Any], *, triage_report: dict[str, Any] | None = None
) -> None:
    if not isinstance(report, dict) or report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise HumanEscalationError("invalid escalation report schema")
    for key, value in AUTHORITY_NONE.items():
        if report.get(key) != value:
            raise HumanEscalationError(f"authority boundary violated: {key}")
    if report.get("docs_claim_status") != "UNVERIFIED":
        raise HumanEscalationError("K1 cannot verify documentation claims")
    if report.get("hidden_architecture_claim") != "NONE":
        raise HumanEscalationError("hidden architecture claim is forbidden")
    fp = report.get("input_triage_fingerprint")
    if not isinstance(fp, str) or not re.fullmatch(r"[0-9a-f]{64}", fp):
        raise HumanEscalationError("input_triage_fingerprint must be SHA-256 hex")
    records = report.get("records")
    if not isinstance(records, list) or report.get("input_record_count") != len(records):
        raise HumanEscalationError("K1 record cardinality mismatch")
    if triage_report is not None:
        verify_triage_report(triage_report)
        if triage_fingerprint(triage_report) != fp:
            raise HumanEscalationError("triage fingerprint mismatch")
        if len(triage_report["records"]) != len(records):
            raise HumanEscalationError("K1 did not preserve K0 cardinality")

    seen: set[int] = set()
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise HumanEscalationError("K1 record must be an object")
        if row.get("finding_index") != index or index in seen:
            raise HumanEscalationError("K1 finding identity/order mismatch")
        seen.add(index)
        if triage_report is not None:
            k0 = triage_report["records"][index]
            if row.get("source_id") != k0.get("source_id") or row.get("anchor_sha256") != k0.get("anchor_sha256"):
                raise HumanEscalationError("K1 source identity changed")
            if row.get("anchor") != k0.get("anchor"):
                raise HumanEscalationError("K1 exact anchor changed")
        if row.get("disposition") not in ALLOWED_DISPOSITIONS:
            raise HumanEscalationError("invalid K1 disposition")
        if row.get("semantic_correctness_decided") is not False:
            raise HumanEscalationError("K1 cannot decide semantic correctness")
        if row.get("evidence_drop_authority") != "NONE":
            raise HumanEscalationError("K1 cannot drop evidence")
        if not isinstance(row.get("residual_routes"), list):
            raise HumanEscalationError("K1 residual routes missing")
        disposition = row["disposition"]
        if disposition == "AI_CONTINUE" and not row["residual_routes"]:
            raise HumanEscalationError("AI_CONTINUE requires a residual route")
        if disposition == "AI_RESOLVE" and not row.get("decision"):
            raise HumanEscalationError("AI_RESOLVE requires a decision")
        if disposition == "WAIT_SAFE_DEFER" and not row.get("safe_defer"):
            raise HumanEscalationError("WAIT_SAFE_DEFER requires a bounded defer")
        if disposition == "HUMAN_NOW":
            if row["residual_routes"]:
                raise HumanEscalationError("HUMAN_NOW cannot retain an AI-side route")
            if not row.get("material_effect"):
                raise HumanEscalationError("HUMAN_NOW requires material effect")
            handoff = row.get("human_handoff")
            if not isinstance(handoff, dict):
                raise HumanEscalationError("HUMAN_NOW requires a human handoff packet")
            required_handoff = {
                "tested_routes",
                "learned_facts",
                "residual_ambiguity",
                "why_ai_has_no_next_route",
                "material_human_choice",
            }
            if set(handoff) != required_handoff:
                raise HumanEscalationError("incomplete HUMAN_NOW handoff packet")
            if EXHAUSTION_SEARCH_ROUTE not in handoff["tested_routes"]:
                raise HumanEscalationError("HUMAN_NOW requires bounded escape-route search evidence")
        if disposition == "HUMAN_CANDIDATE" and row.get("human_handoff") is not None:
            raise HumanEscalationError("HUMAN_CANDIDATE cannot masquerade as completed handoff")

    audit = report.get("audit")
    if not isinstance(audit, dict):
        raise HumanEscalationError("K1 audit missing")
    if audit.get("attempt_count_is_exhaustion") is not False:
        raise HumanEscalationError("attempt count cannot define exhaustion")
    if audit.get("knowledge_integration_required") is not True:
        raise HumanEscalationError("knowledge integration invariant missing")
    if audit.get("automatic_evidence_drop_enabled") is not False:
        raise HumanEscalationError("automatic evidence drop must remain disabled")


def escalation_fingerprint(report: dict[str, Any]) -> str:
    verify_escalation_report(report)
    return _sha256_text(_canonical(report))
