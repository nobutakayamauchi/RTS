from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from execution_controller.cli import _verification_fixture
from execution_controller.controller import ControllerError, run_execution
from execution_controller.models import sha256_value
from execution_controller.store import verify_checkpoint


class ExecutionControllerStateContinuityTests(unittest.TestCase):
    def test_rehashed_discontinuous_event_chain_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "repo"
            state = base / "state"
            authorization, script = _verification_fixture(root)
            result = run_execution(root, authorization, state, script)

            run_dir = state / result["plan_id"]
            event_path = run_dir / "events.jsonl"
            rows = [
                json.loads(line)
                for line in event_path.read_text(encoding="utf-8").splitlines()
            ]

            discontinuous = dict(rows[1])
            discontinuous["state_before"] = "RUNNING"
            discontinuous["state_after"] = "FAILED"
            material = dict(discontinuous)
            material.pop("event_hash")
            material.pop("event_id")
            discontinuous["event_hash"] = sha256_value(material)
            discontinuous["event_id"] = sha256_value(
                {
                    "event_hash": discontinuous["event_hash"],
                    "sequence": discontinuous["sequence"],
                }
            )

            event_path.write_text(
                "\n".join(
                    json.dumps(row, sort_keys=True, separators=(",", ":"))
                    for row in (rows[0], discontinuous)
                )
                + "\n",
                encoding="utf-8",
            )

            checkpoint_path = run_dir / "checkpoint.json"
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            checkpoint["latest_sequence"] = discontinuous["sequence"]
            checkpoint["latest_event_hash"] = discontinuous["event_hash"]
            checkpoint["state"] = discontinuous["state_after"]
            checkpoint["attempt"] = discontinuous["attempt"]
            checkpoint["usage"] = discontinuous["usage"]
            checkpoint_path.write_text(
                json.dumps(checkpoint, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ControllerError, "state continuity mismatch"):
                verify_checkpoint(state, result["plan_id"])


if __name__ == "__main__":
    unittest.main()
