from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

import event_state

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
NOW = "2026-08-13T01:00:00Z"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def case_m() -> dict:
    return load("case_m_rental_move_in.json")


def case_b() -> dict:
    return load("case_b_childbirth_current_sources.json")


class EventStateMeteorTests(unittest.TestCase):
    def test_case_m_gap_is_visible_and_prevents_false_complete(self):
        report = event_state.validate_case(case_m(), evaluated_at=NOW)
        self.assertTrue(any(g["status"] == "MISSING_RECOVERABLE" for g in report["evidence_gaps"]))
        self.assertNotEqual(report["classification"], "PASS")

    def test_case_b_current_official_sources_and_document_draft_survive(self):
        report = event_state.validate_case(case_b(), evaluated_at=NOW)
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(report["documents"][0]["state"], "DOCUMENT_READY_DRAFT")
        self.assertEqual(report["documents"][0]["submission_authority"], "BLOCKED")
        self.assertTrue(any(p["pin_class"] == "DEADLINE_SOON" for p in report["action_pins"]))

    def test_attack_source_ages_past_declared_freshness(self):
        with self.assertRaisesRegex(event_state.EventStateError, "stale|fresh|current"):
            event_state.validate_case(case_b(), evaluated_at="2026-08-21T00:10:00Z")

    def test_attack_verified_user_specific_legal_pin_requires_confirmed_applicability_fact(self):
        case = case_b()
        next(f for f in case["facts"] if f["fact_id"] == "fact-insurance")["status"] = "UNKNOWN"
        with self.assertRaisesRegex(event_state.EventStateError, "fact|applicability|confirmed"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_verified_deadline_requires_current_source(self):
        case = case_b()
        next(a for a in case["actions"] if a["action_id"] == "act-local-deadline")["source_refs"] = []
        with self.assertRaisesRegex(event_state.EventStateError, "source"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_watch_cannot_reference_unknown_source(self):
        case = case_b()
        case["watches"][0]["source_set"] = ["src-does-not-exist"]
        with self.assertRaisesRegex(event_state.EventStateError, "watch.*source|unknown source"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_news_only_cannot_upgrade_document_ready(self):
        case = case_b()
        case["documents"][0]["official_source_ref"] = "src-news"
        with self.assertRaisesRegex(event_state.EventStateError, "current official source"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_submission_authority_does_not_leak_from_document_readiness(self):
        case = case_b()
        case["documents"][0]["state"] = "SUBMISSION_AUTHORIZED"
        with self.assertRaisesRegex(event_state.EventStateError, "submit authority"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_sensitive_notification_stays_protected(self):
        case = case_b()
        case["actions"][0]["notification"] = {
            "disclosure": "MINIMAL",
            "contains_sensitive_detail": True,
        }
        with self.assertRaisesRegex(event_state.EventStateError, "sensitive"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_broken_watch_is_not_treated_as_no_change(self):
        case = case_b()
        case["watches"][0]["failure_state"] = "PROVIDER_ERROR"
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertIn("WATCH_DEGRADED", report["blocking_states"])
        self.assertTrue(any(p["pin_class"] == "WATCH_DEGRADED" for p in report["action_pins"]))

    def test_attack_repeat_is_idempotent_for_same_case_and_time(self):
        case = case_b()
        first = event_state.canonical_json_bytes(event_state.validate_case(copy.deepcopy(case), evaluated_at=NOW))
        second = event_state.canonical_json_bytes(event_state.validate_case(copy.deepcopy(case), evaluated_at=NOW))
        self.assertEqual(first, second)

    def test_attack_unknown_schema_fails_closed(self):
        case = case_b()
        case["schema"] = "new-rts-event-case/v999"
        with self.assertRaisesRegex(event_state.EventStateError, "unsupported schema"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_attack_correction_preserves_prior_decision(self):
        case = case_b()
        case["decisions"] = [
            {"decision_id": "dec-old", "result": "not-applicable", "status": "VERIFIED", "input_refs": ["src-official-national"], "actor_tool": "fixture:v0", "time": "2026-08-13T00:10:00Z", "reason": "Earlier fact interpretation."},
            {"decision_id": "dec-new", "result": "possibly-applicable", "status": "VERIFIED", "input_refs": ["src-official-national", "fact-insurance"], "actor_tool": "fixture:v1", "time": "2026-08-13T00:20:00Z", "reason": "Confirmed insurance context changed the operational classification.", "supersedes": "dec-old"},
        ]
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(len(case["decisions"]), 2)

    def test_counter_da_confirmed_fact_requires_provenance(self):
        case = case_b()
        del case["facts"][0]["source_ref"]
        with self.assertRaisesRegex(event_state.EventStateError, "provenance|source_ref"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_counter_da_blocked_required_authority_blocks_case(self):
        case = case_m()
        case["evidence"] = [e for e in case["evidence"] if e["status"] == "PRESERVED_VERIFIED"]
        case["authorities"]["collect"] = "BLOCKED"
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertIn("ACTION_AUTHORITY_BLOCKED", report["blocking_states"])
        pin = next(p for p in report["action_pins"] if p["action_id"] == "act-capture-room")
        self.assertEqual(pin["authority_state"], "BLOCKED")

    def test_counter_da_past_deadline_is_not_silently_current(self):
        case = case_b()
        for source in case["sources"]:
            if source.get("source_class", "").startswith("OFFICIAL_"):
                source["stale_after"] = "2026-08-30T00:00:00Z"
        report = event_state.validate_case(case, evaluated_at="2026-08-22T00:00:00+09:00")
        pin = next(p for p in report["action_pins"] if p["action_id"] == "act-local-deadline")
        self.assertEqual(pin["deadline_state"], "OVERDUE")
        self.assertIn("DEADLINE_OVERDUE", report["blocking_states"])

    def test_counter_da_mutable_official_url_without_observed_artifact_cannot_verify(self):
        case = case_b()
        source = next(s for s in case["sources"] if s["source_id"] == "src-official-national")
        del source["observed_artifact_ref"]
        del source["observed_sha256"]
        with self.assertRaisesRegex(event_state.EventStateError, "observed artifact|digest|historical"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_counter_da_current_source_artifact_hashes_are_real(self):
        case = case_b()
        prefix = "repo:thin-rts/event-assist/"
        for source in case["sources"]:
            ref = source.get("observed_artifact_ref")
            if not ref:
                continue
            self.assertTrue(ref.startswith(prefix))
            path = HERE / ref[len(prefix):]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source["observed_sha256"])


if __name__ == "__main__":
    unittest.main()
