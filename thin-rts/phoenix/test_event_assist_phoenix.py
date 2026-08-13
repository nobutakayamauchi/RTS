from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
EVENT_ASSIST = HERE.parent / "event-assist"
if not EVENT_ASSIST.exists():
    EVENT_ASSIST = HERE.parent
PACKET = HERE / "event-assist-state-binding-succession-v0.json"
PILOT = EVENT_ASSIST / "fixtures" / "pilot_pr319_completion_audit.json"


def parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)


def reconstruct_protected_projection(case: dict, packet: dict, evaluated_at: str) -> dict:
    """Replacement probe built only from succession-packet rules, not event_state.py."""
    rules = packet["regeneration_rules"]
    evaluated = parse_time(evaluated_at)
    blocked: set[str] = set()

    if case.get("event_truth_state") in rules["event_truth_blocking_states"]:
        blocked.add("EVENT_TRUTH_NOT_CONFIRMED")
    if case.get("unknowns"):
        blocked.add("MATERIAL_UNKNOWNS_PRESENT")

    gaps = [
        evidence["evidence_id"]
        for evidence in case.get("evidence", [])
        if evidence.get("status") in rules["evidence_gap_statuses"]
    ]
    if gaps:
        blocked.add("EVIDENCE_GAPS_PRESENT")

    authorities = case.get("authorities", {})
    overdue: list[str] = []
    blocked_actions: list[str] = []
    for action in case.get("actions", []):
        required = action.get(rules["authority_requirement_field"])
        if required is not None and authorities.get(required) != rules["authorized_state"]:
            blocked_actions.append(action["action_id"])
            blocked.add("ACTION_AUTHORITY_BLOCKED")
        deadline = action.get(rules["deadline_field"])
        if deadline is not None and evaluated > parse_time(deadline):
            overdue.append(action["action_id"])
            blocked.add("DEADLINE_OVERDUE")

    degraded_watches: list[str] = []
    for watch in case.get("watches", []):
        last = parse_time(watch["last_successful_check"])
        stale = evaluated > last + timedelta(seconds=watch["staleness_threshold_seconds"])
        next_expected = watch.get("next_expected_check")
        missed = bool(next_expected) and evaluated > parse_time(next_expected) and last < parse_time(next_expected)
        failed = watch.get("failure_state") not in rules["watch_nonfailure_states"]
        delivery_failed = watch.get("notification_delivery_state") == rules["watch_failed_delivery_state"]
        if stale or missed or failed or delivery_failed:
            degraded_watches.append(watch["watch_id"])
            blocked.add("WATCH_DEGRADED")

    for document in case.get("documents", []):
        if document.get("state") in rules["submission_document_states"] and authorities.get("submit") != rules["authorized_state"]:
            blocked.add("SUBMISSION_AUTHORITY_MISSING")

    return {
        "event_id": case["event_id"],
        "evidence_gap_ids": sorted(gaps),
        "blocked_action_ids": sorted(blocked_actions),
        "overdue_action_ids": sorted(overdue),
        "degraded_watch_ids": sorted(degraded_watches),
        "promote_authority": authorities.get("promote", "UNKNOWN"),
        "blocking_states": sorted(blocked),
        "classification": rules["pass_classification"] if not blocked else rules["blocked_classification"],
    }


class CreatorAbsentPhoenixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packet = json.loads(PACKET.read_text("utf-8"))
        cls.case = json.loads(PILOT.read_text("utf-8"))

    def test_packet_contains_no_creator_or_chat_dependency(self):
        banned = set(self.packet["human_priority_contract"]["must_not_require"])
        self.assertIn("original creator memory", banned)
        self.assertIn("original AI conversation", banned)
        self.assertIn("the original event_state.py implementation", banned)

    def test_creator_absent_replacement_reconstructs_material_pilot(self):
        result = reconstruct_protected_projection(self.case, self.packet, "2026-08-13T01:30:00Z")
        self.assertEqual(result["classification"], "PASS")
        self.assertEqual(result["promote_authority"], "BLOCKED")
        self.assertEqual(result["blocking_states"], [])

    def test_inherited_death_evidence_gap_reopens_failure(self):
        case = copy.deepcopy(self.case)
        case["evidence"].append({
            "evidence_id": "ev-missing",
            "evidence_class": "material-runtime-identity",
            "status": "MISSING_RECOVERABLE",
        })
        result = reconstruct_protected_projection(case, self.packet, "2026-08-13T01:30:00Z")
        self.assertEqual(result["classification"], "UNKNOWN_OR_BLOCKED")
        self.assertIn("EVIDENCE_GAPS_PRESENT", result["blocking_states"])

    def test_inherited_death_required_authority_reopens_failure(self):
        case = copy.deepcopy(self.case)
        case["actions"][0]["authority_required"] = "promote"
        result = reconstruct_protected_projection(case, self.packet, "2026-08-13T01:30:00Z")
        self.assertIn("ACTION_AUTHORITY_BLOCKED", result["blocking_states"])

    def test_inherited_death_watch_failure_reopens_failure(self):
        case = copy.deepcopy(self.case)
        case["watches"] = [{
            "watch_id": "watch-ci",
            "last_successful_check": "2026-08-12T00:00:00Z",
            "next_expected_check": "2026-08-12T12:00:00Z",
            "staleness_threshold_seconds": 3600,
            "failure_state": "PROVIDER_ERROR",
            "notification_delivery_state": "FAILED",
        }]
        result = reconstruct_protected_projection(case, self.packet, "2026-08-13T01:30:00Z")
        self.assertIn("WATCH_DEGRADED", result["blocking_states"])

    def test_inherited_death_overdue_deadline_reopens_failure(self):
        case = copy.deepcopy(self.case)
        case["actions"].append({
            "action_id": "act-expired",
            "deadline": "2026-08-12T00:00:00Z",
        })
        result = reconstruct_protected_projection(case, self.packet, "2026-08-13T01:30:00Z")
        self.assertIn("DEADLINE_OVERDUE", result["blocking_states"])


if __name__ == "__main__":
    unittest.main()
