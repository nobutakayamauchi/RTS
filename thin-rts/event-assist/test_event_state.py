from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import event_state


NOW = "2026-08-13T01:00:00Z"


def base_case() -> dict:
    return {
        "schema": event_state.SCHEMA,
        "event_id": "evt-001",
        "event_type": "software_incident",
        "event_truth_state": "CONFIRMED",
        "event_time": "2026-08-13T00:00:00Z",
        "observed_at": "2026-08-13T00:05:00Z",
        "event_source_ref": "input:operator",
        "sources": [
            {
                "source_id": "src-practical",
                "source_class": "COMMON_PRACTICAL_FAILURE",
                "reference": "repo:pattern/software-incident",
                "retrieved_at": "2026-08-13T00:06:00Z",
                "status": "CURRENT_OBSERVED",
                "observed_artifact_ref": "fixture:official-observation",
                "observed_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
            },
            {
                "source_id": "src-official",
                "source_class": "OFFICIAL_PRIMARY",
                "reference": "official:https://example.invalid/rule",
                "retrieved_at": "2026-08-13T00:06:00Z",
                "status": "CURRENT_OBSERVED",
                "observed_artifact_ref": "fixture:official-observation",
                "observed_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
            },
        ],
        "facts": [
            {
                "fact_id": "fact-jurisdiction",
                "name": "jurisdiction",
                "value": "fixture-jurisdiction",
                "status": "CONFIRMED",
                "source_ref": "src-official",
                "observed_at": "2026-08-13T00:06:00Z",
            }
        ],
        "evidence": [
            {
                "evidence_id": "ev-log",
                "evidence_class": "runtime-log",
                "status": "PRESERVED_VERIFIED",
                "triage": "PRESERVE_HIGH",
                "source_ref": "src-practical",
                "collection_authority": "AUTHORIZED",
                "preservation_ref": "custody:receipt:001",
                "integrity_state": "CONTENT_INTEGRITY_PASS",
            }
        ],
        "authorities": {
            "observe": "AUTHORIZED",
            "collect": "AUTHORIZED",
            "access": "AUTHORIZED",
            "transform": "AUTHORIZED",
            "disclose": "BLOCKED",
            "submit": "BLOCKED",
            "promote": "BLOCKED",
        },
        "decisions": [
            {
                "decision_id": "dec-1",
                "result": "incident-confirmed-for-workflow",
                "status": "VERIFIED",
                "input_refs": ["src-practical"],
                "actor_tool": "fixture:operator",
                "time": "2026-08-13T00:10:00Z",
                "reason": "The event was explicitly reported and bounded to this workflow.",
            }
        ],
        "actions": [],
        "documents": [],
        "watches": [],
        "unknowns": [],
    }


class EventStateTests(unittest.TestCase):
    def test_minimal_verified_case_passes(self):
        report = event_state.validate_case(base_case(), evaluated_at=NOW)
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(report["event_truth_state"], "CONFIRMED")
        self.assertEqual(report["evidence_gaps"], [])

    def test_event_truth_unknown_remains_visible(self):
        case = base_case()
        case["event_truth_state"] = "UNKNOWN"
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertIn("EVENT_TRUTH_NOT_CONFIRMED", report["blocking_states"])
        self.assertNotEqual(report["classification"], "PASS")

    def test_missing_evidence_generates_gap_and_pin(self):
        case = base_case()
        case["evidence"].append(
            {
                "evidence_id": "ev-request-id",
                "evidence_class": "request-id",
                "status": "MISSING_RECOVERABLE",
                "triage": "PRESERVE_HIGH",
                "source_ref": "src-practical",
                "collection_authority": "AUTHORIZED",
            }
        )
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertEqual(report["evidence_gaps"][0]["status"], "MISSING_RECOVERABLE")
        self.assertEqual(
            next(pin for pin in report["action_pins"] if pin["action_id"] == "gap:ev-request-id")["pin_class"],
            "EVIDENCE_GAP",
        )

    def test_preserved_verified_requires_custody_reference_and_integrity(self):
        case = base_case()
        del case["evidence"][0]["preservation_ref"]
        with self.assertRaisesRegex(event_state.EventStateError, "preservation_ref"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_news_only_cannot_be_verified_legal_pin(self):
        case = base_case()
        case["sources"].append(
            {
                "source_id": "src-news",
                "source_class": "NEWS_SIGNAL",
                "reference": "news:https://example.invalid/story",
                "retrieved_at": "2026-08-13T00:20:00Z",
                "status": "UNVERIFIED_SIGNAL",
            }
        )
        case["actions"] = [
            {
                "action_id": "act-claim",
                "pin_class": "CLAIM_MAY_BE_MISSING",
                "assertion_state": "VERIFIED",
                "reason": "fixture",
                "next_action": "Check the official source.",
                "source_refs": ["src-news"],
            }
        ]
        with self.assertRaisesRegex(event_state.EventStateError, "current official source"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_stale_official_source_cannot_be_verified_legal_pin(self):
        case = base_case()
        case["sources"][1]["status"] = "STALE"
        case["actions"] = [
            {
                "action_id": "act-claim",
                "pin_class": "POSSIBLY_ELIGIBLE",
                "assertion_state": "VERIFIED",
                "reason": "fixture",
                "next_action": "Revalidate.",
                "source_refs": ["src-official"],
            }
        ]
        with self.assertRaisesRegex(event_state.EventStateError, "current official source"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_candidate_legal_pin_can_preserve_uncertainty(self):
        case = base_case()
        case["actions"] = [
            {
                "action_id": "act-claim",
                "pin_class": "POSSIBLY_ELIGIBLE",
                "assertion_state": "CANDIDATE",
                "reason": "A weak signal triggers an official check, not a legal conclusion.",
                "next_action": "Check current official eligibility conditions.",
                "source_refs": ["src-practical"],
            }
        ]
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertEqual(report["action_pins"][0]["assertion_state"], "CANDIDATE")

    def test_document_ready_draft_does_not_require_submission_authority(self):
        case = base_case()
        case["documents"] = [
            {
                "document_id": "doc-1",
                "state": "DOCUMENT_READY_DRAFT",
                "official_source_ref": "src-official",
                "required_fact_refs": ["fact-jurisdiction"],
                "required_evidence_refs": ["ev-log"],
            }
        ]
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertEqual(report["documents"][0]["state"], "DOCUMENT_READY_DRAFT")
        self.assertEqual(report["documents"][0]["submission_authority"], "BLOCKED")

    def test_submission_state_requires_explicit_submit_authority(self):
        case = base_case()
        case["documents"] = [
            {
                "document_id": "doc-1",
                "state": "SUBMISSION_AUTHORIZED",
                "official_source_ref": "src-official",
                "required_fact_refs": ["fact-jurisdiction"],
                "required_evidence_refs": ["ev-log"],
            }
        ]
        with self.assertRaisesRegex(event_state.EventStateError, "submit authority"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_watch_degradation_is_not_silence(self):
        case = base_case()
        case["watches"] = [
            {
                "watch_id": "watch-law",
                "last_successful_check": "2026-08-12T00:00:00Z",
                "next_expected_check": "2026-08-12T12:00:00Z",
                "staleness_threshold_seconds": 3600,
                "source_set": ["src-official"],
                "failure_state": "NONE",
                "notification_delivery_state": "DELIVERED",
            }
        ]
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertEqual(report["watches"][0]["status"], "WATCH_DEGRADED")
        self.assertIn("WATCH_DEGRADED", report["blocking_states"])
        self.assertTrue(any(pin["pin_class"] == "WATCH_DEGRADED" for pin in report["action_pins"]))

    def test_correction_must_reference_prior_decision_and_preserve_history(self):
        case = base_case()
        case["decisions"].append(
            {
                "decision_id": "dec-2",
                "result": "prior-classification-revised",
                "status": "VERIFIED",
                "input_refs": ["src-official"],
                "actor_tool": "fixture:reviewer",
                "time": "2026-08-13T00:20:00Z",
                "reason": "New source evidence changed the operational classification.",
                "supersedes": "dec-1",
            }
        )
        report = event_state.validate_case(case, evaluated_at=NOW)
        self.assertEqual(report["classification"], "PASS")
        self.assertEqual(len(case["decisions"]), 2)

        broken = copy.deepcopy(case)
        broken["decisions"][1]["supersedes"] = "missing"
        with self.assertRaisesRegex(event_state.EventStateError, "supersedes"):
            event_state.validate_case(broken, evaluated_at=NOW)

    def test_notification_sensitive_detail_requires_explicit_permission(self):
        case = base_case()
        case["actions"] = [
            {
                "action_id": "act-notify",
                "pin_class": "ACTION_REQUIRED",
                "assertion_state": "VERIFIED",
                "reason": "fixture",
                "next_action": "Open protected view.",
                "source_refs": [],
                "notification": {"disclosure": "MINIMAL", "contains_sensitive_detail": True},
            }
        ]
        with self.assertRaisesRegex(event_state.EventStateError, "leaks sensitive detail"):
            event_state.validate_case(case, evaluated_at=NOW)

    def test_goal_cli_is_deterministic_for_fixed_time(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps(base_case()), encoding="utf-8")
            cmd = ["python3", str(Path(event_state.__file__)), "goal", str(path), "--at", NOW]
            first = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            second = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.assertEqual(first.stdout, second.stdout)
            payload = json.loads(first.stdout)
            self.assertEqual(payload["implementation_id"], event_state.IMPLEMENTATION_ID)


if __name__ == "__main__":
    unittest.main()
