from __future__ import annotations

import re
import unicodedata

from . import meteor_v09_final as _round2
from .core import XArticleEngineError


FRESHNESS_MARKERS = (
    "最新",
    "現在",
    "現時点",
    "最新版",
    "今の仕様",
    "今使える",
)

DATE_RE = re.compile(
    r"(?:20\d{2}[年/-](?:0?[1-9]|1[0-2])(?:[月/-](?:0?[1-9]|[12]\d|3[01])日?)?|"
    r"20\d{2}年(?:0?[1-9]|1[0-2])月時点|20\d{2}年時点)"
)

OUTCOME_CONTEXT = (
    "できます",
    "できる",
    "終わります",
    "終わる",
    "完了",
    "成功",
    "売れ",
    "伸び",
    "稼げ",
    "増え",
    "安全",
    "大丈夫",
    "保証",
    "無料",
    "返金",
    "追加料金",
)

UNIVERSAL_CAPABILITY_RE = re.compile(
    r"(?:誰でも|全員|どんな人でも|初心者でも)[^。\n]{0,35}(?:できます|できる|使えます|使える|完了できます)"
)

HARDCODED_SECRET_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b", re.I)
HARDCODED_SECRET_USE_RE = re.compile(r"(?:API\s*キー|key|認証)[^。\n]{0,50}(?:sk-[A-Za-z0-9_-]{8,})[^。\n]{0,40}(?:使|入力|設定|このまま)", re.I)

PLATFORM_EVASION_MARKERS = (
    "BAN回避",
    "BAN対策",
    "ステルス配信",
    "判定を回避",
    "検知を回避",
    "規制を回避",
    "ゼロ幅文字",
)

RISK_EVIDENCE_KINDS = {"RISK", "SAFETY", "POLICY"}


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _has_dated_verified_evidence(packet: dict) -> bool:
    return any(
        item.get("kind") == "TIMING" or DATE_RE.search(_norm(item.get("claim", "")))
        for item in packet.get("verified_evidence", [])
    )


def _has_risk_evidence(packet: dict) -> bool:
    return any(item.get("kind") in RISK_EVIDENCE_KINDS for item in packet.get("verified_evidence", []))


def _strict_freshness_findings(draft: str, packet: dict) -> list[dict]:
    normalized = _norm(draft)
    if not any(marker in normalized for marker in FRESHNESS_MARKERS):
        return []
    if _has_dated_verified_evidence(packet):
        return []
    return [
        {
            "code": "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE",
            "severity": "REVIEW",
            "detail": "current/latest wording requires dated verified evidence; an as_of label alone is not evidence",
        }
    ]


def _absolute_generalization_findings(draft: str, suppressed_markers: set[str]) -> list[dict]:
    findings = []
    for marker in suppressed_markers:
        for sentence in _sentences(draft):
            if marker not in sentence:
                continue
            if any(context in sentence for context in OUTCOME_CONTEXT):
                continue
            findings.append(
                {
                    "code": "ABSOLUTE_GENERALIZATION_LANGUAGE",
                    "severity": "REVIEW",
                    "detail": sentence,
                }
            )
    return findings


def _universal_capability_findings(draft: str) -> list[dict]:
    return [
        {
            "code": "UNIVERSAL_CAPABILITY_PROMISE",
            "severity": "REVIEW",
            "detail": match.group(0),
        }
        for match in UNIVERSAL_CAPABILITY_RE.finditer(_norm(draft))
    ]


def _hardcoded_secret_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    findings = []
    for sentence in _sentences(normalized):
        if not HARDCODED_SECRET_RE.search(sentence):
            continue
        if any(token in sentence for token in ("例", "ダミー", "placeholder", "プレースホルダー", "使わない", "禁止")):
            continue
        if HARDCODED_SECRET_USE_RE.search(sentence):
            findings.append(
                {
                    "code": "HARDCODED_SECRET_LITERAL_RISK",
                    "severity": "BLOCK",
                    "detail": sentence,
                }
            )
    return findings


def _platform_evasion_findings(draft: str) -> list[dict]:
    normalized = _norm(draft)
    present = sorted({marker for marker in PLATFORM_EVASION_MARKERS if marker in normalized})
    if not present:
        return []
    return [
        {
            "code": "PLATFORM_EVASION_LANGUAGE",
            "severity": "REVIEW",
            "detail": ", ".join(present),
        }
    ]


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _round2.build_generation_packet(source, trusted_source_refs=trusted_source_refs)

    if packet.get("risk_policy", {}).get("risk_level") == "HIGH" and not _has_risk_evidence(packet):
        raise XArticleEngineError(
            "HIGH-risk articles require at least one verified RISK/SAFETY/POLICY evidence claim; warning tone alone is not evidence"
        )

    packet["schema_version"] = "0.9-meteor-r3"
    packet["risk_policy"]["evidence_rule"] = (
        "HIGH-risk mode requires verified RISK/SAFETY/POLICY evidence. The engine may simplify verified risk, but may not invent a scary scenario to justify a stop gate."
    )
    packet["strong_language_policy"] = {
        "outcome_absolute": "BLOCK when unbound: e.g. 必ずできます / 絶対成功 / guaranteed completion.",
        "general_absolute": "REVIEW: e.g. everyone will hit this wall; do not silently convert a broad prediction into fact.",
        "safety_imperative": "ALLOW when it is genuinely protective: e.g. APIキーは絶対に共有しない / 権限は必ず確認する.",
    }
    packet["security_content_policy"] = {
        "hardcoded_secret_rule": "Do not normalize a reusable secret literal as a default credential or API key in a public tutorial.",
        "platform_evasion_rule": (
            "Language about BAN evasion, stealth sending, detection avoidance, or similar platform-evasion tactics requires human review and policy/terms verification; do not inherit it as a growth best practice."
        ),
    }
    packet["generation_constraints"].extend(
        [
            "Classify 必ず/絶対 by meaning: unbound outcome guarantees block; broad predictions require review; genuine safety prohibitions may stay strong.",
            "Do not use a reusable hard-coded secret/API key as the normal public setup path.",
            "Do not turn BAN evasion, stealth sending, detection avoidance, or similar platform-evasion tactics into default marketing optimization doctrine.",
            "In HIGH-risk mode, risk claims themselves must come from verified RISK/SAFETY/POLICY evidence; warning intensity is not evidence.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "Is a strong 必ず/絶対 sentence an outcome guarantee, a broad prediction, or a necessary safety prohibition?",
            "Does any tutorial publish a reusable secret literal or encourage a predictable default credential?",
            "Does any growth/safety advice rely on platform-evasion behavior rather than compliant operation?",
            "For HIGH-risk content, which verified evidence supports the actual risk being described?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _round2.audit_draft(draft, packet)

    filtered = []
    downgraded_absolute_markers: set[str] = set()
    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        # Recompute freshness using evidence only; round 1 could treat as_of as if it were evidence.
        if code == "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE":
            continue

        # v0.2's lexical 必ず/絶対 block is too broad. Keep true outcome promises blocked,
        # let round 2 suppress safety imperatives, and downgrade other broad uses to REVIEW.
        if code == "UNBOUND_STRONG_CLAIM" and detail in {"必ず", "絶対"}:
            matching_sentences = [sentence for sentence in _sentences(draft) if detail in sentence]
            if matching_sentences and not any(
                any(context in sentence for context in OUTCOME_CONTEXT)
                for sentence in matching_sentences
            ):
                downgraded_absolute_markers.add(detail)
                continue

        filtered.append(item)

    findings = [
        *filtered,
        *_strict_freshness_findings(draft, packet),
        *_absolute_generalization_findings(draft, downgraded_absolute_markers),
        *_universal_capability_findings(draft),
        *_hardcoded_secret_findings(draft),
        *_platform_evasion_findings(draft),
    ]

    deduped = []
    seen = set()
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
