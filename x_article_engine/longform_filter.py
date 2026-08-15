from __future__ import annotations

import re
import unicodedata

from . import ai_humanity as _humanity
from .core import XArticleEngineError


LONGFORM_REVIEW_THRESHOLD_CHARS = 2400
DENSE_PARAGRAPH_THRESHOLD_CHARS = 260
MIN_HEADINGS_FOR_LONGFORM_REVIEW = 3

HEADING_RE = re.compile(
    r"^\s*(?:■|#{1,4}\s+|【[^】]{1,80}】|[0-9０-９]+[.．]\s*[^\n]{1,80}$)"
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _nonempty_paragraphs(text: str) -> list[str]:
    normalized = _norm(text).replace("\r\n", "\n")
    return [item.strip() for item in re.split(r"\n\s*\n+", normalized) if item.strip()]


def _heading_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in _norm(text).splitlines()
        if line.strip() and HEADING_RE.match(line)
    ]


def _layout_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    normalized = _norm(draft)

    if len(normalized) >= LONGFORM_REVIEW_THRESHOLD_CHARS:
        headings = _heading_lines(normalized)
        if len(headings) < MIN_HEADINGS_FOR_LONGFORM_REVIEW:
            findings.append(
                {
                    "code": "LONGFORM_WEAK_SCAN_PATH",
                    "severity": "REVIEW",
                    "detail": (
                        f"long draft has only {len(headings)} recognizable headings; "
                        "check whether a mobile reader can follow the story by scanning headings"
                    ),
                }
            )

    for paragraph in _nonempty_paragraphs(normalized):
        if len(paragraph) > DENSE_PARAGRAPH_THRESHOLD_CHARS and "\n" not in paragraph:
            findings.append(
                {
                    "code": "DENSE_MOBILE_PARAGRAPH",
                    "severity": "REVIEW",
                    "detail": paragraph[:120],
                }
            )
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    """Add value-driven long-form and qualified-reader filtering doctrine to v0.6."""
    packet = _humanity.build_generation_packet(
        source,
        trusted_source_refs=trusted_source_refs,
    )
    packet["schema_version"] = "0.7"

    article_goal = source.get("article_goal", "QUALIFIED_READER_EDUCATION")
    if not isinstance(article_goal, str) or not article_goal.strip():
        raise XArticleEngineError("article_goal must be a non-empty string when provided")
    article_goal = article_goal.strip().upper()

    packet["longform_policy"] = {
        "article_goal": article_goal,
        "length_rule": (
            "Length follows useful material and the intended reader journey. Never stretch a short idea into a long article merely to look substantial."
        ),
        "qualified_reader_rule": (
            "A long article may intentionally prioritize the intended, highly interested reader over universal completion, but length alone never proves reader quality. Treat filtering as a strategy, not a guaranteed fact."
        ),
        "section_utility_rule": (
            "Every section must earn its space by adding at least one of: new evidence, lived detail, mechanism, example, objection handling, exception, decision rule, action, or offer bridge. Otherwise cut it."
        ),
        "mobile_rule": (
            "Write for a phone screen: short paragraphs, visible whitespace, and clear transitions. Avoid walls of text."
        ),
        "heading_rule": (
            "Headings should carry the argument. A scanning reader should understand the progression from the headings alone without headings becoming clickbait."
        ),
        "answer_first_rule": (
            "Within a section, prefer the answer or conclusion before the supporting reason when delaying the answer would create needless friction."
        ),
        "why_rule": (
            "When giving a method or instruction, explain why it matters so the reader can judge when to apply it without the author present."
        ),
        "cta_continuity_rule": (
            "Default to a CTA that feels like the next step of the same problem and mechanism. Do not interrupt the article with an unrelated commercial break."
        ),
        "ending_rule": (
            "End by paying off the opening, clarifying the one next action, or continuing naturally into the CTA. Do not add length with a redundant recap."
        ),
    }

    packet["longform_reader_journey"] = {
        "sequence": [
            "hook_or_lived_pain",
            "orientation",
            "first_clear_answer",
            "why_it_matters",
            "mechanism",
            "concrete_scene_or_example",
            "objection_and_exception",
            "deeper_implication",
            "callback_to_earlier_idea",
            "offer_as_continuation",
            "one_next_action",
        ],
        "selective_attrition": (
            "Do not contort the article to keep every possible reader. Make it easy for the intended reader to continue and acceptable for an uninterested reader to leave."
        ),
        "scan_path": (
            "Use headings as a second reading layer: someone scanning headings should still know where the article is going."
        ),
    }

    packet["reference_learning_boundary"].setdefault("not_imported_as_truth", []).extend(
        [
            "reference article like/save ratios",
            "reference article revenue and list conversion results",
            "a universal claim that long articles produce better buyers",
            "a fixed character count required for filtering",
        ]
    )

    packet["generation_constraints"].extend(
        [
            "Do not optimize for brevity by deleting necessary mechanism, evidence, objection handling, or explanation. Long-form is allowed when each section earns its space.",
            "Do not optimize for length either. If the useful material is exhausted, stop rather than padding.",
            "For long-form drafts, make headings informative enough that a scanning reader can follow the argument from headings alone.",
            "Use short mobile-friendly paragraphs and whitespace; avoid dense walls of text.",
            "Prefer a clear answer before its explanation when withholding the answer would only create friction.",
            "Whenever a method is important, explain why it works or why the reader should care; procedure without rationale is incomplete.",
            "Treat reader filtering as a strategic intent, not as a guaranteed causal claim about long articles or buyer quality.",
            "Place the CTA as the natural next step of the article's problem and mechanism rather than as an unrelated mid-article commercial interruption.",
        ]
    )

    packet["human_gate"]["checks"].extend(
        [
            "If this article is long, does every section add a new fact, lived detail, mechanism, example, objection, exception, decision rule, action, or offer bridge?",
            "Could I delete a section without losing anything? If yes, delete it.",
            "Can someone scan only the headings and still understand the article's progression?",
            "Does the mobile layout avoid walls of text and give the reader visual breathing room?",
            "Where I tell the reader what to do, did I also explain why it matters?",
            "Does the CTA feel like the next step of the same article rather than a commercial break?",
            "Am I claiming that length itself creates qualified buyers without evidence, or merely using length as an intentional filtering strategy?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    """Run v0.6 safety/humanity audit plus conservative long-form layout review."""
    result = _humanity.audit_draft(draft, packet)
    findings = [*result.get("findings", []), *_layout_findings(draft)]
    blocked = any(item.get("severity") == "BLOCK" for item in findings)
    review_count = sum(1 for item in findings if item.get("severity") == "REVIEW")
    result["findings"] = findings
    result["status"] = "BLOCKED" if blocked else "HUMAN_REVIEW_REQUIRED"
    result["longform_review_count"] = sum(
        1
        for item in findings
        if item.get("code") in {"LONGFORM_WEAK_SCAN_PATH", "DENSE_MOBILE_PARAGRAPH"}
    )
    result["review_count"] = review_count
    return result
