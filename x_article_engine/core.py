from __future__ import annotations

from copy import deepcopy
import re
import unicodedata


class XArticleEngineError(ValueError):
    """Raised when an article brief is unsafe or incomplete for generation."""


ARTICLE_TYPES = {"HOW_TO", "STORY", "CASE_RESULT"}
OPENING_MODES = {"RELATABLE", "PROOF_FIRST", "CONTRARIAN"}
TOPIC_MODES = {"PROCEDURAL", "HABIT", "RELATIONSHIP", "BUSINESS"}
PRIMARY_INFO_KINDS = {"EXPERIENCE", "BELIEF", "FAILURE", "CHRONOLOGY", "OPINION"}

REQUIRED_FIELDS = (
    "offer",
    "target",
    "pain",
    "primary_info",
    "article_type",
    "cta",
    "evidence",
    "source_refs",
)

NUMERIC_CLAIM_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?|[一二三四五六七八九十百千万億〇零]+)"
    r"(?:円|%|％|時間|分|秒|営業日|日間|日|週間|週|ヶ月|か月|カ月|月間|年|件|社|人|回)"
)

FUZZY_QUANT_RE = re.compile(
    r"(?:数|何十|何百|何千)(?:時間|分|秒|日|週間|週|ヶ月|か月|カ月|月|年|件|社|人|回)"
    r"|(?:\d+|[一二三四五六七八九十百千万億〇零]+)倍"
)

FUZZY_QUANT_MARKERS = (
    "数年前",
    "何度も",
    "大半",
    "ほとんど",
)

IDENTITY_RISK_MARKERS = (
    "数年前",
    "以前",
    "過去",
    "これまで",
    "何度も",
    "長年",
    "普段",
    "仕事",
    "働",
    "担当",
    "顧客",
    "クライアント",
    "受講生",
    "見積もり",
    "現場",
)

FIRST_PERSON_MARKERS = ("私は", "僕は", "俺は", "私自身", "僕自身", "俺自身")

COMMERCIAL_RISK_MARKERS = (
    "追加料金",
    "追加費用",
    "返金",
    "全額返金",
    "返金保証",
    "キャンセル料",
    "違約金",
    "無制限",
    "永久",
    "絶対",
    "必ず",
    "100%",
)


def _norm(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise XArticleEngineError(f"{field} must be a non-empty string")
    return value.strip()


def _normalize_source_refs(items: object) -> dict[str, dict]:
    if not isinstance(items, list) or not items:
        raise XArticleEngineError("source_refs must be a non-empty list")

    index: dict[str, dict] = {}
    for raw in items:
        if not isinstance(raw, dict):
            raise XArticleEngineError("source_refs entries must be objects")
        source_id = _text(raw.get("id"), "source_refs[].id")
        if source_id in index:
            raise XArticleEngineError(f"duplicate source ref: {source_id}")
        status = _text(raw.get("status", "UNVERIFIED"), "source_refs[].status").upper()
        kind = _text(raw.get("kind", "SOURCE"), "source_refs[].kind").upper()
        index[source_id] = {"id": source_id, "status": status, "kind": kind}
    return index


def _normalize_evidence(
    items: object, source_index: dict[str, dict]
) -> tuple[list[dict], list[str]]:
    if not isinstance(items, list) or not items:
        raise XArticleEngineError("evidence must be a non-empty list")

    verified: list[dict] = []
    warnings: list[str] = []
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            raise XArticleEngineError("evidence entries must be objects")
        claim = _text(raw.get("claim"), "evidence[].claim")
        source_ref = _text(raw.get("source_ref"), "evidence[].source_ref")
        status = _text(raw.get("status", "UNVERIFIED"), "evidence[].status").upper()
        kind = _text(raw.get("kind", "FACT"), "evidence[].kind").upper()

        source = source_index.get(source_ref)
        source_verified = bool(source and source["status"] == "VERIFIED")
        if status == "VERIFIED" and source_verified:
            verified.append(
                {
                    "claim": claim,
                    "source_ref": source_ref,
                    "status": "VERIFIED",
                    "kind": kind,
                }
            )
        else:
            if source is None:
                reason = "source_ref is not declared"
            elif not source_verified:
                reason = "declared source is not VERIFIED"
            else:
                reason = "claim is not VERIFIED"
            warnings.append(f"evidence {index} excluded because {reason}: {claim}")

    if not verified:
        raise XArticleEngineError("no verified evidence remains")
    return verified, warnings


def _normalize_primary_info(items: object) -> tuple[list[dict], list[str]]:
    if not isinstance(items, list):
        raise XArticleEngineError("primary_info must be a list")

    accepted: list[dict] = []
    warnings: list[str] = []
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            raise XArticleEngineError("primary_info entries must be objects")
        claim = _text(raw.get("claim"), "primary_info[].claim")
        source_ref = _text(
            raw.get("source_ref", "human_attestation"),
            "primary_info[].source_ref",
        )
        attested = raw.get("attested", False)
        kind = _text(raw.get("kind", "EXPERIENCE"), "primary_info[].kind").upper()
        if kind not in PRIMARY_INFO_KINDS:
            raise XArticleEngineError(
                "primary_info[].kind must be EXPERIENCE, BELIEF, FAILURE, CHRONOLOGY, or OPINION"
            )
        if not isinstance(attested, bool):
            raise XArticleEngineError("primary_info[].attested must be boolean")
        if attested:
            accepted.append(
                {
                    "claim": claim,
                    "source_ref": source_ref,
                    "attested": True,
                    "kind": kind,
                }
            )
        else:
            warnings.append(
                f"primary_info {index} excluded because it is not human-attested: {claim}"
            )
    return accepted, warnings


def normalize_brief(source: dict) -> dict:
    """Normalize one X Article brief and bind every usable factual input."""
    if not isinstance(source, dict):
        raise XArticleEngineError("source must be an object")

    missing = [field for field in REQUIRED_FIELDS if field not in source]
    if missing:
        raise XArticleEngineError(f"missing required fields: {', '.join(missing)}")

    normalized = deepcopy(source)
    for field in ("offer", "target", "pain", "cta"):
        normalized[field] = _text(normalized[field], field)

    article_type = _text(normalized["article_type"], "article_type").upper()
    if article_type not in ARTICLE_TYPES:
        raise XArticleEngineError("article_type must be HOW_TO, STORY, or CASE_RESULT")
    normalized["article_type"] = article_type

    topic_mode = _text(normalized.get("topic_mode", "BUSINESS"), "topic_mode").upper()
    if topic_mode not in TOPIC_MODES:
        raise XArticleEngineError(
            "topic_mode must be PROCEDURAL, HABIT, RELATIONSHIP, or BUSINESS"
        )
    normalized["topic_mode"] = topic_mode

    source_index = _normalize_source_refs(normalized["source_refs"])
    verified, evidence_warnings = _normalize_evidence(normalized["evidence"], source_index)
    primary_info, primary_warnings = _normalize_primary_info(normalized["primary_info"])
    normalized["verified_source_refs"] = [
        item for item in source_index.values() if item["status"] == "VERIFIED"
    ]
    normalized["verified_evidence"] = verified
    normalized["verified_primary_info"] = primary_info
    normalized["warnings"] = [*evidence_warnings, *primary_warnings]

    if article_type == "STORY" and not primary_info:
        raise XArticleEngineError("STORY requires at least one human-attested primary_info item")

    if article_type == "CASE_RESULT":
        has_result = any(item["kind"] in {"RESULT", "CASE_RESULT"} for item in verified)
        if not has_result:
            raise XArticleEngineError("CASE_RESULT requires verified result evidence")

    opening_mode = normalized.get("opening_mode")
    if opening_mode is None:
        opening_mode = "PROOF_FIRST" if any(
            item["kind"] in {"RESULT", "CASE_RESULT"} for item in verified
        ) else "RELATABLE"
    opening_mode = _text(opening_mode, "opening_mode").upper()
    if opening_mode not in OPENING_MODES:
        raise XArticleEngineError(
            "opening_mode must be RELATABLE, PROOF_FIRST, or CONTRARIAN"
        )
    if opening_mode == "PROOF_FIRST" and not verified:
        raise XArticleEngineError("PROOF_FIRST requires verified evidence")
    normalized["opening_mode"] = opening_mode

    normalized["review_state"] = "REVIEW_REQUIRED" if normalized["warnings"] else "DRAFT"
    return normalized


def build_generation_packet(source: dict) -> dict:
    """Compile a safe, model-agnostic generation packet without publishing."""
    brief = normalize_brief(source)

    if brief["topic_mode"] == "PROCEDURAL":
        shape = "Use steps only where the reader is literally performing a procedure."
    elif brief["topic_mode"] == "HABIT":
        shape = "Prefer explanatory reading; do not turn ordinary life into a mechanical manual."
    elif brief["topic_mode"] == "RELATIONSHIP":
        shape = "Protect reader dignity; explain causes before tactics and never shame the reader."
    else:
        shape = "Use concrete business logic, scope, trade-offs, and reproducible reasoning."

    if brief["article_type"] == "HOW_TO":
        body_pattern = [
            "conclusion_or_overview",
            "method",
            "why_it_works",
            "stumbling_points",
            "conditions_and_limits",
        ]
    elif brief["article_type"] == "STORY":
        body_pattern = [
            "interesting_destination_or_failure",
            "previous_state",
            "turning_point",
            "what_changed",
            "lesson",
            "reader_connection",
        ]
    else:
        body_pattern = [
            "before",
            "after",
            "what_changed",
            "why_it_worked",
            "reproduction_conditions",
        ]

    return {
        "schema_version": "0.2",
        "offer": brief["offer"],
        "target": brief["target"],
        "pain": brief["pain"],
        "article_type": brief["article_type"],
        "topic_mode": brief["topic_mode"],
        "opening_mode": brief["opening_mode"],
        "cta": brief["cta"],
        "verified_source_refs": brief["verified_source_refs"],
        "verified_evidence": brief["verified_evidence"],
        "verified_primary_info": brief["verified_primary_info"],
        "narrative": {
            "top_level_order": ["EMOTION", "LOGIC", "EASY_NEXT_ACTION"],
            "body_pattern": body_pattern,
            "depth_layers": ["L1_CONCLUSION", "L2_REASON", "L3_CONDITIONS_EXCEPTIONS"],
            "sequence": [
                "reader_state",
                "evidence_if_available",
                "anticipated_objection",
                "cause",
                "solution",
                "stumbling_point",
                "one_action_today",
                "single_cta",
            ],
            "topic_shape": shape,
        },
        "voice_policy": {
            "preserve_attested_opinion": True,
            "preserve_attested_self_labels": True,
            "hedge_verified_facts": False,
            "generic_filler": "avoid",
            "strong_judgment_rule": (
                "Strong opinions are allowed when they are explicitly human-attested "
                "as BELIEF or OPINION; do not convert them into factual guarantees."
            ),
            "concrete_language_rule": (
                "Be vivid and specific using bound evidence and attested primary "
                "information; safety must not flatten the writer's voice."
            ),
        },
        "generation_constraints": [
            "Use only verified_evidence for externally checkable facts, prices, timing, scope, and results.",
            "Use first-person history, failure, emotion, belief, or chronology only from verified_primary_info.",
            "Never invent a number to satisfy a density or title rule; a numberless title is valid.",
            "Derived arithmetic is allowed only when every operand is verified and the derivation is explicit.",
            "Do not strengthen commercial or contractual wording beyond the verified claim.",
            "Do not present an invented label as established terminology.",
            "Explain specialist terms inline in plain language.",
            "Give useful substance instead of withholding the core method.",
            "Give exactly one practical next action and one CTA.",
            "Do not blame or rank the reader.",
            "Natural hybridization is allowed when strong human-attested primary information helps the article, but the selected article_type remains the dominant structure.",
            "Do not add chronology, job history, customer history, frequency, duration, or role details that are absent from verified_primary_info.",
            "The draft is not publishable until /human review passes.",
        ],
        "human_gate": {
            "required": True,
            "checks": [
                "Would I actually say this?",
                "Are all first-person details true and mine?",
                "Are all numbers, prices, timing, results, and scope evidence-bound?",
                "Did the draft invent emotion, biography, customer outcomes, or certainty?",
                "Does the CTA still match the offer and only ask for one next action?",
                "Did the rewrite preserve factual and risk boundaries?",
            ],
        },
        "publication_state": "BLOCKED_PENDING_HUMAN",
        "publication_authority": "USER_ONLY",
        "warnings": brief["warnings"],
        "review_state": brief["review_state"],
        "external_publication_performed": False,
    }


def _bound_text(packet: dict) -> str:
    chunks: list[str] = [packet["offer"], packet["target"], packet["pain"], packet["cta"]]
    chunks.extend(item["claim"] for item in packet["verified_evidence"])
    chunks.extend(item["claim"] for item in packet["verified_primary_info"])
    return "\n".join(chunks)


def _primary_text(packet: dict) -> str:
    return "\n".join(item["claim"] for item in packet["verified_primary_info"])


def _commercial_text(packet: dict) -> str:
    chunks = [packet["offer"], packet["cta"]]
    chunks.extend(
        item["claim"]
        for item in packet["verified_evidence"]
        if item["kind"] in {"COMMERCIAL", "TIMING", "SCOPE", "POLICY"}
    )
    return "\n".join(chunks)


def _numeric_claims(text: str) -> set[str]:
    return set(NUMERIC_CLAIM_RE.findall(_norm(text)))


def _fuzzy_quant_claims(text: str) -> set[str]:
    normalized = _norm(text)
    claims = set(FUZZY_QUANT_RE.findall(normalized))
    claims.update(marker for marker in FUZZY_QUANT_MARKERS if marker in normalized)
    return claims


def _sentences(text: str) -> list[str]:
    normalized = _norm(text)
    return [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])|\n+", normalized)
        if item.strip()
    ]


def _identity_findings(draft: str, packet: dict) -> list[str]:
    primary = _norm(_primary_text(packet))
    findings: list[str] = []
    for sentence in _sentences(draft):
        if not any(marker in sentence for marker in FIRST_PERSON_MARKERS):
            continue
        for marker in IDENTITY_RISK_MARKERS:
            if marker in sentence and marker not in primary:
                findings.append(sentence)
                break
    return sorted(set(findings))


def _commercial_findings(draft: str, packet: dict) -> list[str]:
    normalized_draft = _norm(draft)
    bound = _norm(_commercial_text(packet))
    return sorted(
        {
            marker
            for marker in COMMERCIAL_RISK_MARKERS
            if marker in normalized_draft and marker not in bound
        }
    )


def audit_draft(draft: str, packet: dict) -> dict:
    """Run a conservative pre-/human audit over a generated draft."""
    draft = _text(draft, "draft")
    if not isinstance(packet, dict):
        raise XArticleEngineError("packet must be an object")

    allowed_numeric = _numeric_claims(_bound_text(packet))
    observed_numeric = _numeric_claims(draft)
    unbound_numeric = sorted(observed_numeric - allowed_numeric)

    allowed_fuzzy = _fuzzy_quant_claims(_bound_text(packet))
    observed_fuzzy = _fuzzy_quant_claims(draft)
    unbound_fuzzy = sorted(observed_fuzzy - allowed_fuzzy)

    identity_details = _identity_findings(draft, packet)
    strengthened = _commercial_findings(draft, packet)

    findings: list[dict] = []
    for claim in unbound_numeric:
        findings.append(
            {"code": "UNBOUND_NUMERIC_CLAIM", "severity": "BLOCK", "detail": claim}
        )
    for claim in unbound_fuzzy:
        findings.append(
            {"code": "UNBOUND_FUZZY_QUANT_CLAIM", "severity": "BLOCK", "detail": claim}
        )
    for sentence in identity_details:
        findings.append(
            {"code": "UNBOUND_IDENTITY_DETAIL", "severity": "BLOCK", "detail": sentence}
        )
    for marker in strengthened:
        findings.append(
            {"code": "UNBOUND_STRONG_CLAIM", "severity": "BLOCK", "detail": marker}
        )

    blocked = any(item["severity"] == "BLOCK" for item in findings)
    return {
        "status": "BLOCKED" if blocked else "HUMAN_REVIEW_REQUIRED",
        "findings": findings,
        "human_review_required": True,
        "publication_state": "BLOCKED_PENDING_HUMAN",
        "publication_authority": "USER_ONLY",
        "external_publication_performed": False,
    }
