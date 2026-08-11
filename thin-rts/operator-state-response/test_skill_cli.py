import unittest

from skill_cli import build_state


class SkillCLITests(unittest.TestCase):
    def test_build_state_from_minimal_payload(self):
        state, ctx = build_state({"state": {"sleep_hours_24h": 5}, "context": {"eta_return_minutes": 7}})
        self.assertEqual(state.sleep_hours_24h, 5)
        self.assertEqual(ctx.eta_return_minutes, 7)

    def test_bad_status_and_recovery_arrays_are_normalized(self):
        state, _ = build_state({
            "state": {
                "bad_status": ["headache", ""],
                "recovery_events": ["nap", "meal"],
            }
        })
        self.assertEqual(state.bad_status, ("headache",))
        self.assertEqual(state.recovery_events, ("nap", "meal"))


if __name__ == "__main__":
    unittest.main()
