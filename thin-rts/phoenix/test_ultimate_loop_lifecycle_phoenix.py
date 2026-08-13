import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = json.loads((HERE / "ultimate-loop-lifecycle-succession-v0.json").read_text(encoding="utf-8"))
ULTIMATE = HERE.parent / "ultimate-loop" / "fixtures"


def load_fixture(name):
    return json.loads((ULTIMATE / name).read_text(encoding="utf-8"))


def replacement_projection(case):
    """Deliberately independent projection reconstructed from the packet rules.

    This function must not import the original lifecycle implementation.
    It protects only the material failure states named in the Succession Packet.
    """
    candidate = case.get("candidate") or {}
    trigger = case.get("trigger") or {}
    authority = case.get("authority") or {}
    recovery = case.get("recovery") or {}

    recovery_state = "NOT_PROVEN"
    if recovery.get("backup_present") and recovery.get("fresh_restore_test") != "PASS":
        recovery_state = "BACKUP_ONLY"
    elif recovery.get("fresh_restore_test") == "PASS" and recovery.get("canonical_material") == "PASS":
        recovery_state = "RECOVERABLE"
        if recovery.get("succession_packet") == "PASS" and recovery.get("phoenix_test") == "PASS":
            recovery_state = "PHOENIX_READY"

    trigger_type = trigger.get("type")
    if trigger_type and trigger_type not in {
        "SERVICE_EOL", "PRIMARY_UNAVAILABLE", "CRITICAL_SECURITY", "DEPENDENCY_FAILURE",
        "UNKNOWN_EVENT", "NEW_CAPABILITY", "PERFORMANCE_JUMP", "PRICE_CHANGE",
        "PROVIDER_DEGRADATION", "SECURITY_IMPROVEMENT", "NEW_REAL_FAILURE"
    }:
        next_state = "BUILD"
    elif trigger_type in {"SERVICE_EOL", "PRIMARY_UNAVAILABLE", "CRITICAL_SECURITY", "DEPENDENCY_FAILURE"}:
        if candidate.get("recovery_probe") != "PASS":
            next_state = "EMERGENCY_BLOCKED"
        elif trigger.get("failure_domain_scope") == "MATERIAL" and candidate.get("failure_domain_independence") != "VERIFIED":
            next_state = "EMERGENCY_BLOCKED"
        elif authority.get("failover") != "AUTHORIZED":
            next_state = "STANDBY"
        else:
            next_state = "RECOVERY"
    else:
        delta = float(candidate.get("performance_delta_pct", 0))
        if candidate:
            fully_survived = (
                candidate.get("stability_state") == "SURVIVED"
                and candidate.get("same_frozen_workload") == "PASS"
                and candidate.get("migration_state", "NOT_APPLICABLE") in {"PASS", "NOT_APPLICABLE"}
                and candidate.get("rollback_state", "NOT_APPLICABLE") in {"PASS", "NOT_APPLICABLE"}
            )
            if not fully_survived:
                if candidate.get("resilience_value") == "HIGH" and candidate.get("recovery_probe") == "PASS":
                    next_state = "STANDBY"
                elif delta >= PACKET["screening_policy"]["observe_delta_pct"]:
                    next_state = "SHADOW"
                else:
                    next_state = case.get("current_state", "STABLE")
            elif (candidate.get("replacement_value") == "MATERIAL_WIN" or delta >= PACKET["screening_policy"]["full_replace_delta_pct"]):
                next_state = "STABLE" if authority.get("promote") == "AUTHORIZED" else "AUTHORITY_BLOCKED"
            elif candidate.get("resilience_value") == "HIGH" and candidate.get("recovery_probe") == "PASS":
                next_state = "STANDBY"
            else:
                next_state = case.get("current_state", "STABLE")
        elif case.get("current_state") == "BUILD" and case.get("core_acceptance") == "PASS":
            if case.get("material_durable") and recovery_state not in {"RECOVERABLE", "PHOENIX_READY"}:
                next_state = "BUILD"
            elif authority.get("promote") == "AUTHORIZED":
                next_state = "STABLE"
            else:
                next_state = "BUILD"
        else:
            next_state = case.get("current_state")

    return {"next_state": next_state, "recovery_state": recovery_state}


class UltimateLoopPhoenixTest(unittest.TestCase):
    def test_packet_rejects_creator_memory_dependency(self):
        self.assertFalse(PACKET["creator_independence"]["original_creator_required"])
        self.assertFalse(PACKET["creator_independence"]["original_ai_conversation_required"])
        self.assertFalse(PACKET["creator_independence"]["original_lifecycle_implementation_required"])

    def test_small_gain_candidate_regenerates_as_standby(self):
        report = replacement_projection(load_fixture("small_gain_standby.json"))
        self.assertEqual(report["next_state"], "STANDBY")

    def test_same_failure_domain_emergency_regenerates_as_blocked(self):
        report = replacement_projection(load_fixture("emergency_same_domain_blocked.json"))
        self.assertEqual(report["next_state"], "EMERGENCY_BLOCKED")

    def test_phoenix_ready_core_can_regenerate_to_stable(self):
        report = replacement_projection(load_fixture("core_freeze_phoenix_ready.json"))
        self.assertEqual(report["recovery_state"], "PHOENIX_READY")
        self.assertEqual(report["next_state"], "STABLE")

    def test_backup_only_does_not_regenerate_as_recoverable(self):
        case = load_fixture("core_freeze_phoenix_ready.json")
        case["recovery"]["fresh_restore_test"] = "NOT_RUN"
        report = replacement_projection(case)
        self.assertEqual(report["recovery_state"], "BACKUP_ONLY")
        self.assertEqual(report["next_state"], "BUILD")

    def test_unknown_future_trigger_reopens_build(self):
        case = load_fixture("small_gain_standby.json")
        case.pop("candidate")
        case["trigger"]["type"] = "FUTURE_UNKNOWN_CLASS"
        report = replacement_projection(case)
        self.assertEqual(report["next_state"], "BUILD")


if __name__ == "__main__":
    unittest.main()
