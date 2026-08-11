import inspect
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock

import custody


class CustodyMeteorAttackTests(unittest.TestCase):
    def _write_manifest(self, root: Path, entries: list[dict]) -> None:
        payload = {
            "schema": custody.SCHEMA,
            "kind": "evidence-bundle-manifest",
            "hash": "sha256",
            "entries": entries,
        }
        (root / custody.INTERNAL_MANIFEST).write_text(
            json.dumps(payload, sort_keys=True), encoding="utf-8"
        )

    def test_empty_evidence_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "input"
            root.mkdir()
            with self.assertRaises(custody.CustodyError):
                custody.create_deterministic_bundle(root, Path(td) / "bundle.tar.gz")

    def test_reserved_internal_manifest_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "input"
            root.mkdir()
            (root / custody.INTERNAL_MANIFEST).write_text("source collision", encoding="utf-8")
            with self.assertRaises(custody.CustodyError):
                custody.create_deterministic_bundle(root, Path(td) / "bundle.tar.gz")

    def test_manifest_parent_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "restored"
            root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            self._write_manifest(
                root,
                [{
                    "path": "../outside.txt",
                    "size": outside.stat().st_size,
                    "sha256": custody.sha256_file(outside),
                }],
            )
            with self.assertRaises(custody.CustodyError):
                custody.verify_extracted_tree(root)

    def test_unmanifested_extra_file_makes_verification_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence.txt"
            evidence.write_text("evidence", encoding="utf-8")
            self._write_manifest(
                root,
                [{
                    "path": "evidence.txt",
                    "size": evidence.stat().st_size,
                    "sha256": custody.sha256_file(evidence),
                }],
            )
            (root / "stale-extra.txt").write_text("stale", encoding="utf-8")
            result = custody.verify_extracted_tree(root)
            self.assertEqual(result["status"], "FAIL")

    def test_duplicate_manifest_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence.txt"
            evidence.write_text("evidence", encoding="utf-8")
            entry = {
                "path": "evidence.txt",
                "size": evidence.stat().st_size,
                "sha256": custody.sha256_file(evidence),
            }
            self._write_manifest(root, [entry, dict(entry)])
            with self.assertRaises(custody.CustodyError):
                custody.verify_extracted_tree(root)

    def test_extract_into_dirty_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            archive = base / "bundle.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                payload = b"fresh"
                ti = tarfile.TarInfo("fresh.txt")
                ti.size = len(payload)
                tar.addfile(ti, io.BytesIO(payload))
            out = base / "out"
            out.mkdir()
            (out / "stale.txt").write_text("stale", encoding="utf-8")
            with self.assertRaises(custody.CustodyError):
                custody.safe_extract_tar_gz(archive, out)

    def test_new_object_upload_uses_generation_zero_precondition(self):
        calls = []

        def fake_run(cmd, *, check=True):
            calls.append(cmd)
            if "describe" in cmd:
                return subprocess.CompletedProcess(
                    cmd, 0, stdout='{"generation":"1","size":"3"}', stderr=""
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "x.gpg"
            local.write_bytes(b"abc")
            with mock.patch.object(custody, "run", side_effect=fake_run):
                custody.gcs_upload(local, "gs://bucket/private/x.gpg")

        upload_cmd = calls[0]
        self.assertIn("--if-generation-match=0", upload_cmd)
        self.assertNotIn("--no-clobber", upload_cmd)

    def test_download_api_requires_recorded_generation(self):
        params = inspect.signature(custody.gcs_download).parameters
        self.assertIn("generation", params)


if __name__ == "__main__":
    unittest.main()
