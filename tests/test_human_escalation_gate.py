from __future__ import annotations

import hashlib
import unittest

from human_escalation_gate import (
    EXHAUSTION_SEARCH_ROUTE,
    HumanEscalationError,
    evaluate_escalation_report,
    verify_escalation_report,
)
from review_necessity_triage import triage_refinement_report
from semantic_claim_refinement import refine_intake_report
from tests.test_semantic_claim_refinement import make_intake


def make_k0(body: str):
    j = refine_intake_report(make_intake(body))
    return triage_refinement_report(j)


def fp(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class HumanEscalationGateTests(unittest.TestCase):
    def test_k0_problem_solving_path_keeps_work_on_ai_side(self):
        k0 = make_k0("A request now uses a managed planner before tool execution.")
        report = evaluate_escalation_report(k0)
        verify_escalation_report(report, triage_report=k0)
        row = report["records"][0]
        self.assertEqual(row["disposition"], "AI_CONTINUE")
        self.assertTrue(row["residual_routes"])

    def test_second_pass_recovers_reasoning_context_route(self):
        k0 = make_k0("Check the response's `reasoning.context` field to confirm the effective mode.")
        self.assertEqual(k0["records"][0]["classification"], "HUMAN_NOW")
        self.assertFalse(k0["records"][0]["da"]["problem_solving_paths"])
        report = evaluate_escalation_report(k0)
        row = report["records"][0]
        self.assertEqual(row["disposition"], "AI_CONTINUE")
        self.assertIn("VERIFY_REASONING_CONTEXT_FIELD", row["recovered_escape_routes"])

    def test_low_priority_item_gets_bounded_safe_defer(self):
        k0 = make_k0("The new model sets a quality and efficiency baseline for complex production workflows.")
        report = evaluate_escalation_report(k0)
        row = report["records"][0]
        self.assertEqual(row["disposition"], "WAIT_SAFE_DEFER")
        self.assertEqual(row["safe_defer"]["trigger"], "SOURCE_OR_ENGINE_IDENTITY_CHANGE")

    def test_material_dead_end_without_exhaustion_evidence_is_candidate_not_human_now(self):
        k0 = make_k0("The context window is 1000000 tokens.")
        self.assertEqual(k0["records"][0]["classification"], "HUMAN_NOW")
        report = evaluate_escalation_report(k0)
        row = report["records"][0]
        self.assertEqual(row["disposition"], "HUMAN_CANDIDATE")
        self.assertIsNone(row["human_handoff"])

    def test_bounded_no_new_route_search_plus_material_choice_allows_human_now(self):
        k0 = make_k0("The context window is 1000000 tokens.")
        evidence = [{
            "evidence_id": "e-search",
            "finding_index": 0,
            "route_id": EXHAUSTION_SEARCH_ROUTE,
            "probe_fingerprint": fp("search-1"),
            "evidence_distinction": "Search bounded official-doc and observable-runtime surfaces for a discriminator that changes the context-window decision.",
            "outcome": "NON_DISCRIMINATING",
            "learned_facts": ["No additional bounded discriminator was found in the searched surfaces."],
            "closed_routes": [],
            "opened_routes": [],
        }]
        report = evaluate_escalation_report(
            k0,
            verification_evidence=evidence,
            human_choices={0: "Choose whether RTS should treat the documented context window as an operational planning bound."},
        )
        row = report["records"][0]
        self.assertEqual(row["disposition"], "HUMAN_NOW")
        self.assertIn(EXHAUSTION_SEARCH_ROUTE, row["human_handoff"]["tested_routes"])
        self.assertTrue(row["human_handoff"]["learned_facts"])

    def test_decision_requires_evidence_and_resolves_without_human(self):
        k0 = make_k0("The context window is 1000000 tokens.")
        evidence = [{
            "evidence_id": "e-contract",
            "finding_index": 0,
            "route_id": EXHAUSTION_SEARCH_ROUTE,
            "probe_fingerprint": fp("decision-evidence"),
            "evidence_distinction": "Compare observed accepted input boundary with the documented limit.",
            "outcome": "OBSERVED",
            "learned_facts": ["Observed behavior is consistent with the documented planning bound."],
            "closed_routes": [],
            "opened_routes": [],
        }]
        report = evaluate_escalation_report(
            k0,
            verification_evidence=evidence,
            decisions={0: {"decision": "Use the observed bound provisionally.", "evidence_ids": ["e-contract"]}},
        )
        self.assertEqual(report["records"][0]["disposition"], "AI_RESOLVE")

    def test_duplicate_probe_fingerprint_is_rejected_even_with_different_ids(self):
        k0 = make_k0("The context window is 1000000 tokens.")
        digest = fp("same-probe")
        evidence = [
            {
                "evidence_id": "e1",
                "finding_index": 0,
                "route_id": EXHAUSTION_SEARCH_ROUTE,
                "probe_fingerprint": digest,
                "evidence_distinction": "Search route A.",
                "outcome": "INCONCLUSIVE",
                "learned_facts": ["No decision yet."],
                "closed_routes": [],
                "opened_routes": [],
            },
            {
                "evidence_id": "e2",
                "finding_index": 0,
                "route_id": EXHAUSTION_SEARCH_ROUTE,
                "probe_fingerprint": digest,
                "evidence_distinction": "Same probe replayed under another evidence id.",
                "outcome": "INCONCLUSIVE",
                "learned_facts": ["Still no decision."],
                "closed_routes": [],
                "opened_routes": [],
            },
        ]
        with self.assertRaises(HumanEscalationError):
            evaluate_escalation_report(k0, verification_evidence=evidence)

    def test_authority_boundaries_remain_none(self):
        k0 = make_k0("Check the response's `reasoning.context` field to confirm the effective mode.")
        report = evaluate_escalation_report(k0)
        self.assertEqual(report["execution_authority"], "NONE")
        self.assertEqual(report["profile_application_authority"], "NONE")
        self.assertEqual(report["promotion_authority"], "NONE")
        self.assertEqual(report["hidden_architecture_claim"], "NONE")
        self.assertFalse(report["audit"]["attempt_count_is_exhaustion"])
        self.assertTrue(report["audit"]["knowledge_integration_required"])


if __name__ == "__main__":
    unittest.main()
