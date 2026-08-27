import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from bounded_probe_executor.core import ProbeExecutionError, authorize_campaign, compile_campaign
from bounded_probe_executor.worker import run_background_chunk
from model_behavior_adaptation.core import plan_probe_matrix
from tests.test_bounded_probe_executor import ENGINE, adapter_for, approval, budget, tasks


class BoundedProbeWorkerTests(unittest.TestCase):
    def test_persisted_checkpoint_resumes_without_replay(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        raw = compile_campaign(plan, tasks(3), budget())
        campaign = authorize_campaign(raw, approval(raw))
        calls = defaultdict(int)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            first = run_background_chunk(
                campaign,
                adapter_for(campaign, calls),
                path,
                max_jobs_this_chunk=2,
            )
            self.assertEqual(first["state"], "PAUSED")
            self.assertTrue(path.exists())
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted, first)

            completed_first = {
                job_id
                for job_id, state in first["jobs"].items()
                if state["state"] == "COMPLETED"
            }
            self.assertEqual(len(completed_first), 2)

            second = run_background_chunk(
                campaign,
                adapter_for(campaign, calls),
                path,
                max_jobs_this_chunk=2,
            )
            self.assertEqual(second["state"], "COMPLETED")
            for job_id in completed_first:
                self.assertEqual(calls[job_id], 1)
            self.assertEqual(sum(calls.values()), 3)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), second)

    def test_persisted_checkpoint_cannot_be_reused_for_other_campaign(self):
        plan = plan_probe_matrix(ENGINE, "coding", max_probes=1)
        raw_one = compile_campaign(plan, tasks(1), budget())
        campaign_one = authorize_campaign(raw_one, approval(raw_one))
        raw_two = compile_campaign(plan, tasks(2), budget())
        campaign_two = authorize_campaign(raw_two, approval(raw_two))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            run_background_chunk(
                campaign_one,
                adapter_for(campaign_one),
                path,
                max_jobs_this_chunk=1,
            )
            with self.assertRaises(ProbeExecutionError):
                run_background_chunk(
                    campaign_two,
                    adapter_for(campaign_two),
                    path,
                    max_jobs_this_chunk=1,
                )


if __name__ == "__main__":
    unittest.main()
