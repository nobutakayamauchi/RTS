from __future__ import annotations

import re
import unicodedata

from . import meteor_v09_gate as _r3
from .core import XArticleEngineError


PAIN_OPENING_KINDS = {"PAIN", "FAILURE"}
CONTRARIAN_HUMAN_KINDS = {"BELIEF", "OPINION"}

EVASION_MARKERS = (
    "BAN回避",
    "ステルス配信",
    "判定を回避",
    "検知を回避",
    "規制を回避",
    "ゼロ幅文字",
)

EVASION_OPERATION_RE = re.compile(
    r"(?:BAN回避|ステルス配信|判定を回避|検知を回避|規制を回避|ゼロ幅文字)"
    r"[^。\n]{0,80}(?:使う|使います|入れる|実装|構築|設定|送信|配信|追加|挿入|有効化)"
)

EVASION_NEGATION_MARKERS = (
    "しない",
    "使わない",
    "避ける",
    "避けて",
    "禁止",
    "推奨しない",
    "やめる",
    "問題",
    "危険",
    "規約",
    "ポリシー",
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _verified_primary(packet: dict, kinds: set[str]) -> list[dict]:
    return [
        item
        for item in packet.get("verified_primary_info", [])
        if item.get("kind") in kinds
    ]


def _contrarian_basis_is_valid(source: dict, packet: dict) -> bool:
    basis = source.get("counterpoint_basis")
    if not isinstance(basis, dict):
        return False

    kind = str(basis.get("kind", "")).strip().upper()
    source_ref = str(basis.get("source_ref", "")).strip()
    if not source_ref:
        return False

    if kind == "HUMAN_OPINION":
        return any(
            item.get("source_ref") == source_ref
            and item.get("kind") in CONTRARIAN_HUMAN_KINDS
            for item in packet.get("verified_primary_info", [])
        )

    if kind == "EVIDENCE":
        return any(
            item.get("source_ref") == source_ref
            for item in packet.get("verified_evidence", [])
        )

    return False


def _evasion_findings(draft: str) -> list[dict]:
    findings: list[dict] = []
    for sentence in _sentences(draft):
        present = [marker for marker in EVASION_MARKERS if marker in sentence]
        if not present:
            continue
        if any(marker in sentence for marker in EVASION_NEGATION_MARKERS):
            findings.append(
                {
                    "code": "PLATFORM_EVASION_LANGUAGE",
                    "severity": "REVIEW",
                    "detail": sentence,
                }
            )
            continue
        if EVASION_OPERATION_RE.search(sentence):
            findings.append(
                {
                    "code": "PLATFORM_EVASION_OPERATIONAL_INSTRUCTION",
                    "severity": "BLOCK",
                    "detail": sentence,
                }
            )
        else:
            findings.append(
                {
                    "code": "PLATFORM_EVASION_LANGUAGE",
                    "severity": "REVIEW",
                    "detail": sentence,
                }
            )
    return findings


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    if not isinstance(source, dict):
        raise XArticleEngineError("source must be an object")

    explicit_opening = source.get("opening_mode")
    packet = _r3.build_generation_packet(source, trusted_source_refs=trusted_source_refs)

    pain_anchors = _verified_primary(packet, PAIN_OPENING_KINDS)

    # Core v0.3 historically allowed ORIGIN to activate LIVED_PAIN. Round 4 narrows
    # the latest root: origin is useful story material, but it is not pain by itself.
    if packet.get("opening_mode") == "LIVED_PAIN" and not pain_anchors:
        if explicit_opening is not None:
            raise XArticleEngineError(
                "LIVED_PAIN in v0.9 requires human-attested PAIN or FAILURE; ORIGIN alone cannot authorize a pain opening"
            )
        packet["opening_mode"] = "RELATABLE"
        packet["lived_pain_anchors"] = []
        packet["narrative"]["sequence"] = [
            "reader_state",
            "evidence_if_available",
            "anticipated_objection",
            "cause",
            "solution",
            "stumbling_point",
            "one_action_today",
            "single_cta",
        ]
        packet["narrative"]["opening_doctrine"] = (
            "An attested origin may explain why the article exists, but do not manufacture pain from origin alone."
        )

    if packet.get("opening_mode") == "CONTRARIAN" and not _contrarian_basis_is_valid(source, packet):
        raise XArticleEngineError(
            "CONTRARIAN opening requires counterpoint_basis bound to verified evidence or a human-attested BELIEF/OPINION"
        )

    packet["schema_version"] = "0.9-meteor-r4"
    packet["opening_integrity_policy"] = {
        "lived_pain_rule": (
            "LIVED_PAIN requires an actual human-attested PAIN or FAILURE anchor. ORIGIN alone may explain causality but must not be converted into drama."
        ),
        "contrarian_rule": (
            "CONTRARIAN requires an explicit counterpoint_basis bound either to verified evidence or to human-attested BELIEF/OPINION."
        ),
        "anti_forcing_rule": (
            "Do not force a pain, proof, or contrarian opening merely because the reference corpus used one successfully. Opening mode follows available material."
        ),
    }
    packet["security_content_policy"]["platform_evasion_rule"] = (
        "Discussion of platform-evasion language requires review. Operational instructions to evade enforcement/detection are blocked from the latest article engine."
    )
    packet["generation_constraints"].extend(
        [
            "Do not treat ORIGIN as pain unless the human also attested PAIN or FAILURE. A neutral origin story must remain neutral.",
            "Do not manufacture a contrarian opening. Require an explicit evidence-bound or human-attested counterpoint basis.",
            "Do not provide operational instructions for BAN/detection/enforcement evasion. Discussion of such claims remains review-only and should favor compliant alternatives.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "Is the opening emotion actually present in PAIN/FAILURE primary information, or did the draft turn a neutral origin into drama?",
            "If the opening is contrarian, what exact evidence or human belief/opinion is the counterpoint based on?",
            "If platform-evasion language appears, is the article explaining/rejecting it rather than teaching how to evade enforcement?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _r3.audit_draft(draft, packet)

    # Replace r3's coarse evasion review with operational-vs-discussion classification.
    findings = [
        item
        for item in result.get("findings", [])
        if item.get("code") != "PLATFORM_EVASION_LANGUAGE"
    ]
    findings.extend(_evasion_findings(draft))

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
