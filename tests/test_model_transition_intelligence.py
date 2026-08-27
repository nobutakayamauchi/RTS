import hashlib
import unittest

from model_transition_intelligence.core import (
    TransitionError,
    compare_bundles,
    validate_bundle,
)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def claim(claim_id, area, key, kind, value, anchor):
    return {
        "claim_id": claim_id,
        "area": area,
        "key": key,
        "kind": kind,
        "value": value,
        "anchor": anchor,
    }


def source(source_id, document_id, content, claims=None, trust="OFFICIAL", source_type="API_DOCS"):
    return {
        "source_id": source_id,
        "document_id": document_id,
        "source_type": source_type,
        "trust": trust,
        "url": f"https://example.test/{document_id}",
        "ref": source_id,
        "content": content,
        "content_sha256": digest(content),
        "claims": list(claims or []),
    }


def bundle(generation, sources, provider="fixture", surface="chat"):
    return {
        "schema_version": "transition-evidence-bundle/v1",
        "provider": provider,
        "product_surface": surface,
        "generation": generation,
        "captured_at": "2026-08-27T00:00:00Z",
        "sources": sources,
    }


class ModelTransitionIntelligenceTests(unittest.TestCase):
    def test_marketing_only_change_is_s0(self):
        old_text = "Fast model. Best experience."
        new_text = "Fast model. Even better experience."
        old = bundle("old", [source("old-readme", "readme", old_text, [
            claim("m-old", "other", "marketing_tagline", "MARKETING", "best", "Best experience")
        ], source_type="README")])
        new = bundle("new", [source("new-readme", "readme", new_text, [
            claim("m-new", "other", "marketing_tagline", "MARKETING", "better", "Even better experience")
        ], source_type="README")])
        report = compare_bundles(old, new)
        self.assertEqual(report["severity"], "S0")
        self.assertEqual(report["transition_state"], "CLASSIFIED")
        self.assertEqual(report["probe_requirements"]["max_probe_count"], 1)

    def test_whitespace_only_document_change_does_not_escalate(self):
        old = bundle("old", [source("old-api", "api", "Context mode is selective.", [
            claim("c1", "context", "context_mode", "CONTRACT", "selective", "Context mode is selective")
        ])])
        new = bundle("new", [source("new-api", "api", "Context   mode is   selective.", [
            claim("c2", "context", "context_mode", "CONTRACT", "selective", "Context   mode is   selective")
        ])])
        report = compare_bundles(old, new)
        self.assertEqual(report["severity"], "S0")
        self.assertEqual(report["transition_state"], "CLASSIFIED")

    def test_context_limit_change_is_s1_and_targets_context(self):
        old_text = "Context window: 100k."
        new_text = "Context window: 200k."
        old = bundle("old", [source("old-limits", "limits", old_text, [
            claim("l1", "context", "context_window", "LIMIT", 100000, "Context window: 100k")
        ], source_type="LIMITS_DOCS")])
        new = bundle("new", [source("new-limits", "limits", new_text, [
            claim("l2", "context", "context_window", "LIMIT", 200000, "Context window: 200k")
        ], source_type="LIMITS_DOCS")])
        report = compare_bundles(old, new)
        self.assertEqual(report["severity"], "S1")
        self.assertIn("context_mode", report["probe_requirements"]["preferred_f_dimensions"])
        self.assertEqual(report["documentation_behavior_status"], "UNVERIFIED")

    def test_instruction_contract_change_is_s2(self):
        old_text = "Detailed instructions are recommended."
        new_text = "Goal-level instructions are recommended; avoid overspecification."
        old = bundle("old", [source("old-guide", "guide", old_text, [
            claim("i1", "instructions", "instruction_guidance", "CONTRACT", "detailed", "Detailed instructions are recommended.")
        ], source_type="MIGRATION_GUIDE")])
        new = bundle("new", [source("new-guide", "guide", new_text, [
            claim("i2", "instructions", "instruction_guidance", "CONTRACT", "goal_level", "Goal-level instructions are recommended; avoid overspecification.")
        ], source_type="MIGRATION_GUIDE")])
        report = compare_bundles(old, new)
        self.assertEqual(report["severity"], "S2")
        self.assertIn("instruction_density", report["probe_requirements"]["preferred_f_dimensions"])
        self.assertEqual(report["profile_disposition"]["old_operating_assumptions"], "HYPOTHESIS_ONLY")

    def test_execution_contract_topology_change_is_s3(self):
        old_text = "Delegation model: none."
        new_text = "Delegation model: managed subagents."
        old = bundle("old", [source("old-tools", "tools", old_text, [
            claim("d1", "delegation", "delegation_model", "CONTRACT", "none", "Delegation model: none")
        ], source_type="TOOL_DOCS")])
        new = bundle("new", [source("new-tools", "tools", new_text, [
            claim("d2", "delegation", "delegation_model", "CONTRACT", "managed_subagents", "Delegation model: managed subagents")
        ], source_type="TOOL_DOCS")])
        report = compare_bundles(old, new)
        self.assertEqual(report["severity"], "S3")
        self.assertEqual(report["hidden_architecture_claim"], "NONE")
        self.assertEqual(report["architecture_claim"], "OBSERVABLE_EXECUTION_CONTRACT_ONLY")
        self.assertEqual(report["profile_disposition"]["direct_application"], "BLOCKED")
        self.assertEqual(report["probe_requirements"]["max_probe_count"], 8)
        self.assertEqual(len(report["probe_requirements"]["preferred_f_dimensions"]), 6)

    def test_conflicting_official_claims_require_review(self):
        old_text = "Tool strategy: bounded."
        old = bundle("old", [source("old-tools", "tools", old_text, [
            claim("t-old", "tools", "tool_strategy", "CONTRACT", "bounded", "Tool strategy: bounded")
        ], source_type="TOOL_DOCS")])
        new_a = source("new-a", "tools-a", "Tool strategy: adaptive.", [
            claim("t-a", "tools", "tool_strategy", "CONTRACT", "adaptive", "Tool strategy: adaptive")
        ], source_type="TOOL_DOCS")
        new_b = source("new-b", "tools-b", "Tool strategy: autonomous.", [
            claim("t-b", "tools", "tool_strategy", "CONTRACT", "autonomous", "Tool strategy: autonomous")
        ], source_type="RELEASE_NOTES")
        report = compare_bundles(old, bundle("new", [new_a, new_b]))
        self.assertEqual(report["transition_state"], "REVIEW_REQUIRED")
        self.assertTrue(report["conflicts"])
        self.assertEqual(report["probe_requirements"]["execution_recommendation"], "HOLD_FOR_REVIEW")

    def test_unofficial_evidence_cannot_raise_severity(self):
        official_old = source("old-api", "api", "Context mode: selective.", [
            claim("o1", "context", "context_mode", "CONTRACT", "selective", "Context mode: selective")
        ])
        official_new = source("new-api", "api", "Context mode: selective.", [
            claim("o2", "context", "context_mode", "CONTRACT", "selective", "Context mode: selective")
        ])
        unofficial_old = source("old-blog", "blog", "No subagents.", [
            claim("u1", "delegation", "delegation_model", "CONTRACT", "none", "No subagents")
        ], trust="UNOFFICIAL", source_type="README")
        unofficial_new = source("new-blog", "blog", "Many subagents.", [
            claim("u2", "delegation", "delegation_model", "CONTRACT", "many", "Many subagents")
        ], trust="UNOFFICIAL", source_type="README")
        report = compare_bundles(bundle("old", [official_old, unofficial_old]), bundle("new", [official_new, unofficial_new]))
        self.assertEqual(report["severity"], "S0")
        self.assertEqual(report["transition_state"], "CLASSIFIED")

    def test_unmapped_official_text_change_requires_review(self):
        old = bundle("old", [source("old-api", "api", "Tools run sequentially.", [])])
        new = bundle("new", [source("new-api", "api", "Tools may run in parallel.", [])])
        report = compare_bundles(old, new)
        self.assertEqual(report["transition_state"], "REVIEW_REQUIRED")
        self.assertTrue(report["unmapped_text_changes"])

    def test_bad_digest_fails_closed(self):
        src = source("bad", "api", "hello", [])
        src["content_sha256"] = "0" * 64
        with self.assertRaises(TransitionError):
            validate_bundle(bundle("old", [src]))

    def test_claim_anchor_must_exist(self):
        src = source("bad", "api", "hello", [
            claim("c", "context", "context_mode", "CONTRACT", "x", "missing anchor")
        ])
        with self.assertRaises(TransitionError):
            validate_bundle(bundle("old", [src]))

    def test_report_never_grants_authority(self):
        old = bundle("old", [source("old", "api", "Reasoning: medium.", [
            claim("r1", "reasoning", "reasoning_tier", "CONTRACT", "medium", "Reasoning: medium")
        ])])
        new = bundle("new", [source("new", "api", "Reasoning: high.", [
            claim("r2", "reasoning", "reasoning_tier", "CONTRACT", "high", "Reasoning: high")
        ])])
        report = compare_bundles(old, new)
        self.assertEqual(report["authority"], {
            "execution_authority": "NONE",
            "profile_application_authority": "NONE",
            "promotion_authority": "NONE",
        })
        for delta in report["deltas"]:
            self.assertEqual(delta["behavior_status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
