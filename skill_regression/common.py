from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SNAPSHOT_SCHEMA = "RTS-SKILL-SNAPSHOT-V1"
ROLLBACK_SCHEMA = "RTS-SKILL-ROLLBACK-SNAPSHOT-V1"
DATASET_SCHEMA = "RTS-SKILL-REGRESSION-DATASET-V1"
RESULT_SCHEMA = "RTS-SKILL-REGRESSION-RESULT-V1"
EXECUTION_SCOPE = "LOCAL_STATIC_EVALUATION_ONLY"
PROMOTION = "NOT_ELIGIBLE"
OUTCOMES = {"PASS", "FAIL", "NOT_APPLICABLE"}
V1_OUTCOMES = ["RTS-OUTCOME-000001", "RTS-OUTCOME-000002", "RTS-OUTCOME-000003"]
V1_THRESHOLDS = {
    "maximum_regressions": 0,
    "maximum_safety_failures": 0,
    "minimum_improvements": 2,
    "minimum_candidate_pass_rate": 1.0,
    "rollback_snapshot_required": True,
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
PRIVATE = {
    "prompt", "prompts", "secret", "secrets", "credential", "credentials",
    "password", "passwords", "token", "tokens", "customer", "private",
    "payload", "provider",
}


class SkillRegressionError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode())


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise SkillRegressionError(f"missing file: {path}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SkillRegressionError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SkillRegressionError(f"invalid JSON: {path}: {exc}") from exc


def exact(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SkillRegressionError(f"{label} must be an object")
    missing, extra = sorted(fields - value.keys()), sorted(value.keys() - fields)
    if missing:
        raise SkillRegressionError(f"{label} missing fields: {', '.join(missing)}")
    if extra:
        raise SkillRegressionError(f"{label} unknown fields: {', '.join(extra)}")
    return value


def text(value: Any, label: str, limit: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SkillRegressionError(f"{label} must be a non-empty string")
    if len(value) > limit or any(c in value for c in ("\x00", "\r")):
        raise SkillRegressionError(f"{label} contains unsafe or excessive text")
    return value


def safe_id(value: Any, label: str) -> str:
    value = text(value, label, 128)
    if not SAFE_ID.fullmatch(value):
        raise SkillRegressionError(f"{label} contains unsafe characters")
    return value


def digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise SkillRegressionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def git_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not GIT_SHA.fullmatch(value):
        raise SkillRegressionError(f"{label} must be a lowercase 40-character Git SHA")
    return value


def relative(value: Any, label: str, prefix: str) -> str:
    value = text(value, label)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SkillRegressionError(f"{label} must be repository-relative")
    if not value.startswith(prefix):
        raise SkillRegressionError(f"{label} must stay inside {prefix}")
    return value


def strings(value: Any, label: str, *, sorted_unique: bool, empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise SkillRegressionError(f"{label} must be an array of non-empty strings")
    if not empty and not value:
        raise SkillRegressionError(f"{label} must not be empty")
    if len(value) != len(set(value)):
        raise SkillRegressionError(f"{label} must contain unique entries")
    if sorted_unique and value != sorted(value):
        raise SkillRegressionError(f"{label} must be sorted")
    return value


def reject_private_keys(value: Any, path: str = "document") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            parts = set(str(key).lower().replace("-", "_").replace(" ", "_").split("_"))
            if parts & PRIVATE:
                raise SkillRegressionError(f"{path} contains a forbidden private field: {key}")
            reject_private_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_keys(child, f"{path}[{index}]")


def material(value: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(fingerprint, None)
    return result


def fingerprint_material(value: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    return material(value, fingerprint)
