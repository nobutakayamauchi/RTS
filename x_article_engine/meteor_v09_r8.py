from __future__ import annotations

from . import meteor_v09_r7 as _r7
from .core import XArticleEngineError


CURRENT_MODES = {"CURRENT", "UPDATE"}
RISK_KINDS = {"RISK", "SAFETY", "POLICY"}


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


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    packet = _r7.build_generation_packet(source, trusted_source_refs=trusted_source_refs)
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

    packet["schema_version"] = "0.9-meteor-r8"
    packet["freshness"]["evidence_refs"] = freshness_refs
    packet["freshness"]["bound_evidence"] = freshness_bound
    packet["freshness"]["binding_rule"] = (
        "CURRENT/UPDATE is not authorized by any arbitrary dated fact. The brief must explicitly bind freshness_evidence_refs to verified TIMING evidence."
    )
    packet["risk_policy"]["evidence_refs"] = risk_refs
    packet["risk_policy"]["bound_evidence"] = risk_bound
    packet["risk_policy"]["binding_rule"] = (
        "HIGH-risk mode is not authorized by an unrelated risk fact. The brief must explicitly bind risk_evidence_refs to verified RISK/SAFETY/POLICY evidence."
    )
    packet["evidence_purpose_binding_policy"] = {
        "principle": "Evidence cannot be borrowed merely because it is verified; the brief must bind evidence to the decision it is supposed to authorize.",
        "freshness": "freshness_evidence_refs -> verified TIMING evidence",
        "high_risk": "risk_evidence_refs -> verified RISK/SAFETY/POLICY evidence",
        "contrarian": "counterpoint_basis -> verified evidence or human-attested opinion/belief",
    }
    packet["generation_constraints"].extend(
        [
            "Do not use an unrelated dated fact to authorize current/latest wording; currentness must be bound to freshness_evidence_refs.",
            "Do not use an unrelated risk fact to authorize a HIGH-risk warning; high-risk mode must be bound to risk_evidence_refs.",
        ]
    )
    packet["human_gate"]["checks"].extend(
        [
            "『最新』を支える freshness_evidence_refs は、その仕様・価格・UI・提供状況そのものの現在性を本当に支えているか？",
            "HIGH-risk の risk_evidence_refs は、本文で警告している具体的な危険と本当に同じ危険を支えているか？",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    result = _r7.audit_draft(draft, packet)

    # R7/flat freshness audit can clear wording merely because some dated evidence exists.
    # R8 re-applies purpose binding: current wording is only clean in CURRENT/UPDATE mode
    # with explicit freshness evidence refs.
    normalized = _r7._norm(draft)
    current_words = [marker for marker in _r7._flat.FRESHNESS_MARKERS if marker in normalized]
    if current_words:
        non_negated_current = [
            marker
            for marker in current_words
            if not _r7._r6._all_marker_mentions_negated(
                draft,
                marker,
                _r7._r6.NEGATED_FRESHNESS_PATTERNS,
            )
        ]
        if non_negated_current:
            clean = (
                packet.get("freshness", {}).get("mode") in CURRENT_MODES
                and bool(packet.get("freshness", {}).get("evidence_refs"))
            )
            if not clean and not any(
                item.get("code") == "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE"
                for item in result.get("findings", [])
            ):
                result.setdefault("findings", []).append(
                    {
                        "code": "FRESHNESS_CLAIM_WITHOUT_BOUND_EVIDENCE",
                        "severity": "REVIEW",
                        "detail": ", ".join(non_negated_current),
                    }
                )

    findings = result.get("findings", [])
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
