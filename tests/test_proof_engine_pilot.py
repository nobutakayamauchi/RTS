from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.cli import build_parser
from proof_engine_pilot.core import ProofEngineError, generate_run, verify_run


class ProofEnginePilotTests(unittest.TestCase):
    def test_committed_run_is_ready_for_human_review(self):
        run = verify_run()
        self.assertEqual(run["result"], "PASS_CANDIDATES_READY")
        self.assertGreaterEqual(run["candidate_count"], 10)
        self.assertEqual(run["review_queue"]["state"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(run["output_asset"]["publication_status"], "NOT_PUBLISHED")

    def test_generation_is_deterministic(self):
        self.assertEqual(generate_run(), verify_run())

    def test_candidate_tamper_fails_closed(self):
        run = copy.deepcopy(verify_run())
        run["candidates"][0]["claim"] += " changed"
        with self.assertRaisesRegex(ProofEngineError, "candidate fingerprint mismatch"):
            verify_run(run)

    def test_evidence_escape_fails_closed(self):
        run = copy.deepcopy(verify_run())
        candidate = run["candidates"][0]
        candidate["evidence_prs"] = [999]
        from proof_engine_pilot.core import fingerprint
        material = copy.deepcopy(candidate)
        material.pop("candidate_fingerprint")
        candidate["candidate_fingerprint"] = fingerprint(material)
        material = copy.deepcopy(run)
        material.pop("run_fingerprint")
        run["run_fingerprint"] = fingerprint(material)
        with self.assertRaisesRegex(ProofEngineError, "escapes source boundary"):
            verify_run(run)

    def test_cli_has_no_consequential_commands(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"generate", "verify", "summary", "review-template"})


if __name__ == "__main__":
    unittest.main()
