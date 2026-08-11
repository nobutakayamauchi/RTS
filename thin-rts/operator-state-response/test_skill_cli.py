import unittest

from skill_cli import build_state


class SkillCLITests(unittest.TestCase):
    def test_build_state_from_minimal_payload(self):
        state, ctx = build_state({"state": {"sleep_hours_24h": 5}, "context": {"eta_return_minutes": 7}})
        self.assertEqual(state.sleep_hours_24h, 5)
        self.assertFalse(state.bad_status_assessed)
        self.assertEqual(ctx.eta_return_minutes, 7)

    def test_bad_status_and_recovery_arrays_are_normalized(self):
        state, _ = build_state({
            "state": {
                "bad_status": ["headache", ""],
                "recovery_events": ["nap", "meal"],
            }
        })
        self.assertEqual(state.bad_status, ("headache",))
        self.assertTrue(state.bad_status_assessed)
        self.assertEqual(state.recovery_events, ("nap", "meal"))

    def test_explicit_none_can_be_distinguished_from_not_asked(self):
        state, _ = build_state({"state": {"bad_status": [], "bad_status_assessed": True}})
        self.assertEqual(state.bad_status, ())
        self.assertTrue(state.bad_status_assessed)


if __name__ == "__main__":
    unittest.main()
