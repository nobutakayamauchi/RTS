from __future__ import annotations

from pathlib import Path
from typing import Any

from skill_regression.models import (
    SkillRegressionError,
    evaluate_dataset,
    load_json,
    sha256_file,
    validate_dataset,
    validate_result,
    validate_rollback,
    validate_snapshot,
)

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent


def resolve_inside(root: Path, relative: str, *, prefix: str) -> Path:
    candidate = (root / relative).resolve()
    allowed = (root / prefix).resolve()
    try:
        candidate.relative_to(allowed)
    except ValueError as exc:
        raise SkillRegressionError(f"path escapes {prefix}: {relative}") from exc
    return candidate


def artifact_paths(root: Path) -> dict[str, Path]:
    return {
        "baseline": root / "skill_regression" / "snapshots" / "feature-build" / "baseline.json",
        "candidate": root / "skill_regression" / "snapshots" / "feature-build" / "candidate.json",
        "rollback": root / "skill_regression" / "rollback" / "feature-build-v1.json",
        "dataset": root / "skill_regression" / "datasets" / "feature-build-v1.json",
        "result": root / "skill_regression" / "results" / "feature-build-v1.json",
    }


def load_artifacts(root: Path = DEFAULT_ROOT) -> dict[str, dict[str, Any]]:
    paths = artifact_paths(root)
    return {name: load_json(path) for name, path in paths.items()}


def verify_snapshot_content(root: Path, snapshot: dict[str, Any]) -> None:
    content_path = resolve_inside(
        root,
        snapshot["content_path"],
        prefix="skill_regression/snapshots",
    )
    digest = sha256_file(content_path)
    if digest != snapshot["content_sha256"]:
        raise SkillRegressionError(
            f"{snapshot['snapshot_id']}: content digest mismatch"
        )
    if digest != snapshot["source"]["source_content_sha256"]:
        raise SkillRegressionError(
            f"{snapshot['snapshot_id']}: source content digest mismatch"
        )


def verify_outcome_bundle_links(root: Path, dataset: dict[str, Any]) -> None:
    examples = root / "outcome_evidence" / "examples"
    by_id: dict[str, dict[str, Any]] = {}
    for path in sorted(examples.glob("*.json")):
        value = load_json(path)
        bundle_id = value.get("bundle_id")
        if isinstance(bundle_id, str):
            by_id[bundle_id] = value
    for bundle_id in dataset["outcome_bundle_ids"]:
        value = by_id.get(bundle_id)
        if value is None:
            raise SkillRegressionError(f"missing referenced outcome bundle: {bundle_id}")
        if value.get("execution_scope") != "SIMULATED_ONLY":
            raise SkillRegressionError(f"{bundle_id}: linked outcome must remain SIMULATED_ONLY")
        if value.get("promotion_eligibility") != "NOT_ELIGIBLE":
            raise SkillRegressionError(f"{bundle_id}: linked outcome must remain NOT_ELIGIBLE")


def verify_all(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    artifacts = load_artifacts(root)
    baseline = validate_snapshot(artifacts["baseline"])
    candidate = validate_snapshot(artifacts["candidate"])
    rollback = validate_rollback(artifacts["rollback"])
    dataset = validate_dataset(artifacts["dataset"])
    committed_result = validate_result(artifacts["result"])

    verify_snapshot_content(root, baseline)
    verify_snapshot_content(root, candidate)
    verify_outcome_bundle_links(root, dataset)

    computed = evaluate_dataset(baseline, candidate, rollback, dataset)
    if committed_result != computed:
        raise SkillRegressionError(
            "committed regression result does not match deterministic evaluation"
        )

    return {
        "dataset_id": dataset["dataset_id"],
        "skill_id": dataset["skill_id"],
        "fixtures": len(dataset["fixture_set"]),
        "recommendation": computed["recommendation"],
        "promotion_eligibility": computed["promotion_eligibility"],
        "regressions": computed["summary"]["regressions"],
        "improvements": computed["summary"]["improvements"],
        "safety_failures": computed["summary"]["safety_failures"],
        "candidate_pass_rate": computed["summary"]["candidate_pass_rate"],
        "result_fingerprint": computed["result_fingerprint"],
    }
