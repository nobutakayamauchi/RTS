from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from execution_controller.cli import _verification_fixture
from execution_controller.controller import (
    ControllerError,
    inspect_run,
    plan_execution,
    resume_execution,
    run_execution,
    stop_execution,
)
from execution_controller.models import (
    authorization_material,
    sha256_value,
    validate_transition,
)
from execution_controller.store import checkpoint_path, verify_checkpoint


class ExecutionControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.state = self.base / "state"
        self.auth, self.script = _verification_fixture(self.root)

    def read_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path: Path, value) -> None:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def resign(self, document: dict) -> None:
        document["authorization_fingerprint"] = sha256_value(authorization_material(document))

    def set_budget(self, field: str, value: int) -> None:
        document = self.read_json(self.auth)
        document["budgets"][field] = value
        self.resign(document)
        self.write_json(self.auth, document)

    def test_plan_is_deterministic(self) -> None:
        self.assertEqual(plan_execution(self.root, self.auth), plan_execution(self.root, self.auth))

    def test_authorization_fingerprint_mismatch_fails_closed(self) -> None:
        doc = self.read_json(self.auth)
        doc["trigger"] = "changed"
        self.write_json(self.auth, doc)
        with self.assertRaisesRegex(ControllerError, "fingerprint mismatch"):
            plan_execution(self.root, self.auth)

    def test_unknown_capability_and_adapter_are_rejected(self) -> None:
        doc = self.read_json(self.auth)
        doc["allowed_capabilities"].append("NETWORK")
        doc["allowed_capabilities"].sort()
        self.resign(doc)
        self.write_json(self.auth, doc)
        with self.assertRaises(ControllerError):
            plan_execution(self.root, self.auth)

        self.auth, self.script = _verification_fixture(self.root)
        doc = self.read_json(self.auth)
        doc["adapter_id"] = "provider-live"
        self.resign(doc)
        self.write_json(self.auth, doc)
        with self.assertRaises(ControllerError):
            plan_execution(self.root, self.auth)

    def test_wip_gate_and_current_gates_fail_closed(self) -> None:
        items_path = self.root / "freezer/index/items.json"
        items = self.read_json(items_path)
        duplicate = dict(items["items"][0])
        duplicate["item_id"] = "RTS-FRZ-999998"
        items["items"].append(duplicate)
        items["count"] = 2
        self.write_json(items_path, items)
        with self.assertRaisesRegex(ControllerError, "WIP=1"):
            plan_execution(self.root, self.auth)

        self.auth, self.script = _verification_fixture(self.root)
        build_path = self.root / "freezer/index/build_priority.json"
        build = self.read_json(build_path)
        build["items"][0]["assessment_state"] = "STALE"
        self.write_json(build_path, build)
        with self.assertRaisesRegex(ControllerError, "missing or stale"):
            plan_execution(self.root, self.auth)

    def test_legal_and_illegal_state_transitions(self) -> None:
        validate_transition("RUNNING", "VERIFYING")
        with self.assertRaises(ControllerError):
            validate_transition("SUCCEEDED", "RUNNING")

    def test_success_creates_hash_chain_checkpoint_and_execution_record(self) -> None:
        result = run_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(result["state"], "SUCCEEDED")
        self.assertFalse(result["external_execution_performed"])
        self.assertEqual(result["execution_record"]["result"]["verification"], "SIMULATED_ONLY")
        plan_id = result["plan_id"]
        events, checkpoint = verify_checkpoint(self.state, plan_id)
        self.assertEqual(len(events), 5)
        self.assertEqual(checkpoint["state"], "SUCCEEDED")
        with self.assertRaisesRegex(ControllerError, "already exists"):
            run_execution(self.root, self.auth, self.state, self.script)

    def test_event_mutation_is_detected(self) -> None:
        result = run_execution(self.root, self.auth, self.state, self.script)
        path = self.state / result["plan_id"] / "events.jsonl"
        rows = path.read_text(encoding="utf-8").splitlines()
        first = json.loads(rows[0])
        first["summary"] = "tampered"
        rows[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ControllerError, "hash mismatch"):
            verify_checkpoint(self.state, result["plan_id"])

    def test_retryable_failure_can_resume(self) -> None:
        retry = {
            "kind": "failure",
            "summary": "retryable fixture failure",
            "retryable": True,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"reason": "fixture"},
            "timestamp": "2026-07-24T00:00:01Z",
        }
        self.write_json(self.script, retry)
        first = run_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(first["state"], "RUNNING")
        success = {
            "kind": "success",
            "summary": "second attempt succeeded",
            "retryable": False,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"status": "ok"},
            "timestamp": "2026-07-24T00:00:02Z",
        }
        self.write_json(self.script, success)
        second = resume_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(second["state"], "SUCCEEDED")
        self.assertEqual(second["attempt"], 2)

    def test_non_retryable_failure_is_terminal(self) -> None:
        failure = {
            "kind": "failure",
            "summary": "non-retryable fixture failure",
            "retryable": False,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"reason": "fixture"},
            "timestamp": "2026-07-24T00:00:01Z",
        }
        self.write_json(self.script, failure)
        result = run_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(result["state"], "FAILED")
        with self.assertRaisesRegex(ControllerError, "terminal"):
            resume_execution(self.root, self.auth, self.state, self.script)

    def test_budget_overrun_escalates_before_adapter_usage_is_applied(self) -> None:
        script = self.read_json(self.script)
        script["usage"]["changed_files"] = 1
        self.write_json(self.script, script)
        result = run_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(result["state"], "ESCALATED")
        self.assertEqual(result["usage"]["changed_files"], 0)

    def test_elapsed_and_changed_byte_budgets_escalate(self) -> None:
        cases = (("max_elapsed_seconds", "elapsed_seconds"), ("max_changed_bytes", "changed_bytes"))
        for budget_field, usage_field in cases:
            with self.subTest(budget=budget_field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                state = Path(temporary) / "state"
                auth, script_path = _verification_fixture(root)
                document = self.read_json(auth)
                document["budgets"][budget_field] = 0
                self.resign(document)
                self.write_json(auth, document)
                script = self.read_json(script_path)
                script["usage"][usage_field] = 1
                self.write_json(script_path, script)
                result = run_execution(root, auth, state, script_path)
                self.assertEqual(result["state"], "ESCALATED")
                self.assertEqual(result["usage"][usage_field], 0)

    def test_event_budget_escalates_instead_of_raising(self) -> None:
        self.set_budget("max_events", 5)
        retry = {
            "kind": "failure",
            "summary": "retryable fixture failure",
            "retryable": True,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"reason": "fixture"},
            "timestamp": "2026-07-24T00:00:01Z",
        }
        self.write_json(self.script, retry)
        first = run_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(first["state"], "RUNNING")
        success = {
            "kind": "success",
            "summary": "success requires a terminal verification event",
            "retryable": False,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"status": "ok"},
            "timestamp": "2026-07-24T00:00:02Z",
        }
        self.write_json(self.script, success)
        second = resume_execution(self.root, self.auth, self.state, self.script)
        self.assertEqual(second["state"], "ESCALATED")
        self.assertEqual(second["usage"]["events"], 5)

    def test_checkpoint_disagreement_is_detected(self) -> None:
        result = run_execution(self.root, self.auth, self.state, self.script)
        path = self.state / result["plan_id"] / "checkpoint.json"
        checkpoint = self.read_json(path)
        checkpoint["state"] = "FAILED"
        self.write_json(path, checkpoint)
        with self.assertRaisesRegex(ControllerError, "checkpoint disagrees"):
            verify_checkpoint(self.state, result["plan_id"])

    def test_run_identifier_cannot_escape_state_directory(self) -> None:
        with self.assertRaisesRegex(ControllerError, "unsafe characters"):
            checkpoint_path(self.state, "../escape")

    def test_committed_child_boundary(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        index_path = repository_root / "freezer" / "index" / "items.json"
        if not index_path.exists():
            self.skipTest("governed repository index is unavailable")
        rows = {row["item_id"]: row for row in self.read_json(index_path)["items"]}
        self.assertEqual(rows["RTS-FRZ-000006"]["status"], "COMPLETED")
        self.assertEqual(rows["RTS-FRZ-000006"]["build_authority"], "APPROVED")
        self.assertEqual(rows["RTS-FRZ-000007"]["status"], "FROZEN")
        self.assertEqual(rows["RTS-FRZ-000007"]["build_authority"], "NOT_APPROVED")

    def test_emergency_stop_preserves_prior_events(self) -> None:
        retry = {
            "kind": "failure",
            "summary": "pause on retryable failure",
            "retryable": True,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"reason": "fixture"},
            "timestamp": "2026-07-24T00:00:01Z",
        }
        self.write_json(self.script, retry)
        result = run_execution(self.root, self.auth, self.state, self.script)
        stopped = stop_execution(
            self.root,
            self.auth,
            self.state,
            "2026-07-24T00:00:02Z",
        )
        self.assertEqual(stopped["state"], "STOPPED")
        events, _ = verify_checkpoint(self.state, result["plan_id"])
        self.assertGreaterEqual(len(events), 5)

    def test_authorization_change_cannot_resume_existing_run(self) -> None:
        retry = {
            "kind": "failure",
            "summary": "retryable fixture failure",
            "retryable": True,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"reason": "fixture"},
            "timestamp": "2026-07-24T00:00:01Z",
        }
        self.write_json(self.script, retry)
        run_execution(self.root, self.auth, self.state, self.script)
        doc = self.read_json(self.auth)
        doc["trigger"] = "changed-and-resigned"
        self.resign(doc)
        self.write_json(self.auth, doc)
        with self.assertRaises(ControllerError):
            resume_execution(self.root, self.auth, self.state, self.script)

    def test_private_script_fields_are_rejected_and_not_persisted(self) -> None:
        script = self.read_json(self.script)
        script["result"] = {"prompt": "secret"}
        self.write_json(self.script, script)
        with self.assertRaisesRegex(ControllerError, "forbidden private field"):
            run_execution(self.root, self.auth, self.state, self.script)
        if self.state.exists():
            persisted = "\n".join(
                path.read_text(encoding="utf-8")
                for path in self.state.rglob("*")
                if path.is_file()
            )
            self.assertNotIn("secret", persisted)

    def test_inspect_verifies_checkpoint_and_events(self) -> None:
        result = run_execution(self.root, self.auth, self.state, self.script)
        inspected = inspect_run(self.root, self.auth, self.state)
        self.assertEqual(inspected["checkpoint"]["state"], "SUCCEEDED")
        self.assertEqual(inspected["plan"]["plan_id"], result["plan_id"])


if __name__ == "__main__":
    unittest.main()
