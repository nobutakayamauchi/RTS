from __future__ import annotations

import hashlib
import unittest

from human_escalation_gate import (
    EXHAUSTION_SEARCH_ROUTE,
    HumanEscalationError,
    evaluate_escalation_report,
)
from review_necessity_triage import triage_refinement_report
from semantic_claim_refinement import refine_intake_report
from tests.test_semantic_claim_refinement import make_intake


REASONING_CONTEXT_ANCHOR = "Check the response's `reasoning.context` field to confirm the effective mode."
REASONING_ROUTE = "VERIFY_REASONING_CONTEXT_FIELD"


def make_k0(body: str):
    return triage_refinement_report(refine_intake_report(make_intake(body)))


def fp(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def close_reasoning_route() -> dict:
    return {
        "evidence_id": "close-reasoning",
        "finding_index": 0,
        "route_id": REASONING_ROUTE,
        "probe_fingerprint": fp("close-reasoning-da"),
        "evidence_distinction": "Inspect reasoning.context and determine whether it resolves the effective-mode ambiguity.",
        "outcome": "NON_DISCRIMINATING",
        "learned_facts": ["The named field route was checked but did not resolve the residual choice."],
        "closed_routes": [REASONING_ROUTE],
        "opened_routes": [],
    }


class HumanEscalationGateDATests(unittest.TestCase):
    def test_attempts_do_not_exhaust_an_open_route(self):
        k0 = make_k0("A request now uses a managed planner before tool execution.")
        route = k0["records"][0]["da"]["problem_solving_paths"][0]
        evidence = [{
            "evidence_id": "e1",
            "finding_index": 0,
            "route_id": route,
            "probe_fingerprint": fp("attempt-1"),
            "evidence_distinction": "Observe one runtime sample without claiming it closes the route.",
            "outcome": "INCONCLUSIVE",
            "learned_facts": ["One sample did not discriminate the execution topology."],
            "closed_routes": [],
            "opened_routes": [],
        }]
        report = evaluate_escalation_report(k0, verification_evidence=evidence)
        self.assertEqual(report["records"][0]["disposition"], "AI_CONTINUE")
        self.assertIn(route, report["records"][0]["residual_routes"])

    def test_refutation_can_close_old_route_and_open_new_route(self):
        k0 = make_k0("A request now uses a managed planner before tool execution.")
        route = k0["records"][0]["da"]["problem_solving_paths"][0]
        evidence = [{
            "evidence_id": "e1",
            "finding_index": 0,
            "route_id": route,
            "probe_fingerprint": fp("refute-and-open"),
            "evidence_distinction": "Check whether the planner is actually present and, if not, inspect routing metadata.",
            "outcome": "REFUTED",
            "learned_facts": ["The observed request did not expose the documented planner path."],
            "closed_routes": [route],
            "opened_routes": ["VERIFY_DEPLOYMENT_OR_SURFACE_IDENTITY"],
        }]
        report = evaluate_escalation_report(k0, verification_evidence=evidence)
        row = report["records"][0]
        self.assertEqual(row["disposition"], "AI_CONTINUE")
        self.assertNotIn(route, row["residual_routes"])
        self.assertIn("VERIFY_DEPLOYMENT_OR_SURFACE_IDENTITY", row["residual_routes"])

    def test_safe_defer_prevents_human_escalation_after_route_is_closed(self):
        k0 = make_k0(REASONING_CONTEXT_ANCHOR)
        report = evaluate_escalation_report(
            k0,
            verification_evidence=[close_reasoning_route()],
            safe_defers={0: {
                "trigger": "NEXT_ENGINE_REVISION_OR_REASONING_MODE_DOC_CHANGE",
                "rationale": "No current operation requires selecting a different mode before that trigger.",
                "evidence_ids": ["close-reasoning"],
            }},
        )
        self.assertEqual(report["records"][0]["disposition"], "WAIT_SAFE_DEFER")

    def test_human_choice_without_exhaustion_search_is_not_enough(self):
        k0 = make_k0(REASONING_CONTEXT_ANCHOR)
        report = evaluate_escalation_report(
            k0,
            verification_evidence=[close_reasoning_route()],
            human_choices={0: "Pick the residual effective-mode interpretation."},
        )
        self.assertEqual(report["records"][0]["disposition"], "HUMAN_CANDIDATE")

    def test_exhaustion_search_that_opens_route_cannot_escalate(self):
        k0 = make_k0(REASONING_CONTEXT_ANCHOR)
        search = {
            "evidence_id": "search",
            "finding_index": 0,
            "route_id": EXHAUSTION_SEARCH_ROUTE,
            "probe_fingerprint": fp("search-opens-route"),
            "evidence_distinction": "Search for an alternate runtime discriminator after the field route was closed.",
            "outcome": "OBSERVED",
            "learned_facts": ["A runtime metadata probe can discriminate the remaining choice."],
            "closed_routes": [],
            "opened_routes": ["PROBE_RUNTIME_REASONING_METADATA"],
        }
        report = evaluate_escalation_report(
            k0,
            verification_evidence=[close_reasoning_route(), search],
            human_choices={0: "Pick the residual effective-mode interpretation."},
        )
        self.assertEqual(report["records"][0]["disposition"], "AI_CONTINUE")
        self.assertIn("PROBE_RUNTIME_REASONING_METADATA", report["records"][0]["residual_routes"])

    def test_escape_search_before_known_route_closure_does_not_prove_exhaustion(self):
        k0 = make_k0(REASONING_CONTEXT_ANCHOR)
        early_search = {
            "evidence_id": "early-search",
            "finding_index": 0,
            "route_id": EXHAUSTION_SEARCH_ROUTE,
            "probe_fingerprint": fp("early-search-before-close"),
            "evidence_distinction": "Search for another route before the already-known reasoning.context route has been exhausted.",
            "outcome": "NON_DISCRIMINATING",
            "learned_facts": ["No additional route was found at this earlier knowledge state."],
            "closed_routes": [],
            "opened_routes": [],
        }
        report = evaluate_escalation_report(
            k0,
            verification_evidence=[early_search, close_reasoning_route()],
            human_choices={0: "Pick the residual effective-mode interpretation."},
        )
        self.assertEqual(report["records"][0]["disposition"], "HUMAN_CANDIDATE")

    def test_k1_does_not_promote_k0_later_or_defer_to_active_work_from_escape_heuristic(self):
        k0 = make_k0("High-efficiency, low-cost, developer-first video generation and editing.")
        self.assertIn(k0["records"][0]["classification"], {"HUMAN_LATER", "DEFER_LOW_VALUE"})
        report = evaluate_escalation_report(k0)
        row = report["records"][0]
        self.assertIn("RECALIBRATE_LIMIT_OR_BUDGET", row["recovered_escape_routes"])
        self.assertEqual(row["disposition"], "WAIT_SAFE_DEFER")
        self.assertFalse(row["residual_routes"])

    def test_non_material_dead_end_does_not_consume_human_now(self):
        k0 = make_k0("New")
        self.assertEqual(k0["records"][0]["classification"], "DEFER_LOW_VALUE")
        evidence = [{
            "evidence_id": "search",
            "finding_index": 0,
            "route_id": EXHAUSTION_SEARCH_ROUTE,
            "probe_fingerprint": fp("non-material-search"),
            "evidence_distinction": "Search for any operational discriminator.",
            "outcome": "NON_DISCRIMINATING",
            "learned_facts": ["No operational contract was present in the anchor."],
            "closed_routes": [],
            "opened_routes": [],
        }]
        report = evaluate_escalation_report(
            k0,
            verification_evidence=evidence,
            human_choices={0: "Interpret the word New."},
        )
        self.assertEqual(report["records"][0]["disposition"], "WAIT_SAFE_DEFER")

    def test_decision_cannot_reference_unknown_evidence(self):
        k0 = make_k0(REASONING_CONTEXT_ANCHOR)
        with self.assertRaises(HumanEscalationError):
            evaluate_escalation_report(
                k0,
                decisions={0: {"decision": "Use observed mode.", "evidence_ids": ["missing"]}},
            )

    def test_evidence_cannot_close_unknown_route(self):
        k0 = make_k0("A request now uses a managed planner before tool execution.")
        route = k0["records"][0]["da"]["problem_solving_paths"][0]
        evidence = [{
            "evidence_id": "bad-close",
            "finding_index": 0,
            "route_id": route,
            "probe_fingerprint": fp("bad-close"),
            "evidence_distinction": "Attempt to close an unrelated route.",
            "outcome": "REFUTED",
            "learned_facts": ["Observed one unrelated fact."],
            "closed_routes": ["NEVER_OPENED"],
            "opened_routes": [],
        }]
        with self.assertRaises(HumanEscalationError):
            evaluate_escalation_report(k0, verification_evidence=evidence)


if __name__ == "__main__":
    unittest.main()
