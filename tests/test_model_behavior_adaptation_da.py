import unittest

from model_behavior_adaptation.core import ProfileError, build_profile, conservative_config, plan_probe_matrix, resolve_operating_policy, validate_observation
from tests.test_model_behavior_adaptation import BASE, ENGINE, ENGINE_B, FAST, obs


class AdaptiveEngineProfilerDATests(unittest.TestCase):
    def test_da_new_engine_cannot_silently_keep_old_tuning(self):
        profile = build_profile([obs(i, config=FAST, variant="fast") for i in range(12)], ENGINE, "coding")
        self.assertEqual(profile["recommended_config"], FAST)
        policy = resolve_operating_policy(profile, ENGINE_B)
        self.assertNotEqual(policy["config"], FAST)
        self.assertEqual(policy["config"], conservative_config())

    def test_da_one_success_cannot_claim_stable(self):
        profile = build_profile([obs(1)], ENGINE, "coding")
        self.assertNotEqual(profile["state"], "STABLE")

    def test_da_faster_but_less_reliable_variant_loses(self):
        safe = [obs(i, config=BASE, status="SUCCESS", wall=30, variant="safe") for i in range(10)]
        fast = [obs(50+i, config=FAST, status="SUCCESS" if i < 5 else "FAILURE", wall=1, variant="fast") for i in range(10)]
        profile = build_profile(safe + fast, ENGINE, "coding")
        self.assertEqual(profile["selected_variant_id"], "safe")

    def test_da_hidden_reasoning_cannot_become_training_input(self):
        row = obs(1)
        row["reasoning_text"] = "private scratchpad"
        with self.assertRaises(ProfileError):
            validate_observation(row)

    def test_da_probe_explosion_is_rejected(self):
        with self.assertRaises(ProfileError):
            plan_probe_matrix(ENGINE, "coding", max_probes=100)

    def test_da_recommendation_has_no_execution_or_promotion_authority(self):
        profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
        self.assertEqual(profile["apply_mode"], "ADVISORY_ONLY")
        self.assertEqual(set(profile["authority"].values()), {"NONE"})


if __name__ == "__main__":
    unittest.main()
