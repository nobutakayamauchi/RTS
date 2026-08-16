from __future__ import annotations

import re
import unicodedata

from . import v09_hardened as _hardened
from . import core as _core


# ---- R9: CTA semantics -----------------------------------------------------

FIT_CHECK_ACTION_RE = re.compile(
    r"(?:無料(?:適合確認|制作可否確認)|無料で(?:適合|制作可否)を?確認)"
    r"[^。\n]{0,30}"
    r"(?:から始め|で始め|を使|を受け|へ進|はこちら|できます|できる|してみ|してください|しませんか)"
)

FIT_CHECK_NON_ACTION_RE = re.compile(
    r"(?:無料適合確認|無料制作可否確認)[^。\n]{0,25}"
    r"(?:という考え|という言葉|を説明|の意味|について書|について話)"
)


# ---- R10: numeric-boundary + rejected bad-example semantics ---------------

NUMERIC_COMPONENT_CLASS = r"0-9一二三四五六七八九十百千万億兆,.，．"

META_REJECTION_MARKERS = (
    "と書くのはやめ",
    "と書かない",
    "とは書かない",
    "という表現は使わない",
    "という表現は使いません",
    "という言い方は使わない",
    "という言い方は使いません",
    "という断言はしない",
    "という断言はしません",
    "と断言するのはやめ",
    "は危険な表現",
    "をAIに作らせてはいけません",
    "をAIに作らせてはいけない",
    "を捏造してはいけません",
    "を捏造してはいけない",
)


# ---- R11: numeric-context laundering --------------------------------------

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


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _reader_actions(draft: str) -> set[str]:
    actions: set[str] = set()
    for sentence in _hardened._sentences(draft):
        if _hardened._is_claim_negation(sentence) or _hardened._is_prohibition(sentence):
            continue
        for name, pattern in _hardened._base.CTA_ACTION_PATTERNS.items():
            if pattern.search(sentence):
                actions.add(name)
        if FIT_CHECK_ACTION_RE.search(sentence) and not FIT_CHECK_NON_ACTION_RE.search(sentence):
            actions.add("fit_check")
    return actions


def _is_meta_rejection(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in META_REJECTION_MARKERS)


def _token_only_in_meta_rejection(draft: str, token: str) -> bool:
    normalized_token = _norm(token)
    matches = [sentence for sentence in _sentences(draft) if normalized_token in sentence]
    return bool(matches) and all(_is_meta_rejection(sentence) for sentence in matches)


def _all_identity_risk_is_meta_rejected(draft: str) -> bool:
    identity_sentences = []
    for sentence in _sentences(draft):
        if any(pattern.search(sentence) for pattern in _core.IDENTITY_RISK_PATTERNS):
            identity_sentences.append(sentence)
    return bool(identity_sentences) and all(_is_meta_rejection(sentence) for sentence in identity_sentences)


def _exact_numeric_in_text(token: str, text: str) -> bool:
    normalized_token = _norm(token)
    normalized_text = _norm(text)
    pattern = re.compile(
        rf"(?<![{NUMERIC_COMPONENT_CLASS}]){re.escape(normalized_token)}(?![{NUMERIC_COMPONENT_CLASS}])"
    )
    return bool(pattern.search(normalized_text))


def _exact_numeric_bound(token: str, packet: dict) -> bool:
    return _exact_numeric_in_text(token, _core._bound_corpus(packet))


def _numeric_binding_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    findings: list[dict] = []
    seen: set[str] = set()
    for match in _core.NUMERIC_RE.finditer(normalized):
        token = _core._canonical_numeric(match.group(0), packet)
        if token in seen:
            continue
        seen.add(token)
        if _token_only_in_meta_rejection(draft, token):
            continue
        if not _exact_numeric_bound(token, packet):
            findings.append(
                {
                    "code": "UNBOUND_NUMERIC_CLAIM",
                    "severity": "BLOCK",
                    "detail": token,
                    "meteor_note": "numeric evidence requires a numeric-token boundary match; substring binding is not sufficient",
                }
            )
    return findings


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
        if not _exact_numeric_in_text(token, str(item.get("claim", ""))):
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
    return any(
        _exact_numeric_in_text(token, str(item.get("claim", "")))
        for item in packet.get("verified_primary_info", [])
    )


def _context_laundering_findings(draft: str, packet: dict) -> list[dict]:
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for sentence in _sentences(draft):
        if _is_meta_rejection(sentence):
            continue
        for match in _core.NUMERIC_RE.finditer(sentence):
            token = _core._canonical_numeric(match.group(0), packet)
            if not _exact_numeric_bound(token, packet):
                continue
            if _primary_context_bound(token, packet):
                continue

            draft_contexts = _numeric_contexts(sentence)
            if not draft_contexts:
                continue
            evidence_contexts = _evidence_contexts_for_numeric(token, packet)
            if not evidence_contexts or draft_contexts.intersection(evidence_contexts):
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
    packet = _hardened.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9"
    packet["meteor_status"] = "R11_SYNTHESIZED"
    packet["cta_semantics_policy"] = {
        "principle": "Count an action as a CTA when the reader is invited to take it, not merely when its noun appears.",
        "fit_check_examples": [
            "無料適合確認から始められます -> CTA",
            "無料適合確認を使ってください -> CTA",
            "無料適合確認という考え方を説明します -> not a CTA",
        ],
    }
    packet["numeric_binding_policy"] = {
        "principle": "Numeric evidence must match at numeric-token boundaries. A shorter number cannot borrow authority by being a substring of a larger verified number.",
    }
    packet["meta_rejection_policy"] = {
        "principle": "A dangerous claim shown only as wording the author rejects is not itself an asserted claim.",
    }
    packet["numeric_context_policy"] = {
        "principle": "Exact numeric equality is necessary but not sufficient; obvious commercial/result/timing category changes require review.",
        "deterministic_scope": "Fine-grained semantic equivalence remains a /human responsibility.",
    }
    packet["generation_constraints"].extend(
        [
            "Treat natural continuation language such as '無料適合確認から始められます' as a real CTA for multi-action review.",
            "Never authorize a numeric claim merely because its digits are a substring of a larger verified number.",
            "When risky wording is shown only as an example to reject, determine polarity before auditing it as an asserted claim.",
            "Do not reuse a verified number under a different claim category merely because the digits match exactly.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "CTAは命令形だけで数えていないか？『〜から始められます』のような自然な次行動も含めて確認したか？",
            "数字の根拠が部分一致になっていないか？10,000円の証拠で0円を通すような誤結合がないか？",
            "悪い文章例として引用して否定している断言を、本文の主張として誤認していないか？",
            "同じ数字でも意味を横流ししていないか？価格の数字を売上・節約額・顧客成果へ化けさせていないか？",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _hardened.audit_draft(draft, packet)
    findings: list[dict] = []
    all_identity_meta_rejected = _all_identity_risk_is_meta_rejected(draft)

    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        # Recompute CTA semantics and numeric evidence below.
        if code in {"MULTIPLE_COMMERCIAL_ACTIONS_RISK", "UNBOUND_NUMERIC_CLAIM"}:
            continue

        if code == "UNBOUND_IDENTITY_DETAIL" and all_identity_meta_rejected:
            continue

        if code in {
            "UNBOUND_STRONG_CLAIM",
            "UNBOUND_GUARANTEE_LANGUAGE",
            "ABSOLUTE_SAFETY_LANGUAGE",
            "OUTCOME_PROMISE_LANGUAGE",
            "UNIVERSAL_CAPABILITY_PROMISE",
            "SUPERLATIVE_OR_TOTALIZING_LANGUAGE",
        }:
            if detail and _token_only_in_meta_rejection(draft, detail):
                continue
            matching = [sentence for sentence in _sentences(draft) if detail and detail in sentence]
            if matching and all(_is_meta_rejection(sentence) for sentence in matching):
                continue

        findings.append(item)

    actions = _reader_actions(draft)
    if len(actions) >= 2:
        findings.append(
            {
                "code": "MULTIPLE_COMMERCIAL_ACTIONS_RISK",
                "severity": "REVIEW",
                "detail": ", ".join(sorted(actions)),
            }
        )

    findings.extend(_numeric_binding_findings(draft, packet))
    findings.extend(_context_laundering_findings(draft, packet))

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
