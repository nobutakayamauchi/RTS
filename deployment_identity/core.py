from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "RTS-DEPLOYMENT-IDENTITY-V1"
STATUS_VALUES = {"ESTABLISHED", "PARTIAL", "UNKNOWN", "CONFLICT"}


class DeploymentIdentityError(RuntimeError):
    """Raised when a deployment identity snapshot is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _field(value: str | int | None, source: str, observed_at: str) -> dict[str, Any]:
    return {"value": value, "source": source, "observed_at": observed_at}


def _distinct(values: Iterable[str | None]) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value.strip()})


def _git_revision(root: Path) -> tuple[str | None, str]:
    env_candidates = _distinct(
        [
            os.getenv("DEPLOYED_REVISION"),
            os.getenv("GIT_COMMIT"),
            os.getenv("SOURCE_VERSION"),
            os.getenv("RENDER_GIT_COMMIT"),
            os.getenv("VERCEL_GIT_COMMIT_SHA"),
            os.getenv("GITHUB_SHA"),
        ]
    )
    if len(env_candidates) == 1:
        return env_candidates[0], "environment"
    if len(env_candidates) > 1:
        return "|".join(env_candidates), "environment_conflict"

    git_dir = root / ".git"
    head = git_dir / "HEAD"
    if not head.is_file():
        return None, "unavailable"
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref: "):
        ref = text.removeprefix("ref: ")
        ref_path = git_dir / ref
        if ref_path.is_file():
            return ref_path.read_text(encoding="utf-8").strip(), ".git/HEAD"
        packed = git_dir / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8").splitlines():
                if line.startswith("#") or line.startswith("^"):
                    continue
                parts = line.split(" ", 1)
                if len(parts) == 2 and parts[1] == ref:
                    return parts[0], ".git/packed-refs"
        return None, ".git/ref_missing"
    return text or None, ".git/HEAD"


def build_snapshot(
    *,
    root: Path | None = None,
    service_unit: str | None = None,
    active_route: str | None = None,
    deployed_revision: str | None = None,
    entrypoint: str | None = None,
    artifact: Path | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Collect a read-only deployment identity snapshot.

    The probe never treats repository code existence as runtime evidence. An
    ESTABLISHED result requires enough runtime/deployment anchors to identify
    the running surface independently from repository contents.
    """

    timestamp = observed_at or utc_now()
    working_directory = (root or Path.cwd()).resolve()
    executable = Path(sys.executable).resolve() if sys.executable else None
    resolved_entrypoint = entrypoint or (sys.argv[0] if sys.argv else None)

    env_service = os.getenv("SYSTEMD_UNIT") or os.getenv("SERVICE_UNIT") or os.getenv("K_SERVICE")
    service_value = service_unit or env_service
    service_source = "argument" if service_unit else ("environment" if env_service else "unavailable")

    env_route = os.getenv("ACTIVE_ROUTE") or os.getenv("SERVICE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    route_value = active_route or env_route
    route_source = "argument" if active_route else ("environment" if env_route else "unavailable")

    auto_revision, auto_revision_source = _git_revision(working_directory)
    revision_value = deployed_revision or auto_revision
    revision_source = "argument" if deployed_revision else auto_revision_source

    artifact_value: str | None = None
    artifact_source = "unavailable"
    artifact_path: str | None = None
    if artifact is not None:
        resolved_artifact = artifact.resolve()
        artifact_path = str(resolved_artifact)
        if not resolved_artifact.is_file():
            raise DeploymentIdentityError(f"artifact is not a readable file: {resolved_artifact}")
        artifact_value = sha256_file(resolved_artifact)
        artifact_source = "sha256(file)"

    revision_conflict = revision_source == "environment_conflict"
    fields = {
        "host": _field(socket.gethostname() or None, "socket.gethostname", timestamp),
        "pid": _field(os.getpid(), "os.getpid", timestamp),
        "service_unit": _field(service_value, service_source, timestamp),
        "working_directory": _field(str(working_directory), "process.cwd", timestamp),
        "executable": _field(str(executable) if executable else None, "sys.executable", timestamp),
        "entrypoint": _field(resolved_entrypoint, "argument" if entrypoint else "sys.argv[0]", timestamp),
        "active_route": _field(route_value, route_source, timestamp),
        "deployed_revision": _field(revision_value, revision_source, timestamp),
        "artifact_sha256": _field(artifact_value, artifact_source, timestamp),
        "artifact_path": _field(artifact_path, "argument" if artifact_path else "unavailable", timestamp),
    }

    required = ["working_directory", "executable", "entrypoint", "deployed_revision"]
    runtime_anchor_present = bool(service_value or route_value)
    missing = [name for name in required if not fields[name]["value"]]
    if revision_conflict:
        status = "CONFLICT"
    elif not missing and runtime_anchor_present:
        status = "ESTABLISHED"
    elif any(fields[name]["value"] for name in required) or runtime_anchor_present:
        status = "PARTIAL"
    else:
        status = "UNKNOWN"

    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "observed_at": timestamp,
        "status": status,
        "runtime_classification_allowed": status == "ESTABLISHED",
        "invariant": "Deployment Identity MUST be established before runtime implementation classification.",
        "code_existence_is_runtime_evidence": False,
        "fields": fields,
        "missing_required_fields": missing + ([] if runtime_anchor_present else ["service_unit_or_active_route"]),
        "conflicts": ["deployed_revision"] if revision_conflict else [],
    }
    validate_snapshot(snapshot)
    return snapshot


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    required_top = {
        "schema_version",
        "observed_at",
        "status",
        "runtime_classification_allowed",
        "invariant",
        "code_existence_is_runtime_evidence",
        "fields",
        "missing_required_fields",
        "conflicts",
    }
    if set(snapshot) != required_top:
        raise DeploymentIdentityError("snapshot top-level fields mismatch")
    if snapshot["schema_version"] != SCHEMA_VERSION:
        raise DeploymentIdentityError("unsupported schema_version")
    if snapshot["status"] not in STATUS_VALUES:
        raise DeploymentIdentityError("unsupported status")
    if snapshot["runtime_classification_allowed"] is not (snapshot["status"] == "ESTABLISHED"):
        raise DeploymentIdentityError("runtime classification gate mismatch")
    if snapshot["code_existence_is_runtime_evidence"] is not False:
        raise DeploymentIdentityError("code existence must never be runtime evidence")
    if not isinstance(snapshot["fields"], dict):
        raise DeploymentIdentityError("fields must be an object")
    for name, field in snapshot["fields"].items():
        if not isinstance(field, dict) or set(field) != {"value", "source", "observed_at"}:
            raise DeploymentIdentityError(f"invalid field evidence record: {name}")
        if field["observed_at"] != snapshot["observed_at"]:
            raise DeploymentIdentityError(f"field timestamp mismatch: {name}")
    if snapshot["status"] != "ESTABLISHED" and snapshot["runtime_classification_allowed"]:
        raise DeploymentIdentityError("fail-closed runtime gate violated")


def pretty_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
