from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CLOUD = HERE.parent / "cloud-custody"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CLOUD))

import continuity
import custody


class ContinuityCustodyIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original_gnupg = os.environ.get("GNUPGHOME")

    def tearDown(self) -> None:
        if self.original_gnupg is None:
            os.environ.pop("GNUPGHOME", None)
        else:
            os.environ["GNUPGHOME"] = self.original_gnupg
        self.tmp.cleanup()

    def run_cmd(self, *args: str, env=None, check=True) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(
            list(args),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
        )
        if check and cp.returncode != 0:
            raise AssertionError(f"command failed: {args}\n{cp.stdout}\n{cp.stderr}")
        return cp

    def make_repo(self) -> Path:
        repo = self.root / "repo"
        self.run_cmd("git", "init", str(repo))
        self.run_cmd("git", "-C", str(repo), "config", "user.email", "test@example.invalid")
        self.run_cmd("git", "-C", str(repo), "config", "user.name", "Recovery Integration")
        (repo / "critical.txt").write_text("critical-state\n", encoding="utf-8")
        self.run_cmd("git", "-C", str(repo), "add", "critical.txt")
        self.run_cmd("git", "-C", str(repo), "commit", "-m", "critical state")
        self.run_cmd("git", "-C", str(repo), "tag", "continuity-test")
        return repo

    def gpg_env(self, home: Path) -> dict[str, str]:
        home.mkdir(parents=True, exist_ok=True)
        os.chmod(home, 0o700)
        env = os.environ.copy()
        env["GNUPGHOME"] = str(home)
        return env

    def generate_recovery_identity(self, name: str) -> tuple[Path, str, bytes]:
        home = self.root / f"gnupg-{name}"
        env = self.gpg_env(home)
        uid = f"Recovery {name} <{name}@example.invalid>"
        self.run_cmd(
            "gpg", "--batch", "--passphrase", "", "--quick-gen-key",
            uid, "rsa2048", "cert", "1d", env=env,
        )
        listing = self.run_cmd(
            "gpg", "--batch", "--with-colons", "--fingerprint", "--list-keys", uid,
            env=env,
        ).stdout
        fpr = None
        saw_pub = False
        for line in listing.splitlines():
            parts = line.split(":")
            if parts[0] == "pub":
                saw_pub = True
            elif saw_pub and parts[0] == "fpr" and len(parts) > 9 and parts[9]:
                fpr = parts[9]
                break
        self.assertIsNotNone(fpr)
        assert fpr is not None
        self.run_cmd(
            "gpg", "--batch", "--passphrase", "", "--quick-add-key",
            fpr, "rsa2048", "encr", "1d", env=env,
        )
        public = subprocess.run(
            ["gpg", "--batch", "--armor", "--export", fpr],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env=env,
        ).stdout
        return home, fpr, public

    def import_public(self, producer: Path, public: bytes) -> None:
        env = self.gpg_env(producer)
        cp = subprocess.run(
            ["gpg", "--batch", "--import"],
            input=public,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
        )
        if cp.returncode != 0:
            raise AssertionError(cp.stderr.decode("utf-8", errors="replace"))

    def test_real_gpg_two_recipient_encryption_survives_primary_domain_loss(self) -> None:
        if shutil.which("gpg") is None:
            self.fail("gpg is required external continuity dependency for this integration")

        repo = self.make_repo()
        capsule = self.root / "capsule"
        continuity.capture_repo(repo, capsule)
        self.assertEqual(continuity.verify_capsule(capsule)["status"], "PASS")

        home_a, fpr_a, pub_a = self.generate_recovery_identity("a")
        home_b, fpr_b, pub_b = self.generate_recovery_identity("b")
        producer = self.root / "gnupg-producer"
        self.import_public(producer, pub_a)
        self.import_public(producer, pub_b)

        os.environ["GNUPGHOME"] = str(producer)
        candidate = custody.build_local_candidate(
            capsule,
            self.root / "custody-work",
            [fpr_a, fpr_b],
            "continuity-test-epoch",
        )
        ciphertext = Path(candidate["ciphertext"]["path"])
        self.assertTrue(ciphertext.is_file())

        replica_receipt = self.root / "replicas.json"
        continuity.replicate_protected_artifact(
            ciphertext,
            [
                ("primary-domain", self.root / "primary-domain"),
                ("alternate-domain", self.root / "alternate-domain"),
            ],
            replica_receipt,
        )

        # Meteor: primary storage disappears completely.
        shutil.rmtree(self.root / "primary-domain")
        recovered_ciphertext = self.root / "recovered.gpg"
        recovered = continuity.recover_replica(
            replica_receipt,
            "alternate-domain",
            recovered_ciphertext,
        )
        self.assertEqual(recovered["status"], "PASS")

        # Fresh recovery trust boundary: only recovery identity B is available.
        os.environ["GNUPGHOME"] = str(home_b)
        recovered_archive = self.root / "recovered.tar.gz"
        custody.decrypt_gpg(recovered_ciphertext, recovered_archive)
        self.assertEqual(
            custody.sha256_file(recovered_archive),
            candidate["plaintext"]["sha256"],
        )

        restored_capsule = self.root / "restored-capsule"
        custody.safe_extract_tar_gz(recovered_archive, restored_capsule)
        verified_tree = custody.verify_extracted_tree(restored_capsule)
        self.assertEqual(verified_tree["status"], "PASS")

        final_restore = self.root / "final-restore"
        drill = continuity.drill_capsule(restored_capsule, final_restore)
        self.assertEqual(drill["status"], "PASS")
        self.assertEqual(drill["code_execution"], "NOT_PERFORMED")

    def test_wrong_recovery_identity_cannot_decrypt(self) -> None:
        if shutil.which("gpg") is None:
            self.fail("gpg is required external continuity dependency for this integration")

        repo = self.make_repo()
        capsule = self.root / "capsule"
        continuity.capture_repo(repo, capsule)
        _, fpr_a, pub_a = self.generate_recovery_identity("a")
        _, fpr_b, pub_b = self.generate_recovery_identity("b")
        wrong_home, _, _ = self.generate_recovery_identity("wrong")
        producer = self.root / "gnupg-producer"
        self.import_public(producer, pub_a)
        self.import_public(producer, pub_b)
        os.environ["GNUPGHOME"] = str(producer)
        candidate = custody.build_local_candidate(
            capsule,
            self.root / "custody-work",
            [fpr_a, fpr_b],
            "continuity-test-epoch",
        )
        os.environ["GNUPGHOME"] = str(wrong_home)
        with self.assertRaises(custody.CustodyError):
            custody.decrypt_gpg(
                Path(candidate["ciphertext"]["path"]),
                self.root / "should-not-decrypt.tar.gz",
            )


if __name__ == "__main__":
    unittest.main()
