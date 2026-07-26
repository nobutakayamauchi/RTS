from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


class PilotRunContractError(RuntimeError):
    """Raised when a pilot seed/run contract fails closed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PilotRunContractError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PilotRunContractError(f"invalid JSON: {path}: {exc}") from exc


def exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PilotRunContractError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    extra = sorted(value.keys() - fields)
    if missing:
        raise PilotRunContractError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise PilotRunContractError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def text(value: Any, label: str, limit: int = 2048) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotRunContractError(f"{label} must be a non-empty string")
    if len(value) > limit or any(char in value for char in ("\x00", "\r")):
        raise PilotRunContractError(f"{label} contains unsafe or excessive text")
    return value


def string_list(value: Any, label: str, *, minimum: int = 1) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise PilotRunContractError(f"{label} must contain at least {minimum} entries")
    result = [text(item, f"{label}[]") for item in value]
    if len(result) != len(set(result)):
        raise PilotRunContractError(f"{label} must contain unique entries")
    return result


def fingerprint_material(seed: dict[str, Any]) -> dict[str, Any]:
    material = copy.deepcopy(seed)
    material.pop("seed_fingerprint", None)
    return material
