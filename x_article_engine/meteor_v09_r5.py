from __future__ import annotations

import re
import unicodedata

from . import meteor_v09_r4 as _r4


ABSTRACT_MARKERS = ("構造", "設計", "本質", "重要です", "大切です", "最適化")
GENERIC_SUBJECT_MARKERS = ("多くの人は", "多くの人が", "現代人は", "誰もが", "みんなが", "一般的に")

EVASION_NEGATION_FORMS = (
    "推奨しない",
    "推奨しません",
    "推奨していない",
    "推奨していません",
    "教えない",
    "教えません",
    "扱わない",
    "扱いません",
    "使わない",
    "実行しない",
    "避ける",
    "禁止",
    "問題がある",
    "危険",
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _generic_abstract_collision_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        subjects = [marker for marker in GENERIC_SUBJECT_MARKERS if marker in sentence]
        abstracts = [marker for marker in ABSTRACT_MARKERS if marker in sentence]
        if not subjects or not abstracts:
            continue
        findings.append(
            {
                "code": "ABSTRACT_WORD_WITHOUT_PAYLOAD",
                "severity": "REVIEW",
                "detail": sentence,
                "markers": abstracts,
                "meteor_note": (
                    "generic subject tokens such as 人 must not count as concrete material merely because the older concrete-signal regex contains a bare unit/character"
                ),
            }
        )
    return findings


def _is_evasion_rejection(detail: str) -> bool:
    normalized = _norm(detail)
    return any(marker in normalized for marker in EVASION_NEGATION_FORMS)


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _r4.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-meteor-r5"
    packet["anti_ai_smell_policy"]["generic_abstract_collision_rule"] = (
        "A generic subject such as 多くの人 must not make 構造/設計/本質 look concrete. Generic humanity words are not evidence payload."
    )
    packet["security_content_policy"]["evasion_negation_rule"] = (
        "Japanese negative forms, including polite forms such as 推奨しません, must be classified as rejection/discussion rather than operational evasion instructions."
    )
    packet["human_gate"]["checks"].append(
        "権限・安全・自動化の説明で、禁止や停止条件を危険な実行指示として誤読していないか？"
    )
    packet["generation_constraints"].extend(
        [
            "Do not count generic words such as 人 as concrete payload for an otherwise empty 構造/設計/本質 sentence.",
            "Recognize polite Japanese negative forms before classifying security/platform-evasion discussion as an operational instruction.",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _r4.audit_draft(draft, packet)

    findings: list[dict] = []
    for item in result.get("findings", []):
        if item.get("code") == "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION" and _is_evasion_rejection(
            str(item.get("detail", ""))
        ):
            findings.append(
                {
                    "code": "PLATFORM_EVASION_LANGUAGE",
                    "severity": "REVIEW",
                    "detail": item.get("detail", ""),
                }
            )
            continue
        findings.append(item)

    findings.extend(_generic_abstract_collision_findings(draft))

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
