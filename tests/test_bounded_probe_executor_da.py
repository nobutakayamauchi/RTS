import unittest
from collections import defaultdict

from bounded_probe_executor.core import (
    ProbeExecutionError,
    authorize_campaign,
    compile_campaign,
    run_campaign,
)
from model_behavior_adaptation.core import plan_probe_matrix
from tests.test_bounded_probe_executor import ENGINE, adapter_for, approval, budget, tasks


class BoundedProbeExecutorDATests(unittest.TestCase):
    def test_approval_is_not_transferable_to_modified_campaign(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=2)
        campaign_one = compile_campaign(plan, tasks(1), budget())
        campaign_two = compile_campaign(plan, tasks(2), budget())
        with self.assertRaises(ProbeExecutionError):
            authorize_campaign(campaign_two, approval(campaign_one))

    def test_external_campaign_refuses_unknown_cost(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        rows = tasks(1)
        rows[0]["estimated_cost_usd"] = None
        with self.assertRaises(ProbeExecutionError):
            compile_campaign(plan, rows, budget(), "external")

    def test_resume_checkpoint_cannot_cross_campaign_fingerprint(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        raw_one = compile_campaign(plan, tasks(1), budget())
        campaign_one = authorize_campaign(raw_one, approval(raw_one))
        checkpoint = run_campaign(
            campaign_one,
            adapter_for(campaign_one),
            max_jobs_this_chunk=1,
        )

        raw_two = compile_campaign(plan, tasks(2), budget())
        campaign_two = authorize_campaign(raw_two, approval(raw_two))
        with self.assertRaises(ProbeExecutionError):
            run_campaign(campaign_two, adapter_for(campaign_two), checkpoint)

    def test_completed_checkpoint_is_idempotent(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        raw = compile_campaign(plan, tasks(1), budget())
        campaign = authorize_campaign(raw, approval(raw))
        calls = defaultdict(int)
        checkpoint = run_campaign(campaign, adapter_for(campaign, calls))
        again = run_campaign(campaign, adapter_for(campaign, calls), checkpoint)
        self.assertEqual(again, checkpoint)
        self.assertEqual(sum(calls.values()), 1)

    def test_retry_ceiling_cannot_be_hidden_by_low_base_cost(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=2)
        with self.assertRaises(ProbeExecutionError):
            compile_campaign(
                plan,
                tasks(2, cost=0.8),
                budget(max_retries_per_job=2, max_estimated_cost_usd=5.0),
                "external",
            )


if __name__ == "__main__":
    unittest.main()
