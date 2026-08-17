from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


class TaskEnvelopeError(ValueError):
    """Raised when benchmark material cannot be safely exposed to the solver."""


SCHEMA_VERSION = "ultimate-loop-reconstruction-furnace/task-envelope-v2"

# Raw benchmark answer/evaluator/validator metadata must never enter solver context.
FORBIDDEN_KEYS = frozenset(
    {
        "instance_id",
        "pull_number",
        "issue_numbers",
        "patch",
        "test_patch",
        "hints_text",
        "all_hints_text",
        "commit_url",
        "commit_urls",
        "created_at",
        "rebuild_cmds",
        "test_cmds",
        "print_cmds",
        "log_parser",
        "FAIL_TO_PASS",
        "PASS_TO_PASS",
        "docker_image",
        "source_record_sha256",
        "source_instance_id_sha256",
        "gold_validation_runs",
        "gold_validation_passes",
    }
)

ENVELOPE_KEYS = frozenset(
    {
        "schema_version",
        "task_id",
        "repo",
        "base_commit",
        "problem_statement",
        "platform",
        "task_valid",
        "network_policy",
    }
)

NETWORK_POLICY = "OFFLINE_AFTER_PREPARE"


@dataclass(frozen=True)
class ValidatorProvenance:
    """Validator-side metadata. Never pass this object to the solver."""

    source_record_sha256: str
    source_instance_id_sha256: str
    gold_validation_runs: int
    gold_validation_passes: int

    @property
    def task_valid(self) -> bool:
        return self.gold_validation_runs == 3 and self.gold_validation_passes == 3


def _exact_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TaskEnvelopeError(f"{field} must be a non-empty exact string")
    return value


def _normalized_public_string(value: Any, field: str) -> str:
    """Normalize transport-only edge whitespace on public benchmark text.

    Raw dataset text is allowed to contain leading/trailing newlines or spaces.
    The solver-visible envelope remains exact and canonical after this boundary.
    Internal whitespace/content is not rewritten.
    """

    if not isinstance(value, str):
        raise TaskEnvelopeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise TaskEnvelopeError(f"{field} must contain public task text")
    return normalized


def _sha256_json(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TaskEnvelopeError("source record must be canonical-JSON serializable") from exc
    return hashlib.sha256(encoded).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_validator_provenance(
    source_record: Mapping[str, Any],
    *,
    gold_validation_runs: int,
    gold_validation_passes: int,
) -> ValidatorProvenance:
    if not isinstance(source_record, Mapping):
        raise TaskEnvelopeError("source_record mapping required")
    instance_id = _exact_string(source_record.get("instance_id"), "instance_id")
    if gold_validation_runs != 3:
        raise TaskEnvelopeError("gold validator must run exactly three times")
    if not isinstance(gold_validation_passes, int) or not 0 <= gold_validation_passes <= 3:
        raise TaskEnvelopeError("gold_validation_passes must be in [0, 3]")
    return ValidatorProvenance(
        source_record_sha256=_sha256_json(dict(source_record)),
        source_instance_id_sha256=_sha256_text(instance_id),
        gold_validation_runs=gold_validation_runs,
        gold_validation_passes=gold_validation_passes,
    )


def sanitize_for_solver(
    source_record: Mapping[str, Any],
    *,
    opaque_task_id: str,
    task_valid: bool,
    platform: str = "linux",
) -> dict[str, Any]:
    """Return the only benchmark artifact permitted to enter solver context."""

    if not isinstance(source_record, Mapping):
        raise TaskEnvelopeError("source_record mapping required")
    if task_valid is not True:
        raise TaskEnvelopeError("only reproducibly gold-valid tasks may enter the furnace")

    envelope = {
        "schema_version": SCHEMA_VERSION,
        "task_id": _exact_string(opaque_task_id, "opaque_task_id"),
        "repo": _exact_string(source_record.get("repo"), "repo"),
        "base_commit": _exact_string(source_record.get("base_commit"), "base_commit"),
        "problem_statement": _normalized_public_string(
            source_record.get("problem_statement"), "problem_statement"
        ),
        "platform": _exact_string(platform, "platform"),
        "task_valid": True,
        "network_policy": NETWORK_POLICY,
    }
    verify_solver_envelope(envelope)
    return envelope


def verify_solver_envelope(envelope: Mapping[str, Any]) -> None:
    """Fail closed if the solver-visible artifact drifts from the exact schema."""

    if not isinstance(envelope, Mapping):
        raise TaskEnvelopeError("solver envelope mapping required")
    keys = set(envelope)
    if keys != ENVELOPE_KEYS:
        extra = sorted(keys - ENVELOPE_KEYS)
        missing = sorted(ENVELOPE_KEYS - keys)
        raise TaskEnvelopeError(
            f"solver envelope shape drift: extra={extra} missing={missing}"
        )
    leaked = sorted(keys & FORBIDDEN_KEYS)
    if leaked:
        raise TaskEnvelopeError(f"forbidden benchmark fields leaked: {leaked}")

    if envelope["schema_version"] != SCHEMA_VERSION:
        raise TaskEnvelopeError("schema_version mismatch")
    if envelope["task_valid"] is not True:
        raise TaskEnvelopeError("task_valid must be true")
    if envelope["network_policy"] != NETWORK_POLICY:
        raise TaskEnvelopeError("network policy widened")

    for field in (
        "task_id",
        "repo",
        "base_commit",
        "problem_statement",
        "platform",
    ):
        _exact_string(envelope[field], field)


def forbidden_key_scan(value: Any) -> list[str]:
    """Recursively report forbidden key names in an arbitrary solver namespace."""

    found: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                if isinstance(key, str) and key in FORBIDDEN_KEYS:
                    found.add(key)
                visit(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                visit(child)

    visit(value)
    return sorted(found)
