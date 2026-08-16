from __future__ import annotations

import re
import unicodedata

from . import v09 as _base
from .core import XArticleEngineError


CURRENT_MODES = {"CURRENT", "UPDATE"}
RISK_KINDS = {"RISK", "SAFETY", "POLICY"}

CLAIM_NEGATION_MARKERS = (
    "とは限りません",
    "とは限らない",
    "とは言いません",
    "とは言わない",
    "とは書けません",
    "とは書かない",
    "とは断言できません",
    "とは断言できない",
    "と断言しません",
    "と断言しない",
    "ではありません",
    "ではない",
    "わけではありません",
    "わけではない",
    "という意味ではありません",
    "という意味ではない",
    "とは約束できません",
    "とは約束できない",
    "保証しません",
    "保証しない",
)

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

NEGATED_FRESHNESS_PATTERNS = (
    re.compile(r"(?:最新|最新版|現在|現時点)[^。\n]{0,25}(?:ではありません|ではない|とは限りません|とは限らない)"),
    re.compile(r"(?:最新|最新版|現在|現時点)[^。\n]{0,25}(?:と断言しません|とは言いません|とは書けません)"),
)

NEGATED_ABSOLUTE_FREE_PATTERNS = (
    re.compile(r"(?:完全無料|ずっと無料|永久無料)[^。\n]{0,25}(?:ではありません|ではない|とは限りません|とは限らない)"),
    re.compile(r"(?:完全無料|ずっと無料|永久無料)[^。\n]{0,25}(?:とは言いません|とは書けません|とは約束できません)"),
)

NEGATED_SUPERLATIVE_PATTERNS = (
    re.compile(r"(?:世界一|唯一|最強)[^。\n]{0,25}(?:ではありません|ではない|とは限りません|とは限らない)"),
    re.compile(r"(?:世界一|唯一|最強)[^。\n]{0,25}(?:とは言いません|とは書けません|と断言しません)"),
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


def _is_claim_negation(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in CLAIM_NEGATION_MARKERS)


def _is_prohibition(sentence: str) -> bool:
    normalized = _norm(sentence)
    return any(marker in normalized for marker in PROHIBITION_MARKERS)


def _token_only_in_negated_sentences(draft: str, token: str) -> bool:
    matches = [sentence for sentence in _sentences(draft) if token in sentence]
    return bool(matches) and all(_is_claim_negation(sentence) for sentence in matches)


def _sentence_matches_any(sentence: str, patterns: tuple[re.Pattern, ...]) -> bool:
    return any(pattern.search(_norm(sentence)) for pattern in patterns)


def _all_marker_mentions_negated(draft: str, marker: str, patterns: tuple[re.Pattern, ...]) -> bool:
    matches = [sentence for sentence in _sentences(draft) if marker in sentence]
    return bool(matches) and all(
        _sentence_matches_any(sentence, patterns) or _is_claim_negation(sentence)
        for sentence in matches
    )


def _verified_by_ref(packet: dict) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for item in packet.get("verified_evidence", []):
        ref = str(item.get("source_ref", "")).strip()
        if ref:
            index.setdefault(ref, []).append(item)
    return index


def _normalize_ref_list(source: dict, field: str) -> list[str]:
    value = source.get(field, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise XArticleEngineError(f"{field} must be a list of source_ref strings")
    refs: list[str] = []
    for item in value:
        ref = str(item).strip()
        if not ref:
            raise XArticleEngineError(f"{field} must not contain empty refs")
        if ref not in refs:
            refs.append(ref)
    return refs


def _require_bound_refs(
    *,
    refs: list[str],
    verified_index: dict[str, list[dict]],
    allowed_kinds: set[str],
    field: str,
) -> list[dict]:
    if not refs:
        raise XArticleEngineError(f"{field} requires at least one explicitly bound verified evidence ref")
    bound: list[dict] = []
    for ref in refs:
        candidates = verified_index.get(ref, [])
        allowed = [item for item in candidates if item.get("kind") in allowed_kinds]
        if not allowed:
            kinds = "/".join(sorted(allowed_kinds))
            raise XArticleEngineError(
                f"{field} ref {ref!r} must resolve to verified evidence of kind {kinds}"
            )
        bound.extend(allowed)
    return bound


def _real_reader_actions(draft: str) -> set[str]:
    actions: set[str] = set()
    for sentence in _sentences(draft):
        if _is_claim_negation(sentence) or _is_prohibition(sentence):
            continue
        for name, pattern in _base.CTA_ACTION_PATTERNS.items():
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
    packet = _base.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
    verified_index = _verified_by_ref(packet)

    freshness_refs = _normalize_ref_list(source, "freshness_evidence_refs")
    if packet.get("freshness", {}).get("mode") in CURRENT_MODES:
        freshness_bound = _require_bound_refs(
            refs=freshness_refs,
            verified_index=verified_index,
            allowed_kinds={"TIMING"},
            field="freshness_evidence_refs",
        )
    else:
        freshness_bound = []

    risk_refs = _normalize_ref_list(source, "risk_evidence_refs")
    if packet.get("risk_policy", {}).get("risk_level") == "HIGH":
        risk_bound = _require_bound_refs(
            refs=risk_refs,
            verified_index=verified_index,
            allowed_kinds=RISK_KINDS,
            field="risk_evidence_refs",
        )
    else:
        risk_bound = []

    packet["schema_version"] = "0.9"
    packet["freshness"]["evidence_refs"] = freshness_refs
    packet["freshness"]["bound_evidence"] = freshness_bound
    packet["freshness"]["binding_rule"] = (
        "CURRENT/UPDATE is not authorized by an arbitrary dated fact; freshness_evidence_refs must bind verified TIMING evidence."
    )
    packet["risk_policy"]["evidence_refs"] = risk_refs
    packet["risk_policy"]["bound_evidence"] = risk_bound
    packet["risk_policy"]["binding_rule"] = (
        "HIGH-risk mode is not authorized by an unrelated risk fact; risk_evidence_refs must bind verified RISK/SAFETY/POLICY evidence."
    )
    packet["negated_claim_policy"] = {
        "principle": "Claims explicitly denied/quoted for criticism are not assertions merely because the same tokens appear."
    }
    packet["polarity_policy"] = {
        "principle": "Security, stop-gate, and CTA audits distinguish recommendation from prohibition/negation.",
        "front_gate_rule": "Negated risk words do not satisfy a HIGH-risk stop gate.",
        "cta_rule": "Rejected actions do not count as CTAs.",
    }
    packet["evidence_purpose_binding_policy"] = {
        "principle": "Verified evidence cannot be borrowed for an unrelated decision; bind it to its purpose.",
        "freshness": "freshness_evidence_refs -> verified TIMING evidence",
        "high_risk": "risk_evidence_refs -> verified RISK/SAFETY/POLICY evidence",
        "contrarian": "counterpoint_basis -> verified evidence or human-attested opinion/belief",
    }
    packet["generation_constraints"].extend(
        [
            "Do not audit an explicitly denied/criticized claim as if the author asserted it.",
            "Determine polarity before classifying security instructions and CTAs.",
            "Do not let negated safety wording satisfy a HIGH-risk front gate.",
            "CURRENT/UPDATE must bind freshness_evidence_refs to verified TIMING evidence.",
            "HIGH-risk mode must bind risk_evidence_refs to verified RISK/SAFETY/POLICY evidence.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "危険な断言を否定・批判するために引用した文まで、断言そのものとして扱っていないか？",
            "危険語・CTA語は実行を勧めているのか、それとも禁止・否定しているのか？",
            "freshness_evidence_refs は、本文の現在性そのものを本当に支えているか？",
            "risk_evidence_refs は、本文で警告している具体的な危険と本当に同じ危険を支えているか？",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _base.audit_draft(draft, packet)
    findings: list[dict] = []

    for item in result.get("findings", []):
        code = item.get("code")
        detail = str(item.get("detail", ""))

        if code in {"UNBOUND_NUMERIC_CLAIM", "UNBOUND_FUZZY_QUANT_CLAIM"}:
            if _token_only_in_negated_sentences(draft, detail):
                continue

        if code == "UNBOUND_IDENTITY_DETAIL" and _is_claim_negation(detail):
            continue

        if code == "UNBOUND_STRONG_CLAIM" and _token_only_in_negated_sentences(draft, detail):
            continue

        if code == "FRESHNESS_CLAIM_WITHOUT_DATED_EVIDENCE":
            freshness_tokens = [marker for marker in _base.FRESHNESS_MARKERS if marker in _norm(draft)]
            if freshness_tokens and all(
                _all_marker_mentions_negated(draft, marker, NEGATED_FRESHNESS_PATTERNS)
                for marker in freshness_tokens
            ):
                continue

        if code == "UNBOUND_ABSOLUTE_FREE_CLAIM":
            if _all_marker_mentions_negated(draft, detail, NEGATED_ABSOLUTE_FREE_PATTERNS):
                continue

        if code == "SUPERLATIVE_OR_TOTALIZING_LANGUAGE":
            present = [marker for marker in _base.SUPERLATIVE_MARKERS if marker in _norm(draft)]
            if present and all(
                _all_marker_mentions_negated(draft, marker, NEGATED_SUPERLATIVE_PATTERNS)
                for marker in present
            ):
                continue

        if code in {
            "UNBOUND_GUARANTEE_LANGUAGE",
            "ABSOLUTE_SAFETY_LANGUAGE",
            "OUTCOME_PROMISE_LANGUAGE",
            "UNIVERSAL_CAPABILITY_PROMISE",
            "ABSOLUTE_GENERALIZATION_LANGUAGE",
        }:
            matching = [
                sentence
                for sentence in _sentences(draft)
                if detail in sentence
                or any(
                    token in sentence
                    for token in re.findall(r"[一-龥ぁ-んァ-ンA-Za-z0-9%％]+", detail)
                )
            ]
            if matching and all(_is_claim_negation(sentence) for sentence in matching):
                continue

        if code in {"UNSAFE_PERMISSION_OR_SECURITY_BYPASS", "SECRET_TRANSFER_TO_MODEL_RISK"}:
            if _is_prohibition(detail):
                continue

        if code in {"MULTIPLE_COMMERCIAL_ACTIONS_RISK", "HIGH_RISK_WITHOUT_FRONT_STOP_GATE"}:
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

    normalized = _norm(draft)
    current_words = [marker for marker in _base.FRESHNESS_MARKERS if marker in normalized]
    if current_words:
        non_negated_current = [
            marker
            for marker in current_words
            if not _all_marker_mentions_negated(draft, marker, NEGATED_FRESHNESS_PATTERNS)
        ]
        if non_negated_current:
            clean = (
                packet.get("freshness", {}).get("mode") in CURRENT_MODES
                and bool(packet.get("freshness", {}).get("evidence_refs"))
            )
            if not clean:
                findings.append(
                    {
                        "code": "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE",
                        "severity": "REVIEW",
                        "detail": ", ".join(non_negated_current),
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
