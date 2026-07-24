from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "RTS-ASSET-MANIFEST-V1"
REPO_VISIBILITIES = {"public", "private", "unknown"}
ASSET_KINDS = {
    "code", "schema", "test", "workflow", "documentation", "data",
    "design", "runtime", "process"
}
CANONICALITY = {
    "CANONICAL", "REFERENCE", "REUSABLE", "EXPERIMENTAL", "FROZEN", "SUPERSEDED"
}
REUSE_MODES = {"DIRECT", "ADAPT", "REFERENCE_ONLY", "NO_REUSE"}
LICENSE_STATUSES = {
    "COMPATIBLE", "REVIEW_REQUIRED", "INCOMPATIBLE", "NOT_APPLICABLE", "UNKNOWN"
}
SENSITIVITIES = {"PUBLIC", "PRIVATE_METADATA_ONLY", "RESTRICTED"}
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ASSET_ID_RE = re.compile(r"^RTS-AM-A[0-9]{4}$")
REF_RE = re.compile(r"^[A-Za-z0-9_./-]{1,128}$")
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[^\s]+"),
    re.compile(r"(?i)sk-[A-Za-z0-9]{12,}"),
    re.compile(r"(?i)nvapi-[A-Za-z0-9_-]{8,}"),
)


class AssetManifestError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AssetManifestError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AssetManifestError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssetManifestError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def package_root(root: Path) -> Path:
    return root / "asset_manifest"


def snapshots_root(root: Path) -> Path:
    return package_root(root) / "snapshots"


def current_path(root: Path) -> Path:
    return snapshots_root(root) / "current.json"


def snapshot_path(root: Path, version: int) -> Path:
    return snapshots_root(root) / f"v{version:03d}.json"


def index_root(root: Path) -> Path:
    return package_root(root) / "index"


def _require_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - value.keys())
    if missing:
        raise AssetManifestError(f"{label}: missing fields: {', '.join(missing)}")


def _require_string(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise AssetManifestError(f"{label}: expected non-empty string")
    return value


def _contains_secret(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in SECRET_PATTERNS)
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_secret(item) for item in value.values())
    return False


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {
        "schema_version", "snapshot_version", "generated_at", "source_refs",
        "repositories", "assets", "known_gaps", "assumptions", "privacy_statement"
    }
    _require_keys(snapshot, required, "snapshot")
    if snapshot["schema_version"] != SCHEMA_VERSION:
        raise AssetManifestError(f"snapshot: unsupported schema_version={snapshot['schema_version']!r}")
    version = snapshot["snapshot_version"]
    if not isinstance(version, int) or version < 1:
        raise AssetManifestError("snapshot: snapshot_version must be a positive integer")
    _require_string(snapshot["generated_at"], "snapshot.generated_at")
    _require_string(snapshot["privacy_statement"], "snapshot.privacy_statement")
    for field in ("source_refs", "known_gaps", "assumptions"):
        values = snapshot[field]
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise AssetManifestError(f"snapshot.{field}: expected string list")
    if _contains_secret(snapshot):
        raise AssetManifestError("snapshot: possible secret material detected")

    repositories = snapshot["repositories"]
    if not isinstance(repositories, list) or not repositories:
        raise AssetManifestError("snapshot.repositories: expected non-empty list")
    repo_by_name: dict[str, dict[str, Any]] = {}
    for index, repo in enumerate(repositories):
        label = f"repository[{index}]"
        if not isinstance(repo, dict):
            raise AssetManifestError(f"{label}: expected object")
        _require_keys(repo, {
            "repository", "visibility", "default_branch", "observed_ref", "role",
            "lifecycle_status", "canonical_responsibility", "allowed_reuse_boundary",
            "safe_metadata_only", "evidence_refs"
        }, label)
        name = _require_string(repo["repository"], f"{label}.repository")
        if not REPO_RE.fullmatch(name):
            raise AssetManifestError(f"{label}: invalid repository name: {name!r}")
        if name in repo_by_name:
            raise AssetManifestError(f"duplicate repository: {name}")
        visibility = repo["visibility"]
        if visibility not in REPO_VISIBILITIES:
            raise AssetManifestError(f"{label}: invalid visibility={visibility!r}")
        _require_string(repo["default_branch"], f"{label}.default_branch")
        observed_ref = _require_string(repo["observed_ref"], f"{label}.observed_ref")
        if not REF_RE.fullmatch(observed_ref):
            raise AssetManifestError(f"{label}: invalid observed_ref={observed_ref!r}")
        for field in ("role", "lifecycle_status", "canonical_responsibility", "allowed_reuse_boundary"):
            _require_string(repo[field], f"{label}.{field}")
        if not isinstance(repo["safe_metadata_only"], bool):
            raise AssetManifestError(f"{label}.safe_metadata_only: expected boolean")
        if visibility == "private" and repo["safe_metadata_only"] is not True:
            raise AssetManifestError(f"{label}: private repository requires safe_metadata_only=true")
        if not isinstance(repo["evidence_refs"], list) or not all(isinstance(item, str) for item in repo["evidence_refs"]):
            raise AssetManifestError(f"{label}.evidence_refs: expected string list")
        repo_by_name[name] = repo

    assets = snapshot["assets"]
    if not isinstance(assets, list):
        raise AssetManifestError("snapshot.assets: expected list")
    seen_ids: set[str] = set()
    canonical_by_capability: dict[str, list[str]] = {}
    for index, asset in enumerate(assets):
        label = f"asset[{index}]"
        if not isinstance(asset, dict):
            raise AssetManifestError(f"{label}: expected object")
        _require_keys(asset, {
            "asset_id", "repository", "locator", "kind", "capability", "source_ref",
            "canonicality", "reuse_mode", "license_status", "sensitivity",
            "consumer_candidates", "notes", "risks", "evidence_refs"
        }, label)
        asset_id = _require_string(asset["asset_id"], f"{label}.asset_id")
        if not ASSET_ID_RE.fullmatch(asset_id):
            raise AssetManifestError(f"{label}: invalid asset_id={asset_id!r}")
        if asset_id in seen_ids:
            raise AssetManifestError(f"duplicate asset_id: {asset_id}")
        seen_ids.add(asset_id)
        repo_name = _require_string(asset["repository"], f"{label}.repository")
        if repo_name not in repo_by_name:
            raise AssetManifestError(f"{asset_id}: unknown repository={repo_name}")
        locator = _require_string(asset["locator"], f"{label}.locator")
        kind = asset["kind"]
        canonicality = asset["canonicality"]
        reuse_mode = asset["reuse_mode"]
        license_status = asset["license_status"]
        sensitivity = asset["sensitivity"]
        if kind not in ASSET_KINDS:
            raise AssetManifestError(f"{asset_id}: invalid kind={kind!r}")
        if canonicality not in CANONICALITY:
            raise AssetManifestError(f"{asset_id}: invalid canonicality={canonicality!r}")
        if reuse_mode not in REUSE_MODES:
            raise AssetManifestError(f"{asset_id}: invalid reuse_mode={reuse_mode!r}")
        if license_status not in LICENSE_STATUSES:
            raise AssetManifestError(f"{asset_id}: invalid license_status={license_status!r}")
        if sensitivity not in SENSITIVITIES:
            raise AssetManifestError(f"{asset_id}: invalid sensitivity={sensitivity!r}")
        capability = _require_string(asset["capability"], f"{label}.capability")
        source_ref = _require_string(asset["source_ref"], f"{label}.source_ref")
        if not REF_RE.fullmatch(source_ref):
            raise AssetManifestError(f"{asset_id}: invalid source_ref={source_ref!r}")
        for field in ("consumer_candidates", "risks", "evidence_refs"):
            if not isinstance(asset[field], list) or not all(isinstance(item, str) for item in asset[field]):
                raise AssetManifestError(f"{asset_id}.{field}: expected string list")
        _require_string(asset["notes"], f"{asset_id}.notes", allow_empty=True)

        repo = repo_by_name[repo_name]
        if repo["visibility"] == "private" or sensitivity != "PUBLIC":
            if not locator.startswith("logical:"):
                raise AssetManifestError(f"{asset_id}: private/restricted assets require logical: locator")
        if sensitivity == "RESTRICTED":
            raise AssetManifestError(f"{asset_id}: restricted assets cannot be committed to the public manifest")
        if reuse_mode == "DIRECT" and license_status not in {"COMPATIBLE", "NOT_APPLICABLE"}:
            raise AssetManifestError(
                f"{asset_id}: DIRECT reuse requires compatible/not-applicable license, got {license_status}"
            )
        if canonicality == "CANONICAL":
            canonical_by_capability.setdefault(capability, []).append(asset_id)

    conflicts = {
        capability: ids for capability, ids in canonical_by_capability.items() if len(ids) > 1
    }
    if conflicts:
        details = "; ".join(f"{capability}={ids}" for capability, ids in sorted(conflicts.items()))
        raise AssetManifestError(f"conflicting canonical ownership: {details}")


def derive_indexes(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_snapshot(snapshot)
    repositories = sorted(snapshot["repositories"], key=lambda row: row["repository"])
    assets = sorted(snapshot["assets"], key=lambda row: row["asset_id"])
    ownership: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        ownership.setdefault(asset["capability"], []).append({
            "asset_id": asset["asset_id"],
            "repository": asset["repository"],
            "canonicality": asset["canonicality"],
            "reuse_mode": asset["reuse_mode"],
            "sensitivity": asset["sensitivity"],
        })
    ownership_rows = [
        {"capability": capability, "claims": claims}
        for capability, claims in sorted(ownership.items())
    ]
    generated_at = snapshot["generated_at"]
    return {
        "repositories.json": {
            "schema_version": SCHEMA_VERSION,
            "snapshot_version": snapshot["snapshot_version"],
            "generated_at": generated_at,
            "count": len(repositories),
            "repositories": repositories,
        },
        "assets.json": {
            "schema_version": SCHEMA_VERSION,
            "snapshot_version": snapshot["snapshot_version"],
            "generated_at": generated_at,
            "count": len(assets),
            "assets": assets,
        },
        "ownership.json": {
            "schema_version": SCHEMA_VERSION,
            "snapshot_version": snapshot["snapshot_version"],
            "generated_at": generated_at,
            "count": len(ownership_rows),
            "capabilities": ownership_rows,
        },
    }


def _current_pointer(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "current_version": snapshot["snapshot_version"],
        "path": f"asset_manifest/snapshots/v{snapshot['snapshot_version']:03d}.json",
        "updated_at": snapshot["generated_at"],
    }


def tracked_files(root: Path) -> list[Path]:
    base = package_root(root)
    files: list[Path] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if relative == "asset_manifest/manifests/manifest.sha256":
            continue
        files.append(path)
    return sorted(files)


def rebuild_manifest(root: Path) -> None:
    lines = []
    for path in tracked_files(root):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    manifest = package_root(root) / "manifests" / "manifest.sha256"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_current_snapshot(root: Path) -> dict[str, Any]:
    pointer = load_json(current_path(root))
    if pointer.get("schema_version") != SCHEMA_VERSION:
        raise AssetManifestError("current pointer schema mismatch")
    version = pointer.get("current_version")
    if not isinstance(version, int) or version < 1:
        raise AssetManifestError("current pointer version invalid")
    expected = f"asset_manifest/snapshots/v{version:03d}.json"
    if pointer.get("path") != expected:
        raise AssetManifestError("current pointer path mismatch")
    snapshot = load_json(root / expected)
    if snapshot.get("snapshot_version") != version:
        raise AssetManifestError("current pointer/snapshot version mismatch")
    return snapshot


def reindex(root: Path) -> dict[str, dict[str, Any]]:
    snapshot = load_current_snapshot(root)
    indexes = derive_indexes(snapshot)
    for name, value in indexes.items():
        write_json(index_root(root) / name, value)
    rebuild_manifest(root)
    return indexes


def create_snapshot(root: Path, source: Path) -> dict[str, Any]:
    raw = load_json(source)
    versions = sorted(snapshots_root(root).glob("v*.json"))
    next_version = max((int(path.stem[1:]) for path in versions), default=0) + 1
    snapshot = deepcopy(raw)
    snapshot["schema_version"] = SCHEMA_VERSION
    snapshot["snapshot_version"] = next_version
    snapshot.setdefault("generated_at", utc_now())
    validate_snapshot(snapshot)
    destination = snapshot_path(root, next_version)
    if destination.exists():
        raise AssetManifestError(f"refusing to overwrite immutable snapshot: {destination}")
    write_json(destination, snapshot)
    write_json(current_path(root), _current_pointer(snapshot))
    reindex(root)
    return snapshot


def _semantic(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def verify_manifest(root: Path) -> list[str]:
    manifest = package_root(root) / "manifests" / "manifest.sha256"
    if not manifest.exists():
        return ["missing asset manifest hash file"]
    expected: dict[str, str] = {}
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError:
            errors.append(f"invalid manifest line: {line}")
            continue
        expected[relative] = digest
    current = {path.relative_to(root).as_posix(): path for path in tracked_files(root)}
    missing = sorted(set(current) - set(expected))
    stale = sorted(set(expected) - set(current))
    if missing:
        errors.append(f"manifest missing paths: {missing}")
    if stale:
        errors.append(f"manifest has stale paths: {stale}")
    for relative, path in current.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected.get(relative) != digest:
            errors.append(f"hash mismatch: {relative}")
    return errors


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        snapshot = load_current_snapshot(root)
        validate_snapshot(snapshot)
        version = snapshot["snapshot_version"]
        versions = sorted(int(path.stem[1:]) for path in snapshots_root(root).glob("v*.json"))
        if versions != list(range(1, version + 1)):
            errors.append(f"non-contiguous snapshots: {versions}")
        expected_indexes = derive_indexes(snapshot)
        for name, expected in expected_indexes.items():
            path = index_root(root) / name
            try:
                actual = load_json(path)
            except AssetManifestError as exc:
                errors.append(str(exc))
                continue
            if _semantic(actual) != _semantic(expected):
                errors.append(f"stale index: asset_manifest/index/{name}")
    except AssetManifestError as exc:
        errors.append(str(exc))
    errors.extend(verify_manifest(root))
    return errors


def diff_snapshots(root: Path, old_version: int, new_version: int) -> dict[str, Any]:
    old = load_json(snapshot_path(root, old_version))
    new = load_json(snapshot_path(root, new_version))
    validate_snapshot(old)
    validate_snapshot(new)

    def keyed(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
        return {row[key]: row for row in rows}

    old_repos = keyed(old["repositories"], "repository")
    new_repos = keyed(new["repositories"], "repository")
    old_assets = keyed(old["assets"], "asset_id")
    new_assets = keyed(new["assets"], "asset_id")

    def delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
        return {
            "added": sorted(set(after) - set(before)),
            "removed": sorted(set(before) - set(after)),
            "changed": sorted(key for key in set(before) & set(after) if before[key] != after[key]),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "old_version": old_version,
        "new_version": new_version,
        "repositories": delta(old_repos, new_repos),
        "assets": delta(old_assets, new_assets),
    }
