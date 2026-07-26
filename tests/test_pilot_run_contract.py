from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pilot_run_contract.cli import build_parser, load_and_validate
from pilot_run_contract.common import PilotRunContractError, fingerprint_material, sha256_value
from pilot_run_contract.models import validate_seed


class PilotRunContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.path = self.root / "pilot_run_contract/examples/value-discovery-case-001.json"
        self.seed = json.loads(self.path.read_text(encoding="utf-8"))

    def resign(self, seed: dict) -> None:
        seed["seed_fingerprint"] = sha256_value(fingerprint_material(seed))

    def test_committed_case_001_seed_is_ready(self) -> None:
        seed = load_and_validate(self.path)
        self.assertEqual(seed["readiness"]["state"], "READY_FOR_PILOT")
        self.assertEqual(seed["constraints"]["wip_limit"], 1)
        self.assertTrue(seed["constraints"]["human_gate_required"])

    def test_authority_is_non_authorizing(self) -> None:
        authority = validate_seed(copy.deepcopy(self.seed))["authority"]
        self.assertTrue(authority["advisory_only"])
        for field, value in authority.items():
            if field not in {"mode", "advisory_only"}:
                self.assertFalse(value)

    def test_widened_authority_is_rejected_even_when_resigned(self) -> None:
        seed = copy.deepcopy(self.seed)
        seed["authority"]["provider_authorized"] = True
        self.resign(seed)
        with self.assertRaisesRegex(PilotRunContractError, "authority boundary widened"):
            validate_seed(seed)

    def test_wip_above_one_is_rejected(self) -> None:
        seed = copy.deepcopy(self.seed)
        seed["constraints"]["wip_limit"] = 2
        self.resign(seed)
        with self.assertRaisesRegex(PilotRunContractError, "wip_limit"):
            validate_seed(seed)

    def test_fingerprint_drift_is_rejected(self) -> None:
        seed = copy.deepcopy(self.seed)
        seed["objective"]["current_goal"] += " changed"
        with self.assertRaisesRegex(PilotRunContractError, "fingerprint mismatch"):
            validate_seed(seed)

    def test_duplicate_stop_condition_is_rejected(self) -> None:
        seed = copy.deepcopy(self.seed)
        seed["work_policy"]["stop_conditions"].append(seed["work_policy"]["stop_conditions"][0])
        self.resign(seed)
        with self.assertRaisesRegex(PilotRunContractError, "unique"):
            validate_seed(seed)

    def test_cli_exposes_only_verify_and_summary(self) -> None:
        parser = build_parser()
        action = next(action for action in parser._actions if getattr(action, "choices", None))
        self.assertEqual(set(action.choices), {"verify", "summary"})


if __name__ == "__main__":
    unittest.main()
