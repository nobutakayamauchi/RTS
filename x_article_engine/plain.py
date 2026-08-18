from __future__ import annotations

from copy import deepcopy

from . import v09_final as _final
from .core import XArticleEngineError


PLAIN_PROFILE_ID = "X_ARTICLE_PLAIN_V0"
PLAIN_PROFILE_VERSION = "0.1"

# These replacements apply only to engine-owned policy text. User supplied content
# (offer, target, pain, evidence, primary_info, CTA, product name) is never rewritten.
_POLICY_REPLACEMENTS = {
    "BridgePatch-style": "offer-oriented",
    "BridgePatch": "the configured offer",
    "CapCut": "the configured tool",
    "シムシティ化": "an attested coined label",
    "無料適合確認": "the configured CTA",
}

_CONTENT_KEYS = (
    "offer",
    "target",
    "pain",
    "cta",
    "verified_source_refs",
    "verified_evidence",
    "verified_primary_info",
    "lived_pain_anchors",
)

_CONFIGURATION_KEYS = (
    "article_type",
    "topic_mode",
    "opening_mode",
    "reader_model",
    "product_naming_policy",
    "freshness",
    "review_state",
    "warnings",
)

# Fail closed: only engine-known policy surfaces are exported to provider adapters.
# New policy surfaces must be added here deliberately after review.
_RULE_KEYS = (
    "narrative",
    "voice_policy",
    "generation_constraints",
    "human_gate",
    "terminology_policy",
    "comprehension_doctrine",
    "claim_layer_policy",
    "reader_progression_policy",
    "commercial_article_policy",
    "material_first_policy",
    "anti_ai_smell_policy",
    "specificity_policy",
    "longform_policy",
    "longform_reader_journey",
    "audience_depth_policy",
    "source_depth_policy",
    "desire_timing_policy",
    "market_gap_policy",
    "speed_quality_policy",
    "reach_conversion_policy",
    "risk_policy",
    "decision_then_path_policy",
    "completion_design_policy",
    "human_automation_boundary",
    "pain_to_promise_policy",
    "strong_language_policy",
    "opening_integrity_policy",
    "security_content_policy",
    "knowledge_conflict_rules",
    "cta_semantics_policy",
    "numeric_binding_policy",
    "meta_rejection_policy",
    "numeric_context_policy",
    "commercial_promise_polarity_policy",
    "negated_claim_policy",
    "polarity_policy",
    "evidence_purpose_binding_policy",
)

_LOCKED_CAPABILITY_KEYS = (
    "verified_source_refs",
    "verified_evidence",
    "verified_primary_info",
    "publication_state",
    "publication_authority",
    "external_publication_performed",
    "freshness",
    "risk_policy",
    "human_automation_boundary",
    "security_content_policy",
    "commercial_promise_polarity_policy",
)


def _sanitize_engine_policy(value: object) -> object:
    """Remove developer-specific defaults from engine-owned policy text only."""
    if isinstance(value, str):
        result = value
        for old, new in _POLICY_REPLACEMENTS.items():
            result = result.replace(old, new)
        if result == "Would I actually say this?":
            return "Is this natural for the configured writer, audience, and evidence?"
        return result
    if isinstance(value, list):
        return [_sanitize_engine_policy(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_engine_policy(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_engine_policy(item) for key, item in value.items()}
    return deepcopy(value)


def _assert_capabilities_preserved(before: dict, after: dict) -> None:
    for key in _LOCKED_CAPABILITY_KEYS:
        if before.get(key) != after.get(key):
            raise XArticleEngineError(f"plain profile changed locked capability field: {key}")

    human_gate = after.get("human_gate") or {}
    if human_gate.get("required") is not True:
        raise XArticleEngineError("plain profile must preserve mandatory /human review")
    if after.get("publication_state") != "BLOCKED_PENDING_HUMAN":
        raise XArticleEngineError("plain profile cannot weaken publication_state")
    if after.get("publication_authority") != "USER_ONLY":
        raise XArticleEngineError("plain profile cannot weaken publication_authority")
    if after.get("external_publication_performed") is not False:
        raise XArticleEngineError("plain profile cannot claim external publication")


def build_plain_generation_view(packet: dict) -> dict:
    """Build the provider-facing neutral knowledge view.

    Unknown packet keys are intentionally omitted so an article brief cannot add a
    new provider-level instruction surface by inventing fields such as
    ``system_override`` or ``developer_prompt``.
    """
    if not isinstance(packet, dict):
        raise XArticleEngineError("packet must be an object")
    plain_profile = packet.get("plain_profile") or {}
    if plain_profile.get("profile_id") != PLAIN_PROFILE_ID:
        raise XArticleEngineError("packet is not an X Article Plain profile")

    content = {key: deepcopy(packet.get(key)) for key in _CONTENT_KEYS if key in packet}
    configuration = {
        key: deepcopy(packet.get(key)) for key in _CONFIGURATION_KEYS if key in packet
    }
    rules = {
        key: _sanitize_engine_policy(packet.get(key))
        for key in _RULE_KEYS
        if key in packet
    }

    return {
        "profile": deepcopy(plain_profile),
        "content": content,
        "configuration": configuration,
        "rules": rules,
        "publication_boundary": {
            "publication_state": packet.get("publication_state"),
            "publication_authority": packet.get("publication_authority"),
            "external_publication_performed": packet.get("external_publication_performed"),
        },
    }


def plainize_packet(packet: dict) -> dict:
    """Return a neutral provider-ready profile without deleting engine capability."""
    if not isinstance(packet, dict):
        raise XArticleEngineError("packet must be an object")

    original = deepcopy(packet)
    plain = deepcopy(packet)

    # Style defaults are neutralized, but attested information remains available as
    # material. It may shape content when the brief explicitly calls for it; it is
    # not used as an implicit developer imitation target.
    voice = deepcopy(plain.get("voice_policy") or {})
    voice.update(
        {
            "profile": "PLAIN_NEUTRAL",
            "imitate_engine_author": False,
            "default_tone": "natural, clear, neutral Japanese",
            "default_colloquial_force": "do not force",
            "raw_pain_style": "use only when explicitly selected by the brief; do not infer it as the developer's house style",
            "coined_label_style": "preserve only when supplied/attested; never invent a signature label",
        }
    )
    plain["voice_policy"] = voice

    # The v0.8 packet contains one product-specific objective learned during
    # development. Keep the capability (reach vs qualified progress) while removing
    # the developer's own product as the default destination.
    reach = deepcopy(plain.get("reach_conversion_policy") or {})
    if reach:
        reach["goal_rule"] = (
            "For offer-oriented articles, the useful end state is an intended reader who understands the problem, "
            "understands why the configured offer may be relevant, and can take the single configured CTA."
        )
        plain["reach_conversion_policy"] = reach

    plain["generation_constraints"] = _sanitize_engine_policy(
        plain.get("generation_constraints", [])
    )
    plain["human_gate"] = _sanitize_engine_policy(plain.get("human_gate", {}))

    plain["distribution_profile"] = "PLAIN"
    plain["plain_profile"] = {
        "profile_id": PLAIN_PROFILE_ID,
        "version": PLAIN_PROFILE_VERSION,
        "purpose": "preserve X Article Engine capability while removing the engine developer's implicit voice/product defaults",
        "style": "natural neutral",
        "brand_default": None,
        "offer_default": None,
        "cta_default": None,
        "author_imitation": False,
        "first_person_rule": (
            "Use first-person facts/opinions only from verified_primary_info. Do not treat them as a style imitation corpus unless the brief explicitly asks for that style."
        ),
        "capability_rule": (
            "Evidence, audit, freshness, risk, security, recovery, and /human boundaries must survive plainization unchanged."
        ),
    }

    _assert_capabilities_preserved(original, plain)
    plain["plain_generation_view"] = build_plain_generation_view(plain)
    return plain


def build_plain_generation_packet(
    source: dict, *, trusted_source_refs: list[dict]
) -> dict:
    """Build final v0.9 capability, then apply the neutral Plain profile."""
    packet = _final.build_generation_packet(
        source,
        trusted_source_refs=trusted_source_refs,
    )
    return plainize_packet(packet)


def audit_draft(draft: str, packet: dict) -> dict:
    """Plain mode deliberately reuses the final v0.9 auditor unchanged."""
    return _final.audit_draft(draft, packet)
