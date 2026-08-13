import unittest

from debug_harness import DebugEvidenceError, evaluate


def base_case():
    return {
        "deployment_identity": {"status": "ESTABLISHED", "evidence_ref": "d1", "fingerprint": "fp1"},
        "probes": [{"probe_id": "r", "status": "FAIL", "evidence_refs": ["p1"], "deployment_fingerprint": "fp1"}],
        "patch": {
            "applied": True,
            "post_deployment_identity": {"status": "ESTABLISHED", "evidence_ref": "d2", "fingerprint": "fp2"},
            "replay_results": [{"probe_id": "r", "status": "PASS", "evidence_refs": ["p2"], "deployment_fingerprint": "fp2"}],
            "regression_status": "PASS",
            "regression_evidence_refs": ["g1"],
            "regression_deployment_fingerprint": "fp2",
        },
    }


class TestDebugHarness(unittest.TestCase):
    def test_valid_chain(self):
        self.assertEqual(evaluate(base_case())["state"], "FIX_VALIDATED")

    def test_stale_replay_identity_blocks(self):
        case = base_case()
        case["patch"]["replay_results"][0]["deployment_fingerprint"] = "fp1"
        self.assertIn("FAILED_PROBE_REPLAY_IDENTITY_MISMATCH:r", evaluate(case)["blocking_states"])

    def test_stale_regression_identity_blocks(self):
        case = base_case()
        case["patch"]["regression_deployment_fingerprint"] = "fp1"
        self.assertIn("REGRESSION_IDENTITY_MISMATCH", evaluate(case)["blocking_states"])

    def test_null_replay_is_malformed(self):
        case = base_case()
        case["patch"]["replay_results"] = None
        with self.assertRaises(DebugEvidenceError):
            evaluate(case)

    def test_initial_probe_must_bind_identity(self):
        case = base_case()
        case["probes"][0]["deployment_fingerprint"] = "wrong"
        self.assertEqual(evaluate(case)["state"], "BLOCKED_PROBE_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
