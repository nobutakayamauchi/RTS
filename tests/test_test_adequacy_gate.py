from __future__ import annotations

import hashlib
import unittest

from human_escalation_gate import EXHAUSTION_SEARCH_ROUTE, HumanEscalationError, evaluate_escalation_report
from test_adequacy_gate import evaluate_test_adequacy, run_mutation_suite, verify_test_adequacy_report
from tests.test_human_escalation_gate import make_k0


REASONING_ROUTE = "VERIFY_REASONING_CONTEXT_FIELD"
HELD_REASONING = "Before accepting an effective mode, inspect the response's `reasoning.context` value as an observable discriminator."


def fp(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def close_route(tag: str = "held-close") -> dict:
    return {
        "evidence_id": f"e-{tag}",
        "finding_index": 0,
        "route_id": REASONING_ROUTE,
        "probe_fingerprint": fp(tag),
        "evidence_distinction": "Inspect the observable reasoning.context field and test whether it distinguishes the residual mode choice.",
        "outcome": "NON_DISCRIMINATING",
        "learned_facts": ["The observable field did not discriminate the remaining choice in this held-out case."],
        "closed_routes": [REASONING_ROUTE],
        "opened_routes": [],
    }


def no_new_route_search(tag: str = "held-search") -> dict:
    return {
        "evidence_id": f"e-{tag}",
        "finding_index": 0,
        "route_id": EXHAUSTION_SEARCH_ROUTE,
        "probe_fingerprint": fp(tag),
        "evidence_distinction": "After known routes are closed, search bounded observable and official-document surfaces for a new discriminator.",
        "outcome": "NON_DISCRIMINATING",
        "learned_facts": ["The bounded post-integration search found no new discriminator."],
        "closed_routes": [],
        "opened_routes": [],
    }


def collect_nonmutation_lanes():
    known_bad = []
    k0 = make_k0(HELD_REASONING)
    open_report = evaluate_escalation_report(k0)
    known_bad.append({
        "case_id": "KB_ROUTE_REMAINS_AI_SIDE",
        "passed": open_report["records"][0]["disposition"] == "AI_CONTINUE",
        "detail": open_report["records"][0]["disposition"],
    })

    candidate = evaluate_escalation_report(
        k0,
        verification_evidence=[close_route("kb-close")],
        human_choices={0: "Select the residual effective-mode interpretation."},
    )
    known_bad.append({
        "case_id": "KB_HUMAN_CHOICE_IS_NOT_EXHAUSTION",
        "passed": candidate["records"][0]["disposition"] == "HUMAN_CANDIDATE",
        "detail": candidate["records"][0]["disposition"],
    })

    human = evaluate_escalation_report(
        k0,
        verification_evidence=[close_route("kb-full-close"), no_new_route_search("kb-full-search")],
        human_choices={0: "Select the residual effective-mode interpretation after bounded AI routes are exhausted."},
    )
    known_bad.append({
        "case_id": "KB_PROVEN_MATERIAL_EXHAUSTION_REACHES_HUMAN",
        "passed": human["records"][0]["disposition"] == "HUMAN_NOW",
        "detail": human["records"][0]["disposition"],
    })

    low = make_k0("A lower-cost model is available for routine video generation and editing workflows.")
    low_report = evaluate_escalation_report(low)
    known_bad.append({
        "case_id": "KB_LOW_PRIORITY_COST_SIGNAL_NOT_PROMOTED",
        "passed": low_report["records"][0]["disposition"] == "WAIT_SAFE_DEFER",
        "detail": low_report["records"][0]["disposition"],
    })

    duplicate_detected = False
    try:
        evaluate_escalation_report(
            k0,
            verification_evidence=[
                {
                    **close_route("dup-source"),
                    "evidence_id": "e-dup-1",
                    "probe_fingerprint": fp("same-held-probe"),
                    "closed_routes": [],
                },
                {
                    **close_route("dup-source-2"),
                    "evidence_id": "e-dup-2",
                    "probe_fingerprint": fp("same-held-probe"),
                    "closed_routes": [],
                },
            ],
        )
    except HumanEscalationError:
        duplicate_detected = True
    known_bad.append({
        "case_id": "KB_DUPLICATE_PROBE_REPLAY_REJECTED",
        "passed": duplicate_detected,
        "detail": "rejected" if duplicate_detected else "accepted",
    })

    held_out = []
    state_k0 = make_k0("A response can carry `previous_response_id`; verify whether that identifier preserves the intended continuation contract.")
    state_report = evaluate_escalation_report(state_k0)
    held_out.append({
        "case_id": "HO_STATE_CONTINUATION_CONTRACT",
        "passed": state_report["records"][0]["disposition"] == "AI_CONTINUE",
        "detail": state_report["records"][0]["disposition"],
    })

    legacy_k0 = make_k0("Legacy models remain available during a transition window; map the effective model identity before assuming equivalent behavior.")
    legacy_report = evaluate_escalation_report(legacy_k0)
    held_out.append({
        "case_id": "HO_LEGACY_ENGINE_IDENTITY",
        "passed": legacy_report["records"][0]["disposition"] == "AI_CONTINUE",
        "detail": legacy_report["records"][0]["disposition"],
    })

    low_held = make_k0("A cost-efficient creative model is described for routine media drafts.")
    low_held_report = evaluate_escalation_report(low_held)
    held_out.append({
        "case_id": "HO_LOW_PRIORITY_CATALOG_TEXT",
        "passed": low_held_report["records"][0]["disposition"] == "WAIT_SAFE_DEFER",
        "detail": low_held_report["records"][0]["disposition"],
    })

    metamorphic = []
    lower = evaluate_escalation_report(make_k0(HELD_REASONING))["records"][0]
    upper = evaluate_escalation_report(make_k0("Before accepting an effective mode, INSPECT the response's `REASONING.CONTEXT` value as an observable discriminator."))["records"][0]
    metamorphic.append({
        "case_id": "MM_CASE_CHANGE_PRESERVES_ROUTE_DECISION",
        "passed": lower["disposition"] == upper["disposition"] == "AI_CONTINUE",
        "detail": f"{lower['disposition']}->{upper['disposition']}",
    })

    changed = evaluate_escalation_report(
        make_k0(HELD_REASONING),
        verification_evidence=[close_route("mm-close")],
    )["records"][0]
    metamorphic.append({
        "case_id": "MM_ROUTE_CLOSURE_CHANGES_CONTINUE_TO_CANDIDATE",
        "passed": lower["disposition"] == "AI_CONTINUE" and changed["disposition"] == "HUMAN_CANDIDATE",
        "detail": f"{lower['disposition']}->{changed['disposition']}",
    })

    deferred = evaluate_escalation_report(
        make_k0(HELD_REASONING),
        verification_evidence=[close_route("mm-defer-close")],
        safe_defers={0: {
            "trigger": "NEXT_ENGINE_OR_OFFICIAL_DOC_CHANGE",
            "rationale": "Wait until a source or engine change creates a new discriminating surface.",
            "evidence_ids": ["e-mm-defer-close"],
        }},
    )["records"][0]
    metamorphic.append({
        "case_id": "MM_SAFE_DEFER_CHANGES_CANDIDATE_TO_WAIT",
        "passed": changed["disposition"] == "HUMAN_CANDIDATE" and deferred["disposition"] == "WAIT_SAFE_DEFER",
        "detail": f"{changed['disposition']}->{deferred['disposition']}",
    })
    return known_bad, held_out, metamorphic


class TestAdequacyGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mutation_report = run_mutation_suite()
        cls.known_bad, cls.held_out, cls.metamorphic = collect_nonmutation_lanes()

    def test_critical_mutants_are_killed_and_controls_are_sound(self):
        audit = self.mutation_report["audit"]
        self.assertTrue(audit["mutation_lane_pass"], self.mutation_report["results"])
        self.assertTrue(audit["controls_pass"], self.mutation_report["results"])
        self.assertTrue(audit["production_source_unchanged"])
        self.assertEqual(audit["critical_total"], audit["critical_killed"])

    def test_known_bad_held_out_and_metamorphic_lanes_pass(self):
        for lane in (self.known_bad, self.held_out, self.metamorphic):
            self.assertTrue(all(row["passed"] for row in lane), lane)

    def test_full_adequacy_requires_all_lanes(self):
        report = evaluate_test_adequacy(
            self.mutation_report,
            known_bad=self.known_bad,
            held_out=self.held_out,
            metamorphic=self.metamorphic,
        )
        verify_test_adequacy_report(report)
        self.assertEqual(report["status"], "ADEQUATE")
        self.assertFalse(report["audit"]["test_pass_proves_bug_absence"])
        self.assertEqual(report["execution_authority"], "NONE")

    def test_one_failed_lane_forces_hold(self):
        broken = [dict(row) for row in self.held_out]
        broken[0]["passed"] = False
        report = evaluate_test_adequacy(
            self.mutation_report,
            known_bad=self.known_bad,
            held_out=broken,
            metamorphic=self.metamorphic,
        )
        self.assertEqual(report["status"], "HOLD_FALSE_GREEN_RISK")


if __name__ == "__main__":
    unittest.main()
