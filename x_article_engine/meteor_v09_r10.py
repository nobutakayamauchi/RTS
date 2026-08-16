from __future__ import annotations

import re
import unicodedata

from . import meteor_v09_r9 as _r9
from . import core as _core


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


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _is_meta_rejection(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in META_REJECTION_MARKERS)


def _token_only_in_meta_rejection(draft: str, token: str) -> bool:
    normalized_token = _norm(token)
    matches = [sentence for sentence in _sentences(draft) if normalized_token in sentence]
    return bool(matches) and all(_is_meta_rejection(sentence) for sentence in matches)


def _exact_numeric_bound(token: str, packet: dict) -> bool:
    normalized_token = _norm(token)
    corpus = _norm(_core._bound_corpus(packet))
    pattern = re.compile(
        rf"(?<![{NUMERIC_COMPONENT_CLASS}]){re.escape(normalized_token)}(?![{NUMERIC_COMPONENT_CLASS}])"
    )
    return bool(pattern.search(corpus))


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


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _r9.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-meteor-r10"
    packet["numeric_binding_policy"] = {
        "principle": "Numeric evidence must match at numeric-token boundaries. A shorter number cannot borrow authority by being a substring of a larger verified number.",
        "examples": [
            "10,000円 does not bind 0円",
            "15分 does not bind 5分",
            "100人 does not bind 0人",
        ],
    }
    packet["meta_rejection_policy"] = {
        "principle": "A dangerous claim shown only as an example of wording the author rejects is not itself an asserted claim.",
        "examples": [
            "『30分で終わります』と書くのはやめます -> not a duration promise",
            "『100%できます』という表現は使いません -> not an outcome claim",
            "invented first-person biography shown only as something AI must not fabricate -> not asserted biography",
        ],
    }
    packet["generation_constraints"].extend(
        [
            "Never authorize a numeric claim merely because its digits are a substring of a larger verified number.",
            "When a risky sentence is shown only as wording to reject/avoid, audit its polarity before treating it as an asserted claim.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "数字の根拠が部分一致になっていないか？10,000円の証拠で0円を通すような誤結合がないか？",
            "悪い文章例として引用して否定している断言を、本文の主張として誤認していないか？",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _r9.audit_draft(draft, packet)
    findings: list[dict] = []

    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        # Recompute all numeric claims with exact numeric-token boundaries below.
        if code == "UNBOUND_NUMERIC_CLAIM":
            continue

        if code in {
            "UNBOUND_STRONG_CLAIM",
            "UNBOUND_IDENTITY_DETAIL",
            "UNBOUND_GUARANTEE_LANGUAGE",
            "ABSOLUTE_SAFETY_LANGUAGE",
            "OUTCOME_PROMISE_LANGUAGE",
            "UNIVERSAL_CAPABILITY_PROMISE",
            "SUPERLATIVE_OR_TOTALIZING_LANGUAGE",
        }:
            if detail and _token_only_in_meta_rejection(draft, detail):
                continue
            if not detail:
                continue
            matching = [sentence for sentence in _sentences(draft) if detail in sentence]
            if matching and all(_is_meta_rejection(sentence) for sentence in matching):
                continue

        findings.append(item)

    findings.extend(_numeric_binding_findings(draft, packet))

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
