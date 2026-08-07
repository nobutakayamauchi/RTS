from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deployment_identity.core import build_snapshot
from runtime_debug_gate.core import DebugGateError, evaluate_debug_gate, validate_gate_result


OBSERVATION = {"event": "HTTP 500", "surface": "/health"}


class RuntimeDebugGateTests(unittest.TestCase):
    def test_missing_identity_blocks_runtime_classification(self) -> None:
        result = evaluate_debug_gate(observation=OBSERVATION, deployment_identity=None)
        self.assertEqual(result["state"], "BLOCKED_IDENTITY_MISSING")
        self.assertFalse(result["runtime_classification_allowed"])
        self.assertEqual(result["runtime_implementation"], "UNKNOWN")

    def test_partial_identity_blocks_runtime_classification(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            identity = build_snapshot(
                root=Path(temp),
                service_unit="rts.service",
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        self.assertEqual(identity["status"], "PARTIAL")
        result = evaluate_debug_gate(observation=OBSERVATION, deployment_identity=identity)
        self.assertEqual(result["state"], "BLOCKED_IDENTITY_NOT_ESTABLISHED")
        self.assertFalse(result["runtime_classification_allowed"])
        self.assertEqual(result["runtime_implementation"], "UNKNOWN")

    def test_established_identity_allows_evidence_correlation_not_code_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            identity = build_snapshot(
                root=Path(temp),
                service_unit="rts.service",
                deployed_revision="a" * 40,
                entrypoint="app.py",
                observed_at="2026-08-08T00:00:00Z",
            )
        result = evaluate_debug_gate(observation=OBSERVATION, deployment_identity=identity)
        self.assertEqual(result["state"], "READY_FOR_EVIDENCE_CORRELATION")
        self.assertTrue(result["runtime_classification_allowed"])
        self.assertEqual(result["runtime_implementation"], "UNCLASSIFIED")
        self.assertEqual(result["next_action"], "CORRELATE_RUNTIME_EVIDENCE_BEFORE_CODE_MAPPING")
        self.assertFalse(result["code_existence_is_runtime_evidence"])

    def test_empty_observation_is_rejected(self) -> None:
        with self.assertRaisesRegex(DebugGateError, "must not be empty"):
            evaluate_debug_gate(observation={}, deployment_identity=None)

    def test_invalid_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(DebugGateError, "invalid deployment identity"):
            evaluate_debug_gate(
                observation=OBSERVATION,
                deployment_identity={"status": "ESTABLISHED"},
            )

    def test_validator_rejects_manufactured_ready_state(self) -> None:
        result = evaluate_debug_gate(observation=OBSERVATION, deployment_identity=None)
        result["state"] = "READY_FOR_EVIDENCE_CORRELATION"
        result["runtime_classification_allowed"] = True
        result["runtime_implementation"] = "UNCLASSIFIED"
        with self.assertRaisesRegex(DebugGateError, "requires ESTABLISHED"):
            validate_gate_result(result)

    def test_blocked_state_cannot_claim_runtime_implementation(self) -> None:
        result = evaluate_debug_gate(observation=OBSERVATION, deployment_identity=None)
        result["runtime_implementation"] = "repo/app.py"
        with self.assertRaisesRegex(DebugGateError, "fail-closed"):
            validate_gate_result(result)


if __name__ == "__main__":
    unittest.main()
