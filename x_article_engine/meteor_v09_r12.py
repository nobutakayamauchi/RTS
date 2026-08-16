from __future__ import annotations

import re

from . import v09_final as _final


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
            for sentence in _final._sentences(draft)
            if any(pattern.search(sentence) for pattern in positive_patterns)
            and not _final._is_meta_rejection(sentence)
        ]
        if not positive_sentences:
            continue

        negative_patterns = NEGATIVE_EVIDENCE_PATTERNS[category]
        negative_evidence = [
            sentence
            for sentence in _final._sentences(evidence)
            if any(pattern.search(sentence) for pattern in negative_patterns)
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
    packet = _final.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-meteor-r12"
    packet["commercial_promise_polarity_policy"] = {
        "principle": (
            "A verified commercial term cannot authorize its semantic opposite merely because both sentences contain the same word. "
            "Negative/conditional terms outrank strengthened positive promises."
        ),
        "blocked_reversals": [
            "返金しない -> 全額返金します",
            "追加料金が発生する場合あり -> 追加料金なし",
            "保証しない -> 保証します",
            "上限あり -> 無制限",
            "永続提供を保証しない -> 永続利用できます",
        ],
    }
    packet["generation_constraints"].append(
        "Do not reverse a verified commercial limitation, exclusion, conditional fee, no-refund term, no-guarantee term, usage cap, or non-permanence statement into a stronger promise."
    )
    packet["human_gate"]["checks"].append(
        "販売条件の単語だけ一致して、意味が逆転していないか？『返金しない』を『返金する』、『追加料金あり得る』を『追加料金なし』へ強化していないか？"
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _final.audit_draft(draft, packet)
    findings = [*result.get("findings", []), *_promise_polarity_findings(draft, packet)]

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
