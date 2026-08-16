from __future__ import annotations

import re
import unicodedata

from . import meteor_v09_r6 as _r6
from . import v09 as _flat


PROHIBITION_MARKERS = (
    "てはいけません",
    "てはいけない",
    "ではいけません",
    "ではいけない",
    "ないでください",
    "禁止です",
    "禁止します",
    "やめてください",
    "避けてください",
    "推奨しません",
    "推奨しない",
    "書いてはいけません",
    "書いてはいけない",
)

POSITIVE_RISK_FRONT_PATTERNS = (
    re.compile(r"警告\s*[:：]"),
    re.compile(r"(?:危険|リスク)[^。\n]{0,30}(?:があります|がある|を伴|が高|が生じ|が発生|可能性があります|可能性がある)"),
    re.compile(r"対象外[^。\n]{0,45}(?:進めない|進まない|使わない|避けて|やめて)"),
    re.compile(r"(?:進め|使わ|実行し|共有し)[^。\n]{0,20}(?:ないでください|てはいけません|てはいけない)"),
    re.compile(r"(?:停止|中止)[^。\n]{0,20}(?:してください|して戻|する必要|します)"),
)

NEGATED_RISK_FRONT_PATTERNS = (
    re.compile(r"(?:危険|リスク)[^。\n]{0,20}(?:ではありません|ではない|はありません|はない)"),
    re.compile(r"(?:停止|中止)[^。\n]{0,15}(?:しないで|不要|する必要はない)"),
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _sentences(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", _norm(text))
        if item.strip()
    ]


def _is_prohibition(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in PROHIBITION_MARKERS)


def _real_reader_actions(draft: str) -> set[str]:
    actions: set[str] = set()
    for sentence in _sentences(draft):
        if _r6._is_claim_negation(sentence) or _is_prohibition(sentence):
            continue
        for name, pattern in _flat.CTA_ACTION_PATTERNS.items():
            if pattern.search(sentence):
                actions.add(name)
    return actions


def _has_positive_front_gate(draft: str) -> bool:
    front = _norm(draft)[:700]
    for sentence in _sentences(front):
        if any(pattern.search(sentence) for pattern in NEGATED_RISK_FRONT_PATTERNS):
            continue
        if any(pattern.search(sentence) for pattern in POSITIVE_RISK_FRONT_PATTERNS):
            return True
    return False


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _r6.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9-meteor-r7"
    packet["polarity_policy"] = {
        "principle": (
            "Operational and safety audits must distinguish recommendation from prohibition. "
            "A dangerous phrase inside 'do not do this' is not the same as an instruction to do it."
        ),
        "front_gate_rule": (
            "HIGH-risk front gates require an actual warning/stop/exclusion meaning; a negated phrase such as 'リスクはありません' cannot satisfy the gate."
        ),
        "cta_rule": (
            "A rejected action such as '登録してくださいとは言いません' is not a CTA and must not contribute to multi-CTA counting."
        ),
    }
    packet["generation_constraints"].extend(
        [
            "Determine polarity before classifying a security instruction: '送ってはいけません' is a prohibition, not a transfer instruction.",
            "Do not let a negated safety phrase such as 'リスクはありません' or '停止しないでください' satisfy a HIGH-risk front stop gate.",
            "Do not count an action that the draft explicitly refuses/rejects as a CTA.",
        ]
    )
    packet["human_gate"]["checks"].append(
        "危険語・CTA語が出ているだけで判定せず、その文は実行を勧めているのか、禁止・否定しているのかを確認したか？"
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _r6.audit_draft(draft, packet)
    findings: list[dict] = []

    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        if code in {"UNSAFE_PERMISSION_OR_SECURITY_BYPASS", "SECRET_TRANSFER_TO_MODEL_RISK"}:
            if _is_prohibition(detail):
                continue

        if code == "MULTIPLE_COMMERCIAL_ACTIONS_RISK":
            continue

        if code == "HIGH_RISK_WITHOUT_FRONT_STOP_GATE":
            continue

        findings.append(item)

    actions = _real_reader_actions(draft)
    if len(actions) >= 2:
        findings.append(
            {
                "code": "MULTIPLE_COMMERCIAL_ACTIONS_RISK",
                "severity": "REVIEW",
                "detail": ", ".join(sorted(actions)),
            }
        )

    if packet.get("risk_policy", {}).get("risk_level") == "HIGH" and not _has_positive_front_gate(draft):
        findings.append(
            {
                "code": "HIGH_RISK_WITHOUT_FRONT_STOP_GATE",
                "severity": "BLOCK",
                "detail": "high-risk guide lacks an affirmative warning/stop/exclusion meaning near the front; negated risk words do not count",
            }
        )

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
