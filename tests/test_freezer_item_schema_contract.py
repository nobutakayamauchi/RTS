from __future__ import annotations

import unittest
from pathlib import Path

from freezer.cli import FreezerError, iter_current_items, load_config, load_current, validate_item


ROOT = Path(__file__).resolve().parents[1]


class FreezerItemSchemaContractTests(unittest.TestCase):
    def test_current_string_list_fields_match_published_contract(self) -> None:
        fields = {
            "preserved_value",
            "trigger_conditions",
            "negative_triggers",
            "dependencies",
            "source_refs",
            "possible_destinations",
            "tags",
        }
        for item in iter_current_items(ROOT):
            for field in fields:
                with self.subTest(item_id=item["item_id"], field=field):
                    self.assertIsInstance(item[field], list)
                    self.assertTrue(all(isinstance(value, str) for value in item[field]))

    def test_string_preserved_value_is_rejected(self) -> None:
        item = dict(load_current(ROOT, "RTS-FRZ-000004"))
        item["preserved_value"] = "invalid scalar"
        with self.assertRaisesRegex(FreezerError, "preserved_value must be an array of strings"):
            validate_item(item, load_config(ROOT))


if __name__ == "__main__":
    unittest.main()
