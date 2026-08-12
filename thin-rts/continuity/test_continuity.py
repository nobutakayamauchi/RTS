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

    def run(self, *args, cwd: Path | None = None, check: bool = True):  # type: ignore[override]
        cp = subprocess.run(
            list(args),
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and cp.returncode != 0:
            raise AssertionError(f"command failed: {args}\n{cp.stdout}\n{cp.stderr}")
        return cp

    def make_repo(self, name: str = "repo") -> Path:
        repo = self.root / name
        self.run("git", "init", str(repo))
        self.run("git", "-C", str(repo), "config", "user.email", "test@example.invalid")
        self.run("git", "-C", str(repo), "config", "user.name", "Continuity Test")
        (repo / "alpha.txt").write_text("alpha\n", encoding="utf-8")
        self.run("git", "-C", str(repo), "add", "alpha.txt")
        self.run("git", "-C", str(repo), "commit", "-m", "alpha")
        self.run("git", "-C", str(repo), "tag", "v0")
        self.run("git", "-C", str(repo), "branch", "recovery-test")
        return repo

    def make_platform_export(self, *, secret_values_excluded: bool = True, scope=None) -> Path:
        root = self.root / "platform"
        root.mkdir()
        scope = scope or ["issues", "pull_requests", "repository_rules"]
        attestation = {
            "schema": continuity.PLATFORM_ATTESTATION_SCHEMA,
            "producer_id": "fixture:github-export-v0",
            "captured_at": "2026-08-13T00:00:00Z",
            "secret_values_excluded": secret_values_excluded,
            "scope": scope,
        }
        (root / "EXPORT_ATTESTATION.json").write_text(
            json.dumps(attestation), encoding="utf-8"
        )
        (root / "issues.json").write_text("[]\n", encoding="utf-8")
        (root / "pulls.json").write_text("[]\n", encoding="utf-8")
        (root / "rules.json").write_text("{}\n", encoding="utf-8")
        return root

    def capture(self, repo: Path, *, platform: bool = False) -> Path:
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
        verified = continuity.verify_capsule(capsule)
        self.assertEqual(verified["status"], "PASS")
        restored = continuity.drill_capsule(capsule, self.root / "restore")
        self.assertEqual(restored["status"], "PASS")
        self.assertEqual(restored["platform_export"], "PASS")
        self.assertEqual(restored["code_execution"], "NOT_PERFORMED")

    def test_dirty_tree_is_rejected(self) -> None:
        repo = self.make_repo()
        (repo / "uncommitted.txt").write_text("lost if ignored\n", encoding="utf-8")
        with self.assertRaisesRegex(continuity.ContinuityError, "dirty/untracked"):
            continuity.capture_repo(repo, self.root / "capsule")

    def test_shallow_clone_is_rejected(self) -> None:
        source = self.make_repo("source")
        (source / "beta.txt").write_text("beta\n", encoding="utf-8")
        self.run("git", "-C", str(source), "add", "beta.txt")
        self.run("git", "-C", str(source), "commit", "-m", "beta")
        shallow = self.root / "shallow"
        self.run("git", "clone", "--depth", "1", source.as_uri(), str(shallow))
        with self.assertRaisesRegex(continuity.ContinuityError, "shallow"):
            continuity.capture_repo(shallow, self.root / "capsule")

    def test_submodule_marker_is_rejected(self) -> None:
        repo = self.make_repo()
        (repo / ".gitmodules").write_text(
            '[submodule "x"]\n\tpath = x\n\turl = https://example.invalid/x.git\n',
            encoding="utf-8",
        )
        self.run("git", "-C", str(repo), "add", ".gitmodules")
        self.run("git", "-C", str(repo), "commit", "-m", "submodule marker")
        with self.assertRaisesRegex(continuity.ContinuityError, "submodules"):
            continuity.capture_repo(repo, self.root / "capsule")

    def test_lfs_pointer_policy_is_rejected(self) -> None:
        repo = self.make_repo()
        (repo / ".gitattributes").write_text("*.bin filter=lfs diff=lfs merge=lfs -text\n")
        self.run("git", "-C", str(repo), "add", ".gitattributes")
        self.run("git", "-C", str(repo), "commit", "-m", "lfs marker")
        with self.assertRaisesRegex(continuity.ContinuityError, "Git LFS"):
            continuity.capture_repo(repo, self.root / "capsule")

    def test_required_platform_export_missing_is_rejected(self) -> None:
        repo = self.make_repo()
        with self.assertRaisesRegex(continuity.ContinuityError, "required"):
            continuity.capture_repo(
                repo,
                self.root / "capsule",
                require_platform_export=True,
            )

    def test_platform_export_must_attest_no_secret_values(self) -> None:
        repo = self.make_repo()
        export = self.make_platform_export(secret_values_excluded=False)
        with self.assertRaisesRegex(continuity.ContinuityError, "secret values"):
            continuity.capture_repo(repo, self.root / "capsule", export)

    def test_platform_export_required_scope_is_fail_closed(self) -> None:
        repo = self.make_repo()
        export = self.make_platform_export(scope=["issues"])
        with self.assertRaisesRegex(continuity.ContinuityError, "missing required scope"):
            continuity.capture_repo(
                repo,
                self.root / "capsule",
                export,
                {"issues", "pull_requests"},
                True,
            )

    def test_bundle_tamper_is_detected(self) -> None:
        repo = self.make_repo()
        capsule = self.capture(repo)
        bundle = capsule / "repository.bundle"
        data = bytearray(bundle.read_bytes())
        data[len(data) // 2] ^= 0x01
        bundle.write_bytes(data)
        with self.assertRaises(continuity.ContinuityError):
            continuity.verify_capsule(capsule)

    def test_manifest_ref_tamper_is_detected(self) -> None:
        repo = self.make_repo()
        capsule = self.capture(repo)
        manifest_path = capsule / continuity.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text("utf-8"))
        first_ref = next(iter(manifest["source"]["refs"]))
        manifest["source"]["refs"][first_ref] = "0" * 40
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(continuity.ContinuityError, "refs"):
            continuity.verify_capsule(capsule)

    def test_platform_export_archive_tamper_is_detected(self) -> None:
        repo = self.make_repo()
        capsule = self.capture(repo, platform=True)
        archive = capsule / "platform-export.tar.gz"
        archive.write_bytes(archive.read_bytes() + b"tamper")
        with self.assertRaisesRegex(continuity.ContinuityError, "digest"):
            continuity.verify_capsule(capsule)

    def test_restore_root_must_be_empty(self) -> None:
        repo = self.make_repo()
        capsule = self.capture(repo)
        restore = self.root / "restore"
        restore.mkdir()
        (restore / "stale.txt").write_text("stale\n")
        with self.assertRaisesRegex(continuity.ContinuityError, "empty"):
            continuity.drill_capsule(capsule, restore)

    def test_replication_requires_two_domains(self) -> None:
        artifact = self.root / "opaque.gpg"
        artifact.write_bytes(b"ciphertext")
        with self.assertRaisesRegex(continuity.ContinuityError, "at least two"):
            continuity.replicate_protected_artifact(
                artifact,
                [("domain-a", self.root / "a")],
                self.root / "receipt.json",
            )

    def test_replication_rejects_duplicate_or_nested_domains(self) -> None:
        artifact = self.root / "opaque.gpg"
        artifact.write_bytes(b"ciphertext")
        with self.assertRaisesRegex(continuity.ContinuityError, "duplicate failure-domain"):
            continuity.replicate_protected_artifact(
                artifact,
                [("same", self.root / "a"), ("same", self.root / "b")],
                self.root / "receipt.json",
            )
        with self.assertRaisesRegex(continuity.ContinuityError, "nested"):
            continuity.replicate_protected_artifact(
                artifact,
                [("a", self.root / "r"), ("b", self.root / "r" / "child")],
                self.root / "receipt2.json",
            )

    def test_second_domain_survives_first_domain_loss(self) -> None:
        artifact = self.root / "opaque.gpg"
        artifact.write_bytes(b"ciphertext-v1")
        receipt_path = self.root / "receipt.json"
        receipt = continuity.replicate_protected_artifact(
            artifact,
            [("domain-a", self.root / "a"), ("domain-b", self.root / "b")],
            receipt_path,
        )
        shutil.rmtree(self.root / "a")
        recovered = self.root / "recovered.gpg"
        result = continuity.recover_replica(receipt_path, "domain-b", recovered)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(recovered.read_bytes(), b"ciphertext-v1")
        self.assertEqual(result["artifact_sha256"], receipt["artifact"]["sha256"])

    def test_corrupt_replica_is_detected_without_poisoning_other_domain(self) -> None:
        artifact = self.root / "opaque.gpg"
        artifact.write_bytes(b"ciphertext-v1")
        receipt_path = self.root / "receipt.json"
        receipt = continuity.replicate_protected_artifact(
            artifact,
            [("domain-a", self.root / "a"), ("domain-b", self.root / "b")],
            receipt_path,
        )
        domain_a_path = Path(receipt["replicas"][0]["path"])
        domain_a_path.write_bytes(b"corrupt")
        with self.assertRaisesRegex(continuity.ContinuityError, "corruption"):
            continuity.recover_replica(receipt_path, "domain-a", self.root / "bad.gpg")
        good = continuity.recover_replica(receipt_path, "domain-b", self.root / "good.gpg")
        self.assertEqual(good["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
