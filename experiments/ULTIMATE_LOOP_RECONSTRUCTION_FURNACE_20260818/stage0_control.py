from __future__ import annotations

import hashlib
import random
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence


SUPPORTED_SPLITS = ("c", "cpp", "cs", "go", "java", "js", "rust", "ts")
RUN_SCHEMA = "ultimate-loop-reconstruction-furnace/run-manifest-v1"


class FurnaceControlError(ValueError):
    pass


@dataclass(frozen=True)
class RunManifest:
    schema_version: str
    dataset_repo: str
    dataset_revision: str
    evaluator_repo: str
    evaluator_revision: str
    seed_sha256: str
    selected_splits: tuple[str, ...]
    stage: str
    solver_dataset_access: bool

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["selected_splits"] = list(self.selected_splits)
        return out


def _exact_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise FurnaceControlError(f"{field} must be a non-empty exact string")
    return value


def _seed_hex(label: str, dataset_revision: str, evaluator_revision: str) -> str:
    material = "|".join((
        _exact_string(label, "seed_label"),
        _exact_string(dataset_revision, "dataset_revision"),
        _exact_string(evaluator_revision, "evaluator_revision"),
    ))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_run_manifest(
    *, stage: str, seed_label: str, dataset_revision: str,
    evaluator_revision: str, split_count: int,
    dataset_repo: str = "SWE-bench-Live/MultiLang",
    evaluator_repo: str = "microsoft/SWE-bench-Live",
) -> RunManifest:
    if stage not in {"STAGE0", "STAGE1", "STAGE3"}:
        raise FurnaceControlError("unsupported stage")
    if not isinstance(split_count, int) or not 1 <= split_count <= len(SUPPORTED_SPLITS):
        raise FurnaceControlError("split_count out of range")
    seed_sha256 = _seed_hex(seed_label, dataset_revision, evaluator_revision)
    rng = random.Random(int(seed_sha256, 16))
    selected = tuple(rng.sample(list(SUPPORTED_SPLITS), split_count))
    return RunManifest(
        schema_version=RUN_SCHEMA,
        dataset_repo=_exact_string(dataset_repo, "dataset_repo"),
        dataset_revision=_exact_string(dataset_revision, "dataset_revision"),
        evaluator_repo=_exact_string(evaluator_repo, "evaluator_repo"),
        evaluator_revision=_exact_string(evaluator_revision, "evaluator_revision"),
        seed_sha256=seed_sha256,
        selected_splits=selected,
        stage=stage,
        solver_dataset_access=False,
    )


def candidate_order(rows: Iterable[Mapping[str, Any]], *, split: str, seed_sha256: str) -> list[Mapping[str, Any]]:
    if split not in SUPPORTED_SPLITS:
        raise FurnaceControlError("unsupported split")
    _exact_string(seed_sha256, "seed_sha256")
    decorated: list[tuple[str, Mapping[str, Any]]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise FurnaceControlError("candidate row mapping required")
        instance_id = _exact_string(row.get("instance_id"), "instance_id")
        rank = hashlib.sha256(f"{seed_sha256}|{split}|{instance_id}".encode("utf-8")).hexdigest()
        decorated.append((rank, row))
    decorated.sort(key=lambda item: item[0])
    return [row for _, row in decorated]


def opaque_task_id(*, instance_id: str, seed_sha256: str, ordinal: int) -> str:
    if not isinstance(ordinal, int) or ordinal < 1:
        raise FurnaceControlError("ordinal must be >= 1")
    instance_id = _exact_string(instance_id, "instance_id")
    seed_sha256 = _exact_string(seed_sha256, "seed_sha256")
    digest = hashlib.sha256(f"{seed_sha256}|task|{ordinal}|{instance_id}".encode("utf-8")).hexdigest()[:16].upper()
    return f"FURNACE-{ordinal:02d}-{digest}"


def resource_preflight(
    *, cpu_count: int, memory_gib: float, requested_cpu: int = 4,
    guidance_memory_gib: float = 16.0, hard_min_memory_gib: float = 14.0,
) -> dict[str, Any]:
    """Separate nominal benchmark guidance from a hard Stage 0 admission floor."""
    if (
        cpu_count < 1 or memory_gib <= 0 or requested_cpu < 1
        or guidance_memory_gib <= 0 or hard_min_memory_gib <= 0
        or hard_min_memory_gib > guidance_memory_gib
    ):
        raise FurnaceControlError("resource values invalid")
    blockers: list[str] = []
    warnings: list[str] = []
    if cpu_count < requested_cpu:
        blockers.append("CPU_BELOW_HARD_MIN")
    if memory_gib < hard_min_memory_gib:
        blockers.append("MEMORY_BELOW_HARD_MIN")
    elif memory_gib < guidance_memory_gib:
        warnings.append("MEMORY_BELOW_GUIDANCE")
    state = "RESOURCE_BLOCKED" if blockers else ("RESOURCE_READY_WITH_WARNING" if warnings else "RESOURCE_READY")
    return {
        "state": state,
        "solver_failure": False,
        "cpu_count": cpu_count,
        "memory_gib": memory_gib,
        "requested_cpu": requested_cpu,
        "guidance_memory_gib": guidance_memory_gib,
        "hard_min_memory_gib": hard_min_memory_gib,
        "blockers": blockers,
        "warnings": warnings,
    }


def choose_first_valid(ordered_rows: Sequence[Mapping[str, Any]], validation_passes: Mapping[str, int]) -> Mapping[str, Any]:
    for row in ordered_rows:
        instance_id = _exact_string(row.get("instance_id"), "instance_id")
        passes = validation_passes.get(instance_id)
        if passes is None:
            raise FurnaceControlError("missing gold-validation result in deterministic prefix")
        if passes not in {0, 1, 2, 3}:
            raise FurnaceControlError("gold-validation pass count must be in [0, 3]")
        if passes == 3:
            return row
    raise FurnaceControlError("no reproducibly valid candidate in supplied deterministic prefix")
