import unittest
from datetime import datetime, timezone, timedelta

import eta
from decision_sentinel import DecisionState
from operator_guard import advise


class OperatorGuardTests(unittest.TestCase):
    def make_obs(self, minutes):
        start = datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)
        return eta.Observation(
            task_class="meteor-round",
            started_at=start,
            human_hinge_at=start + timedelta(minutes=minutes),
            terminal="DONE",
            duration_minutes=float(minutes),
            weighted_chunks=None,
            evidence_strength="STRONG",
            source="test",
        )

    def test_shadow_features_do_not_change_active_eta(self):
        observations = [self.make_obs(4), self.make_obs(5), self.make_obs(6)]
        baseline = eta.estimate(observations, "meteor-round")
        guarded = advise(
            observations,
            task_class="meteor-round",
            decision_state=DecisionState(
                severity=3,
                evidence_quality=0.4,
                axis_coverage=0.4,
                recent_revision_load=10,
                recent_context_switch_load=8,
                unresolved_counterevidence=True,
                irreversible=True,
            ),
            known_governed_stages=9,
        )
        self.assertEqual(guarded["active_eta"]["come_back_after_minutes"], baseline["come_back_after_minutes"])
        self.assertFalse(guarded["authority"]["eta_adjusted_by_shadow_features"])
        self.assertEqual(guarded["decision_sentinel"]["level"], "RED")

    def test_sentinel_has_no_auto_authority(self):
        guarded = advise(
            [],
            task_class="new-task",
            decision_state=DecisionState(
                severity=1,
                evidence_quality=1.0,
                axis_coverage=1.0,
            ),
            known_governed_stages=1,
        )
        self.assertFalse(guarded["authority"]["sentinel_can_auto_approve"])
        self.assertFalse(guarded["authority"]["sentinel_can_auto_execute_irreversible_action"])
        self.assertEqual(guarded["mode"], "SHADOW")


if __name__ == "__main__":
    unittest.main()
