from __future__ import annotations

from copy import deepcopy
import re
import unicodedata

from . import core as _core


DEFAULT_READER_MODEL = "GENERAL_NON_TECH"
EXPLANATION_WINDOW_CHARS = 180

DEFAULT_GENERAL_READER_GLOSSARY = (
    {
        "term": "CSV",
        "explanation": "Excelなどで開ける、表の形でデータを保存するファイル",
        "anchors": ("Excel", "表", "データ", "ファイル"),
        "min_anchor_matches": 2,
    },
    {
        "term": "デバッグ",
        "explanation": "プログラムの不具合の原因を探して直す作業",
        "anchors": ("不具合", "原因", "直"),
        "min_anchor_matches": 2,
    },
    {
        "term": "ログ",
        "explanation": "プログラムがいつ何をしたか残す記録",
        "anchors": ("プログラム", "記録", "残"),
        "min_anchor_matches": 2,
    },
    {
        "term": "API",
        "explanation": "サービスやプログラム同士が情報をやり取りするための仕組み",
        "anchors": ("情報", "やり取り", "仕組み"),
        "min_anchor_matches": 2,
    },
    {
        "term": "リポジトリ",
        "explanation": "プログラムのファイルと変更履歴をまとめて保管する場所",
        "anchors": ("ファイル", "変更", "履歴", "保管"),
        "min_anchor_matches": 2,
    },
    {
        "term": "プロンプト",
        "explanation": "AIに渡す指示やお願い",
        "anchors": ("AI", "指示"),
        "min_anchor_matches": 2,
    },
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise _core.XArticleEngineError(f"{field} must be a non-empty string when provided")
    return value.strip()


def _normalize_term(raw: object, field: str) -> dict:
    if not isinstance(raw, dict):
        raise _core.XArticleEngineError(f"{field} entries must be objects")
    term = _optional_text(raw.get("term"), f"{field}[].term")
    explanation = _optional_text(raw.get("explanation"), f"{field}[].explanation")
    if term is None or explanation is None:
        raise _core.XArticleEngineError(f"{field} entries require term and explanation")

    anchors_raw = raw.get("anchors")
    if anchors_raw is None:
        anchors = [explanation]
    else:
        if not isinstance(anchors_raw, (list, tuple)) or not anchors_raw:
            raise _core.XArticleEngineError(f"{field}[].anchors must be a non-empty list")
        anchors = []
        for item in anchors_raw:
            anchor = _optional_text(item, f"{field}[].anchors[]")
            if anchor is None:
                raise _core.XArticleEngineError(f"{field}[].anchors[] cannot be empty")
            anchors.append(anchor)

    minimum = raw.get("min_anchor_matches", min(2, len(anchors)))
    if not isinstance(minimum, int) or minimum < 1 or minimum > len(anchors):
        raise _core.XArticleEngineError(
            f"{field}[].min_anchor_matches must be between 1 and len(anchors)"
        )

    return {
        "term": term,
        "explanation": explanation,
        "anchors": anchors,
        "min_anchor_matches": minimum,
    }


def _compile_glossary(source: dict) -> list[dict]:
    merged: dict[str, dict] = {}
    for item in DEFAULT_GENERAL_READER_GLOSSARY:
        normalized = _normalize_term(deepcopy(item), "default_glossary")
        merged[_norm(normalized["term"])] = normalized

    custom = source.get("terms_to_explain", [])
    if not isinstance(custom, list):
        raise _core.XArticleEngineError("terms_to_explain must be a list")
    for item in custom:
        normalized = _normalize_term(item, "terms_to_explain")
        merged[_norm(normalized["term"])] = normalized
    return list(merged.values())


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    """Build the core packet and add general-reader comprehension policy.

    The wrapper keeps the evidence and publication boundaries in ``core`` intact,
    while adding a deterministic first-occurrence terminology contract.
    """
    packet = _core.build_generation_packet(
        source,
        trusted_source_refs=trusted_source_refs,
    )

    reader_model = _optional_text(
        source.get("reader_knowledge_level", DEFAULT_READER_MODEL),
        "reader_knowledge_level",
    )
    product_name = _optional_text(source.get("product_name"), "product_name")
    product_reading = _optional_text(source.get("product_reading"), "product_reading")
    if (product_name is None) != (product_reading is None):
        raise _core.XArticleEngineError(
            "product_name and product_reading must be provided together"
        )

    glossary = _compile_glossary(source)
    packet["schema_version"] = "0.4"
    packet["reader_model"] = {
        "knowledge_level": reader_model,
        "default_assumption": (
            "Assume a general non-technical reader unless the brief explicitly says otherwise."
        ),
    }
    packet["terminology_policy"] = {
        "explain_on_first_use": True,
        "placement": "same_sentence_or_immediately_after",
        "style": "short_plain_language_apposition_not_dictionary_entry",
        "when_in_doubt": "explain",
        "do_not_label_reader": True,
        "glossary": glossary,
    }
    packet["product_naming_policy"] = {
        "product_name": product_name,
        "product_reading": product_reading,
        "first_mention_format": (
            f"{product_name}（{product_reading}）"
            if product_name and product_reading
            else None
        ),
        "reading_occurrences": 1 if product_name else 0,
        "later_mentions": product_name,
    }

    packet["generation_constraints"].extend(
        [
            "Assume the reader may not know technical or industry-specific terms. Explain each unfamiliar term at its first occurrence in the same sentence or immediately after it.",
            "After an unfamiliar term has been explained once, use the short term normally; do not repeatedly re-explain it.",
            "Do not call the reader an IT novice, non-engineer, beginner, or similar label merely to justify an explanation; just explain the word naturally.",
            "If product_naming_policy.first_mention_format is set, use that exact product-name-plus-katakana-reading form at the first natural product introduction and use only the product name thereafter.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "Could a general non-technical reader understand every necessary unfamiliar word without leaving the article?",
            "Are unfamiliar terms explained exactly where they first appear, rather than much later?",
            "If a product reading is configured, is it shown only on the first product mention?",
        ]
    )
    return packet


def _product_name_findings(draft: str, packet: dict) -> list[dict]:
    policy = packet.get("product_naming_policy") or {}
    name = policy.get("product_name")
    reading = policy.get("product_reading")
    expected = policy.get("first_mention_format")
    if not name or not reading or not expected:
        return []

    normalized = _norm(draft)
    normalized_name = _norm(name)
    normalized_expected = _norm(expected)
    first = normalized.find(normalized_name)
    if first < 0:
        return [
            {
                "code": "MISSING_PRODUCT_INTRODUCTION",
                "severity": "BLOCK",
                "detail": expected,
            }
        ]

    findings = []
    if not normalized.startswith(normalized_expected, first):
        findings.append(
            {
                "code": "MISSING_PRODUCT_READING_ON_FIRST_USE",
                "severity": "BLOCK",
                "detail": expected,
            }
        )
    if normalized.count(normalized_expected) > 1:
        findings.append(
            {
                "code": "REPEATED_PRODUCT_READING",
                "severity": "BLOCK",
                "detail": expected,
            }
        )
    return findings


def _is_all_katakana_token(value: str) -> bool:
    return bool(value) and all(
        ("ァ" <= char <= "ヺ") or char in {"ー", "・"}
        for char in value
    )


def _is_all_ascii_word_token(value: str) -> bool:
    return bool(value) and all(char.isascii() and (char.isalnum() or char in {"_", "-"}) for char in value)


def _term_first_position(text: str, term: str) -> int:
    """Find a lexical term occurrence without matching inside a larger same-script token.

    This prevents short glossary terms such as ``ログ`` from firing inside
    ``プログラム`` or ``ブログ``. If a compound such as ``アクセスログ`` needs its
    own explanation, it should be listed explicitly as an article-specific term.
    """
    if _is_all_katakana_token(term):
        pattern = re.compile(rf"(?<![ァ-ヺー・]){re.escape(term)}(?![ァ-ヺー・])")
        match = pattern.search(text)
        return -1 if match is None else match.start()
    if _is_all_ascii_word_token(term):
        pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(term)}(?![A-Za-z0-9_-])", re.I)
        match = pattern.search(text)
        return -1 if match is None else match.start()
    return text.find(term)


def _term_findings(draft: str, packet: dict) -> list[dict]:
    policy = packet.get("terminology_policy") or {}
    if not policy.get("explain_on_first_use"):
        return []

    normalized = _norm(draft)
    findings = []
    for item in policy.get("glossary", []):
        term = _norm(item["term"])
        position = _term_first_position(normalized, term)
        if position < 0:
            continue
        window = normalized[position : position + EXPLANATION_WINDOW_CHARS]
        anchors = [_norm(anchor) for anchor in item.get("anchors", [])]
        matches = sum(1 for anchor in anchors if anchor in window)
        minimum = int(item.get("min_anchor_matches", 1))
        if matches < minimum:
            findings.append(
                {
                    "code": "UNEXPLAINED_TERM_ON_FIRST_USE",
                    "severity": "BLOCK",
                    "detail": item["term"],
                    "expected_explanation": item["explanation"],
                }
            )
    return findings


def audit_draft(draft: str, packet: dict) -> dict:
    """Run core evidence audit plus reader-comprehension checks."""
    result = _core.audit_draft(draft, packet)
    findings = [
        *result.get("findings", []),
        *_product_name_findings(draft, packet),
        *_term_findings(draft, packet),
    ]
    blocked = any(item.get("severity") == "BLOCK" for item in findings)
    result["findings"] = findings
    result["status"] = "BLOCKED" if blocked else "HUMAN_REVIEW_REQUIRED"
    return result
