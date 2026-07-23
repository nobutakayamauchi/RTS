import json
import tempfile
import unittest
from pathlib import Path

from freezer.cli import (
    FreezerError,
    compute_score,
    load_config,
    rebuild,
    validate_item,
    verify,
)


class FreezerTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.config = load_config(self.repo_root)
        self.item = json.loads(
            (
                self.repo_root
                / "freezer"
                / "items"
                / "RTS-FRZ-000001"
                / "v001.json"
            ).read_text(encoding="utf-8")
        )

    def test_seed_item_is_valid(self):
        validate_item(self.item, self.config)

    def test_priority_score_is_deterministic(self):
        self.assertEqual(compute_score(self.item, self.config), 65.25)

    def test_effort_reduction_improves_score(self):
        easier = json.loads(json.dumps(self.item))
        easier["priority"]["effort"] = 1
        self.assertGreater(
            compute_score(easier, self.config),
            compute_score(self.item, self.config),
        )

    def test_invalid_score_is_rejected(self):
        invalid = json.loads(json.dumps(self.item))
        invalid["priority"]["impact"] = 6
        with self.assertRaises(FreezerError):
            validate_item(invalid, self.config)

    def test_rebuild_and_verify(self):
        rows = rebuild(self.repo_root)
        self.assertEqual(rows[0]["item_id"], "RTS-FRZ-000001")
        self.assertEqual(verify(self.repo_root), [])


if __name__ == "__main__":
    unittest.main()
