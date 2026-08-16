from __future__ import annotations

import re
import unicodedata

from . import v09 as _flat


CLAIM_NEGATION_MARKERS = (
    "とは限りません",
    "とは限らない",
    "とは言いません",
    "とは言わない",
    "とは書けません",
    "とは書かない",
    "とは断言できません",
    "とは断言できない",
    "と断言しません",
    "と断言しない",
    "ではありません",
    "ではない",
    "わけではありません",
    "わけではない",
    "という意味ではありません",
    "という意味ではない",
    "とは約束できません",
    "とは約束できない",
    "保証しません",
    "保証しない",
)

NEGATED_FRESHNESS_PATTERNS = (
    re.compile(r"(?:最新|最新版|現在|現時点)[^。\n]{0,25}(?:ではありません|ではない|とは限りません|とは限らない)"),
    re.compile(r"(?:最新|最新版|現在|現時点)[^。\n]{0,25}(?:と断言しません|とは言いません|とは書けません)"),
)

NEGATED_ABSOLUTE_FREE_PATTERNS = (
    re.compile(r"(?:完全無料|ずっと無料|永久無料)[^。\n]{0,25}(?:ではありません|ではない|とは限りません|とは限らない)"),
    re.compile(r"(?:完全無料|ずっと無料|永久無料)[^。\n]{0,25}(?:とは言いません|とは書けません|とは約束できません)"),
)

NEGATED_SUPERLATIVE_PATTERNS = (
    re.compile(r"(?:世界一|唯一|最強)[^。\n]{0,25}(?:ではありません|ではない|とは限りません|とは限らない)"),
    re.compile(r"(?:世界一|唯一|最強)[^。\n]{0,25}(?:とは言いません|とは書けません|と断言しません)"),
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _is_claim_negation(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in CLAIM_NEGATION_MARKERS)


def _token_only_in_negated_sentences(draft: str, token: str) -> bool:
    matches = [sentence for sentence in _sentences(draft) if token in sentence]
    return bool(matches) and all(_is_claim_negation(sentence) for sentence in matches)


def _sentence_matches_any(sentence: str, patterns: tuple[re.Pattern, ...]) -> bool:
    return any(pattern.search(_norm(sentence)) for pattern in patterns)


def _all_marker_mentions_negated(draft: str, marker: str, patterns: tuple[re.Pattern, ...]) -> bool:
    matches = [sentence for sentence in _sentences(draft) if marker in sentence]
    return bool(matches) and all(_sentence_matches_any(sentence, patterns) or _is_claim_negation(sentence) for sentence in matches)


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _flat.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-meteor-r6"
    packet["negated_claim_policy"] = {
        "principle": (
            "A draft may quote or explicitly reject a dangerous claim without adopting it. "
            "The audit must judge whether the claim is asserted, not merely whether its tokens appear."
        ),
        "examples": [
            "必ず成功するとは限りません -> not a guarantee",
            "完全無料ではありません -> not a free promise",
            "保証します、とは書けません -> not a guarantee",
            "30分で終わるとは言いません -> not a duration promise",
            "これは最新版ではありません -> not a currentness claim",
        ],
    }
    packet["generation_constraints"].append(
        "Do not convert a claim being explicitly denied, quoted for criticism, or refused into an asserted factual/commercial promise merely because the same tokens appear."
    )
    packet["human_gate"]["checks"].append(
        "危険な断言を『否定・批判するために引用した文』まで、断言そのものとして扱っていないか？"
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _flat.audit_draft(draft, packet)
    findings: list[dict] = []

    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        if code in {"UNBOUND_NUMERIC_CLAIM", "UNBOUND_FUZZY_QUANT_CLAIM"}:
            if _token_only_in_negated_sentences(draft, detail):
                continue

        if code == "UNBOUND_IDENTITY_DETAIL" and _is_claim_negation(detail):
            continue

        if code == "UNBOUND_STRONG_CLAIM":
            if _token_only_in_negated_sentences(draft, detail):
                continue

        if code == "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE":
            freshness_tokens = [marker for marker in _flat.FRESHNESS_MARKERS if marker in _norm(draft)]
            if freshness_tokens and all(
                _all_marker_mentions_negated(draft, marker, NEGATED_FRESHNESS_PATTERNS)
                for marker in freshness_tokens
            ):
                continue

        if code == "UNBOUND_ABSOLUTE_FREE_CLAIM":
            if _all_marker_mentions_negated(draft, detail, NEGATED_ABSOLUTE_FREE_PATTERNS):
                continue

        if code == "SUPERLATIVE_OR_TOTALIZING_LANGUAGE":
            present = [marker for marker in _flat.SUPERLATIVE_MARKERS if marker in _norm(draft)]
            if present and all(
                _all_marker_mentions_negated(draft, marker, NEGATED_SUPERLATIVE_PATTERNS)
                for marker in present
            ):
                continue

        if code in {
            "UNBOUND_GUARANTEE_LANGUAGE",
            "ABSOLUTE_SAFETY_LANGUAGE",
            "OUTCOME_PROMISE_LANGUAGE",
            "UNIVERSAL_CAPABILITY_PROMISE",
            "ABSOLUTE_GENERALIZATION_LANGUAGE",
        }:
            matching = [
                sentence
                for sentence in _sentences(draft)
                if detail in sentence or any(token in sentence for token in re.findall(r"[一-龥ぁ-んァ-ンA-Za-z0-9%％]+", detail))
            ]
            if matching and all(_is_claim_negation(sentence) for sentence in matching):
                continue

        findings.append(item)

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
