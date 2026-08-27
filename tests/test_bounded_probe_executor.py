import unittest
from collections import defaultdict

from bounded_probe_executor.core import (
    ProbeExecutionError,
    authorize_application,
    authorize_campaign,
    build_application_preview,
    compile_campaign,
    materialize_policy_artifact,
    run_campaign,
)
from model_behavior_adaptation.core import build_profile, conservative_config, plan_probe_matrix


ENGINE = {"provider": "fixture", "model": "engine-a", "model_revision": "r1", "adapter_version": "1"}
ENGINE_B = {"provider": "fixture", "model": "engine-b", "model_revision": "r2", "adapter_version": "1"}
BASE = conservative_config()


def tasks(count=2, cost=0.1):
    return [
        {
            "task_id": f"task-{i}",
            "input_ref": f"dataset://task-{i}",
            "estimated_cost_usd": cost,
            "timeout_seconds": 60,
        }
        for i in range(count)
    ]


def budget(**changes):
    value = {
        "max_jobs": 16,
        "max_total_attempts": 32,
        "max_parallel": 2,
        "max_retries_per_job": 1,
        "max_failures": 4,
        "max_wall_clock_seconds": 600,
        "max_estimated_cost_usd": 10.0,
    }
    value.update(changes)
    return value


def approval(campaign):
    return {
        "approved_by": "human",
        "approved_fingerprint": campaign["fingerprint"],
        "approved_at": "2026-08-27T00:00:00Z",
    }


def adapter_for(campaign, calls=None, engine=ENGINE, fail_ids=None, hidden=False):
    fail_ids = set(fail_ids or [])

    def adapter(job):
        if calls is not None:
            calls[job["job_id"]] += 1
        if job["job_id"] in fail_ids:
            raise RuntimeError("fixture failure")
        row = {
            "observation_id": f"obs-{job['job_id']}",
            "engine": engine,
            "domain": campaign["domain"],
            "task_id": job["task_id"],
            "variant_id": job["variant_id"],
            "config": job["config"],
            "outcome": {"status": "SUCCESS"},
            "metrics": {
                "wall_clock_seconds": 1,
                "retry_count": 0,
                "human_intervention_count": 0,
                "tool_call_count": 1,
                "quality_score": 1.0,
            },
            "provenance": {"run_id": job["job_id"]},
        }
        if hidden:
            row["chain_of_thought"] = "secret"
        return row

    return adapter


def profile_observation(index, config=BASE, engine=ENGINE, variant="base"):
    return {
        "observation_id": f"p-{variant}-{index}",
        "engine": engine,
        "domain": "coding",
        "task_id": f"profile-task-{index}",
        "variant_id": variant,
        "config": config,
        "outcome": {"status": "SUCCESS"},
        "metrics": {
            "wall_clock_seconds": 10,
            "retry_count": 0,
            "human_intervention_count": 0,
            "tool_call_count": 2,
            "quality_score": 1.0,
        },
        "provenance": {"run_id": f"profile-run-{variant}-{index}"},
    }


class BoundedProbeExecutorTests(unittest.TestCase):
    def test_compile_and_authorize_exact_fingerprint(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=3)
        campaign = compile_campaign(plan, tasks(2), budget())
        self.assertEqual(campaign["job_count"], 6)
        self.assertEqual(campaign["execution_authority"], "NONE")
        authorized = authorize_campaign(campaign, approval(campaign))
        self.assertEqual(authorized["execution_authority"], "BOUNDED_CAMPAIGN_ONLY")

    def test_overflow_fails_instead_of_truncating(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=4)
        with self.assertRaises(ProbeExecutionError):
            compile_campaign(plan, tasks(3), budget(max_jobs=8))

    def test_retry_adjusted_cost_and_attempts_are_preauthorized(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=2)
        with self.assertRaises(ProbeExecutionError):
            compile_campaign(
                plan,
                tasks(2, cost=1.0),
                budget(max_estimated_cost_usd=5.0, max_retries_per_job=1),
            )
        with self.assertRaises(ProbeExecutionError):
            compile_campaign(
                plan,
                tasks(2),
                budget(max_total_attempts=4, max_retries_per_job=1),
            )

    def test_unapproved_campaign_cannot_invoke_adapter(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        campaign = compile_campaign(plan, tasks(1), budget())
        calls = defaultdict(int)
        with self.assertRaises(ProbeExecutionError):
            run_campaign(campaign, adapter_for(campaign, calls))
        self.assertEqual(sum(calls.values()), 0)

    def test_chunk_resume_never_reruns_completed_jobs(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=2)
        raw = compile_campaign(plan, tasks(3), budget())
        campaign = authorize_campaign(raw, approval(raw))
        calls = defaultdict(int)
        checkpoint = run_campaign(
            campaign,
            adapter_for(campaign, calls),
            max_jobs_this_chunk=2,
        )
        self.assertEqual(checkpoint["state"], "PAUSED")
        completed_first = {
            job_id
            for job_id, state in checkpoint["jobs"].items()
            if state["state"] == "COMPLETED"
        }
        checkpoint = run_campaign(campaign, adapter_for(campaign, calls), checkpoint)
        self.assertEqual(checkpoint["state"], "COMPLETED")
        for job_id in completed_first:
            self.assertEqual(calls[job_id], 1)

    def test_engine_identity_mismatch_stops(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=2)
        raw = compile_campaign(plan, tasks(2), budget())
        campaign = authorize_campaign(raw, approval(raw))
        checkpoint = run_campaign(campaign, adapter_for(campaign, engine=ENGINE_B))
        self.assertEqual(checkpoint["state"], "STOPPED")
        self.assertEqual(checkpoint["stop_reason"], "ENGINE_IDENTITY_MISMATCH")

    def test_hidden_reasoning_is_quarantined_not_persisted(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        raw = compile_campaign(plan, tasks(1), budget(max_retries_per_job=0))
        campaign = authorize_campaign(raw, approval(raw))
        checkpoint = run_campaign(campaign, adapter_for(campaign, hidden=True))
        self.assertEqual(checkpoint["state"], "COMPLETED")
        self.assertEqual(checkpoint["failure_count"], 1)
        self.assertNotIn("chain_of_thought", str(checkpoint))
        self.assertEqual(checkpoint["observations"][0]["outcome"]["status"], "UNKNOWN")

    def test_failure_budget_stops_new_work(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=3)
        raw = compile_campaign(
            plan,
            tasks(2),
            budget(max_parallel=1, max_failures=1, max_retries_per_job=0),
        )
        campaign = authorize_campaign(raw, approval(raw))
        failing = {raw["jobs"][0]["job_id"]}
        calls = defaultdict(int)
        checkpoint = run_campaign(
            campaign,
            adapter_for(campaign, calls, fail_ids=failing),
        )
        self.assertEqual(checkpoint["state"], "STOPPED")
        self.assertEqual(checkpoint["stop_reason"], "FAILURE_BUDGET_REACHED")
        self.assertLess(sum(calls.values()), raw["job_count"])

    def test_stable_same_engine_profile_only_creates_local_artifact(self):
        profile = build_profile(
            [profile_observation(i) for i in range(12)],
            ENGINE,
            "coding",
        )
        current = dict(BASE, autonomy="high")
        preview = build_application_preview(profile, ENGINE, current)
        self.assertEqual(preview["state"], "REVIEW_REQUIRED")
        self.assertEqual(preview["runtime_mutation"], "NOT_PERFORMED")
        application_approval = {
            "approved_by": "human",
            "approved_fingerprint": preview["fingerprint"],
            "approved_at": "2026-08-27T00:00:00Z",
        }
        artifact = materialize_policy_artifact(
            authorize_application(preview, application_approval)
        )
        self.assertEqual(artifact["runtime_application_authority"], "NONE")
        self.assertEqual(artifact["runtime_mutation"], "NOT_PERFORMED")
        self.assertEqual(artifact["rollback_config"]["autonomy"], "high")

    def test_cross_engine_or_provisional_profile_is_blocked(self):
        stable = build_profile(
            [profile_observation(i) for i in range(12)], ENGINE, "coding"
        )
        self.assertEqual(
            build_application_preview(stable, ENGINE_B, BASE)["state"],
            "BLOCKED",
        )
        provisional = build_profile(
            [profile_observation(i) for i in range(4)], ENGINE, "coding"
        )
        self.assertNotEqual(provisional["state"], "STABLE")
        self.assertEqual(
            build_application_preview(provisional, ENGINE, BASE)["state"],
            "BLOCKED",
        )


if __name__ == "__main__":
    unittest.main()
