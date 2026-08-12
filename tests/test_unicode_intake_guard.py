from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_invisible_unicode as guard
import egress_quarantine
import intake_quarantine
import quarantine_core


class UnicodeIntakeGuardTests(unittest.TestCase):
    def make_file(self, relative: str, text: str) -> Path:
        root = Path(tempfile.mkdtemp())
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_ascii_code_is_clean(self) -> None:
        self.assertEqual(guard.scan_file(self.make_file("x.py", "print('ok')\n")), [])

    def test_zero_width_is_blocked(self) -> None:
        payload = "x=1" + chr(0x200B) + "\n"
        findings = guard.scan_file(self.make_file("x.py", payload))
        self.assertTrue(any(f.codepoint == 0x200B for f in findings))

    def test_basic_variation_selector_is_blocked_in_code(self) -> None:
        payload = "const x='a" + chr(0xFE0F) + "';\n"
        findings = guard.scan_file(self.make_file("x.js", payload))
        self.assertTrue(any(f.codepoint == 0xFE0F for f in findings))

    def test_supplementary_variation_selector_is_blocked_in_markdown(self) -> None:
        payload = "hello" + chr(0xE0100) + "\n"
        findings = guard.scan_file(self.make_file("x.md", payload))
        self.assertTrue(any(f.codepoint == 0xE0100 for f in findings))

    def test_normal_emoji_selector_is_allowed_in_markdown(self) -> None:
        payload = "hello " + chr(0x2764) + chr(0xFE0F) + "\n"
        findings = guard.scan_file(self.make_file("x.md", payload))
        self.assertEqual(findings, [])

    def test_non_emoji_basic_selector_is_blocked_in_markdown(self) -> None:
        payload = "hello" + chr(0xFE00) + "\n"
        findings = guard.scan_file(self.make_file("x.md", payload))
        self.assertTrue(any(f.codepoint == 0xFE00 for f in findings))

    def test_github_workflow_is_not_excluded(self) -> None:
        path = self.make_file(".github/workflows/x.yml", "name: x\n")
        self.assertTrue(guard.should_check(path))

    def test_dependency_tree_is_excluded(self) -> None:
        path = self.make_file("node_modules/x.js", "const x=1\n")
        self.assertFalse(guard.should_check(path))

    def test_core_fails_closed_without_boundary_identity(self) -> None:
        path = self.make_file("x.py", "print('ok')\n")
        record = quarantine_core.inspect_file(path, phase="test", identity={})
        self.assertEqual(record["verdict"], "BLOCK")
        self.assertIn("missing boundary identity", record["findings"])

    def test_intake_record_hashes_and_cleans_supported_file(self) -> None:
        path = self.make_file("x.py", "print('ok')\n")
        record = intake_quarantine.inspect_file(path, "commit:abc123")
        self.assertEqual(record["verdict"], "CLEAN")
        self.assertEqual(len(record["sha256"]), 64)
        self.assertEqual(record["source_id"], "commit:abc123")
        self.assertEqual(record["phase"], "pre-witness-intake")

    def test_intake_fails_closed_for_unsupported_file(self) -> None:
        path = self.make_file("x.bin", "not executed")
        record = intake_quarantine.inspect_file(path, "commit:abc123")
        self.assertEqual(record["verdict"], "BLOCK")
        self.assertIn("unsupported/unscanned", record["findings"][0])

    def test_egress_hashes_and_cleans_supported_output(self) -> None:
        path = self.make_file("generated.py", "print('ok')\n")
        record = egress_quarantine.inspect_file(
            path,
            "run:ultimate-loop-123",
            "branch:feature/example",
        )
        self.assertEqual(record["verdict"], "CLEAN")
        self.assertEqual(len(record["sha256"]), 64)
        self.assertEqual(record["producer_id"], "run:ultimate-loop-123")
        self.assertEqual(record["target_id"], "branch:feature/example")
        self.assertEqual(record["phase"], "pre-promotion-egress")

    def test_egress_blocks_variation_selector_output(self) -> None:
        payload = "const x='a" + chr(0xFE0F) + "';\n"
        path = self.make_file("generated.js", payload)
        record = egress_quarantine.inspect_file(
            path,
            "run:ultimate-loop-123",
            "branch:feature/example",
        )
        self.assertEqual(record["verdict"], "BLOCK")
        self.assertTrue(any("U+FE0F" in item for item in record["findings"]))

    def test_egress_fails_closed_for_unsupported_output(self) -> None:
        path = self.make_file("generated.bin", "not executed")
        record = egress_quarantine.inspect_file(
            path,
            "run:ultimate-loop-123",
            "release:v0",
        )
        self.assertEqual(record["verdict"], "BLOCK")
        self.assertIn("unsupported/unscanned", record["findings"][0])


if __name__ == "__main__":
    unittest.main()
