from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from pilot_run_contract.cli import load_and_validate


class ReconnectSeedPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.pack = self.root / "pilot_run_contract/packs/reconnect_seed_pack_v1"
        self.seed_path = self.pack / "seed_active_scope_cut.json"
        self.run_path = self.root / "pilot_runs/reconnect_pilot_p0/run_record.json"
        self.checkpoint_path = self.root / "pilot_runs/reconnect_pilot_p0/checkpoint_0001.json"

    def test_active_seed_is_ready_and_non_authorizing(self) -> None:
        seed = load_and_validate(self.seed_path)
        self.assertEqual(seed["readiness"]["state"], "READY_FOR_PILOT")
        self.assertEqual(seed["constraints"]["wip_limit"], 1)
        self.assertTrue(seed["constraints"]["human_gate_required"])
        self.assertTrue(seed["authority"]["advisory_only"])
        for field, value in seed["authority"].items():
            if field not in {"mode", "advisory_only"}:
                self.assertFalse(value)

    def test_pack_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(self.pack / "validate_pack.py")],
            cwd=self.root, check=False, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PACK READY_FOR_PILOT", result.stdout)

    def test_scope_profiles_and_sources_are_complete(self) -> None:
        profiles = json.loads((self.pack / "scope_profiles.json").read_text(encoding="utf-8"))
        self.assertEqual(profiles["active_profile"], "P0_SCOPE_CUT")
        self.assertEqual(len(profiles["profiles"]), 7)
        seed = json.loads(self.seed_path.read_text(encoding="utf-8"))
        for source in seed["inputs"]["source_refs"]:
            if source.endswith((".md", ".json")):
                self.assertTrue((self.pack / source).is_file(), source)

    def test_run_stops_at_human_gate(self) -> None:
        run = json.loads(self.run_path.read_text(encoding="utf-8"))
        self.assertEqual(run["state"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(run["result"], "PASS_SCOPE_CUT_READY")
        self.assertFalse(run["observed"]["implementation_performed"])
        self.assertFalse(run["observed"]["publication_performed"])
        self.assertFalse(run["observed"]["provider_used"])
        self.assertEqual(run["recommendation"]["first_next_scope"], "P1_MASTER_SPEC")

    def test_run_and_checkpoint_fingerprints_are_current(self) -> None:
        run = json.loads(self.run_path.read_text(encoding="utf-8"))
        material = copy.deepcopy(run)
        actual = material.pop("run_fingerprint")
        expected = hashlib.sha256(
            json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(actual, expected)

        checkpoint = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        material = copy.deepcopy(checkpoint)
        actual = material.pop("checkpoint_fingerprint")
        expected = hashlib.sha256(
            json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(actual, expected)

    def test_checkpoint_matches_pack(self) -> None:
        seed = json.loads(self.seed_path.read_text(encoding="utf-8"))
        checkpoint = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        manifest_digest = hashlib.sha256((self.pack / "manifest.sha256").read_bytes()).hexdigest()
        self.assertEqual(checkpoint["seed_fingerprint"], seed["seed_fingerprint"])
        self.assertEqual(checkpoint["pack_manifest_sha256"], manifest_digest)
        self.assertFalse(checkpoint["authority"]["implementation_authorized"])


if __name__ == "__main__":
    unittest.main()
