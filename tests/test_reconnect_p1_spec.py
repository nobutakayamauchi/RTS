from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from pilot_run_contract.cli import load_and_validate


def fingerprint(value: dict, field: str) -> str:
    material = copy.deepcopy(value)
    actual = material.pop(field)
    rendered = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if actual != expected:
        raise AssertionError(f"{field} mismatch")
    return actual


class ReconnectP1SpecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.run_dir = self.root / "pilot_runs/reconnect_pilot_p1"
        self.seed_path = self.root / "pilot_run_contract/packs/reconnect_seed_pack_v1/seed_p1_master_spec.json"

    def test_p1_seed_is_ready_and_non_authorizing(self) -> None:
        seed = load_and_validate(self.seed_path)
        self.assertEqual(seed["seed_id"], "RTS-PILOT-SEED-RECONNECT-MASTER-SPEC-V1")
        self.assertEqual(seed["constraints"]["wip_limit"], 1)
        self.assertFalse(seed["authority"]["target_write_authorized"])

    def test_human_decision_is_approved_and_fingerprinted(self) -> None:
        value = json.loads((self.run_dir / "HUMAN_SCOPE_DECISION_0001.json").read_text(encoding="utf-8"))
        fingerprint(value, "decision_fingerprint")
        self.assertEqual(value["decision_type"], "APPROVE_P1_P3")
        self.assertEqual(value["decision_status"], "APPROVED")

    def test_p1_run_stops_before_implementation(self) -> None:
        run = json.loads((self.run_dir / "run_record.json").read_text(encoding="utf-8"))
        fingerprint(run, "run_fingerprint")
        self.assertEqual(run["state"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(run["result"], "PASS_MASTER_SPEC_READY")
        self.assertFalse(run["observed"]["implementation_performed"])

    def test_checkpoint_is_bound_to_run_sources(self) -> None:
        run = json.loads((self.run_dir / "run_record.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((self.run_dir / "checkpoint_0001.json").read_text(encoding="utf-8"))
        fingerprint(checkpoint, "checkpoint_fingerprint")
        self.assertEqual(checkpoint["source"], run["source"])
        self.assertFalse(checkpoint["authority"]["target_write_authorized"])

    def test_required_p1_artifacts_exist(self) -> None:
        required = {
            "MASTER_PRODUCT_SPECIFICATION_V1.md", "HYPOTHESIS_MAP_V1.md",
            "CANONICAL_DATA_MODEL_V1.md", "MVP_IMPLEMENTATION_CONTRACT_V1.md",
            "ACCEPTANCE_CRITERIA_V1.md", "FUTURE_BRANCH_UNLOCK_TRIGGERS_V1.md",
            "CONTRADICTION_AUDIT_V1.md", "P3_HUMAN_REVIEW_PACKET_V1.md",
        }
        self.assertEqual(required, {p.name for p in self.run_dir.iterdir() if p.name in required})


if __name__ == "__main__":
    unittest.main()
