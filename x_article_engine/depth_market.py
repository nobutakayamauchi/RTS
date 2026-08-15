from __future__ import annotations

from . import longform_filter as _longform


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    """Add layered-reader depth, source depth, desire timing, and market-gap doctrine.

    This layer learns article strategy from a public reference article while keeping
    its metrics, timing, product claims, and causal conclusions outside engine truth.
    Evidence, /human, and USER_ONLY publication boundaries remain unchanged.
    """
    packet = _longform.build_generation_packet(
        source,
        trusted_source_refs=trusted_source_refs,
    )
    packet["schema_version"] = "0.8"

    packet["audience_depth_policy"] = {
        "principle": (
            "Use one broad entrance, then progressively add depth so a first-time reader can enter "
            "without forcing an experienced reader to stay at beginner level."
        ),
        "beginner_layer": {
            "reader_state": "I finally understand what this means.",
            "tools": [
                "translate unfamiliar terms immediately",
                "give comparison context for evidence-bound numbers when a single number has no intuitive meaning",
                "state the first useful conclusion early",
            ],
        },
        "intermediate_layer": {
            "reader_state": "I can picture how this applies and want to try or evaluate it.",
            "tools": [
                "use primary or official sources when they are the best available evidence for fresh technical claims",
                "show concrete examples, cases, inputs, outputs, or before/after mechanics",
                "surface conditions and exceptions that matter in practice",
            ],
        },
        "advanced_layer": {
            "reader_state": "I learned a deeper decision rule, implication, or viewpoint.",
            "tools": [
                "explain why information or an asset appears at that point in the article",
                "show trade-offs, second-order effects, or decision criteria",
                "end with a human-attested viewpoint when one exists rather than inventing authority",
            ],
        },
        "anti_label_rule": (
            "Do not call readers beginner/intermediate/advanced inside the article unless that labeling is useful. "
            "The layers are an authoring model, not a ranking of people."
        ),
    }

    packet["source_depth_policy"] = {
        "primary_source_preference": (
            "For fresh, technical, product, policy, or platform claims, prefer primary/official sources when available and appropriate. "
            "Do not turn 'official-only' into a blanket rule when a trustworthy secondary source is the better evidence for a different claim."
        ),
        "anti_summary_of_summary": (
            "When source depth matters, avoid building a factual section entirely from other people's summaries. "
            "Trace important claims back to the strongest available source before treating them as evidence."
        ),
        "freshness_rule": (
            "If the article depends on current or newly released information, preserve the date/scope in the evidence and do not generalize it into timeless doctrine."
        ),
    }

    packet["desire_timing_policy"] = {
        "principle": (
            "Place a useful asset, example, prompt, template, or next-step option after the reader understands why it is valuable, "
            "not before the value is legible."
        ),
        "utility_asset_rule": (
            "A prompt/template/resource may appear at the moment of maximum practical relevance as article content. "
            "This does not authorize multiple competing commercial CTAs."
        ),
        "commercial_cta_rule": (
            "Keep the commercial CTA singular and make it the natural continuation of the same problem and mechanism."
        ),
        "anti_manipulation_rule": (
            "Do not manufacture anxiety, fake scarcity, or emotional pressure merely to create a desire peak. "
            "The peak should come from genuine understanding of usefulness."
        ),
    }

    packet["market_gap_policy"] = {
        "principle": (
            "Before choosing an angle, inspect what the intended audience currently lacks: missing explanation, unanswered question, fresh change, "
            "under-served counterpoint, or an emerging split that creates confusion."
        ),
        "candidate_patterns": [
            "fresh information with an unmet explanation need",
            "a widely repeated claim with a well-evidenced counterpoint",
            "a field split where readers need a clearer comparison or decision rule",
            "a common topic where a missing practical example or first-party lesson creates a useful gap",
        ],
        "whitespace_rule": (
            "Market whitespace is a hypothesis about reader need, not proof of reach. Do not claim an empty slot guarantees impressions or sales."
        ),
        "counterpoint_rule": (
            "Do not take the opposite side merely because opposition attracts attention. A counterpoint must be supported by evidence or a genuine human-attested belief."
        ),
        "conflict_rule": (
            "Do not manufacture faction conflict, humiliation, or outrage for distribution. If a real disagreement matters, clarify the competing claims and useful decision boundary."
        ),
    }

    packet["speed_quality_policy"] = {
        "order": [
            "commercial_or_reader_goal",
            "market_gap_hypothesis",
            "evidence_collection",
            "article_depth",
            "speed_or_release_timing",
        ],
        "speed_rule": (
            "Speed can matter for time-sensitive topics, but it is an amplifier, not a substitute for evidence, usefulness, or a clear destination."
        ),
        "quality_floor": (
            "Do not publish a thin or unsafe article solely to be first. If freshness matters, compress the workflow rather than lowering evidence and comprehension boundaries."
        ),
    }

    packet["reach_conversion_policy"] = {
        "axes": ["READ_OR_REACH", "QUALIFIED_COMMERCIAL_PROGRESS"],
        "matrix": [
            "low reach / low commercial progress",
            "high reach / low commercial progress",
            "low reach / high commercial progress",
            "high reach / high commercial progress",
        ],
        "diagnostic_rule": (
            "Do not let strong attention metrics hide weak movement toward the intended business or reader outcome. "
            "Diagnose distribution and qualified progress separately."
        ),
        "goal_rule": (
            "For BridgePatch-style articles, the useful end state is not generic virality; it is an intended reader who understands the problem, "
            "sees the one-process approach as relevant, and can take the single fit-check next step."
        ),
    }

    packet["reference_learning_boundary"].setdefault("not_imported_as_truth", []).extend(
        [
            "reference article impression, follower, or list-growth results",
            "reference article creation time, release-time advantage, or taxi/coworking anecdote as a universal tactic",
            "a universal claim that being first captures the whole market",
            "a universal claim that beginner/intermediate/advanced readers behave in fixed ways",
            "a universal claim that contrarian or factional posts will grow reach",
        ]
    )

    packet["generation_constraints"].extend(
        [
            "Build depth progressively: first make the idea understandable, then make it applicable, then add a deeper decision rule, implication, or attested viewpoint when the material supports it.",
            "When an evidence-bound number is meaningful only in comparison, provide a relevant evidence-bound baseline or plain-language context rather than presenting the number in isolation.",
            "For fresh technical claims, prefer the strongest available primary/official evidence when appropriate; do not import another author's summary as proof.",
            "Place prompts, templates, examples, or other utility assets after the reader understands why they are useful; do not use placement to manufacture pressure.",
            "Before writing a distribution-sensitive article, identify a plausible information gap or reader need, but never treat market whitespace as guaranteed reach.",
            "Do not manufacture a contrarian stance or faction conflict for engagement. Use counterpoints only when supported by evidence or genuine human-attested judgment.",
            "Treat speed as an amplifier after reader goal, evidence, and article destination are clear. Do not sacrifice evidence or comprehension merely to publish first.",
            "Evaluate attention and qualified commercial progress separately; a high-reach article can still fail its intended business objective.",
            "If an attested human viewpoint can pay off the article, prefer that to a generic summary. If no such viewpoint exists, do not invent one.",
        ]
    )

    packet["human_gate"]["checks"].extend(
        [
            "Does the article let a first-time reader understand the topic before increasing depth?",
            "After the beginner-friendly explanation, is there enough mechanism, evidence, example, exception, or decision logic to reward a more experienced reader?",
            "Are comparison numbers evidence-bound on both sides, rather than one verified number plus an invented baseline?",
            "For fresh technical claims, did I use the strongest available source and preserve the claim's date/scope?",
            "Are prompts, examples, templates, or CTA-like assets placed after their usefulness becomes clear rather than before?",
            "Did I choose the article angle because there is a real information need, or merely because controversy might get attention?",
            "If I used a counterpoint, is it actually mine or evidence-supported rather than manufactured for reach?",
            "Am I separating reach/read metrics from qualified progress toward the offer?",
            "Does the ending leave a real human judgment, decision rule, or next action instead of generic recap?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    """Run all v0.7 deterministic checks; v0.8 depth/market checks remain semantic /human gates."""
    return _longform.audit_draft(draft, packet)
