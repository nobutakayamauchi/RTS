from __future__ import annotations

import re

from . import v09_hardened as _hardened


FIT_CHECK_ACTION_RE = re.compile(
    r"(?:無料(?:適合確認|制作可否確認)|無料で(?:適合|制作可否)を?確認)"
    r"[^。\n]{0,30}"
    r"(?:から始め|で始め|を使|を受け|へ進|はこちら|できます|できる|してみ|してください|しませんか)"
)

FIT_CHECK_NON_ACTION_RE = re.compile(
    r"(?:無料適合確認|無料制作可否確認)[^。\n]{0,25}"
    r"(?:という考え|という言葉|を説明|の意味|について書|について話)"
)


def _reader_actions(draft: str) -> set[str]:
    actions: set[str] = set()
    for sentence in _hardened._sentences(draft):
        if _hardened._is_claim_negation(sentence) or _hardened._is_prohibition(sentence):
            continue
        for name, pattern in _hardened._base.CTA_ACTION_PATTERNS.items():
            if pattern.search(sentence):
                actions.add(name)
        if FIT_CHECK_ACTION_RE.search(sentence) and not FIT_CHECK_NON_ACTION_RE.search(sentence):
            actions.add("fit_check")
    return actions


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _hardened.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    packet["schema_version"] = "0.9"
    packet["meteor_round"] = "R9_DOGFOOD_CTA"
    packet["cta_semantics_policy"] = {
        "principle": "Count an action as a CTA when the reader is invited to take it, not merely when the action's noun appears.",
        "fit_check_examples": [
            "無料適合確認から始められます -> CTA",
            "無料適合確認を使ってください -> CTA",
            "無料適合確認という考え方を説明します -> not a CTA",
        ],
    }
    packet["generation_constraints"].append(
        "Treat natural continuation language such as '無料適合確認から始められます' as an actual CTA when checking whether the draft asks for multiple competing actions."
    )
    packet["human_gate"]["checks"].append(
        "CTAは命令形だけで数えていないか？『〜から始められます』のような自然な次行動も含めて、読者に何個の行動を求めているか確認したか？"
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _hardened.audit_draft(draft, packet)
    findings = [
        item
        for item in result.get("findings", [])
        if item.get("code") != "MULTIPLE_COMMERCIAL_ACTIONS_RISK"
    ]

    actions = _reader_actions(draft)
    if len(actions) >= 2:
        findings.append(
            {
                "code": "MULTIPLE_COMMERCIAL_ACTIONS_RISK",
                "severity": "REVIEW",
                "detail": ", ".join(sorted(actions)),
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
