from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import continuity


class ContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cmd(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        cp = subprocess.run(
            list(args), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
        if check and cp.returncode != 0:
            raise AssertionError(f"command failed: {args}\n{cp.stdout}\n{cp.stderr}")
        return cp

    def make_repo(self, name: str = "repo") -> Path:
        repo = self.root / name
        self.run_cmd("git", "init", str(repo))
        self.run_cmd("git", "-C", str(repo), "config", "user.email", "test@example.invalid")
        self.run_cmd("git", "-C", str(repo), "config", "user.name", "Continuity Test")
        (repo / "alpha.txt").write_text("alpha\n", encoding="utf-8")
        self.run_cmd("git", "-C", str(repo), "add", "alpha.txt")
        self.run_cmd("git", "-C", str(repo), "commit", "-m", "alpha")
        self.run_cmd("git", "-C", str(repo), "tag", "v0")
        self.run_cmd("git", "-C", str(repo), "branch", "recovery-test")
        return repo

    def make_platform_export(self, *, secret_ok: bool = True, scope=None) -> Path:
        root = self.root / "platform"
        root.mkdir()
        payload = {
            "schema": continuity.PLATFORM_ATTESTATION_SCHEMA,
            "producer_id": "fixture:provider-export-v0",
            "captured_at": "2026-08-13T00:00:00Z",
            "secret_values_excluded": secret_ok,
            "scope": scope or ["issues", "pull_requests", "repository_rules"],
        }
        (root / "EXPORT_ATTESTATION.json").write_text(json.dumps(payload), encoding="utf-8")
        (root / "issues.json").write_text("[]\n", encoding="utf-8")
        (root / "pulls.json").write_text("[]\n", encoding="utf-8")
        (root / "rules.json").write_text("{}\n", encoding="utf-8")
        return root

    def capture(self, repo: Path, platform: bool = False) -> Path:
        capsule = self.root / f"capsule-{repo.name}"
        export = self.make_platform_export() if platform else None
        continuity.capture_repo(
            repo,
            capsule,
            export,
            {"issues", "pull_requests", "repository_rules"} if platform else set(),
            platform,
        )
        return capsule

    def test_clean_capture_and_fresh_drill_preserve_refs(self) -> None:
        repo = self.make_repo()
        capsule = self.capture(repo, platform=True)
        self.assertEqual(continuity.verify_capsule(capsule)["status"], "PASS")
        drill = continuity.drill_capsule(capsule, self.root / "restore")
        self.assertEqual(drill["status"], "PASS")
        self.assertEqual(drill["platform_export"], "PASS")
        self.assertEqual(drill["code_execution"], "NOT_PERFORMED")

    def test_dirty_tree_is_rejected(self) -> None:
        repo = self.make_repo()
        (repo / "uncommitted.txt").write_text("would be lost\n", encoding="utf-8")
        with self.assertRaisesRegex(continuity.ContinuityError, "dirty/untracked"):
            continuity.capture_repo(repo, self.root / "capsule")

    def test_shallow_clone_is_rejected(self) -> None:
        source = self.make_repo("source")
        (source / "beta.txt").write_text("beta\n", encoding="utf-8")
        self.run_cmd("git", "-C", str(source), "add", "beta.txt")
        self.run_cmd("git", "-C", str(source), "commit", "-m", "beta")
        shallow = self.root / "shallow"
        self.run_cmd("git", "clone", "--depth", "1", source.as_uri(), str(shallow))
        with self.assertRaisesRegex(continuity.ContinuityError, "shallow"):
            continuity.capture_repo(shallow, self.root / "capsule")

    def test_submodule_and_lfs_partial_custody_are_rejected(self) -> None:
        repo = self.make_repo("submodule")
        (repo / ".gitmodules").write_text('[submodule "x"]\n\tpath=x\n\turl=https://example.invalid/x\n')
        self.run_cmd("git", "-C", str(repo), "add", ".gitmodules")
        self.run_cmd("git", "-C", str(repo), "commit", "-m", "submodule")
        with self.assertRaisesRegex(continuity.ContinuityError, "submodules"):
            continuity.capture_repo(repo, self.root / "capsule-submodule")

        repo2 = self.make_repo("lfs")
        (repo2 / ".gitattributes").write_text("*.bin filter=lfs diff=lfs merge=lfs -text\n")
        self.run_cmd("git", "-C", str(repo2), "add", ".gitattributes")
        self.run_cmd("git", "-C", str(repo2), "commit", "-m", "lfs")
        with self.assertRaisesRegex(continuity.ContinuityError, "Git LFS"):
            continuity.capture_repo(repo2, self.root / "capsule-lfs")

    def test_platform_export_is_explicit_fail_closed_scope(self) -> None:
        repo = self.make_repo()
        with self.assertRaisesRegex(continuity.ContinuityError, "required"):
            continuity.capture_repo(repo, self.root / "missing", require_platform_export=True)

        bad_secret = self.make_platform_export(secret_ok=False)
        with self.assertRaisesRegex(continuity.ContinuityError, "secret values"):
            continuity.capture_repo(repo, self.root / "bad-secret", bad_secret)

    def test_platform_scope_gap_is_rejected(self) -> None:
        repo = self.make_repo()
        export = self.make_platform_export(scope=["issues"])
        with self.assertRaisesRegex(continuity.ContinuityError, "missing required scope"):
            continuity.capture_repo(
                repo,
                self.root / "scope-gap",
                export,
                {"issues", "pull_requests"},
                True,
            )

    def test_bundle_manifest_and_platform_tamper_are_detected(self) -> None:
        repo = self.make_repo("bundle")
        capsule = self.capture(repo)
        bundle = capsule / "repository.bundle"
        data = bytearray(bundle.read_bytes())
        data[len(data) // 2] ^= 1
        bundle.write_bytes(data)
        with self.assertRaises(continuity.ContinuityError):
            continuity.verify_capsule(capsule)

        repo2 = self.make_repo("manifest")
        capsule2 = self.capture(repo2)
        manifest_path = capsule2 / continuity.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text("utf-8"))
        first_ref = next(iter(manifest["source"]["refs"]))
        manifest["source"]["refs"][first_ref] = "0" * 40
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(continuity.ContinuityError, "refs"):
            continuity.verify_capsule(capsule2)

        repo3 = self.make_repo("platform-tamper")
        capsule3 = self.capture(repo3, platform=True)
        archive = capsule3 / "platform-export.tar.gz"
        archive.write_bytes(archive.read_bytes() + b"tamper")
        with self.assertRaisesRegex(continuity.ContinuityError, "digest"):
            continuity.verify_capsule(capsule3)

    def test_stale_restore_directory_is_rejected(self) -> None:
        repo = self.make_repo()
        capsule = self.capture(repo)
        restore = self.root / "restore"
        restore.mkdir()
        (restore / "stale.txt").write_text("stale\n")
        with self.assertRaisesRegex(continuity.ContinuityError, "empty"):
            continuity.drill_capsule(capsule, restore)

    def test_replica_domains_must_be_distinct_and_non_overlapping(self) -> None:
        artifact = self.root / "opaque.gpg"
        artifact.write_bytes(b"ciphertext")
        with self.assertRaisesRegex(continuity.ContinuityError, "at least two"):
            continuity.replicate_protected_artifact(
                artifact, [("a", self.root / "a")], self.root / "r1.json"
            )
        with self.assertRaisesRegex(continuity.ContinuityError, "duplicate failure-domain"):
            continuity.replicate_protected_artifact(
                artifact,
                [("same", self.root / "a"), ("same", self.root / "b")],
                self.root / "r2.json",
            )
        with self.assertRaisesRegex(continuity.ContinuityError, "nested"):
            continuity.replicate_protected_artifact(
                artifact,
                [("a", self.root / "root"), ("b", self.root / "root" / "child")],
                self.root / "r3.json",
            )

    def test_alternate_domain_survives_loss_and_corruption(self) -> None:
        artifact = self.root / "opaque.gpg"
        artifact.write_bytes(b"ciphertext-v1")
        receipt_path = self.root / "replicas.json"
        receipt = continuity.replicate_protected_artifact(
            artifact,
            [("domain-a", self.root / "a"), ("domain-b", self.root / "b")],
            receipt_path,
        )

        # Corrupt A: recovery must stop on A, not silently accept it.
        Path(receipt["replicas"][0]["path"]).write_bytes(b"corrupt")
        with self.assertRaisesRegex(continuity.ContinuityError, "corruption"):
            continuity.recover_replica(receipt_path, "domain-a", self.root / "bad.gpg")

        # B still recovers. Then model total loss of A.
        good = continuity.recover_replica(receipt_path, "domain-b", self.root / "good.gpg")
        self.assertEqual(good["status"], "PASS")
        shutil.rmtree(self.root / "a")
        good2 = continuity.recover_replica(receipt_path, "domain-b", self.root / "good2.gpg")
        self.assertEqual(good2["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
