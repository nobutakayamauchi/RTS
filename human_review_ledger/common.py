from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PRIVATE_SEGMENTS = {
    "prompt", "prompts", "secret", "secrets", "credential", "credentials",
    "password", "passwords", "token", "tokens", "customer", "customers",
    "private", "payload", "provider", "providers",
}
PRIVATE_MARKERS = (
    "credential:",
    "password:",
    "token:",
    "raw prompt",
    "customer data",
    "provider payload",
    "private repository body",
)


class HumanReviewLedgerError(RuntimeError):
    """Raised when the human review ledger fails closed."""


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
        raise HumanReviewLedgerError(f"missing file: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HumanReviewLedgerError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HumanReviewLedgerError(f"invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(value), encoding="utf-8")


def exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HumanReviewLedgerError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise HumanReviewLedgerError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise HumanReviewLedgerError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def text(value: Any, label: str, limit: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanReviewLedgerError(f"{label} must be a non-empty string")
    if len(value) > limit or any(char in value for char in ("\x00", "\r")):
        raise HumanReviewLedgerError(f"{label} contains unsafe or excessive text")
    return value


def safe_id(value: Any, label: str) -> str:
    value = text(value, label, 128)
    if not SAFE_ID.fullmatch(value):
        raise HumanReviewLedgerError(f"{label} contains unsafe characters")
    return value


def digest(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or set(value) - set("0123456789abcdef")
    ):
        raise HumanReviewLedgerError(f"{label} must be a lowercase SHA-256 digest")
    return value


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise HumanReviewLedgerError(f"{label} must be an integer >= {minimum}")
    return value


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise HumanReviewLedgerError(f"{label} must be a boolean")
    return value


def string_list(value: Any, label: str, *, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise HumanReviewLedgerError(f"{label} must be an array with at least {minimum} entries")
    result = [text(item, f"{label}[]") for item in value]
    if result != sorted(set(result)):
        raise HumanReviewLedgerError(f"{label} must be sorted and unique")
    return result


def optional_time(value: Any, label: str) -> datetime | None:
    if value is None:
        return None
    raw = text(value, label, 64)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HumanReviewLedgerError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise HumanReviewLedgerError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def require_relative_path(value: Any, label: str, allowed_prefix: str) -> str:
    value = text(value, label, 256)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value.startswith(allowed_prefix):
        raise HumanReviewLedgerError(f"{label} escapes the allowed path boundary")
    return value


def ensure_inside(root: Path, path: Path) -> Path:
    root = root.resolve()
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise HumanReviewLedgerError(f"path escapes repository root: {path}")
    return resolved


def reject_private_content(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).lower())
            segments = {segment for segment in normalized.split("_") if segment}
            if segments & PRIVATE_SEGMENTS:
                raise HumanReviewLedgerError(f"forbidden private field at {path}.{key}")
            reject_private_content(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PRIVATE_MARKERS):
            raise HumanReviewLedgerError(f"forbidden private marker at {path}")


def fingerprint_material(record: dict[str, Any], field: str) -> dict[str, Any]:
    material = copy.deepcopy(record)
    material.pop(field, None)
    return material
