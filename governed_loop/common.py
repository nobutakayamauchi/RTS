from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FORBIDDEN_PRIVATE_KEYS = {
    "prompt",
    "raw_prompt",
    "credential",
    "credentials",
    "secret",
    "token",
    "customer_data",
    "provider_payload",
    "private_payload",
    "repository_body",
    "private_repository_body",
}
FORBIDDEN_VALUE_MARKERS = (
    "credential:",
    "customer_data:",
    "provider_payload:",
    "private_repository_body:",
)


class GovernedLoopError(RuntimeError):
    """Raised when a governed loop record is unsafe, stale, or invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise GovernedLoopError(f"missing governed file: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GovernedLoopError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GovernedLoopError(f"invalid JSON: {path}: {exc}") from exc


def ensure_inside(root: Path, path: Path) -> Path:
    root = root.resolve()
    path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise GovernedLoopError(f"path escapes repository root: {path}") from exc
    return path


def exact_object(value: Any, expected: set[str], *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GovernedLoopError(f"{field} must be an object")
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        raise GovernedLoopError(f"{field} missing fields: {', '.join(missing)}")
    if extra:
        raise GovernedLoopError(f"{field} unknown fields: {', '.join(extra)}")
    return value


def reject_private_content(value: Any, *, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_PRIVATE_KEYS:
                raise GovernedLoopError(f"forbidden private field at {path}.{key}")
            reject_private_content(child, path=f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_content(child, path=f"{path}[{index}]")
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_VALUE_MARKERS):
            raise GovernedLoopError(f"forbidden private marker at {path}")
