from __future__ import annotations

import re
import unicodedata

from . import core as _core
from . import v09_hardened as _hardened


# Final v0.9 keeps only the behaviors that survived METEOR:
# - natural CTA counting
# - numeric token boundary binding
# - rejected-example polarity
# - obvious numeric context laundering review
# - verified commercial-term polarity protection

FIT_CHECK_ACTION_RE = re.compile(
    r"(?:無料(?:適合確認|制作可否確認)|無料で(?:適合|制作可否)を?確認)"
    r"[^。\n]{0,30}"
    r"(?:から始め|で始め|を使|を受け|へ進|はこちら|できます|できる|してみ|してください|しませんか)"
)
FIT_CHECK_NON_ACTION_RE = re.compile(
    r"(?:無料適合確認|無料制作可否確認)[^。\n]{0,25}"
    r"(?:という考え|という言葉|を説明|の意味|について書|について話)"
)

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

COMMERCIAL_MARKERS = (
    "価格", "料金", "税込", "月額", "費用", "設計書", "購入", "支払", "標準", "追加料金"
)
RESULT_MARKERS = (
    "売上", "売れ", "節約", "削減", "短縮", "増え", "減った", "減りました",
    "実績", "成果", "顧客", "フォロワー", "リスト", "獲得", "作業時間"
)
TIMING_MARKERS = ("営業日", "納期", "納品", "以内", "までに", "目安")

POSITIVE_PROMISE_PATTERNS = {
    "REFUND": (
        re.compile(r"(?:全額|一部)?返金[^。\n]{0,18}(?:します|いたします|できます|可能です|対応します)"),
    ),
    "NO_EXTRA_FEE": (
        re.compile(r"追加料金[^。\n]{0,18}(?:ありません|発生しません|かかりません|不要です)"),
    ),
    "GUARANTEE": (
        re.compile(r"(?:成果|結果|成功)?[^。\n]{0,10}保証[^。\n]{0,16}(?:します|いたします|できます|されます)"),
    ),
    "UNLIMITED": (
        re.compile(r"(?:利用|使用|回数|アクセス)?[^。\n]{0,10}無制限[^。\n]{0,18}(?:です|で利用|で使用|使え|利用でき)"),
    ),
    "PERMANENT": (
        re.compile(r"(?:永続的|永久)[^。\n]{0,20}(?:利用できます|使えます|提供します|アクセスできます|利用可能です)"),
    ),
}
NEGATIVE_EVIDENCE_PATTERNS = {
    "REFUND": (
        re.compile(r"返金[^。\n]{0,20}(?:行いません|しません|不可|できません|対応しません|対象外)"),
    ),
    "NO_EXTRA_FEE": (
        re.compile(r"追加料金[^。\n]{0,25}(?:発生する|発生します|かかる|必要|場合があります|場合がある)"),
    ),
    "GUARANTEE": (
        re.compile(r"保証[^。\n]{0,25}(?:しません|しない|できません|できない|するものではありません|いたしません)"),
    ),
    "UNLIMITED": (
        re.compile(r"(?:利用|使用|回数|アクセス)?[^。\n]{0,20}(?:上限|制限)[^。\n]{0,20}(?:あります|ある|設定|設け)"),
    ),
    "PERMANENT": (
        re.compile(r"(?:永続的|永久)[^。\n]{0,30}(?:保証しません|保証しない|保証するものではありません|ではありません|ではない)"),
    ),
}


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if part.strip()
    ]


def _bound_text(packet: dict) -> str:
    chunks = [
        str(packet.get("offer", "")),
        str(packet.get("target", "")),
        str(packet.get("pain", "")),
        str(packet.get("cta", "")),
    ]
    chunks.extend(str(item.get("claim", "")) for item in packet.get("verified_evidence", []))
    chunks.extend(str(item.get("claim", "")) for item in packet.get("verified_primary_info", []))
    return "\n".join(chunks)


def _primary_text(packet: dict) -> str:
    return "\n".join(
        str(item.get("claim", "")) for item in packet.get("verified_primary_info", [])
    )


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
    return any(marker in _norm(sentence) for marker in META_REJECTION_MARKERS)


def _token_only_in_meta_rejection(draft: str, token: str) -> bool:
    normalized_token = _norm(token)
    matches = [sentence for sentence in _sentences(draft) if normalized_token in sentence]
    return bool(matches) and all(_is_meta_rejection(sentence) for sentence in matches)


def _all_identity_risk_is_meta_rejected(draft: str) -> bool:
    risky: list[str] = []
    for sentence in _sentences(draft):
        if not any(marker in sentence for marker in _core.FIRST_PERSON_MARKERS):
            continue
        if any(marker in sentence for marker in _core.IDENTITY_RISK_MARKERS):
            risky.append(sentence)
    return bool(risky) and all(_is_meta_rejection(sentence) for sentence in risky)


def _numeric_tokens(text: str) -> list[str]:
    return [_norm(match.group(0)) for match in _core.NUMERIC_CLAIM_RE.finditer(_norm(text))]


def _exact_numeric_in_text(token: str, text: str) -> bool:
    pattern = re.compile(
        rf"(?<![{NUMERIC_COMPONENT_CLASS}]){re.escape(_norm(token))}(?![{NUMERIC_COMPONENT_CLASS}])"
    )
    return bool(pattern.search(_norm(text)))


def _numeric_binding_findings(draft: str, packet: dict) -> list[dict]:
    findings: list[dict] = []
    seen: set[str] = set()
    bound = _bound_text(packet)
    for token in _numeric_tokens(draft):
        if token in seen:
            continue
        seen.add(token)
        if _token_only_in_meta_rejection(draft, token):
            continue
        if not _exact_numeric_in_text(token, bound):
            findings.append(
                {
                    "code": "UNBOUND_NUMERIC_CLAIM",
                    "severity": "BLOCK",
                    "detail": token,
                    "meteor_note": "numeric evidence requires a token-boundary match; substring binding is not authority",
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


def _evidence_contexts(token: str, packet: dict) -> set[str]:
    contexts: set[str] = set()
    for item in packet.get("verified_evidence", []):
        if not _exact_numeric_in_text(token, str(item.get("claim", ""))):
            continue
        kind = str(item.get("kind", ""))
        if kind == "COMMERCIAL":
            contexts.add("COMMERCIAL")
        if kind in {"RESULT", "CASE_RESULT"}:
            contexts.add("RESULT")
        if kind == "TIMING":
            contexts.add("TIMING")
    return contexts


def _primary_binds_numeric(token: str, packet: dict) -> bool:
    return _exact_numeric_in_text(token, _primary_text(packet))


def _context_laundering_findings(draft: str, packet: dict) -> list[dict]:
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    bound = _bound_text(packet)
    for sentence in _sentences(draft):
        if _is_meta_rejection(sentence):
            continue
        for token in _numeric_tokens(sentence):
            if not _exact_numeric_in_text(token, bound) or _primary_binds_numeric(token, packet):
                continue
            draft_contexts = _numeric_contexts(sentence)
            evidence_contexts = _evidence_contexts(token, packet)
            if not draft_contexts or not evidence_contexts:
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


def _commercial_evidence_text(packet: dict) -> str:
    return "\n".join(
        str(item.get("claim", ""))
        for item in packet.get("verified_evidence", [])
        if item.get("kind") in {"COMMERCIAL", "POLICY", "SCOPE", "TIMING"}
    )


def _promise_polarity_findings(draft: str, packet: dict) -> list[dict]:
    evidence = _commercial_evidence_text(packet)
    findings: list[dict] = []
    for category, positive_patterns in POSITIVE_PROMISE_PATTERNS.items():
        positive_sentences = [
            sentence
            for sentence in _sentences(draft)
            if any(pattern.search(sentence) for pattern in positive_patterns)
            and not _is_meta_rejection(sentence)
            and not _hardened._is_claim_negation(sentence)
        ]
        if not positive_sentences:
            continue
        negative_evidence = [
            sentence
            for sentence in _sentences(evidence)
            if any(pattern.search(sentence) for pattern in NEGATIVE_EVIDENCE_PATTERNS[category])
        ]
        if not negative_evidence:
            continue
        for sentence in positive_sentences:
            findings.append(
                {
                    "code": "CONTRADICTS_VERIFIED_COMMERCIAL_TERM",
                    "severity": "BLOCK",
                    "detail": category,
                    "draft_sentence": sentence,
                    "verified_conflict": negative_evidence[0],
                }
            )
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _hardened.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9"
    packet["meteor_status"] = "R11_SYNTHESIZED"
    packet["release_status"] = "FINAL_SYNTHESIZED"
    packet["cta_semantics_policy"] = {
        "principle": "Count an action as a CTA when the reader is invited to take it, not merely when its noun appears."
    }
    packet["numeric_binding_policy"] = {
        "principle": "Numeric evidence must match at numeric-token boundaries; substring matches are not authority."
    }
    packet["meta_rejection_policy"] = {
        "principle": "Dangerous wording shown only as wording the author rejects is not itself an asserted claim."
    }
    packet["numeric_context_policy"] = {
        "principle": "Exact numeric equality is necessary but not sufficient; obvious commercial/result/timing category changes require review.",
        "deterministic_scope": "Fine-grained semantic equivalence remains a /human responsibility.",
    }
    packet["commercial_promise_polarity_policy"] = {
        "principle": "Verified limitations cannot authorize their semantic opposite.",
        "blocked_reversals": [
            "返金しない -> 返金する",
            "追加料金が発生する場合あり -> 追加料金なし",
            "保証しない -> 保証する",
            "上限あり -> 無制限",
            "永続保証なし -> 永続利用可能",
        ],
    }
    packet["generation_constraints"].extend(
        [
            "Treat natural continuation language such as '無料適合確認から始められます' as a real CTA for multi-action review.",
            "Never authorize a numeric claim because its digits are only a substring of a larger verified number.",
            "Determine polarity before auditing rejected bad-copy examples as asserted claims.",
            "Do not reuse a verified number under a different claim category merely because the digits match.",
            "Do not reverse verified commercial limitations into stronger promises.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "自然な次行動も含めてCTAが一つか？",
            "数字の根拠が部分一致や別用途への横流しになっていないか？",
            "否定・禁止している悪い文章例を本文の主張として誤認していないか？",
            "販売条件の意味を逆転・強化していないか？",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _hardened.audit_draft(draft, packet)
    findings: list[dict] = []
    all_identity_meta_rejected = _all_identity_risk_is_meta_rejected(draft)

    for item in result.get("findings", []):
        code = str(item.get("code", ""))
        detail = str(item.get("detail", ""))

        # These are recomputed below with the final semantics.
        if code in {"MULTIPLE_COMMERCIAL_ACTIONS_RISK", "UNBOUND_NUMERIC_CLAIM"}:
            continue
        if code == "UNBOUND_IDENTITY_DETAIL" and all_identity_meta_rejected:
            continue
        if code == "UNBOUND_FUZZY_QUANT_CLAIM" and detail and _token_only_in_meta_rejection(draft, detail):
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
    findings.extend(_promise_polarity_findings(draft, packet))

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
    result["meteor_v09_block_count"] = sum(
        1 for item in deduped if item.get("severity") == "BLOCK"
    )
    result["meteor_v09_gate"] = (
        "BLOCK" if blocked else ("REVIEW" if review_count else "CLEAN_BY_HEURISTIC")
    )
    return result
