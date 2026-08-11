import unittest

from decision_sentinel import DecisionState
from dogfood_run import (
    DogfoodRunError,
    LaunchSnapshot,
    complete_record,
    eta_training_record,
    start_record,
)


class DogfoodRunTests(unittest.TestCase):
    def make_started(self, predicted=7.0):
        return start_record(
            LaunchSnapshot(
                task_class="meteor-round",
                decision_hinge_at="2026-08-12T07:00:00+09:00",
                predicted_return_minutes=predicted,
                known_governed_stages=3,
                decision_state=DecisionState(
                    severity=2,
                    evidence_quality=0.8,
                    axis_coverage=0.6,
                    recent_revision_load=2,
                    recent_context_switch_load=1,
                ),
            )
        )

    def test_eta_learns_human_required_time_not_late_observed_return(self):
        started = self.make_started(predicted=7)
        done = complete_record(
            started,
            human_required_at="2026-08-12T07:06:00+09:00",
            observed_human_return_at="2026-08-12T07:10:00+09:00",
            terminal="DONE",
            revision_outcome="ROUTINE_ITERATION",
        )
        self.assertEqual(done["outcome"]["target_return_minutes"], 6.0)
        self.assertEqual(done["outcome"]["late_return_prediction_waste_minutes"], 1.0)
        self.assertEqual(done["outcome"]["observed_human_delta_from_required_minutes"], 4.0)
        training = eta_training_record(done)
        self.assertEqual(training["human_hinge_at"], "2026-08-12T07:06:00+09:00")
        self.assertNotEqual(training["human_hinge_at"], done["outcome"]["observed_human_return_at"])

    def test_early_prediction_waste_is_separate(self):
        started = self.make_started(predicted=4)
        done = complete_record(
            started,
            human_required_at="2026-08-12T07:06:00+09:00",
            terminal="APPROVAL_REQUIRED",
            revision_outcome="NEW_EVIDENCE",
        )
        self.assertEqual(done["outcome"]["early_return_prediction_waste_minutes"], 2.0)
        self.assertEqual(done["outcome"]["late_return_prediction_waste_minutes"], 0.0)
        self.assertEqual(done["outcome"]["revision_label_semantics"], "NOT_ERROR_LABEL")

    def test_completion_cannot_run_twice(self):
        started = self.make_started()
        done = complete_record(
            started,
            human_required_at="2026-08-12T07:06:00+09:00",
            terminal="DONE",
        )
        with self.assertRaises(DogfoodRunError):
            complete_record(
                done,
                human_required_at="2026-08-12T07:07:00+09:00",
                terminal="DONE",
            )

    def test_required_time_must_follow_hinge(self):
        started = self.make_started()
        with self.assertRaises(DogfoodRunError):
            complete_record(
                started,
                human_required_at="2026-08-12T06:59:00+09:00",
                terminal="DONE",
            )


if __name__ == "__main__":
    unittest.main()
