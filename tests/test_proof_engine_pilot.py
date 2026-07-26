from __future__ import annotations

import copy
import unittest

from proof_engine_pilot.cli import build_parser
from proof_engine_pilot.core import (
    BUILD_DECISION_PATH,
    PILOT_RECORD_PATH,
    SOURCE_PATH,
    ProofEngineError,
    fingerprint,
    generate_run,
    load,
    verify_build_decision,
    verify_pilot_record,
    verify_run,
    verify_source,
)


def resign(value: dict, field: str) -> None:
    material = copy.deepcopy(value)
    material.pop(field)
    value[field] = fingerprint(material)


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
        resign(run, "run_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "candidate .* fingerprint mismatch"):
            verify_run(run)

    def test_evidence_escape_fails_closed(self):
        run = copy.deepcopy(verify_run())
        candidate = run["candidates"][0]
        candidate["evidence_prs"] = [999]
        resign(candidate, "candidate_fingerprint")
        resign(run, "run_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "escapes source boundary"):
            verify_run(run)

    def test_missing_authority_denial_fails_closed(self):
        run = copy.deepcopy(verify_run())
        run["authority"].pop("publication_authorized")
        resign(run, "run_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "authority fields"):
            verify_run(run)

    def test_unmerged_source_cannot_be_eligible(self):
        source = copy.deepcopy(load(SOURCE_PATH))
        source["prs"][0]["merged"] = False
        source["prs"][0]["status"] = "SUPERSEDED"
        resign(source, "source_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "unmerged PR"):
            verify_source(source)

    def test_build_decision_is_bound_to_source(self):
        source = verify_source(load(SOURCE_PATH))
        decision = copy.deepcopy(load(BUILD_DECISION_PATH))
        decision["source_boundary"]["snapshot_ref"] = "0" * 40
        resign(decision, "decision_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "decision/source boundary mismatch"):
            verify_build_decision(decision, source)

    def test_pilot_record_is_bound_to_run(self):
        run = verify_run()
        source = verify_source(load(SOURCE_PATH))
        decision = verify_build_decision(load(BUILD_DECISION_PATH), source)
        record = copy.deepcopy(load(PILOT_RECORD_PATH))
        record["proof_engine_run_fingerprint"] = "0" * 64
        resign(record, "record_fingerprint")
        with self.assertRaisesRegex(ProofEngineError, "record/run mismatch"):
            verify_pilot_record(record, decision, source, run)

    def test_cli_has_no_consequential_commands(self):
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"generate", "verify", "summary", "review-template"})


if __name__ == "__main__":
    unittest.main()
