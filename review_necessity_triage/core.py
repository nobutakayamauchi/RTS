from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from official_docs_intake.core import AUTHORITY_NONE, _chunk_blocks, _sha256_text
from semantic_claim_refinement.core import (
    refinement_fingerprint,
    verify_refinement_report,
)


class ReviewTriageError(ValueError):
    pass


REPORT_SCHEMA_VERSION = "review-necessity-triage-report/v1"
DA_LENS = "RETAIN_ATTENTION_DA_V1"
COUNTER_DA_LENS = "DEFER_ATTENTION_COUNTER_DA_V1"
ALLOWED_CLASSES = {"HUMAN_NOW", "HUMAN_LATER", "DEFER_LOW_VALUE", "REVIEW_BLOCKED"}
MAX_FINDINGS = 512


@dataclass(frozen=True)
class AttentionSignal:
    signal_id: str
    patterns: tuple[str, ...]
    impact: int
    causal_reach: int
    counter_importance: int
    causal_paths: tuple[str, ...]
    explicit_contract: bool = True


SIGNALS: tuple[AttentionSignal, ...] = (
    AttentionSignal(
        "execution_topology",
        (
            r"\bexecution model\b",
            r"\bexecution (?:flow|path|runtime|environment)\b",
            r"\bruntime\b",
            r"\bplanner\b",
            r"\bmanaged agents?\b",
            r"\borchestrat(?:e|es|ed|ion|ing)\b",
            r"\bdelegat(?:e|es|ed|ion|ing)\b",
            r"\bworkers?\b",
            r"\bsandbox\b",
            r"\bisolated (?:execution )?environment\b",
        ),
        5,
        5,
        4,
        ("H_ARCHITECTURE_CLASSIFICATION", "F_ENGINE_PROFILE", "G_PROBE_CAMPAIGN"),
    ),
    AttentionSignal(
        "reasoning_context_instructions",
        (
            r"\breasoning\b",
            r"\bcontext\b",
            r"\bsystem prompt\b",
            r"\bdeveloper instructions?\b",
            r"\binstruction(?:s| hierarchy)?\b",
            r"\bprompt engineering\b",
        ),
        5,
        5,
        4,
        ("F_ENGINE_PROFILE", "G_PROBE_CAMPAIGN", "CONTEXT_ROUTING"),
    ),
    AttentionSignal(
        "state_persistence",
        (
            r"\bstateful\b",
            r"\bstate persistence\b",
            r"\bpersist(?:s|ed|ence)?\b",
            r"\bpreserv(?:e|es|ed|ing)\b.{0,100}\b(?:calls?|requests?|turns?|state|reasoning)\b",
            r"\bacross calls\b",
            r"\bsession state\b",
            r"\bconversation state\b",
            r"\bcach(?:e|ed|ing)\b",
            r"\bmemory\b",
        ),
        4,
        5,
        3,
        ("F_ENGINE_PROFILE", "RESTART_STATE_STRATEGY", "G_PROBE_CAMPAIGN"),
    ),
    AttentionSignal(
        "tool_contract",
        (
            r"\btool(?:s| calling| use)?\b",
            r"\bfunction(?:s| calling)?\b",
            r"\bparallel\b",
            r"\bconcurrent(?:ly)?\b",
            r"\bcomputer use\b",
            r"\bcode execution\b",
            r"\bweb search\b",
            r"\bfile search\b",
        ),
        4,
        4,
        3,
        ("TOOL_STRATEGY", "F_ENGINE_PROFILE", "G_PROBE_CAMPAIGN"),
    ),
    AttentionSignal(
        "migration_identity",
        (
            r"\bmigrat(?:e|es|ed|ion|ing)\b",
            r"\bdeprecat(?:e|es|ed|ion|ing)\b",
            r"\bsunset\b",
            r"\blegacy models?\b",
            r"\brenam(?:e|es|ed|ing)\b",
            r"\bnew naming scheme\b",
            r"\bmodel ids?\b",
            r"\balias(?:es)?\b",
            r"\bsnapshot\b",
            r"\bendpoint\b",
        ),
        3,
        5,
        3,
        ("ENGINE_IDENTITY_ROUTING", "H_TRANSITION_CLASSIFICATION", "F_ENGINE_PROFILE"),
    ),
    AttentionSignal(
        "future_breaking_version_transition",
        (
            r"\bbreaking changes?\b",
            r"\bversion\b.{0,120}\b(?:change|changed|changes|update|updated|updates|replace|replaced|replaces)\b",
            r"\bnotice\b.{0,120}\b(?:version|latest|breaking change)\b",
        ),
        3,
        5,
        3,
        ("ENGINE_IDENTITY_ROUTING", "API_CONTRACT", "H_TRANSITION_CLASSIFICATION", "F_ENGINE_PROFILE"),
    ),
    AttentionSignal(
        "request_response_schema",
        (
            r"\brequests?\b",
            r"\bresponses?\b",
            r"\bschema\b",
            r"\bparameters?\b",
            r"\bfields?\b",
            r"\bheaders?\b",
            r"\bmax_input_tokens\b",
            r"\bmax_tokens\b",
            r"\bcapabilities\b",
        ),
        4,
        4,
        3,
        ("API_CONTRACT", "H_TRANSITION_CLASSIFICATION", "G_PROBE_CAMPAIGN"),
    ),
    AttentionSignal(
        "limits_usage",
        (
            r"\btokens?\b",
            r"\brate limits?\b",
            r"\bmaximum\b",
            r"\bminimum\b",
            r"\blimits?\b",
            r"\bpricing\b",
            r"\bprice\b",
            r"\bcost\b",
            r"\blatency\b",
            r"\bthroughput\b",
        ),
        3,
        4,
        3,
        ("LIMIT_BUDGETING", "F_ENGINE_PROFILE", "G_PROBE_CAMPAIGN"),
    ),
    AttentionSignal(
        "model_availability",
        (
            r"\bavailable models?\b",
            r"\bmodel availability\b",
            r"\bstable\b",
            r"\bpreview\b",
            r"\bavailable\b",
        ),
        2,
        3,
        2,
        ("ENGINE_IDENTITY_ROUTING", "H_TRANSITION_CLASSIFICATION"),
        explicit_contract=False,
    ),
    AttentionSignal(
        "performance_positioning",
        (
            r"\bperformance\b",
            r"\bquality\b",
            r"\befficien(?:cy|t)\b",
            r"\bfaster\b",
            r"\bcapability\b",
            r"\bcomplex tasks?\b",
        ),
        2,
        2,
        1,
        ("F_ENGINE_PROFILE",),
        explicit_contract=False,
    ),
)


PURE_NOISE_PATTERNS: tuple[str, ...] = (
    r"^\s*#+\s*[^\n]+$",
    r"^\s*new\s+(?:stable|preview)\s*$",
    r"\bmarkdown versions? of documentation pages?\b",
    r"\bthis guide introduces\b",
    r"\bsupport team\b",
    r"\bdiscord community\b",
    r"\bcontact support\b",
)

MARKETING_PATTERNS: tuple[str, ...] = (
    r"\bmost advanced\b",
    r"\bhighest available capability\b",
    r"\bquality and efficiency baseline\b",
    r"\bcomplex production workflows\b",
    r"\bstate[- ]of[- ]the[- ]art\b",
    r"\bfrontier\b",
    r"\bmost capable\b",
    r"\bmost intelligent\b",
)

DOCS_LINK_PATTERNS: tuple[str, ...] = (
    r"^\s*learn how to\b",
    r"^\s*see (?:the|our)\b",
    r"^\s*read more\b",
)

NORMATIVE_PATTERNS: tuple[str, ...] = (
    r"\bmust\b",
    r"\brequired\b",
    r"\brequires\b",
    r"\bunsupported\b",
    r"\bdeprecated\b",
    r"\bdeprecation\b",
    r"\bremoved\b",
    r"\brenamed\b",
    r"\bnow uses?\b",
    r"\bresponse includes\b",
    r"\bsupports? up to\b",
)

OPERATIONAL_GUIDANCE_PATTERNS: tuple[str, ...] = (
    r"\b(?:use|set|configure|provide|keep|select|choose|test|start with|switch|enable|disable|preserve|migrate)\b",
    r"\bdo not\b",
    r"\bshould\b",
    r"\brecommend(?:ed|s)?\b",
)

DESCRIPTIVE_CAPABILITY_PATTERNS: tuple[str, ...] = (
    r"\b(?:cost|price)[- ](?:efficient|effective|optimized|friendly)\b",
    r"\b(?:model|engine|product)\s+(?:is\s+)?(?:described|positioned|marketed|presented)\s+(?:as|for)\b",
    r"\b(?:described|positioned|marketed|presented)\s+for\b",
    r"\bmodel for\b",
    r"\bmodel that\b",
    r"\bengine with\b",
    r"\bfeaturing\b",
    r"\bcapabilit(?:y|ies)\b",
    r"\bvideo generation\b",
    r"\bimage generation\b",
    r"\brobotic agents?\b",
    r"\bstudio[- ]quality\b",
)

EXPECTED_BEHAVIOR_PATTERNS: tuple[str, ...] = (
    r"\bas expected\b",
    r"\bexpected behavior\b",
    r"\bby default\b",
    r"\bdefault behavior\b",
    r"\bcontinues? to\b",
    r"\bremains?\b",
    r"\bstill supports?\b",
    r"\bunchanged\b",
    r"\bnormal(?:ly)?\b",
)

CHANGE_TRIGGER_PATTERNS: tuple[str, ...] = (
    r"\bbreaking changes?\b",
    r"\bmigrat(?:e|es|ed|ion|ing)\b",
    r"\bdeprecat(?:e|es|ed|ion|ing)\b",
    r"\bremoved\b",
    r"\brenamed\b",
    r"\bnow uses?\b",
    r"\bchang(?:e|es|ed|ing)\b",
    r"\bupdat(?:e|es|ed|ing)\b",
    r"\breplac(?:e|es|ed|ing)\b",
    r"\bnew default\b",
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def _looks_like_short_heading(text: str) -> bool:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text)
    return 0 < len(words) <= 6 and not re.search(r"[.!?:;]", text)


def _is_concrete_operational_signal(anchor: str, signals: list[AttentionSignal]) -> bool:
    base = any(signal.explicit_contract and signal.impact >= 3 for signal in signals)
    if not base:
        return False
    normative = _matches_any(anchor, NORMATIVE_PATTERNS)
    operational = _matches_any(anchor, OPERATIONAL_GUIDANCE_PATTERNS)
    descriptive = _matches_any(anchor, DESCRIPTIVE_CAPABILITY_PATTERNS) or _matches_any(anchor, MARKETING_PATTERNS)
    docs_link = _matches_any(anchor, DOCS_LINK_PATTERNS) or bool(re.match(r"^\s*see\b", anchor, re.IGNORECASE))
    if _looks_like_short_heading(anchor) and not normative:
        return False
    if docs_link and not (normative or operational):
        return False
    if descriptive and not (normative or operational):
        return False
    return True


def _signal_matches(anchor: str) -> list[AttentionSignal]:
    matched: list[AttentionSignal] = []
    for signal in SIGNALS:
        if _matches_any(anchor, signal.patterns):
            matched.append(signal)
    return matched


def _expected_behavior_context(anchor: str) -> bool:
    return _matches_any(anchor, EXPECTED_BEHAVIOR_PATTERNS) and not _matches_any(anchor, CHANGE_TRIGGER_PATTERNS)


def _problem_solving_paths(anchor: str, signals: list[AttentionSignal], *, explicit: bool) -> list[str]:
    if not explicit:
        return []
    normative = _matches_any(anchor, NORMATIVE_PATTERNS)
    operational = _matches_any(anchor, OPERATIONAL_GUIDANCE_PATTERNS)
    transition = _matches_any(anchor, CHANGE_TRIGGER_PATTERNS)
    signal_ids = {signal.signal_id for signal in signals}
    paths: set[str] = set()
    if "future_breaking_version_transition" in signal_ids:
        paths.add("SCHEDULE_ENGINE_IDENTITY_REVALIDATION")
    if "migration_identity" in signal_ids and transition:
        paths.add("MIGRATE_OR_REMAP_ENGINE_IDENTITY")
    actionable_contract = normative or operational or transition
    if not actionable_contract:
        return sorted(paths)
    if "execution_topology" in signal_ids:
        paths.add("REVALIDATE_EXECUTION_STRATEGY")
    if "reasoning_context_instructions" in signal_ids:
        paths.add("ADJUST_OR_PROBE_REASONING_CONTEXT")
    if "state_persistence" in signal_ids:
        paths.add("ADJUST_OR_PROBE_STATE_STRATEGY")
    if "tool_contract" in signal_ids:
        paths.add("ADJUST_OR_PROBE_TOOL_STRATEGY")
    if "request_response_schema" in signal_ids:
        paths.add("ADAPT_OR_VERIFY_API_CONTRACT")
    if "limits_usage" in signal_ids:
        paths.add("RECALIBRATE_LIMIT_OR_BUDGET")
    return sorted(paths)


def _da_case(anchor: str) -> dict[str, Any]:
    signals = _signal_matches(anchor)
    pure_noise = _matches_any(anchor, PURE_NOISE_PATTERNS) or _looks_like_short_heading(anchor)
    marketing = _matches_any(anchor, MARKETING_PATTERNS)
    descriptive = _matches_any(anchor, DESCRIPTIVE_CAPABILITY_PATTERNS)
    docs_link = _matches_any(anchor, DOCS_LINK_PATTERNS) or bool(re.match(r"^\s*see\b", anchor, re.IGNORECASE))

    if signals:
        explicit = _is_concrete_operational_signal(anchor, signals)
        if (pure_noise or docs_link) and not explicit:
            impact, causal, factors, paths = 0, 0, ["non_actionable_surface"], []
        elif (marketing or descriptive) and not explicit:
            impact = min(2, max(signal.impact for signal in signals))
            causal = min(2, max(signal.causal_reach for signal in signals))
            factors = ["descriptive_positioning_with_bounded_signal"] + [signal.signal_id for signal in signals]
            paths = sorted({path for signal in signals for path in signal.causal_paths})
        else:
            impact = max(signal.impact for signal in signals)
            causal = max(signal.causal_reach for signal in signals)
            factors = [signal.signal_id for signal in signals]
            paths = sorted({path for signal in signals for path in signal.causal_paths})
    elif marketing:
        impact, causal, factors, paths, explicit = 1, 1, ["marketing_only"], [], False
    elif pure_noise or docs_link:
        impact, causal, factors, paths, explicit = 0, 0, ["non_actionable_surface"], [], False
    else:
        # J left this sentence unresolved, so retain a small uncertainty floor even
        # when the bounded signal registry cannot explain it yet.
        impact, causal, factors, paths, explicit = 1, 1, ["unclassified_unknown"], [], False

    importance = max(impact, causal)
    expected_behavior = _expected_behavior_context(anchor)
    solving_paths = _problem_solving_paths(anchor, signals, explicit=bool(explicit))
    return {
        "lens": DA_LENS,
        "impact": impact,
        "causal_reach": causal,
        "human_review_importance": importance,
        "explicit_contract_signal": explicit,
        "factors": factors,
        "causal_paths": paths,
        "expected_behavior_context": expected_behavior,
        "problem_solving_paths": solving_paths,
        "problem_solving_reach": min(5, max(2, causal)) if solving_paths else 0,
        "causal_reach_is_probability": False,
    }


def _counter_da_case(anchor: str) -> dict[str, Any]:
    signals = _signal_matches(anchor)
    pure_noise = _matches_any(anchor, PURE_NOISE_PATTERNS) or _looks_like_short_heading(anchor)
    marketing = _matches_any(anchor, MARKETING_PATTERNS)
    descriptive = _matches_any(anchor, DESCRIPTIVE_CAPABILITY_PATTERNS)
    docs_link = _matches_any(anchor, DOCS_LINK_PATTERNS) or bool(re.match(r"^\s*see\b", anchor, re.IGNORECASE))
    normative = _matches_any(anchor, NORMATIVE_PATTERNS)
    explicit = _is_concrete_operational_signal(anchor, signals)

    if explicit:
        importance = max(signal.counter_importance for signal in signals if signal.explicit_contract)
        reasons = ["concrete_contract_language_survives_skeptical_lens"]
        if normative:
            importance = max(importance, 4)
            reasons.append("normative_or_transition_wording")
        if pure_noise or docs_link or marketing:
            # Noise can weaken urgency, but cannot erase a concrete contract signal
            # in the same exact anchor.
            importance = max(2, importance - 1)
            reasons.append("surface_noise_present_but_not_dispositive")
    elif pure_noise:
        importance = 0
        reasons = ["heading_navigation_or_support_surface"]
    elif docs_link:
        importance = 1
        reasons = ["documentation_pointer_not_contract_by_itself"]
    elif marketing or descriptive:
        importance = 1
        reasons = ["marketing_or_positioning_without_concrete_contract"]
    elif signals:
        importance = max(signal.counter_importance for signal in signals)
        reasons = ["technical_but_not_yet_concrete_contract"]
    else:
        importance = 0
        reasons = ["no_bounded_operational_signal_found"]

    expected_behavior = _expected_behavior_context(anchor)
    solving_paths = _problem_solving_paths(anchor, signals, explicit=bool(explicit))
    return {
        "lens": COUNTER_DA_LENS,
        "human_review_importance": max(0, min(5, importance)),
        "reasons": reasons,
        "expected_behavior_context": expected_behavior,
        "problem_solving_paths": solving_paths,
        "problem_solving_reach": min(5, max(2, importance)) if solving_paths else 0,
        "docs_claim_is_not_observed_behavior": True,
    }


def _classify(da: dict[str, Any], counter: dict[str, Any], *, blocked: bool) -> tuple[str, list[str]]:
    if blocked:
        return "REVIEW_BLOCKED", ["UPSTREAM_COMPLETENESS_OR_RECOVERY_BLOCK"]

    gap = abs(int(da["human_review_importance"]) - int(counter["human_review_importance"]))
    da_solving = list(da.get("problem_solving_paths", []))
    counter_solving = list(counter.get("problem_solving_paths", []))
    expected_without_solution = bool(da.get("expected_behavior_context")) and bool(counter.get("expected_behavior_context")) and not da_solving and not counter_solving
    if expected_without_solution:
        max_importance = max(int(da["human_review_importance"]), int(counter["human_review_importance"]))
        if max_importance >= 2 or int(da["causal_reach"]) >= 2 or gap >= 2:
            return "HUMAN_LATER", ["EXPECTED_BEHAVIOR_NO_PROBLEM_SOLVING_PATH"]
        return "DEFER_LOW_VALUE", ["EXPECTED_BEHAVIOR_NO_PROBLEM_SOLVING_PATH"]
    reasons: list[str] = []
    if int(da["impact"]) >= 4:
        reasons.append("HIGH_IMPACT")
    if int(da["causal_reach"]) >= 4:
        reasons.append("FUTURE_CAUSAL_REACH")
    if gap >= 2 and max(int(da["human_review_importance"]), int(counter["human_review_importance"])) >= 3:
        reasons.append("MATERIAL_PERSPECTIVE_GAP")
    if int(counter["human_review_importance"]) >= 4:
        reasons.append("COUNTER_DA_STILL_FINDS_HIGH_REVIEW_VALUE")

    if reasons:
        return "HUMAN_NOW", reasons

    max_importance = max(int(da["human_review_importance"]), int(counter["human_review_importance"]))
    if max_importance >= 2 or int(da["causal_reach"]) >= 2 or gap >= 2:
        later_reasons: list[str] = []
        if int(da["causal_reach"]) >= 2:
            later_reasons.append("NONZERO_CAUSAL_PATH")
        if gap >= 2:
            later_reasons.append("PERSPECTIVE_GAP")
        if max_importance >= 2:
            later_reasons.append("TECHNICAL_RELEVANCE")
        return "HUMAN_LATER", later_reasons or ["PRESERVE_FOR_REVIEW"]

    return "DEFER_LOW_VALUE", ["LOW_VALUE_CONSENSUS"]


def _source_anchor_maps(refinement_report: dict[str, Any]) -> dict[str, dict[str, str]]:
    bundle = refinement_report.get("bundle")
    if not isinstance(bundle, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for source in bundle.get("sources", []):
        if not isinstance(source, dict) or not isinstance(source.get("source_id"), str):
            continue
        hashes: dict[str, str] = {}
        for anchor in _chunk_blocks(str(source.get("content", ""))):
            hashes.setdefault(_sha256_text(anchor), anchor)
        result[source["source_id"]] = hashes
    return result


def triage_refinement_report(refinement_report: dict[str, Any]) -> dict[str, Any]:
    verify_refinement_report(refinement_report)
    fp = refinement_fingerprint(refinement_report)
    audit = refinement_report.get("audit", {})
    unresolved = audit.get("unresolved", [])
    if not isinstance(unresolved, list):
        raise ReviewTriageError("J unresolved audit must be a list")
    if len(unresolved) > MAX_FINDINGS:
        raise ReviewTriageError(f"unresolved findings exceed cap {MAX_FINDINGS}")

    source_maps = _source_anchor_maps(refinement_report)
    globally_blocked = bool(audit.get("upstream_ambiguous_findings_truncated")) or bool(audit.get("fetch_failure_count"))
    records: list[dict[str, Any]] = []

    for index, finding in enumerate(unresolved):
        if not isinstance(finding, dict):
            raise ReviewTriageError("unresolved finding must be an object")
        source_id = finding.get("source_id")
        anchor_hash = finding.get("anchor_sha256")
        if not isinstance(source_id, str) or not isinstance(anchor_hash, str):
            raise ReviewTriageError("unresolved finding source/hash missing")
        anchor = source_maps.get(source_id, {}).get(anchor_hash)
        recovery_blocked = anchor is None
        if anchor is None:
            anchor = str(finding.get("preview") or "")

        da = _da_case(anchor) if anchor else {
            "lens": DA_LENS,
            "impact": 0,
            "causal_reach": 0,
            "human_review_importance": 0,
            "explicit_contract_signal": False,
            "factors": ["anchor_not_recovered"],
            "causal_paths": [],
            "expected_behavior_context": False,
            "problem_solving_paths": [],
            "problem_solving_reach": 0,
            "causal_reach_is_probability": False,
        }
        counter = _counter_da_case(anchor) if anchor else {
            "lens": COUNTER_DA_LENS,
            "human_review_importance": 0,
            "reasons": ["anchor_not_recovered"],
            "expected_behavior_context": False,
            "problem_solving_paths": [],
            "problem_solving_reach": 0,
            "docs_claim_is_not_observed_behavior": True,
        }
        gap = abs(int(da["human_review_importance"]) - int(counter["human_review_importance"]))
        classification, reason_codes = _classify(da, counter, blocked=globally_blocked or recovery_blocked)
        records.append({
            "finding_index": index,
            "source_id": source_id,
            "anchor_sha256": anchor_hash,
            "anchor": anchor,
            "j_reason": finding.get("reason"),
            "da": da,
            "counter_da": counter,
            "perspective_gap": gap,
            "classification": classification,
            "human_review_reason_codes": reason_codes,
            "semantic_correctness_decided": False,
            "evidence_drop_authority": "NONE",
        })

    counts = {key: 0 for key in sorted(ALLOWED_CLASSES)}
    causal_counts: dict[str, int] = {}
    disagreement_count = 0
    for record in records:
        counts[record["classification"]] += 1
        if int(record["perspective_gap"]) >= 2:
            disagreement_count += 1
        for path in record["da"].get("causal_paths", []):
            causal_counts[path] = causal_counts.get(path, 0) + 1

    status = "REVIEW_BLOCKED" if globally_blocked or any(r["classification"] == "REVIEW_BLOCKED" for r in records) else "READY"
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "input_refinement_fingerprint": fp,
        "provider": refinement_report.get("provider"),
        "product_surface": refinement_report.get("product_surface"),
        "generation": refinement_report.get("generation"),
        "input_unresolved_count": len(unresolved),
        "records": records,
        "audit": {
            "class_counts": counts,
            "perspective_disagreement_count": disagreement_count,
            "top_causal_paths": sorted(causal_counts.items(), key=lambda item: (-item[1], item[0])),
            "impact_and_causal_reach_are_distinct": True,
            "causal_reach_is_heuristic_not_probability": True,
            "problem_solving_actionability_is_distinct_from_importance": True,
            "lower_priority_is_not_semantic_correctness": True,
            "automatic_drop_enabled": False,
            "upstream_ambiguous_findings_truncated": bool(audit.get("upstream_ambiguous_findings_truncated")),
            "fetch_failure_count": int(audit.get("fetch_failure_count", 0) or 0),
        },
        "docs_claim_status": "UNVERIFIED",
        "hidden_architecture_claim": "NONE",
        **AUTHORITY_NONE,
    }
    verify_triage_report(report, refinement_report=refinement_report)
    return report


def verify_triage_report(report: dict[str, Any], *, refinement_report: dict[str, Any] | None = None) -> None:
    if not isinstance(report, dict):
        raise ReviewTriageError("triage report must be an object")
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ReviewTriageError("invalid triage schema")
    if report.get("status") not in {"READY", "REVIEW_BLOCKED"}:
        raise ReviewTriageError("invalid triage status")
    for key, value in AUTHORITY_NONE.items():
        if report.get(key) != value:
            raise ReviewTriageError(f"authority boundary violated: {key}")
    if report.get("docs_claim_status") != "UNVERIFIED":
        raise ReviewTriageError("triage cannot verify docs claims")
    if report.get("hidden_architecture_claim") != "NONE":
        raise ReviewTriageError("hidden architecture claim is forbidden")

    fp = report.get("input_refinement_fingerprint")
    if not isinstance(fp, str) or not re.fullmatch(r"[0-9a-f]{64}", fp):
        raise ReviewTriageError("input_refinement_fingerprint must be SHA-256 hex")

    records = report.get("records")
    if not isinstance(records, list):
        raise ReviewTriageError("triage records missing")
    if report.get("input_unresolved_count") != len(records):
        raise ReviewTriageError("unresolved finding count changed during triage")

    expected_pairs: list[tuple[str, str]] | None = None
    if refinement_report is not None:
        verify_refinement_report(refinement_report)
        if refinement_fingerprint(refinement_report) != fp:
            raise ReviewTriageError("refinement report fingerprint mismatch")
        unresolved = refinement_report.get("audit", {}).get("unresolved", [])
        expected_pairs = [(str(row.get("source_id")), str(row.get("anchor_sha256"))) for row in unresolved]
        if len(expected_pairs) != len(records):
            raise ReviewTriageError("triage did not preserve unresolved cardinality")

    seen_indices: set[int] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ReviewTriageError("triage record must be an object")
        finding_index = record.get("finding_index")
        if not isinstance(finding_index, int) or finding_index < 0 or finding_index >= len(records):
            raise ReviewTriageError("invalid finding_index")
        if finding_index in seen_indices:
            raise ReviewTriageError("duplicate finding_index")
        seen_indices.add(finding_index)
        if finding_index != index:
            raise ReviewTriageError("triage order changed")
        if expected_pairs is not None:
            actual_pair = (str(record.get("source_id")), str(record.get("anchor_sha256")))
            if actual_pair != expected_pairs[index]:
                raise ReviewTriageError("unresolved finding identity changed")

        anchor = record.get("anchor")
        anchor_hash = record.get("anchor_sha256")
        if not isinstance(anchor, str) or not isinstance(anchor_hash, str):
            raise ReviewTriageError("anchor identity missing")
        if anchor and _sha256_text(anchor) != anchor_hash:
            raise ReviewTriageError("exact anchor digest mismatch")

        da = record.get("da")
        counter = record.get("counter_da")
        if not isinstance(da, dict) or not isinstance(counter, dict):
            raise ReviewTriageError("both adversarial cases are required")
        if da.get("lens") != DA_LENS or counter.get("lens") != COUNTER_DA_LENS:
            raise ReviewTriageError("adversarial lens identity lost")
        if da.get("lens") == counter.get("lens"):
            raise ReviewTriageError("DA and Counter-DA cannot collapse to one lens")
        for key in ("impact", "causal_reach", "human_review_importance"):
            value = da.get(key)
            if not isinstance(value, int) or not 0 <= value <= 5:
                raise ReviewTriageError(f"invalid DA score: {key}")
        c_importance = counter.get("human_review_importance")
        if not isinstance(c_importance, int) or not 0 <= c_importance <= 5:
            raise ReviewTriageError("invalid Counter-DA importance")
        for lens_name, lens in (("DA", da), ("Counter-DA", counter)):
            if not isinstance(lens.get("expected_behavior_context"), bool):
                raise ReviewTriageError(f"{lens_name} expected behavior marker missing")
            solving_paths = lens.get("problem_solving_paths")
            if not isinstance(solving_paths, list) or any(not isinstance(path, str) or not path for path in solving_paths):
                raise ReviewTriageError(f"{lens_name} problem-solving paths invalid")
            solving_reach = lens.get("problem_solving_reach")
            if not isinstance(solving_reach, int) or not 0 <= solving_reach <= 5:
                raise ReviewTriageError(f"{lens_name} problem-solving reach invalid")
            if bool(solving_paths) != bool(solving_reach):
                raise ReviewTriageError(f"{lens_name} problem-solving path/reach mismatch")
        if da.get("causal_reach_is_probability") is not False:
            raise ReviewTriageError("causal reach cannot masquerade as probability")

        gap = record.get("perspective_gap")
        expected_gap = abs(int(da["human_review_importance"]) - int(counter["human_review_importance"]))
        if gap != expected_gap:
            raise ReviewTriageError("perspective gap mismatch")
        classification = record.get("classification")
        if classification not in ALLOWED_CLASSES:
            raise ReviewTriageError("invalid triage classification")
        if record.get("evidence_drop_authority") != "NONE":
            raise ReviewTriageError("triage cannot drop evidence")
        if record.get("semantic_correctness_decided") is not False:
            raise ReviewTriageError("triage cannot decide semantic correctness")

        if classification == "DEFER_LOW_VALUE":
            if int(da["impact"]) >= 4 or int(da["causal_reach"]) >= 4:
                raise ReviewTriageError("high-impact/high-causal item was deferred")
            if bool(da.get("explicit_contract_signal")):
                raise ReviewTriageError("explicit contract signal was deferred")
            if int(gap) >= 2:
                raise ReviewTriageError("material perspective disagreement was deferred")
        if classification != "REVIEW_BLOCKED":
            expected_without_solution = bool(da.get("expected_behavior_context")) and bool(counter.get("expected_behavior_context")) and not da.get("problem_solving_paths") and not counter.get("problem_solving_paths")
            if expected_without_solution and classification == "HUMAN_NOW":
                raise ReviewTriageError("expected behavior without a problem-solving path cannot be HUMAN_NOW")
            if int(da["causal_reach"]) >= 4 and not expected_without_solution and classification != "HUMAN_NOW":
                raise ReviewTriageError("high causal reach must be HUMAN_NOW")
            if int(da["impact"]) >= 4 and not expected_without_solution and classification != "HUMAN_NOW":
                raise ReviewTriageError("high impact must be HUMAN_NOW")
            if int(gap) >= 2 and max(int(da["human_review_importance"]), int(counter["human_review_importance"])) >= 3 and not expected_without_solution and classification != "HUMAN_NOW":
                raise ReviewTriageError("material high-value perspective gap must be HUMAN_NOW")

    audit = report.get("audit")
    if not isinstance(audit, dict):
        raise ReviewTriageError("triage audit missing")
    if audit.get("causal_reach_is_heuristic_not_probability") is not True:
        raise ReviewTriageError("causal reach semantics missing")
    if audit.get("problem_solving_actionability_is_distinct_from_importance") is not True:
        raise ReviewTriageError("problem-solving actionability semantics missing")
    if audit.get("automatic_drop_enabled") is not False:
        raise ReviewTriageError("automatic drop must remain disabled")
    if report["status"] == "READY" and any(r.get("classification") == "REVIEW_BLOCKED" for r in records):
        raise ReviewTriageError("READY report cannot contain blocked records")
    if report["status"] == "REVIEW_BLOCKED" and records and not any(r.get("classification") == "REVIEW_BLOCKED" for r in records):
        raise ReviewTriageError("blocked report must expose blocked records")


def triage_fingerprint(report: dict[str, Any]) -> str:
    verify_triage_report(report)
    return hashlib.sha256(_canonical(report).encode("utf-8")).hexdigest()
