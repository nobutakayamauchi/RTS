from __future__ import annotations

import re
import unicodedata

from . import deep_readable as _deep


ABSTRACT_FILLER_MARKERS = (
    "構造",
    "設計",
    "本質",
    "重要です",
    "大切です",
    "最適化",
)

GENERIC_SUBJECT_MARKERS = (
    "多くの人は",
    "多くの人が",
    "現代人は",
    "誰もが",
    "みんなが",
    "一般的に",
)

AI_BOILERPLATE_MARKERS = (
    "いかがでしたでしょうか",
    "することが可能です",
    "することができます",
    "〜ではないでしょうか",
    "ではないでしょうか",
    "と言えるでしょう",
)

FORCED_LIST_PATTERNS = (
    re.compile(r"ポイントは\s*[三3]つ(?:です|あります)"),
    re.compile(r"理由は\s*[三3]つ(?:です|あります)"),
    re.compile(r"方法は\s*[三3]つ(?:です|あります)"),
)

COINED_LABEL_RE = re.compile(
    r"(?:これ|この状態|こうした状態|この現象|この問題)を[^。\n]{0,50}(?:と呼んでいます|と呼びます|と名付けています)"
)

SUMMARY_MARKERS = (
    "■ まとめ",
    "■まとめ",
    "最後にまとめると",
    "ここまでをまとめると",
)

CONCRETE_SIGNAL_RE = re.compile(
    r"(?:\d|円|%|％|時間|分|日|件|回|人|社|月|年|→|：|:|「|」|Excel|CSV|AI|X|BridgePatch|CapCut|Claude|GitHub)"
)

BULLET_RE = re.compile(r"^\s*(?:[-・●▪︎]|\d+[.．)]|[①-⑳])")


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    normalized = _norm(text)
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", normalized)
        if item.strip()
    ]


def _primary_text(packet: dict) -> str:
    return "\n".join(
        item.get("claim", "") for item in packet.get("verified_primary_info", [])
    )


def _abstract_filler_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        markers = [marker for marker in ABSTRACT_FILLER_MARKERS if marker in sentence]
        if not markers:
            continue
        if CONCRETE_SIGNAL_RE.search(sentence):
            continue
        if len(sentence) >= 90:
            continue
        findings.append(
            {
                "code": "ABSTRACT_WORD_WITHOUT_PAYLOAD",
                "severity": "REVIEW",
                "detail": sentence,
                "markers": markers,
            }
        )
    return findings


def _generic_subject_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    return [
        {
            "code": "GENERIC_OVERSIZED_SUBJECT",
            "severity": "REVIEW",
            "detail": marker,
        }
        for marker in GENERIC_SUBJECT_MARKERS
        if marker in normalized
    ]


def _boilerplate_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    findings = [
        {
            "code": "AI_BOILERPLATE_PHRASE",
            "severity": "REVIEW",
            "detail": marker,
        }
        for marker in AI_BOILERPLATE_MARKERS
        if marker in normalized
    ]
    for pattern in FORCED_LIST_PATTERNS:
        match = pattern.search(normalized)
        if match:
            findings.append(
                {
                    "code": "FORCED_LIST_FRAME",
                    "severity": "REVIEW",
                    "detail": match.group(0),
                }
            )
    return findings


def _summary_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    return [
        {
            "code": "REDUNDANT_SUMMARY_RISK",
            "severity": "REVIEW",
            "detail": marker,
        }
        for marker in SUMMARY_MARKERS
        if marker in normalized
    ]


def _bullet_escape_findings(draft: str) -> list[dict]:
    lines = [line.strip() for line in _norm(draft).splitlines() if line.strip()]
    if len(lines) < 10:
        return []
    bullet_count = sum(1 for line in lines if BULLET_RE.match(line))
    ratio = bullet_count / len(lines)
    if bullet_count >= 8 and ratio >= 0.45:
        return [
            {
                "code": "EXCESSIVE_BULLET_ESCAPE",
                "severity": "REVIEW",
                "detail": f"{bullet_count}/{len(lines)} non-empty lines are bullets",
            }
        ]
    return []


def _coined_label_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    primary = _norm(_primary_text(packet))
    findings: list[dict] = []
    for match in COINED_LABEL_RE.finditer(normalized):
        phrase = match.group(0)
        if phrase not in primary and not any(
            token and token in primary
            for token in re.findall(r"[「『]([^」』]+)[」』]", phrase)
        ):
            findings.append(
                {
                    "code": "MODEL_COINED_LABEL_RISK",
                    "severity": "BLOCK",
                    "detail": phrase,
                }
            )
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    """Add material-first and anti-AI-smell writing doctrine to the v0.5 packet."""
    packet = _deep.build_generation_packet(
        source,
        trusted_source_refs=trusted_source_refs,
    )
    packet["schema_version"] = "0.6"

    packet["material_first_policy"] = {
        "principle": "The model may organize material, but it may not manufacture material to make prose feel specific.",
        "available_material": [
            "verified external facts and exact numbers",
            "human-attested failures and lived scenes",
            "human-attested opinions and judgments",
            "specific tools, products, places, documents, and other proper nouns when evidence-bound or attested",
            "reader objections that are supplied or safely inferred as questions rather than claimed facts",
        ],
        "recipe_vs_ingredients": (
            "Writing rules are the recipe. Evidence, primary experience, target detail, numbers, failures, proper nouns, and opinions are the ingredients. A better recipe cannot compensate for missing ingredients."
        ),
        "no_padding_rule": (
            "When material is thin, shorten the article or request/flag missing material; do not pad with abstract nouns, generic advice, invented jargon, or fake specificity."
        ),
    }

    packet["anti_ai_smell_policy"] = {
        "abstract_word_rule": (
            "Words such as 構造, 設計, 本質, 重要, and 最適化 are allowed only when the sentence immediately says what concrete thing they refer to."
        ),
        "list_rule": (
            "Do not force 'three points' or a numbered list merely because it looks organized. Use a list only when the items are genuinely parallel and each item earns its place."
        ),
        "prose_rule": "If ordinary prose is clearer than bullets, write prose.",
        "summary_rule": (
            "Do not add a generic final summary that merely repeats the article. Close by paying off the opening, giving the one next action, or making the CTA natural."
        ),
        "subject_rule": (
            "Avoid unsupported giant subjects such as 多くの人 or 現代人. Name the actual target or describe the observed situation."
        ),
        "assertion_rule": (
            "Prefer a direct evidence-bound statement or clearly labeled opinion over reflexive hedging such as 〜ではないでしょうか."
        ),
        "coined_term_rule": (
            "Do not invent 'これを○○と呼びます' terminology. Source-originated self-labels such as an attested シムシティ化 may be preserved and explained."
        ),
        "compression_rule": (
            "Replace padded constructions such as 〜することが可能です with the shortest natural wording such as できます when meaning is preserved."
        ),
    }

    packet["specificity_policy"] = {
        "target_first": (
            "A specific reader changes what details matter. Do not write for everyone when the offer is for someone in a concrete situation."
        ),
        "specificity_without_hallucination": (
            "Specificity must come from evidence or human-attested material. If a useful number or proper noun is unavailable, do not invent one just to sound human."
        ),
        "translation_rule": (
            "When a verified technical number or concept can be translated into a familiar comparison without changing its meaning, use the comparison after the original fact."
        ),
    }

    packet["generation_constraints"].extend(
        [
            "Do not use abstract nouns such as 構造, 設計, 本質, 重要, or 最適化 as substitutes for missing content; immediately name the concrete object, action, condition, or trade-off they refer to.",
            "Do not force three-point lists, bullet lists, or a final summary for visual neatness. Structure must follow the material, not the other way around.",
            "Avoid unsupported giant subjects such as 多くの人, 現代人, or 誰もが; write to the configured target or the observed situation.",
            "Prefer direct natural Japanese over padded AI boilerplate such as 〜することが可能です or generic 〜ではないでしょうか hedging.",
            "Do not invent a named concept using 'これを○○と呼びます'. Preserve a coined label only when it exists in human-attested primary information, and explain it on first use when unfamiliar.",
            "If the available evidence and primary information cannot support three genuinely new concrete takeaways, do not fake them. Shorten, narrow, or surface the material gap.",
            "Use failure, exact experience, proper nouns, exact verified numbers, objections, and real opinion when available; these are content ingredients, not decorative style tokens.",
        ]
    )

    packet["human_gate"]["checks"].extend(
        [
            "If I delete words like 構造・設計・本質, does concrete meaning remain in the surrounding sentences?",
            "Are any bullet lists present because the ideas are genuinely parallel, or because the draft escaped into formatting?",
            "Does the ending add a payoff or next action instead of repeating the article as a generic summary?",
            "Did the draft use a giant subject such as 多くの人 without evidence or need?",
            "Can I name at least three concrete things this intended reader could genuinely say they learned from this article? If not, is the article too thin?",
            "Which sentences could only have come from my evidence, experience, failure, judgment, or specific context rather than from a generic model average?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    """Run v0.5 safety/comprehension audit plus deterministic AI-smell heuristics."""
    result = _deep.audit_draft(draft, packet)
    findings = [
        *result.get("findings", []),
        *_coined_label_findings(draft, packet),
        *_abstract_filler_findings(draft),
        *_generic_subject_findings(draft),
        *_boilerplate_findings(draft),
        *_summary_findings(draft),
        *_bullet_escape_findings(draft),
    ]
    blocked = any(item.get("severity") == "BLOCK" for item in findings)
    review_count = sum(1 for item in findings if item.get("severity") == "REVIEW")
    result["findings"] = findings
    result["status"] = "BLOCKED" if blocked else "HUMAN_REVIEW_REQUIRED"
    result["ai_smell_review_count"] = review_count
    result["ai_smell_gate"] = "REVIEW" if review_count else "CLEAN_BY_HEURISTIC"
    return result
