from __future__ import annotations

import unittest

from deployment_identity.core import BOUND, bind_runtime_observation, fingerprint_observation
from deployment_identity.outcome import (
    OUTCOME_BOUND,
    OUTCOME_NOT_BOUND,
    bind_outcome_evidence,
    compute_outcome_signature,
)


class OutcomeClosureTests(unittest.TestCase):
    def deployment_proof(self):
        return {
            "status": "DEPLOYMENT_IDENTITY_ESTABLISHED",
            "runtime_classification_authorized": True,
            "observation_fingerprint": "dep-fp",
            "expectation_fingerprint": "expect-fp",
            "identity": {
                "observation_session_id": "session-001",
                "observed_at": "2026-08-09T17:00:00+09:00",
            },
        }

    def runtime(self):
        return {
            "deployment_identity_fingerprint": "dep-fp",
            "deployment_expectation_fingerprint": "expect-fp",
            "observation_session_id": "session-001",
            "execution_id": "exec-001",
            "observed_at": "2026-08-09T17:00:15+09:00",
            "result": {"status": "running"},
        }

    def bound_runtime(self, runtime=None):
        runtime = runtime or self.runtime()
        return bind_runtime_observation(self.deployment_proof(), runtime, max_skew_seconds=30)

    def outcome_keys(self):
        return {"outcome-collector-01": "outcome-secret"}

    def outcome(self, runtime=None, **overrides):
        runtime = runtime or self.runtime()
        material = {
            "evidence_id": "outcome-001",
            "outcome_source_id": "outcome-collector-01",
            "execution_id": runtime["execution_id"],
            "observation_session_id": runtime["observation_session_id"],
            "deployment_identity_fingerprint": runtime["deployment_identity_fingerprint"],
            "deployment_expectation_fingerprint": runtime["deployment_expectation_fingerprint"],
            "runtime_observation_fingerprint": fingerprint_observation(runtime),
            "outcome_at": "2026-08-09T17:00:25+09:00",
            "outcome_type": "SUCCESS",
            "outcome_status": "SUCCEEDED",
        }
        material.update(overrides)
        return {**material, "signature": compute_outcome_signature(material, self.outcome_keys()["outcome-collector-01"])}

    def bind(self, runtime=None, outcome=None, seen=(), max_delay=3600):
        runtime = runtime or self.runtime()
        outcome = outcome or self.outcome(runtime)
        return bind_outcome_evidence(
            self.bound_runtime(runtime),
            runtime,
            outcome,
            trusted_outcome_keys=self.outcome_keys(),
            seen_evidence_ids=seen,
            max_outcome_delay_seconds=max_delay,
        )

    def resign(self, outcome):
        material = {k: v for k, v in outcome.items() if k != "signature"}
        outcome["signature"] = compute_outcome_signature(material, self.outcome_keys()["outcome-collector-01"])

    def test_signed_outcome_binds_to_exact_runtime_execution(self):
        result = self.bind()
        self.assertEqual(result["status"], OUTCOME_BOUND)
        self.assertTrue(result["outcome_evidence_authorized"])
        self.assertEqual(result["execution_id"], "exec-001")

    def test_unbound_runtime_cannot_authorize_outcome(self):
        runtime = self.runtime()
        proof = self.bound_runtime(runtime)
        proof["status"] = "RUNTIME_OBSERVATION_NOT_BOUND"
        result = bind_outcome_evidence(proof, runtime, self.outcome(runtime), trusted_outcome_keys=self.outcome_keys(), seen_evidence_ids=())
        self.assertEqual(result["status"], OUTCOME_NOT_BOUND)
        self.assertEqual(result["reason"], "RUNTIME_OBSERVATION_NOT_AUTHORIZED")

    def test_runtime_mutation_after_binding_fails(self):
        runtime = self.runtime()
        proof = self.bound_runtime(runtime)
        outcome = self.outcome(runtime)
        runtime["result"] = {"status": "tampered"}
        result = bind_outcome_evidence(proof, runtime, outcome, trusted_outcome_keys=self.outcome_keys(), seen_evidence_ids=())
        self.assertEqual(result["reason"], "RUNTIME_OBSERVATION_FINGERPRINT_MISMATCH")

    def test_outcome_from_different_execution_fails(self):
        outcome = self.outcome(execution_id="exec-other")
        result = self.bind(outcome=outcome)
        self.assertEqual(result["reason"], "EXECUTION_ID_MISMATCH")

    def test_outcome_from_different_session_fails(self):
        outcome = self.outcome(observation_session_id="session-other")
        result = self.bind(outcome=outcome)
        self.assertEqual(result["reason"], "OUTCOME_SESSION_MISMATCH")

    def test_outcome_from_different_runtime_fingerprint_fails(self):
        outcome = self.outcome(runtime_observation_fingerprint="forged")
        result = self.bind(outcome=outcome)
        self.assertEqual(result["reason"], "OUTCOME_RUNTIME_FINGERPRINT_MISMATCH")

    def test_outcome_from_different_deployment_fails(self):
        outcome = self.outcome(deployment_identity_fingerprint="other-deployment")
        result = self.bind(outcome=outcome)
        self.assertEqual(result["reason"], "OUTCOME_DEPLOYMENT_FINGERPRINT_MISMATCH")

    def test_untrusted_outcome_source_fails(self):
        outcome = self.outcome()
        outcome["outcome_source_id"] = "attacker"
        material = {k: v for k, v in outcome.items() if k != "signature"}
        outcome["signature"] = "0" * 64
        result = self.bind(outcome=outcome)
        self.assertEqual(result["reason"], "UNTRUSTED_OUTCOME_SOURCE")

    def test_forged_outcome_signature_fails(self):
        outcome = self.outcome()
        outcome["signature"] = "0" * 64
        result = self.bind(outcome=outcome)
        self.assertEqual(result["reason"], "INVALID_OUTCOME_SIGNATURE")

    def test_outcome_replay_id_fails_closed(self):
        result = self.bind(seen={"outcome-001"})
        self.assertEqual(result["reason"], "OUTCOME_EVIDENCE_REPLAY")

    def test_outcome_before_runtime_or_too_late_fails(self):
        before = self.outcome(outcome_at="2026-08-09T17:00:14+09:00")
        self.assertEqual(self.bind(outcome=before)["reason"], "OUTCOME_OUTSIDE_EXECUTION_WINDOW")
        late = self.outcome(outcome_at="2026-08-09T17:01:00+09:00")
        self.assertEqual(self.bind(outcome=late, max_delay=30)["reason"], "OUTCOME_OUTSIDE_EXECUTION_WINDOW")


if __name__ == "__main__":
    unittest.main()
