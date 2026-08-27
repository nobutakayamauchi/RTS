import unittest

from model_behavior_adaptation.core import (
    ProfileError,
    aggregate_variants,
    build_profile,
    conservative_config,
    detect_drift,
    engine_key,
    plan_probe_matrix,
    resolve_operating_policy,
    validate_observation,
    validate_observations,
)


ENGINE = {"provider": "fixture", "model": "engine-a", "model_revision": "r1", "adapter_version": "1"}
ENGINE_B = {"provider": "fixture", "model": "engine-b", "model_revision": "r2", "adapter_version": "1"}
BASE = conservative_config()
FAST = dict(BASE, autonomy="high")


def obs(i, config=BASE, status="SUCCESS", task=None, wall=10, retry=0, human=0, quality=1.0, engine=ENGINE, variant="base"):
    return {
        "observation_id": f"o-{variant}-{i}-{engine['model']}",
        "engine": engine,
        "domain": "coding",
        "task_id": task or f"task-{i}",
        "variant_id": variant,
        "config": config,
        "outcome": {"status": status},
        "metrics": {
            "wall_clock_seconds": wall,
            "retry_count": retry,
            "human_intervention_count": human,
            "tool_call_count": 3,
            "quality_score": quality,
        },
        "provenance": {"run_id": f"run-{variant}-{i}"},
    }


class AdaptiveEngineProfilerTests(unittest.TestCase):
    def test_probe_plan_is_bounded_and_one_dimension_at_a_time(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=8)
        self.assertLessEqual(plan["probe_count"], 8)
        baseline = plan["probes"][0]["config"]
        for probe in plan["probes"][1:]:
            changed = [k for k in baseline if baseline[k] != probe["config"][k]]
            self.assertEqual(changed, [probe["changed_dimension"]])
        self.assertEqual(plan["execution"], "NOT_PERFORMED")
        self.assertEqual(plan["authority"]["execution_authority"], "NONE")

    def test_probe_plan_honors_single_probe_cap(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        self.assertEqual(plan["probe_count"], 1)
        self.assertEqual(len(plan["probes"]), 1)
        self.assertEqual(plan["probes"][0]["probe_id"], "baseline")

    def test_hidden_reasoning_and_raw_text_are_rejected(self):
        row = obs(1)
        row["chain_of_thought"] = "secret"
        with self.assertRaises(ProfileError):
            validate_observation(row)
        row = obs(2)
        row["provenance"]["prompt_text"] = "raw prompt"
        with self.assertRaises(ProfileError):
            validate_observation(row)

    def test_missing_metrics_remain_none_not_zero(self):
        row = obs(1)
        row["metrics"]["retry_count"] = None
        row["metrics"]["human_intervention_count"] = None
        agg = aggregate_variants([row, obs(2), obs(3)])[0]
        self.assertIsNotNone(agg["retry_median"])
        rows = [obs(i) for i in range(3)]
        for r in rows:
            r["metrics"]["retry_count"] = None
        agg = aggregate_variants(rows)[0]
        self.assertIsNone(agg["retry_median"])

    def test_one_task_repeated_cannot_become_stable(self):
        rows = [obs(i, task="same-task") for i in range(12)]
        profile = build_profile(rows, ENGINE, "coding")
        self.assertEqual(profile["state"], "UNCHARACTERIZED")

    def test_stable_requires_cross_task_evidence(self):
        rows = [obs(i) for i in range(12)]
        profile = build_profile(rows, ENGINE, "coding")
        self.assertEqual(profile["state"], "STABLE")
        self.assertEqual(profile["authority"]["profile_application_authority"], "NONE")
        self.assertEqual(profile["architecture_claim"], "NONE")

    def test_success_dominates_speed(self):
        good = [obs(i, config=BASE, status="SUCCESS", wall=20, variant="good") for i in range(10)]
        bad = [obs(i+20, config=FAST, status="SUCCESS" if i < 6 else "FAILURE", wall=1, variant="fast") for i in range(10)]
        profile = build_profile(good + bad, ENGINE, "coding")
        self.assertEqual(profile["selected_variant_id"], "good")

    def test_engine_change_does_not_inherit_profile_as_authority(self):
        profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
        policy = resolve_operating_policy(profile, ENGINE_B)
        self.assertEqual(policy["state"], "NEW_ENGINE")
        self.assertEqual(policy["inheritance"], "PRIOR_ONLY")
        self.assertEqual(policy["config"], conservative_config())

    def test_probe_plan_uses_prior_only_when_engine_changes(self):
        profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
        plan = plan_probe_matrix(ENGINE_B, "coding", profile, 5)
        self.assertEqual(plan["inheritance"], "PRIOR_ONLY")
        self.assertEqual(plan["probes"][0]["config"], conservative_config())

    def test_duplicate_observation_ids_fail_closed(self):
        row = obs(1)
        with self.assertRaises(ProfileError):
            validate_observations([row, row])

    def test_drift_is_detected_from_observable_outcomes(self):
        profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
        recent = [obs(100+i, status="FAILURE" if i < 4 else "SUCCESS", retry=3, human=1) for i in range(6)]
        drift = detect_drift(profile, recent, ENGINE)
        self.assertEqual(drift["state"], "DRIFT_CONFIRMED")
        self.assertEqual(drift["action"], "CONSERVATIVE_REPROFILE")
        self.assertEqual(drift["architecture_claim"], "NONE")

    def test_unknown_outcomes_are_not_zero_failures(self):
        rows = [obs(1, status="SUCCESS"), obs(2, status="SUCCESS"), obs(3, status="SUCCESS"), obs(4, status="UNKNOWN")]
        agg = aggregate_variants(rows)[0]
        self.assertEqual(agg["known_outcomes"], 3)
        self.assertEqual(agg["unknown_outcomes"], 1)
        self.assertEqual(agg["success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
