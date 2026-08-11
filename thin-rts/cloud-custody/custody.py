#!/usr/bin/env python3
"""Thin RTS encrypted cloud custody candidate.

No custom cryptography. This module orchestrates standard tar/gzip semantics implemented
with Python stdlib, GnuPG for public-key encryption, and Google Cloud CLI for the first
provider adapter.

Generated evidence, ciphertext, receipts, recovery material, and provider credentials
must remain outside the public repository.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from typing import Iterable

SCHEMA = "thin-rts-cloud-custody/v0"
INTERNAL_MANIFEST = "RTS_BUNDLE_MANIFEST.json"
FINGERPRINT_RE = re.compile(r"^[0-9A-Fa-f]{40,64}$")
REPO_ROOT = Path(__file__).resolve().parents[2]


class CustodyError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(obj))


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def assert_private_runtime_path(path: Path, *, repo_root: Path = REPO_ROOT) -> Path:
    resolved = path.expanduser().resolve()
    repo = repo_root.expanduser().resolve()
    if resolved == repo or resolved.is_relative_to(repo):
        raise CustodyError(f"private runtime path must be outside public repository: {resolved}")
    return resolved


def normalized_rel_files(root: Path) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_symlink():
            raise CustodyError(f"symlink rejected from evidence bundle: {p}")
        if p.is_file():
            files.append(p)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def _validate_manifest_relpath(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise CustodyError("manifest path must be a non-empty string")
    rel = PurePosixPath(value)
    if rel.is_absolute() or ".." in rel.parts or value == ".":
        raise CustodyError(f"unsafe manifest path: {value!r}")
    if value == INTERNAL_MANIFEST:
        raise CustodyError("reserved internal manifest path cannot be an evidence entry")
    return rel.as_posix()


def build_manifest(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise CustodyError(f"input directory not found: {root}")

    entries = []
    for p in normalized_rel_files(root):
        rel = p.relative_to(root).as_posix()
        if rel == INTERNAL_MANIFEST:
            raise CustodyError(f"source evidence collides with reserved path: {INTERNAL_MANIFEST}")
        entries.append({
            "path": rel,
            "size": p.stat().st_size,
            "sha256": sha256_file(p),
        })

    if not entries:
        raise CustodyError("evidence bundle is empty")

    return {
        "schema": SCHEMA,
        "kind": "evidence-bundle-manifest",
        "hash": "sha256",
        "entries": entries,
    }


def _normalized_tarinfo(name: str, size: int, mode: int = 0o644) -> tarfile.TarInfo:
    ti = tarfile.TarInfo(name=name)
    ti.size = size
    ti.mode = mode
    ti.uid = 0
    ti.gid = 0
    ti.uname = ""
    ti.gname = ""
    ti.mtime = 0
    return ti


def create_deterministic_bundle(input_dir: Path, output_path: Path) -> dict:
    input_dir = input_dir.resolve()
    manifest = build_manifest(input_dir)
    manifest_bytes = canonical_json_bytes(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(prefix="rts-custody-", suffix=".tar", delete=False) as tf:
        tar_tmp = Path(tf.name)
    try:
        with tarfile.open(tar_tmp, "w", format=tarfile.PAX_FORMAT) as tar:
            for p in normalized_rel_files(input_dir):
                rel = p.relative_to(input_dir).as_posix()
                data = p.read_bytes()
                tar.addfile(_normalized_tarinfo(rel, len(data)), io.BytesIO(data))
            tar.addfile(_normalized_tarinfo(INTERNAL_MANIFEST, len(manifest_bytes)), io.BytesIO(manifest_bytes))
        with tar_tmp.open("rb") as src, output_path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
                shutil.copyfileobj(src, gz)
    finally:
        tar_tmp.unlink(missing_ok=True)

    return {
        "manifest": manifest,
        "archive": str(output_path),
        "archive_sha256": sha256_file(output_path),
        "archive_size": output_path.stat().st_size,
    }


def _validate_fingerprint(value: str) -> str:
    if not FINGERPRINT_RE.fullmatch(value):
        raise CustodyError("recipient must be a full hexadecimal OpenPGP fingerprint")
    return value.upper()


def gpg_version() -> str:
    cp = run(["gpg", "--version"])
    return cp.stdout.splitlines()[0].strip() if cp.stdout else "gpg/version-unknown"


def gpg_public_fingerprints(query: str) -> set[str]:
    cp = run(["gpg", "--batch", "--with-colons", "--fingerprint", "--list-keys", query], check=False)
    if cp.returncode != 0:
        return set()
    result = set()
    for line in cp.stdout.splitlines():
        parts = line.split(":")
        if parts and parts[0] == "fpr" and len(parts) > 9 and parts[9]:
            result.add(parts[9].upper())
    return result


def gpg_has_secret_record(fingerprint: str) -> bool:
    cp = run(["gpg", "--batch", "--with-colons", "--list-secret-keys", fingerprint], check=False)
    for line in cp.stdout.splitlines():
        kind = line.split(":", 1)[0]
        if kind in {"sec", "ssb"}:
            return True
    return False


def assert_recipient_separation(recipients: Iterable[str]) -> list[str]:
    normalized = [_validate_fingerprint(r) for r in recipients]
    if len(set(normalized)) != len(normalized):
        raise CustodyError("duplicate recipient fingerprint")
    for fpr in normalized:
        if fpr not in gpg_public_fingerprints(fpr):
            raise CustodyError(f"public recipient key unavailable: {fpr}")
        if gpg_has_secret_record(fpr):
            raise CustodyError(f"key separation failed: producer has secret-key record for recipient {fpr}")
    return normalized


def encrypt_gpg(plaintext: Path, ciphertext: Path, recipients: list[str]) -> dict:
    recipients = assert_recipient_separation(recipients)
    ciphertext.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["gpg", "--batch", "--yes", "--no-default-recipient", "--output", str(ciphertext), "--encrypt"]
    for fpr in recipients:
        cmd.extend(["--recipient", fpr])
    cmd.append(str(plaintext))
    cp = run(cmd, check=False)
    if cp.returncode != 0:
        raise CustodyError(f"gpg encryption failed: {cp.stderr.strip()}")
    return {
        "tool": gpg_version(),
        "format": "OpenPGP",
        "recipients": recipients,
        "ciphertext_sha256": sha256_file(ciphertext),
        "ciphertext_size": ciphertext.stat().st_size,
    }


def decrypt_gpg(ciphertext: Path, plaintext: Path) -> None:
    plaintext.parent.mkdir(parents=True, exist_ok=True)
    cp = run(["gpg", "--batch", "--yes", "--output", str(plaintext), "--decrypt", str(ciphertext)], check=False)
    if cp.returncode != 0:
        plaintext.unlink(missing_ok=True)
        raise CustodyError(f"gpg decryption failed: {cp.stderr.strip()}")


def validate_gs_base(uri: str) -> str:
    if not uri.startswith("gs://"):
        raise CustodyError("GCS target must start with gs://")
    tail = uri[5:].strip("/")
    if "/" not in tail:
        raise CustodyError("GCS target must include a dedicated prefix, not bucket root")
    if ".." in PurePosixPath(tail).parts:
        raise CustodyError("invalid GCS target")
    return "gs://" + tail


def gcs_object_uri(base: str, object_id: str) -> str:
    return f"{validate_gs_base(base)}/{object_id}.gpg"


def gcs_upload(local: Path, remote: str) -> dict:
    cp = run([
        "gcloud", "storage", "cp", str(local), remote,
        "--if-generation-match=0",
    ], check=False)
    if cp.returncode != 0:
        raise CustodyError(f"cloud upload failed: {cp.stderr.strip() or cp.stdout.strip()}")
    meta = gcs_stat(remote)
    if not str(meta.get("generation", "")):
        raise CustodyError("remote object metadata missing generation")
    return meta


def gcs_stat(remote: str) -> dict:
    cp = run([
        "gcloud", "storage", "objects", "describe", remote,
        "--format=json(name,bucket,generation,size,updateTime,md5Hash,crc32c)",
    ], check=False)
    if cp.returncode != 0:
        raise CustodyError(f"remote object describe failed: {cp.stderr.strip() or cp.stdout.strip()}")
    try:
        data = json.loads(cp.stdout)
    except json.JSONDecodeError as e:
        raise CustodyError("remote object metadata was not valid JSON") from e
    return data


def gcs_download(remote: str, local: Path, generation: str) -> None:
    if not generation or not generation.isdigit():
        raise CustodyError("recorded remote generation must be numeric")
    local.parent.mkdir(parents=True, exist_ok=True)
    cp = run([
        "gcloud", "storage", "cp", remote, str(local),
        f"--if-generation-match={generation}",
    ], check=False)
    if cp.returncode != 0:
        local.unlink(missing_ok=True)
        raise CustodyError(f"cloud download failed or generation changed: {cp.stderr.strip() or cp.stdout.strip()}")


def safe_extract_tar_gz(archive: Path, output_dir: Path) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise CustodyError(f"restore destination is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise CustodyError(f"restore destination must be empty: {output_dir}")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    root = output_dir.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        seen = set()
        for member in tar.getmembers():
            member_path = PurePosixPath(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise CustodyError(f"unsafe archive member: {member.name}")
            if member.name in seen:
                raise CustodyError(f"duplicate archive member: {member.name}")
            seen.add(member.name)
            if member.issym() or member.islnk() or member.isdev():
                raise CustodyError(f"unsupported archive member type: {member.name}")
            target = (root / Path(*member_path.parts)).resolve()
            if target != root and root not in target.parents:
                raise CustodyError(f"archive escapes output directory: {member.name}")
        tar.extractall(root, filter="data")


def verify_extracted_tree(root: Path) -> dict:
    root = root.resolve()
    manifest_path = root / INTERNAL_MANIFEST
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise CustodyError("internal manifest missing or unsafe")

    try:
        manifest = json.loads(manifest_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise CustodyError("internal manifest is unreadable or invalid JSON") from e

    if manifest.get("schema") != SCHEMA:
        raise CustodyError("manifest schema mismatch")
    if manifest.get("kind") != "evidence-bundle-manifest" or manifest.get("hash") != "sha256":
        raise CustodyError("manifest kind/hash contract mismatch")

    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise CustodyError("manifest entries must be a non-empty list")

    expected_paths: set[str] = set()
    failures = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise CustodyError("manifest entry must be an object")
        rel = _validate_manifest_relpath(entry.get("path"))
        if rel in expected_paths:
            raise CustodyError(f"duplicate manifest path: {rel}")
        expected_paths.add(rel)

        p = (root / Path(*PurePosixPath(rel).parts)).resolve()
        if p != root and root not in p.parents:
            raise CustodyError(f"manifest path escapes restored root: {rel}")
        if not p.is_file() or p.is_symlink():
            failures.append({"path": rel, "reason": "missing_or_unsafe"})
            continue

        actual_size = p.stat().st_size
        actual_hash = sha256_file(p)
        if actual_size != entry.get("size") or actual_hash != entry.get("sha256"):
            failures.append({"path": rel, "reason": "digest_or_size_mismatch"})

    actual_paths = {
        p.relative_to(root).as_posix()
        for p in normalized_rel_files(root)
        if p.relative_to(root).as_posix() != INTERNAL_MANIFEST
    }
    for rel in sorted(actual_paths - expected_paths):
        failures.append({"path": rel, "reason": "unmanifested_extra"})
    for rel in sorted(expected_paths - actual_paths):
        if not any(f.get("path") == rel for f in failures):
            failures.append({"path": rel, "reason": "missing"})

    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "entries": len(entries)}


def verify_bundle_archive(archive: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="rts-custody-selfverify-") as td:
        out = Path(td) / "restored"
        safe_extract_tar_gz(archive, out)
        result = verify_extracted_tree(out)
        if result["status"] != "PASS":
            raise CustodyError(f"deterministic bundle self-verification failed: {result['failures']}")
        return result


def make_recovery_card(receipt: dict, path: Path) -> None:
    lines = [
        "# Thin RTS Recovery Card",
        "",
        f"Schema: `{receipt['schema']}`",
        f"Key epoch: `{receipt['key_epoch']}`",
        f"Bundle ID: `{receipt['bundle_id']}`",
        f"Ciphertext SHA-256: `{receipt['ciphertext']['sha256']}`",
        f"Remote generation: `{receipt['provider'].get('generation', 'UNKNOWN')}`",
        f"Authority ref: `{receipt.get('authority_ref', 'NOT_RECORDED')}`",
        "",
        "Recovery requires:",
        "- this recovery receipt/card;",
        "- the separated OpenPGP recovery identity for the matching key epoch;",
        "- GnuPG;",
        "- access to the recorded provider object or an equivalent transported copy.",
        "",
        "A successful restore is not 'file opened'. It must verify ciphertext digest, plaintext bundle digest, and the internal manifest.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_local_candidate(input_dir: Path, work_dir: Path, recipients: list[str], key_epoch: str) -> dict:
    work_dir = assert_private_runtime_path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    object_id = secrets.token_hex(16)
    archive = work_dir / f"{object_id}.tar.gz"
    ciphertext = work_dir / f"{object_id}.gpg"
    bundle = create_deterministic_bundle(input_dir, archive)
    verify_bundle_archive(archive)
    enc = encrypt_gpg(archive, ciphertext, recipients)
    return {
        "schema": SCHEMA,
        "created_at": now_utc(),
        "bundle_id": object_id,
        "key_epoch": key_epoch,
        "plaintext": {"sha256": bundle["archive_sha256"], "size": bundle["archive_size"]},
        "ciphertext": {"path": str(ciphertext), "sha256": enc["ciphertext_sha256"], "size": enc["ciphertext_size"], "format": enc["format"], "tool": enc["tool"]},
        "recipients": enc["recipients"],
        "provider": {"type": "gcs", "status": "NOT_UPLOADED"},
    }


def live_upload(candidate: dict, gcs_base: str, recovery_dir: Path, authority_ref: str) -> dict:
    if not authority_ref.strip():
        raise CustodyError("live upload requires a non-empty authority reference")
    recovery_dir = assert_private_runtime_path(recovery_dir)
    remote = gcs_object_uri(gcs_base, candidate["bundle_id"])
    meta = gcs_upload(Path(candidate["ciphertext"]["path"]), remote)
    remote_size = int(meta.get("size", -1))
    if remote_size != int(candidate["ciphertext"]["size"]):
        raise CustodyError(f"remote size mismatch: expected {candidate['ciphertext']['size']} got {remote_size}")
    candidate["provider"] = {
        "type": "gcs",
        "uri": remote,
        "generation": str(meta.get("generation", "")),
        "size": remote_size,
        "update_time": meta.get("updateTime"),
        "verification": "REMOTE_OBJECT_PRESENT_SIZE_MATCH",
    }
    candidate["authority_ref"] = authority_ref.strip()
    candidate["upload_observed_at"] = now_utc()
    recovery_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = recovery_dir / f"{candidate['bundle_id']}.receipt.json"
    write_json(receipt_path, candidate)
    make_recovery_card(candidate, recovery_dir / f"{candidate['bundle_id']}.RECOVERY_CARD.md")
    return candidate


def restore_from_receipt(receipt_path: Path, output_dir: Path, work_dir: Path) -> dict:
    work_dir = assert_private_runtime_path(work_dir)
    output_dir = assert_private_runtime_path(output_dir)
    receipt = json.loads(receipt_path.read_text("utf-8"))
    if receipt.get("schema") != SCHEMA:
        raise CustodyError("receipt schema mismatch")
    remote = receipt.get("provider", {}).get("uri")
    generation = str(receipt.get("provider", {}).get("generation", ""))
    if not remote or not generation:
        raise CustodyError("receipt does not contain a verified remote object generation")

    meta = gcs_stat(remote)
    if str(meta.get("generation", "")) != generation:
        raise CustodyError("remote object generation mismatch / possible stale or replaced object")

    work_dir.mkdir(parents=True, exist_ok=True)
    ciphertext = work_dir / f"restore-{receipt['bundle_id']}.gpg"
    archive = work_dir / f"restore-{receipt['bundle_id']}.tar.gz"
    gcs_download(remote, ciphertext, generation)
    if sha256_file(ciphertext) != receipt["ciphertext"]["sha256"]:
        raise CustodyError("ciphertext digest mismatch")
    decrypt_gpg(ciphertext, archive)
    if sha256_file(archive) != receipt["plaintext"]["sha256"]:
        raise CustodyError("decrypted bundle digest mismatch")
    safe_extract_tar_gz(archive, output_dir)
    verify = verify_extracted_tree(output_dir)
    if verify["status"] != "PASS":
        raise CustodyError(f"manifest verification failed: {verify['failures']}")
    return {"status": "PASS", "bundle_id": receipt["bundle_id"], "verified_entries": verify["entries"], "generation": generation}


def doctor(recipients: list[str] | None = None, gcs_base: str | None = None) -> dict:
    tools = {name: tool_path(name) for name in ("gpg", "gcloud")}
    errors = [f"missing tool: {name}" for name, path in tools.items() if not path]
    result: dict = {"schema": SCHEMA, "tools": tools, "errors": errors}
    if recipients:
        try:
            result["recipients"] = assert_recipient_separation(recipients)
        except CustodyError as e:
            errors.append(str(e))
    if gcs_base:
        try:
            result["gcs_base"] = validate_gs_base(gcs_base)
        except CustodyError as e:
            errors.append(str(e))
    result["status"] = "PASS" if not errors else "ERROR"
    return result


def cmd_goal(args: argparse.Namespace) -> int:
    d = doctor(args.recipient, args.gcs_base)
    if d["status"] != "PASS":
        print(json.dumps({"goal": "ERROR", "detail": d}, ensure_ascii=False, indent=2))
        return 2
    if len(args.recipient) < 2:
        print(json.dumps({"goal": "ERROR", "reason": "at least two separated recovery recipients are required for this candidate"}, indent=2))
        return 2

    work_dir = assert_private_runtime_path(Path(args.work))
    recovery_dir = assert_private_runtime_path(Path(args.recovery_dir))
    candidate = build_local_candidate(Path(args.input), work_dir, args.recipient, args.key_epoch)
    recovery_dir.mkdir(parents=True, exist_ok=True)
    local_receipt = recovery_dir / f"{candidate['bundle_id']}.preupload.json"
    write_json(local_receipt, candidate)

    if not args.approve_live_upload:
        print(json.dumps({
            "goal": "APPROVAL_REQUIRED",
            "reason": "local deterministic bundle and public-key ciphertext created and self-verified; live provider write not executed",
            "bundle_id": candidate["bundle_id"],
            "ciphertext_sha256": candidate["ciphertext"]["sha256"],
            "planned_remote": gcs_object_uri(args.gcs_base, candidate["bundle_id"]),
            "preupload_receipt": str(local_receipt),
        }, ensure_ascii=False, indent=2))
        return 3

    if not args.authority_ref:
        print(json.dumps({
            "goal": "APPROVAL_REQUIRED",
            "reason": "--approve-live-upload was supplied but no explicit --authority-ref was recorded",
        }, ensure_ascii=False, indent=2))
        return 3

    uploaded = live_upload(candidate, args.gcs_base, recovery_dir, args.authority_ref)
    print(json.dumps({
        "goal": "LIVE_UPLOAD_VERIFIED",
        "bundle_id": uploaded["bundle_id"],
        "remote_generation": uploaded["provider"].get("generation"),
        "authority_ref": uploaded.get("authority_ref"),
        "next_gate": "fresh-environment restore using separated recovery identity",
        "full_completion": "NOT_COMPLETE",
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Thin RTS encrypted cloud custody candidate")
    sub = p.add_subparsers(dest="command", required=True)

    doc = sub.add_parser("doctor")
    doc.add_argument("--recipient", action="append", default=[])
    doc.add_argument("--gcs-base")

    goal = sub.add_parser("goal", help="run until approval is required, an error occurs, or a verified live upload completes")
    goal.add_argument("--input", required=True, help="ready evidence bundle directory")
    goal.add_argument("--work", required=True, help="private local work directory outside the repository")
    goal.add_argument("--recovery-dir", required=True, help="private recovery-package output directory outside the repository")
    goal.add_argument("--recipient", action="append", required=True, help="full OpenPGP recipient fingerprint; repeat for recovery recipients")
    goal.add_argument("--key-epoch", required=True)
    goal.add_argument("--gcs-base", required=True, help="dedicated gs://bucket/prefix")
    goal.add_argument("--approve-live-upload", action="store_true")
    goal.add_argument("--authority-ref", help="normalized reference to explicit live-upload authority; required with --approve-live-upload")

    restore = sub.add_parser("restore")
    restore.add_argument("--receipt", required=True)
    restore.add_argument("--output", required=True)
    restore.add_argument("--work", required=True)
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "doctor":
            result = doctor(args.recipient, args.gcs_base)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "PASS" else 2
        if args.command == "goal":
            return cmd_goal(args)
        if args.command == "restore":
            result = restore_from_receipt(Path(args.receipt), Path(args.output), Path(args.work))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
    except CustodyError as e:
        print(json.dumps({"goal": "ERROR", "error": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
