import hashlib
import base64
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import custody


class CustodyMeteorRound2Tests(unittest.TestCase):
    def test_two_recipients_cannot_be_primary_and_subkey_of_same_key(self):
        primary = "A" * 40
        subkey = "B" * 40
        public_listing = (
            "pub::::::::::\n"
            f"fpr:::::::::{primary}:\n"
            "sub::::::::::\n"
            f"fpr:::::::::{subkey}:\n"
        )

        def fake_run(cmd, *, check=True):
            if "--list-secret-keys" in cmd:
                return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="")
            if "--list-keys" in cmd:
                return subprocess.CompletedProcess(cmd, 0, stdout=public_listing, stderr="")
            raise AssertionError(cmd)

        with mock.patch.object(custody, "run", side_effect=fake_run):
            with self.assertRaises(custody.CustodyError):
                custody.assert_recipient_separation([primary, subkey])

    def test_authority_ref_rejects_free_text_and_newlines(self):
        candidate = {
            "schema": custody.SCHEMA,
            "bundle_id": "a" * 32,
            "key_epoch": "epoch-1",
            "plaintext": {"sha256": "0" * 64, "size": 1},
            "ciphertext": {
                "path": "/tmp/fake.gpg",
                "sha256": "1" * 64,
                "size": 1,
                "format": "OpenPGP",
                "tool": "gpg",
            },
            "recipients": ["A" * 40, "C" * 40],
            "provider": {"type": "gcs", "status": "NOT_UPLOADED"},
        }
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(
                custody,
                "gcs_upload",
                return_value={"generation": "1", "size": "1", "updateTime": "now"},
            ):
                with self.assertRaises(custody.CustodyError):
                    custody.live_upload(
                        candidate,
                        "gs://bucket/private",
                        Path(td),
                        "approved\nraw private wording",
                    )

    def test_gcs_target_rejects_generation_fragment_or_control_chars(self):
        for value in (
            "gs://bucket/private#123",
            "gs://bucket/private?x=1",
            "gs://bucket/private\nother",
        ):
            with self.subTest(value=value):
                with self.assertRaises(custody.CustodyError):
                    custody.validate_gs_base(value)

    def test_upload_binds_provider_md5_to_local_ciphertext(self):
        calls = []

        def fake_run(cmd, *, check=True):
            calls.append(cmd)
            if "describe" in cmd:
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout='{"generation":"1","size":"3","md5Hash":"WRONG"}',
                    stderr="",
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "cipher.gpg"
            local.write_bytes(b"abc")
            with mock.patch.object(custody, "run", side_effect=fake_run):
                with self.assertRaises(custody.CustodyError):
                    custody.gcs_upload(local, "gs://bucket/private/x.gpg")

    def test_upload_sends_content_md5_for_provider_transfer_check(self):
        calls = []

        def fake_run(cmd, *, check=True):
            calls.append(cmd)
            if "describe" in cmd:
                local_md5 = base64.b64encode(hashlib.md5(b"abc").digest()).decode("ascii")
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout=(
                        '{"generation":"1","size":"3","md5Hash":"'
                        + local_md5
                        + '"}'
                    ),
                    stderr="",
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / "cipher.gpg"
            local.write_bytes(b"abc")
            with mock.patch.object(custody, "run", side_effect=fake_run):
                custody.gcs_upload(local, "gs://bucket/private/x.gpg")

        upload_cmd = calls[0]
        self.assertTrue(any(arg.startswith("--content-md5=") for arg in upload_cmd))

    def test_restore_rejects_receipt_inside_public_repository_before_read(self):
        inside_repo = custody.REPO_ROOT / "DO_NOT_CREATE.receipt.json"
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            with self.assertRaises(custody.CustodyError):
                custody.restore_from_receipt(
                    inside_repo,
                    base / "restore",
                    base / "work",
                )


if __name__ == "__main__":
    unittest.main()
