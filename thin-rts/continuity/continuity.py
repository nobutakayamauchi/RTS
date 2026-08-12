#!/usr/bin/env python3
"""Provider-neutral continuity/recovery glue for 新RTS（仮称）.

No custom source host, cloud, crypto, key vault, scheduler, or database is implemented here.
The durable responsibility is narrower: prove that critical Git state can leave the current
provider, bind optional provider metadata exports, replicate already-protected artifacts
across declared failure domains, and survive a fresh non-executing reconstruction drill.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone

SCHEMA = "new-rts-provisional-continuity/v0"
PLATFORM_ATTESTATION_SCHEMA = "new-rts-provisional-platform-export-attestation/v0"
REPLICA_RECEIPT_SCHEMA = "new-rts-provisional-replica-receipt/v0"
MANIFEST_NAME = "CONTINUITY_MANIFEST.json"
PLATFORM_MANIFEST_NAME = "PLATFORM_EXPORT_MANIFEST.json"
DOMAIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")


class ContinuityError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    if check and cp.returncode != 0:
        raise ContinuityError(
            f"command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stderr.strip()}"
        )
    return cp


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(repo), *args], check=check)


def assert_git_repo(repo: Path) -> Path:
    repo = repo.expanduser().resolve()
    cp = git(repo, "rev-parse", "--is-inside-work-tree", check=False)
    if cp.returncode != 0 or cp.stdout.strip() != "true":
        raise ContinuityError(f"not a Git work tree: {repo}")
    return repo


def assert_outside_source(path: Path, source_repo: Path) -> Path:
    resolved = path.expanduser().resolve()
    source = source_repo.expanduser().resolve()
    if resolved == source or source in resolved.parents:
        raise ContinuityError(
            f"continuity runtime path must be outside source repository: {resolved}"
        )
    return resolved


def ensure_empty_output(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise ContinuityError(f"output path is not a directory: {path}")
        if any(path.iterdir()):
            raise ContinuityError(f"output directory must be empty: {path}")
    else:
        path.mkdir(parents=True, exist_ok=True)


def git_refs(repo: Path) -> dict[str, str]:
    cp = git(repo, "for-each-ref", "--format=%(refname)%00%(objectname)")
    refs: dict[str, str] = {}
    for line in cp.stdout.splitlines():
        if "\x00" not in line:
            continue
        ref, oid = line.split("\x00", 1)
        if ref and oid:
            refs[ref] = oid
    if not refs:
        raise ContinuityError("repository has no refs to preserve")
    return dict(sorted(refs.items()))


def head_identity(repo: Path) -> tuple[str, str]:
    head_sha = git(repo, "rev-parse", "HEAD").stdout.strip()
    sym = git(repo, "symbolic-ref", "-q", "HEAD", check=False)
    head_ref = sym.stdout.strip() if sym.returncode == 0 and sym.stdout.strip() else "DETACHED"
    return head_ref, head_sha


def tracked_attribute_files(repo: Path) -> list[Path]:
    cp = git(repo, "ls-files")
    return [repo / raw for raw in cp.stdout.splitlines() if Path(raw).name == ".gitattributes"]


def assert_capture_safe(repo: Path) -> None:
    dirty = git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if dirty.strip():
        raise ContinuityError(
            "dirty/untracked working tree is not silently excluded; commit or separately archive it first"
        )

    shallow = git(repo, "rev-parse", "--is-shallow-repository").stdout.strip().lower()
    if shallow == "true":
        raise ContinuityError("shallow repository cannot prove full reachable history")

    promisor = git(repo, "config", "--get-regexp", r"^remote\..*\.promisor$", check=False)
    if promisor.returncode == 0 and promisor.stdout.strip():
        raise ContinuityError("partial/promisor clone cannot prove locally complete object custody")

    gitmodules = repo / ".gitmodules"
    if gitmodules.is_file() and gitmodules.read_text("utf-8", errors="replace").strip():
        raise ContinuityError(
            "submodules require separate provider-neutral exports; refusing a partial Tier-0 snapshot"
        )

    for attrs in tracked_attribute_files(repo):
        text = attrs.read_text("utf-8", errors="replace")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "filter=lfs" in stripped:
                raise ContinuityError(
                    "Git LFS content requires a separate export adapter; refusing pointer-only custody"
                )

    # The source object database must itself be internally readable before we freeze it.
    git(repo, "fsck", "--full", "--no-reflogs")


def list_bundle_refs(bundle: Path) -> dict[str, str]:
    cp = run(["git", "bundle", "list-heads", str(bundle)])
    refs: dict[str, str] = {}
    for line in cp.stdout.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        oid, ref = parts
        if ref == "HEAD":
            continue
        refs[ref] = oid
    if not refs:
        raise ContinuityError("bundle exposes no named refs")
    return dict(sorted(refs.items()))


def verify_bundle_file(bundle: Path) -> dict[str, str]:
    if not bundle.is_file() or bundle.is_symlink():
        raise ContinuityError(f"Git bundle missing/unsafe: {bundle}")
    with tempfile.TemporaryDirectory(prefix="new-rts-bundle-verify-") as td:
        bare = Path(td) / "verify.git"
        run(["git", "init", "--bare", str(bare)])
        run(["git", "-C", str(bare), "bundle", "verify", str(bundle)])
    return list_bundle_refs(bundle)


def safe_relpath(value: str) -> str:
    rel = PurePosixPath(value)
    if not value or rel.is_absolute() or ".." in rel.parts or value == ".":
        raise ContinuityError(f"unsafe relative path: {value!r}")
    return rel.as_posix()


def normalized_files(root: Path) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ContinuityError(f"symlink rejected: {path}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def normalized_tarinfo(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=name)
    info.size = size
    info.mode = 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


def load_platform_attestation(root: Path, required_scope: set[str]) -> dict:
    path = root / "EXPORT_ATTESTATION.json"
    if not path.is_file() or path.is_symlink():
        raise ContinuityError("platform export requires EXPORT_ATTESTATION.json")
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContinuityError("platform export attestation is invalid JSON") from exc
    if data.get("schema") != PLATFORM_ATTESTATION_SCHEMA:
        raise ContinuityError("platform export attestation schema mismatch")
    if data.get("secret_values_excluded") is not True:
        raise ContinuityError("platform export must attest that secret values were excluded")
    if not isinstance(data.get("producer_id"), str) or not data["producer_id"].strip():
        raise ContinuityError("platform export attestation requires producer_id")
    if not isinstance(data.get("captured_at"), str) or not data["captured_at"].strip():
        raise ContinuityError("platform export attestation requires captured_at")
    scope = data.get("scope")
    if not isinstance(scope, list) or not scope or not all(isinstance(v, str) and v for v in scope):
        raise ContinuityError("platform export attestation requires a non-empty scope list")
    missing = sorted(required_scope - set(scope))
    if missing:
        raise ContinuityError(f"platform export missing required scope: {', '.join(missing)}")
    return data


def create_platform_export_archive(
    root: Path,
    output: Path,
    required_scope: set[str],
) -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ContinuityError(f"platform export directory missing: {root}")
    attestation = load_platform_attestation(root, required_scope)
    files = normalized_files(root)
    if not files:
        raise ContinuityError("platform export is empty")
    for path in files:
        if path.relative_to(root).as_posix() == PLATFORM_MANIFEST_NAME:
            raise ContinuityError(
                f"reserved export manifest path already exists: {PLATFORM_MANIFEST_NAME}"
            )

    entries = [
        {
            "path": safe_relpath(path.relative_to(root).as_posix()),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]
    export_manifest = {
        "schema": SCHEMA,
        "kind": "platform-export-manifest",
        "entries": entries,
        "attestation": attestation,
    }
    manifest_bytes = canonical_json_bytes(export_manifest)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="new-rts-platform-", suffix=".tar", delete=False) as tf:
        tmp_tar = Path(tf.name)
    try:
        with tarfile.open(tmp_tar, "w", format=tarfile.PAX_FORMAT) as tar:
            for path in files:
                rel = path.relative_to(root).as_posix()
                data = path.read_bytes()
                tar.addfile(normalized_tarinfo(rel, len(data)), io.BytesIO(data))
            tar.addfile(
                normalized_tarinfo(PLATFORM_MANIFEST_NAME, len(manifest_bytes)),
                io.BytesIO(manifest_bytes),
            )
        with tmp_tar.open("rb") as src, output.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
                shutil.copyfileobj(src, gz)
    finally:
        tmp_tar.unlink(missing_ok=True)

    return {
        "path": output.name,
        "sha256": sha256_file(output),
        "size": output.stat().st_size,
        "producer_id": attestation["producer_id"],
        "captured_at": attestation["captured_at"],
        "scope": sorted(attestation["scope"]),
    }


def safe_extract_archive(archive: Path, output: Path) -> None:
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise ContinuityError(f"restore destination must be an empty directory: {output}")
    else:
        output.mkdir(parents=True, exist_ok=True)
    root = output.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        seen: set[str] = set()
        for member in tar.getmembers():
            rel = safe_relpath(member.name)
            if rel in seen:
                raise ContinuityError(f"duplicate archive member: {rel}")
            seen.add(rel)
            if member.issym() or member.islnk() or member.isdev():
                raise ContinuityError(f"unsafe archive member type: {rel}")
            target = (root / Path(*PurePosixPath(rel).parts)).resolve()
            if target != root and root not in target.parents:
                raise ContinuityError(f"archive member escapes destination: {rel}")
        tar.extractall(root, filter="data")


def verify_platform_export_archive(archive: Path, output: Path) -> dict:
    safe_extract_archive(archive, output)
    manifest_path = output / PLATFORM_MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ContinuityError("platform export internal manifest missing/unsafe")
    try:
        manifest = json.loads(manifest_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContinuityError("platform export internal manifest invalid") from exc
    if manifest.get("schema") != SCHEMA or manifest.get("kind") != "platform-export-manifest":
        raise ContinuityError("platform export internal manifest contract mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ContinuityError("platform export internal manifest has no entries")
    expected: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ContinuityError("platform export manifest entry invalid")
        rel = safe_relpath(str(entry.get("path", "")))
        if rel in expected:
            raise ContinuityError(f"duplicate platform export path: {rel}")
        expected.add(rel)
        path = output / Path(*PurePosixPath(rel).parts)
        if not path.is_file() or path.is_symlink():
            raise ContinuityError(f"platform export file missing/unsafe: {rel}")
        if path.stat().st_size != entry.get("size") or sha256_file(path) != entry.get("sha256"):
            raise ContinuityError(f"platform export digest mismatch: {rel}")
    actual = {
        path.relative_to(output).as_posix()
        for path in normalized_files(output)
        if path.relative_to(output).as_posix() != PLATFORM_MANIFEST_NAME
    }
    if actual != expected:
        raise ContinuityError("platform export contains missing or unmanifested files")
    return {
        "status": "PASS",
        "entries": len(entries),
        "attestation": manifest.get("attestation"),
    }


def capture_repo(
    repo: Path,
    output: Path,
    platform_export: Path | None = None,
    required_platform_scope: set[str] | None = None,
    require_platform_export: bool = False,
) -> dict:
    repo = assert_git_repo(repo)
    output = assert_outside_source(output, repo)
    ensure_empty_output(output)
    assert_capture_safe(repo)
    required_platform_scope = required_platform_scope or set()

    head_ref, head_sha = head_identity(repo)
    refs = git_refs(repo)
    object_format = git(repo, "rev-parse", "--show-object-format").stdout.strip()
    git_version = run(["git", "--version"]).stdout.strip()

    bundle = output / "repository.bundle"
    git(repo, "bundle", "create", str(bundle), "--all")
    bundle_refs = verify_bundle_file(bundle)
    if bundle_refs != refs:
        raise ContinuityError("Git bundle ref set does not exactly match source refs")

    artifacts: list[dict] = [
        {
            "role": "tier0-git-history",
            "path": bundle.name,
            "sha256": sha256_file(bundle),
            "size": bundle.stat().st_size,
        }
    ]

    platform_record = None
    if platform_export is not None:
        platform_record = create_platform_export_archive(
            platform_export,
            output / "platform-export.tar.gz",
            required_platform_scope,
        )
        artifacts.append(
            {
                "role": "provider-export",
                "path": platform_record["path"],
                "sha256": platform_record["sha256"],
                "size": platform_record["size"],
            }
        )
    elif require_platform_export:
        raise ContinuityError(
            "declared Tier-0 platform metadata export is required but was not supplied"
        )

    snapshot_seed = head_sha + artifacts[0]["sha256"] + (
        platform_record["sha256"] if platform_record else ""
    )
    snapshot_id = hashlib.sha256(snapshot_seed.encode("ascii")).hexdigest()[:24]
    manifest = {
        "schema": SCHEMA,
        "system_name": "新RTS（仮称）",
        "snapshot_id": snapshot_id,
        "created_at": now_utc(),
        "source": {
            "head_ref": head_ref,
            "head_sha": head_sha,
            "refs": refs,
            "ref_count": len(refs),
            "object_format": object_format,
            "git_version": git_version,
        },
        "artifacts": artifacts,
        "platform_export": platform_record,
        "coverage": {
            "git_history_and_refs": "CAPTURED",
            "platform_metadata": "CAPTURED" if platform_record else "NOT_SUPPLIED",
            "secret_values": "INTENTIONALLY_NOT_CAPTURED",
            "working_tree_uncommitted": "REJECTED_IF_PRESENT",
            "git_lfs": "REJECTED_UNLESS_SEPARATELY_EXPORTED",
            "git_submodules": "REJECTED_UNLESS_SEPARATELY_EXPORTED",
            "partial_or_shallow_clone": "REJECTED",
        },
        "status": "COMPLETE_FOR_DECLARED_SCOPE" if platform_record else "CORE_GIT_ONLY",
        "next_gate": (
            "encrypt with separated recovery identities, replicate across independent failure "
            "domains, then perform a fresh non-executing recovery drill"
        ),
    }
    write_json(output / MANIFEST_NAME, manifest)
    return manifest


def load_manifest(capsule: Path) -> dict:
    path = capsule / MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        raise ContinuityError(f"continuity manifest missing/unsafe: {path}")
    try:
        manifest = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContinuityError("continuity manifest invalid JSON") from exc
    if manifest.get("schema") != SCHEMA:
        raise ContinuityError("continuity manifest schema mismatch")
    return manifest


def verify_capsule(capsule: Path) -> dict:
    capsule = capsule.expanduser().resolve()
    manifest = load_manifest(capsule)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ContinuityError("continuity manifest has no artifacts")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ContinuityError("continuity artifact entry invalid")
        rel = safe_relpath(str(artifact.get("path", "")))
        path = capsule / rel
        if not path.is_file() or path.is_symlink():
            raise ContinuityError(f"continuity artifact missing/unsafe: {rel}")
        if path.stat().st_size != artifact.get("size") or sha256_file(path) != artifact.get("sha256"):
            raise ContinuityError(f"continuity artifact digest mismatch: {rel}")

    expected_refs = manifest.get("source", {}).get("refs")
    if not isinstance(expected_refs, dict) or not expected_refs:
        raise ContinuityError("source refs missing from continuity manifest")
    actual_refs = verify_bundle_file(capsule / "repository.bundle")
    if actual_refs != expected_refs:
        raise ContinuityError("bundle refs do not match continuity manifest")

    platform_result = None
    if manifest.get("platform_export"):
        with tempfile.TemporaryDirectory(prefix="new-rts-platform-verify-") as td:
            platform_result = verify_platform_export_archive(
                capsule / "platform-export.tar.gz",
                Path(td) / "platform",
            )

    return {
        "status": "PASS",
        "snapshot_id": manifest.get("snapshot_id"),
        "ref_count": len(actual_refs),
        "platform_export": platform_result,
        "manifest_sha256": sha256_file(capsule / MANIFEST_NAME),
    }


def drill_capsule(
    capsule: Path,
    restore_root: Path,
    receipt_path: Path | None = None,
) -> dict:
    capsule = capsule.expanduser().resolve()
    restore_root = restore_root.expanduser().resolve()
    ensure_empty_output(restore_root)

    verify = verify_capsule(capsule)
    manifest = load_manifest(capsule)
    restored_git = restore_root / "repository.git"
    run(["git", "clone", "--mirror", str(capsule / "repository.bundle"), str(restored_git)])
    run(["git", "-C", str(restored_git), "fsck", "--full"])
    restored_refs = git_refs(restored_git)
    expected_refs = manifest["source"]["refs"]
    if restored_refs != expected_refs:
        raise ContinuityError("fresh mirror restore refs differ from captured refs")

    head_sha = manifest["source"]["head_sha"]
    cat = run(
        ["git", "-C", str(restored_git), "cat-file", "-e", f"{head_sha}^{{commit}}"],
        check=False,
    )
    if cat.returncode != 0:
        raise ContinuityError("captured HEAD commit is absent from restored repository")

    platform_status = "NOT_SUPPLIED"
    if manifest.get("platform_export"):
        platform_out = restore_root / "platform-export"
        result = verify_platform_export_archive(
            capsule / "platform-export.tar.gz",
            platform_out,
        )
        platform_status = result["status"]

    receipt = {
        "schema": SCHEMA,
        "kind": "fresh-recovery-drill-receipt",
        "system_name": "新RTS（仮称）",
        "snapshot_id": manifest["snapshot_id"],
        "drilled_at": now_utc(),
        "status": "PASS",
        "manifest_sha256": verify["manifest_sha256"],
        "restored_head_sha": head_sha,
        "restored_ref_count": len(restored_refs),
        "git_fsck": "PASS",
        "platform_export": platform_status,
        "code_execution": "NOT_PERFORMED",
    }
    if receipt_path:
        write_json(receipt_path.expanduser().resolve(), receipt)
    return receipt


def parse_destination(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ContinuityError("replica destination must be DOMAIN_ID=PATH")
    domain_id, raw_path = spec.split("=", 1)
    if not DOMAIN_ID_RE.fullmatch(domain_id):
        raise ContinuityError(f"invalid failure-domain id: {domain_id!r}")
    if not raw_path:
        raise ContinuityError("replica destination path is empty")
    return domain_id, Path(raw_path).expanduser().resolve()


def assert_independent_declared_destinations(destinations: list[tuple[str, Path]]) -> None:
    if len(destinations) < 2:
        raise ContinuityError("at least two declared failure domains are required")
    ids = [domain_id for domain_id, _ in destinations]
    if len(ids) != len(set(ids)):
        raise ContinuityError("duplicate failure-domain ids are not independent")
    paths = [path for _, path in destinations]
    if len(paths) != len(set(paths)):
        raise ContinuityError("duplicate replica paths are not independent")
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            if left in right.parents or right in left.parents:
                raise ContinuityError(
                    "nested replica roots share a local failure domain; use non-overlapping roots"
                )


def atomic_copy_verified(source: Path, destination: Path, expected_sha256: str) -> dict:
    source = source.expanduser().resolve()
    if not source.is_file() or source.is_symlink():
        raise ContinuityError(f"source artifact missing/unsafe: {source}")
    if sha256_file(source) != expected_sha256:
        raise ContinuityError("source artifact digest does not match declared digest")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ContinuityError(f"existing replica path is unsafe: {destination}")
        if sha256_file(destination) != expected_sha256:
            raise ContinuityError("existing replica conflicts with expected immutable artifact")
        return {
            "path": str(destination),
            "sha256": expected_sha256,
            "size": destination.stat().st_size,
            "status": "ALREADY_PRESENT_VERIFIED",
        }
    tmp = destination.with_name(destination.name + f".tmp-{os.getpid()}")
    try:
        shutil.copyfile(source, tmp)
        os.chmod(tmp, 0o600)
        if sha256_file(tmp) != expected_sha256:
            raise ContinuityError("replica copy digest mismatch")
        os.replace(tmp, destination)
    finally:
        tmp.unlink(missing_ok=True)
    return {
        "path": str(destination),
        "sha256": expected_sha256,
        "size": destination.stat().st_size,
        "status": "COPIED_VERIFIED",
    }


def replicate_protected_artifact(
    artifact: Path,
    destinations: list[tuple[str, Path]],
    receipt_path: Path,
    artifact_kind: str = "encrypted-continuity-artifact",
) -> dict:
    assert_independent_declared_destinations(destinations)
    artifact = artifact.expanduser().resolve()
    if not artifact.is_file() or artifact.is_symlink():
        raise ContinuityError(f"protected artifact missing/unsafe: {artifact}")
    digest = sha256_file(artifact)
    replicas = []
    for domain_id, root in destinations:
        target = root / digest[:16] / artifact.name
        result = atomic_copy_verified(artifact, target, digest)
        replicas.append({"failure_domain": domain_id, **result})
    receipt = {
        "schema": REPLICA_RECEIPT_SCHEMA,
        "system_name": "新RTS（仮称）",
        "kind": artifact_kind,
        "created_at": now_utc(),
        "artifact": {
            "name": artifact.name,
            "sha256": digest,
            "size": artifact.stat().st_size,
        },
        "replicas": replicas,
        "independence_claim": (
            "declared logical failure domains with non-overlapping local reference paths; "
            "physical/provider independence requires external evidence"
        ),
    }
    write_json(receipt_path.expanduser().resolve(), receipt)
    return receipt


def recover_replica(
    receipt_path: Path,
    failure_domain: str,
    output: Path,
) -> dict:
    try:
        receipt = json.loads(receipt_path.expanduser().resolve().read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContinuityError("replica receipt unreadable/invalid") from exc
    if receipt.get("schema") != REPLICA_RECEIPT_SCHEMA:
        raise ContinuityError("replica receipt schema mismatch")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, dict):
        raise ContinuityError("replica receipt artifact record missing")
    expected_sha = str(artifact.get("sha256", ""))
    if len(expected_sha) != 64:
        raise ContinuityError("replica receipt digest invalid")
    replicas = receipt.get("replicas")
    if not isinstance(replicas, list):
        raise ContinuityError("replica receipt list missing")
    matches = [item for item in replicas if isinstance(item, dict) and item.get("failure_domain") == failure_domain]
    if len(matches) != 1:
        raise ContinuityError(f"failure domain not uniquely recorded: {failure_domain}")
    source = Path(str(matches[0].get("path", ""))).expanduser().resolve()
    if not source.is_file() or source.is_symlink():
        raise ContinuityError(f"replica unavailable/unsafe in domain {failure_domain}")
    if sha256_file(source) != expected_sha:
        raise ContinuityError(f"replica corruption detected in domain {failure_domain}")
    output = output.expanduser().resolve()
    result = atomic_copy_verified(source, output, expected_sha)
    return {
        "status": "PASS",
        "failure_domain": failure_domain,
        "artifact_sha256": expected_sha,
        "output": result["path"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="新RTS（仮称） continuity/recovery core")
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture")
    capture.add_argument("--repo", required=True)
    capture.add_argument("--output", required=True)
    capture.add_argument("--platform-export")
    capture.add_argument("--require-platform-export", action="store_true")
    capture.add_argument("--required-platform-scope", action="append", default=[])

    verify = sub.add_parser("verify")
    verify.add_argument("--capsule", required=True)

    drill = sub.add_parser("drill")
    drill.add_argument("--capsule", required=True)
    drill.add_argument("--restore-root", required=True)
    drill.add_argument("--receipt")

    replicate = sub.add_parser("replicate")
    replicate.add_argument("--artifact", required=True)
    replicate.add_argument("--destination", action="append", required=True, help="DOMAIN_ID=PATH")
    replicate.add_argument("--receipt", required=True)

    recover = sub.add_parser("recover-replica")
    recover.add_argument("--receipt", required=True)
    recover.add_argument("--failure-domain", required=True)
    recover.add_argument("--output", required=True)

    goal = sub.add_parser("goal")
    goal.add_argument("--repo", required=True)
    goal.add_argument("--output", required=True)
    goal.add_argument("--restore-root", required=True)
    goal.add_argument("--platform-export")
    goal.add_argument("--require-platform-export", action="store_true")
    goal.add_argument("--required-platform-scope", action="append", default=[])
    goal.add_argument("--receipt")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "capture":
            result = capture_repo(
                Path(args.repo),
                Path(args.output),
                Path(args.platform_export) if args.platform_export else None,
                set(args.required_platform_scope),
                args.require_platform_export,
            )
        elif args.command == "verify":
            result = verify_capsule(Path(args.capsule))
        elif args.command == "drill":
            result = drill_capsule(
                Path(args.capsule),
                Path(args.restore_root),
                Path(args.receipt) if args.receipt else None,
            )
        elif args.command == "replicate":
            result = replicate_protected_artifact(
                Path(args.artifact),
                [parse_destination(spec) for spec in args.destination],
                Path(args.receipt),
            )
        elif args.command == "recover-replica":
            result = recover_replica(
                Path(args.receipt),
                args.failure_domain,
                Path(args.output),
            )
        elif args.command == "goal":
            capture = capture_repo(
                Path(args.repo),
                Path(args.output),
                Path(args.platform_export) if args.platform_export else None,
                set(args.required_platform_scope),
                args.require_platform_export,
            )
            drill = drill_capsule(
                Path(args.output),
                Path(args.restore_root),
                Path(args.receipt) if args.receipt else None,
            )
            result = {
                "goal": "CORE_CONTINUITY_DRILL_PASS",
                "capture": capture,
                "drill": drill,
                "next_gate": "encrypt then replicate protected artifact across independent failure domains",
            }
        else:
            raise ContinuityError("unsupported command")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except ContinuityError as exc:
        print(json.dumps({"goal": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
