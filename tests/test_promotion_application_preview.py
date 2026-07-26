from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from promotion_application_preview.cli import build_parser
from promotion_application_preview.common import PromotionApplicationPreviewError, sha256_value
from promotion_application_preview.corpus import _verify_forbidden_imports, source_paths, verify_all
from promotion_application_preview.generation import generate_preview
from promotion_application_preview.models import fingerprint_material, validate_preview


class PromotionApplicationPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def resign(self, preview: dict) -> None:
        preview["preview_id"] = ""
        preview["preview_fingerprint"] = ""
        fingerprint = sha256_value(fingerprint_material(preview))
        preview["preview_fingerprint"] = fingerprint
        preview["preview_id"] = f"RTS-PROMOTION-PREVIEW-{fingerprint[:16].upper()}"

    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(generate_preview(self.root), generate_preview(self.root))

    def test_current_state_is_blocked_and_non_applying(self) -> None:
        preview = generate_preview(self.root)
        self.assertEqual(preview["state"], "BLOCKED")
        self.assertIn("human review approval is not current", preview["blockers"])
        self.assertEqual(preview["authority"]["approval_status"], "NOT_APPROVED")
        self.assertEqual(preview["authority"]["application_status"], "NOT_APPLIED")
        self.assertFalse(preview["authority"]["target_write_authorized"])
        self.assertFalse(preview["authority"]["adjacent_repository_write_authorized"])

    def test_proposed_change_is_hash_pinned(self) -> None:
        change = generate_preview(self.root)["proposed_change_set"][0]
        self.assertEqual(change["operation"], "REPLACE_FILE")
        self.assertEqual(change["repository"], "nobutakayamauchi/RTS-Skills-")
        self.assertEqual(change["path"], "rts-skills/bundles/feature-build.md")
        self.assertNotEqual(change["expected_before_sha256"], change["proposed_after_sha256"])

    def test_widened_write_authority_is_rejected(self) -> None:
        preview = copy.deepcopy(generate_preview(self.root))
        preview["authority"]["target_write_authorized"] = True
        self.resign(preview)
        with self.assertRaisesRegex(PromotionApplicationPreviewError, "authority boundary widened"):
            validate_preview(preview)

    def test_target_path_escape_is_rejected(self) -> None:
        preview = copy.deepcopy(generate_preview(self.root))
        preview["proposed_change_set"][0]["path"] = "../escape.md"
        self.resign(preview)
        with self.assertRaisesRegex(PromotionApplicationPreviewError, "path boundary"):
            validate_preview(preview)

    def test_generation_does_not_modify_sources(self) -> None:
        before = {path: path.read_bytes() for path in source_paths(self.root)}
        generate_preview(self.root)
        after = {path: path.read_bytes() for path in source_paths(self.root)}
        self.assertEqual(before, after)

    def test_forbidden_external_action_import_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(self.root / "promotion_application_preview", root / "promotion_application_preview")
            (root / "promotion_application_preview" / "unsafe.py").write_text(
                "import subprocess\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(PromotionApplicationPreviewError, "forbidden external-action import"):
                _verify_forbidden_imports(root)

    def test_cli_has_no_apply_or_write_command(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("generate", help_text)
        self.assertIn("verify", help_text)
        self.assertIn("summary", help_text)
        self.assertNotIn("\n    apply", help_text)
        self.assertNotIn("\n    write", help_text)

    def test_committed_preview_matches(self) -> None:
        path = self.root / "promotion_application_preview/previews/current.json"
        committed = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(committed, generate_preview(self.root))
        summary = verify_all(self.root)
        self.assertEqual(summary["state"], "BLOCKED")
        self.assertEqual(summary["application_status"], "NOT_APPLIED")


if __name__ == "__main__":
    unittest.main()
