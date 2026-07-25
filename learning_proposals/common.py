from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PRIVATE_SEGMENTS = {
    "prompt", "prompts", "secret", "secrets", "credential", "credentials",
    "password", "passwords", "token", "tokens", "customer", "customers",
    "private", "payload", "provider", "providers",
}


class LearningProposalError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise LearningProposalError(f"missing file: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LearningProposalError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LearningProposalError(f"invalid JSON: {path}: {exc}") from exc


def exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LearningProposalError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise LearningProposalError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise LearningProposalError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def text(value: Any, label: str, limit: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LearningProposalError(f"{label} must be a non-empty string")
    if len(value) > limit or any(char in value for char in ("\x00", "\r")):
        raise LearningProposalError(f"{label} contains unsafe or excessive text")
    return value


def optional_text(value: Any, label: str, limit: int = 256) -> str | None:
    if value is None:
        return None
    return text(value, label, limit)


def safe_id(value: Any, label: str) -> str:
    value = text(value, label, 128)
    if not SAFE_ID.fullmatch(value):
        raise LearningProposalError(f"{label} contains unsafe characters")
    return value


def digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise LearningProposalError(f"{label} must be a lowercase SHA-256 digest")
    return value


def string_list(value: Any, label: str, *, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise LearningProposalError(f"{label} must be an array with at least {minimum} entries")
    result = [text(item, f"{label}[]") for item in value]
    if result != sorted(set(result)):
        raise LearningProposalError(f"{label} must be sorted and unique")
    return result


def reject_private_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower())
            segments = {segment for segment in normalized.split("_") if segment}
            if segments & PRIVATE_SEGMENTS:
                raise LearningProposalError(f"forbidden private field at {path}.{key}")
            reject_private_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_keys(child, f"{path}[{index}]")


def require_relative_path(value: Any, label: str, allowed_prefix: str) -> str:
    value = text(value, label, 256)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value.startswith(allowed_prefix):
        raise LearningProposalError(f"{label} escapes the allowed path boundary")
    return value
