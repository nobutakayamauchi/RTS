from __future__ import annotations

import re

from . import meteor_v09_r10 as _r10
from . import core as _core


COMMERCIAL_KINDS = {"COMMERCIAL"}
RESULT_KINDS = {"RESULT", "CASE_RESULT"}
TIMING_KINDS = {"TIMING"}

COMMERCIAL_MARKERS = (
    "価格",
    "料金",
    "税込",
    "月額",
    "費用",
    "設計書",
    "購入",
    "支払",
    "標準",
    "追加料金",
)

RESULT_MARKERS = (
    "売上",
    "売れ",
    "節約",
    "削減",
    "短縮",
    "増え",
    "減った",
    "減りました",
    "実績",
    "成果",
    "顧客",
    "フォロワー",
    "リスト",
    "獲得",
    "作業時間",
)

TIMING_MARKERS = (
    "営業日",
    "納期",
    "納品",
    "以内",
    "までに",
    "目安",
)


def _numeric_contexts(sentence: str) -> set[str]:
    contexts: set[str] = set()
    if any(marker in sentence for marker in COMMERCIAL_MARKERS):
        contexts.add("COMMERCIAL")
    if any(marker in sentence for marker in RESULT_MARKERS):
        contexts.add("RESULT")
    if any(marker in sentence for marker in TIMING_MARKERS):
        contexts.add("TIMING")
    return contexts


def _evidence_contexts_for_numeric(token: str, packet: dict) -> set[str]:
    contexts: set[str] = set()
    for item in packet.get("verified_evidence", []):
        claim = str(item.get("claim", ""))
        if not _r10._exact_numeric_bound(token, {**packet, "verified_primary_info": [], "offer": "", "target": "", "pain": "", "verified_evidence": [item]}):
            continue
        kind = item.get("kind")
        if kind in COMMERCIAL_KINDS:
            contexts.add("COMMERCIAL")
        if kind in RESULT_KINDS:
            contexts.add("RESULT")
        if kind in TIMING_KINDS:
            contexts.add("TIMING")
    return contexts


def _primary_context_bound(token: str, packet: dict) -> bool:
    for item in packet.get("verified_primary_info", []):
        claim = str(item.get("claim", ""))
        # Use the same numeric-token boundary rule against this single primary claim.
        temp = {
            **packet,
            "offer": "",
            "target": "",
            "pain": "",
            "verified_evidence": [],
            "verified_primary_info": [item],
        }
        if _r10._exact_numeric_bound(token, temp):
            return True
    return False


def _context_laundering_findings(draft: str, packet: dict) -> list[dict]:
    findings: list[dict] = []
    normalized = _r10._norm(draft)
    seen: set[tuple[str, str]] = set()

    for sentence in _r10._sentences(normalized):
        if _r10._is_meta_rejection(sentence):
            continue
        for match in _core.NUMERIC_RE.finditer(sentence):
            token = _core._canonical_numeric(match.group(0), packet)
            if not _r10._exact_numeric_bound(token, packet):
                continue
            if _primary_context_bound(token, packet):
                # First-person/lived numeric material can carry context that does not fit commercial/result/timing buckets.
                continue

            draft_contexts = _numeric_contexts(sentence)
            if not draft_contexts:
                continue
            evidence_contexts = _evidence_contexts_for_numeric(token, packet)
            if not evidence_contexts:
                continue
            if draft_contexts.intersection(evidence_contexts):
                continue

            key = (token, sentence)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "code": "NUMERIC_CONTEXT_REUSE_RISK",
                    "severity": "REVIEW",
                    "detail": token,
                    "draft_context": sorted(draft_contexts),
                    "evidence_context": sorted(evidence_contexts),
                    "sentence": sentence,
                }
            )
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _r10.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-meteor-r11"
    packet["numeric_context_policy"] = {
        "principle": "Exact numeric-token equality is necessary but not sufficient. A number verified as a price must not silently become a result, savings figure, follower count, or other claim category.",
        "deterministic_scope": "Only clear commercial/result/timing category changes are reviewed. Fine-grained semantic equivalence remains a /human responsibility.",
    }
    packet["generation_constraints"].append(
        "Do not reuse a verified number under a different claim category merely because the digits match exactly."
    )
    packet["human_gate"]["checks"].append(
        "同じ数字でも意味を横流ししていないか？価格の10,000円を売上・節約額・顧客成果の10,000円として使っていないか？"
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _r10.audit_draft(draft, packet)
    findings = [*result.get("findings", []), *_context_laundering_findings(draft, packet)]

    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for item in findings:
        key = (str(item.get("code")), str(item.get("severity")), str(item.get("detail")))
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    blocked = any(item.get("severity") == "BLOCK" for item in deduped)
    review_count = sum(1 for item in deduped if item.get("severity") == "REVIEW")
    result["findings"] = deduped
    result["status"] = "BLOCKED" if blocked else "HUMAN_REVIEW_REQUIRED"
    result["meteor_v09_review_count"] = review_count
    result["meteor_v09_block_count"] = sum(1 for item in deduped if item.get("severity") == "BLOCK")
    result["meteor_v09_gate"] = "BLOCK" if blocked else ("REVIEW" if review_count else "CLEAN_BY_HEURISTIC")
    return result
