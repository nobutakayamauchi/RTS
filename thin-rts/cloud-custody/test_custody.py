import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import custody


class CustodyPureTests(unittest.TestCase):
    def test_deterministic_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "input"
            root.mkdir()
            (root / "a.txt").write_text("alpha\n", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.bin").write_bytes(b"beta\x00")
            out1 = Path(td) / "one.tar.gz"
            out2 = Path(td) / "two.tar.gz"
            r1 = custody.create_deterministic_bundle(root, out1)
            r2 = custody.create_deterministic_bundle(root, out2)
            self.assertEqual(r1["archive_sha256"], r2["archive_sha256"])
            self.assertEqual(out1.read_bytes(), out2.read_bytes())

    def test_manifest_verification_detects_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "input"
            root.mkdir()
            (root / "evidence.txt").write_text("original", encoding="utf-8")
            archive = Path(td) / "bundle.tar.gz"
            custody.create_deterministic_bundle(root, archive)
            extracted = Path(td) / "out"
            custody.safe_extract_tar_gz(archive, extracted)
            self.assertEqual(custody.verify_extracted_tree(extracted)["status"], "PASS")
            (extracted / "evidence.txt").write_text("mutated", encoding="utf-8")
            self.assertEqual(custody.verify_extracted_tree(extracted)["status"], "FAIL")

    def test_safe_extract_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "evil.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                payload = b"evil"
                ti = tarfile.TarInfo("../escape.txt")
                ti.size = len(payload)
                tar.addfile(ti, io.BytesIO(payload))
            with self.assertRaises(custody.CustodyError):
                custody.safe_extract_tar_gz(archive, Path(td) / "out")

    def test_gcs_target_requires_prefix(self):
        with self.assertRaises(custody.CustodyError):
            custody.validate_gs_base("gs://bucket")
        self.assertEqual(custody.validate_gs_base("gs://bucket/private/custody"), "gs://bucket/private/custody")

    def test_full_fingerprint_required(self):
        with self.assertRaises(custody.CustodyError):
            custody._validate_fingerprint("DEADBEEF")
        value = "A" * 40
        self.assertEqual(custody._validate_fingerprint(value), value)


if __name__ == "__main__":
    unittest.main()
