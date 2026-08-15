from __future__ import annotations

from . import terminology as _terminology


def build_generation_packet(source: dict, *, trusted_source_refs: list[dict]) -> dict:
    """Build an evidence-bound article packet with broad-entry/deep-body teaching rules.

    This layer learns writing structure from public reference articles without
    importing their time-sensitive platform claims as facts. It extends the
    terminology-aware packet and keeps /human + USER_ONLY publication intact.
    """
    packet = _terminology.build_generation_packet(
        source,
        trusted_source_refs=trusted_source_refs,
    )

    packet["schema_version"] = "0.5"
    packet["comprehension_doctrine"] = {
        "entry_rule": "Make the entrance understandable to a reader who has never heard the concept before.",
        "depth_rule": "After the reader is oriented, go deep enough that an experienced reader still learns something.",
        "orientation_rule": (
            "After a strong hook or lived scene, if the article becomes concept-dense, give a compact 2-3 line orientation: what happened, what it means, and what scope this article covers."
        ),
        "scope_rule": (
            "State the scope early when a claim applies only to one surface, workflow, feature, period, or condition; do not let a narrow fact sound universal."
        ),
        "analogy_rule": "Explain abstract mechanisms with one familiar analogy before adding technical detail.",
    }

    packet["claim_layer_policy"] = {
        "separate": ["VERIFIED_FACT", "HUMAN_EXPERIENCE", "INTERPRETATION", "OPINION"],
        "verified_fact": "State directly when evidence-bound.",
        "human_experience": "Use only attested primary information.",
        "interpretation": "Signal clearly that the sentence is an interpretation, inference, or reading rather than source fact.",
        "opinion": "Allow strong human-attested judgment without upgrading it into a factual guarantee.",
        "transition_rule": "When moving from source-backed fact to interpretation, tell the reader the boundary changed.",
    }

    packet["reader_progression_policy"] = {
        "sequence": [
            "hook_or_lived_pain",
            "orientation_if_needed",
            "plain_language_definition",
            "simple_mechanism",
            "concrete_example",
            "obvious_reader_objection",
            "scope_or_exception",
            "deeper_mechanism",
            "synthesis_callback",
            "one_action",
            "single_cta",
        ],
        "objection_rule": (
            "When a reasonable reader is likely to think 'but what about X?', answer it near the claim instead of waiting until the end."
        ),
        "callback_rule": (
            "Reuse an earlier concept near the synthesis so the article feels connected rather than like separate sections."
        ),
        "promise_payoff_rule": (
            "A forward promise such as 'this connects later' is allowed only when the article actually returns to it and pays it off."
        ),
    }

    packet["commercial_article_policy"] = {
        "priority_order": [
            "WHO_TO_REACH",
            "WHAT_TO_HELP_THEM_UNDERSTAND",
            "WHAT_STATE_TO_LEAVE_THEM_IN",
            "HOW_TO_MAXIMIZE_DISTRIBUTION",
        ],
        "read_axis": "The article must be understandable and compelling enough to keep the intended reader moving.",
        "sell_axis": (
            "By the end, the intended reader should understand why the offer is relevant; the goal is product curiosity or qualified next-step interest, not raw reach alone."
        ),
        "anti_metric_trap": (
            "Do not treat impressions, likes, replies, saves, shares, or any single platform metric as the business objective unless the brief explicitly makes it the objective."
        ),
        "offer_bridge_rule": (
            "The offer should appear as the natural consequence of the article's problem and mechanism, not as a detached advertisement appended at the end."
        ),
    }

    packet["reference_learning_boundary"] = {
        "imported": [
            "broad entrance plus deep body",
            "early scope clarification",
            "fact-versus-interpretation labeling",
            "nearby objection handling",
            "callbacks and promise/payoff structure",
            "read-through plus commercial-relevance dual objective",
        ],
        "not_imported_as_truth": [
            "platform algorithm weights",
            "ranking constants",
            "time windows",
            "named internal systems",
            "reference author's business results",
        ],
    }

    packet["generation_constraints"].extend(
        [
            "Open broadly enough for a first-time reader, then deepen the explanation; do not confuse accessibility with shallowness.",
            "If a technical or dense section follows the hook, orient the reader in 2-3 short lines before the deep explanation when that improves comprehension.",
            "State narrow scope and exceptions near the first claim they qualify.",
            "Keep verified facts, human experience, interpretation, and opinion visibly distinct; explicitly signal the transition from fact to interpretation.",
            "Answer the most obvious reasonable objection close to the claim that creates it.",
            "Use callbacks to earlier ideas when synthesizing the article, and never make a forward promise that is not paid off later.",
            "For commercial articles, optimize both read-through and qualified product curiosity; do not substitute raw platform engagement for business relevance.",
            "Do not import time-sensitive claims, algorithm constants, or third-party results from a reference article unless they separately enter verified_evidence.",
        ]
    )

    packet["human_gate"]["checks"].extend(
        [
            "Can a first-time reader enter the article without prior domain knowledge while an experienced reader still gets a deeper mechanism or useful distinction?",
            "Did I clearly separate source-backed fact from my interpretation or opinion?",
            "Did I state important scope limits close to the claim they limit?",
            "Did every forward promise or callback actually pay off?",
            "Does the article leave the intended reader more interested in the relevant offer rather than merely chasing engagement metrics?",
        ]
    )
    return packet


def audit_draft(draft: str, packet: dict) -> dict:
    """Run evidence + terminology audit; semantic teaching checks remain /human."""
    return _terminology.audit_draft(draft, packet)
