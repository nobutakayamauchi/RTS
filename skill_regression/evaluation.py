from __future__ import annotations

from typing import Any

from skill_regression.common import (
    PROMOTION,
    RESULT_SCHEMA,
    V1_THRESHOLDS,
    SkillRegressionError,
    sha256_value,
)
from skill_regression.validators import (
    validate_dataset,
    validate_rollback,
    validate_snapshot,
)


def subsequence(required: list[str], actual: list[str]) -> bool:
    cursor = iter(actual)
    return all(any(item == step for item in cursor) for step in required)


def fixture_outcome(contract: dict[str, Any], fixture: dict[str, Any]) -> str:
    req = fixture["requirements"]
    if fixture["mode"] == "NOT_APPLICABLE":
        return "NOT_APPLICABLE" if set(req["not_for"]) <= set(contract["not_for"]) else "FAIL"
    if not subsequence(req["steps"], contract["ordered_steps"]):
        return "FAIL"
    if not set(req["outputs"]) <= set(contract["expected_outputs"]):
        return "FAIL"
    if not set(req["safety_rules"]) <= set(contract["safety_rules"]):
        return "FAIL"
    return "PASS"


def evaluate_dataset(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    rollback: dict[str, Any],
    dataset: dict[str, Any],
) -> dict[str, Any]:
    validate_snapshot(baseline)
    validate_snapshot(candidate)
    validate_rollback(rollback)
    validate_dataset(dataset)
    if baseline["role"] != "BASELINE" or candidate["role"] != "CANDIDATE":
        raise SkillRegressionError("evaluation requires BASELINE and CANDIDATE snapshots")
    if len({baseline["skill_id"], candidate["skill_id"], dataset["skill_id"]}) != 1:
        raise SkillRegressionError("Skill id mismatch across regression artifacts")
    if candidate["source"]["derived_from_snapshot_id"] != baseline["snapshot_id"]:
        raise SkillRegressionError("candidate must derive from the selected baseline")
    if dataset["baseline_snapshot_id"] != baseline["snapshot_id"]:
        raise SkillRegressionError("dataset baseline snapshot mismatch")
    if dataset["candidate_snapshot_id"] != candidate["snapshot_id"]:
        raise SkillRegressionError("dataset candidate snapshot mismatch")
    if dataset["rollback_id"] != rollback["rollback_id"]:
        raise SkillRegressionError("dataset rollback id mismatch")
    if rollback["baseline_snapshot_id"] != baseline["snapshot_id"]:
        raise SkillRegressionError("rollback baseline snapshot mismatch")
    if rollback["candidate_snapshot_id"] != candidate["snapshot_id"]:
        raise SkillRegressionError("rollback candidate snapshot mismatch")
    if rollback["baseline_snapshot_fingerprint"] != baseline["snapshot_fingerprint"]:
        raise SkillRegressionError("rollback baseline fingerprint mismatch")
    if rollback["restore_content_path"] != baseline["content_path"]:
        raise SkillRegressionError("rollback restore path mismatch")
    if rollback["restore_content_sha256"] != baseline["content_sha256"]:
        raise SkillRegressionError("rollback restore digest mismatch")

    rows = []
    for fixture in dataset["fixture_set"]:
        old = fixture_outcome(baseline["contract"], fixture)
        new = fixture_outcome(candidate["contract"], fixture)
        if {"baseline": old, "candidate": new} != fixture["expected"]:
            raise SkillRegressionError(
                f"{fixture['fixture_id']}: committed expected outcomes do not match deterministic evaluation"
            )
        rows.append({
            "fixture_id": fixture["fixture_id"],
            "baseline": old,
            "candidate": new,
            "regression": old == "PASS" and new != "PASS",
            "improvement": old != "PASS" and new == "PASS",
            "safety_failure": fixture["kind"] == "SAFETY" and new != "PASS",
        })

    applicable = [row for row in rows if row["candidate"] != "NOT_APPLICABLE"]
    summary = {
        "total_fixtures": len(rows),
        "applicable_fixtures": len(applicable),
        "baseline_passed": sum(row["baseline"] == "PASS" for row in rows),
        "candidate_passed": sum(row["candidate"] == "PASS" for row in rows),
        "regressions": sum(row["regression"] for row in rows),
        "improvements": sum(row["improvement"] for row in rows),
        "safety_failures": sum(row["safety_failure"] for row in rows),
        "candidate_pass_rate": round(
            sum(row["candidate"] == "PASS" for row in applicable) / len(applicable), 4
        ) if applicable else 0.0,
    }
    ready = (
        summary["regressions"] <= V1_THRESHOLDS["maximum_regressions"]
        and summary["safety_failures"] <= V1_THRESHOLDS["maximum_safety_failures"]
        and summary["improvements"] >= V1_THRESHOLDS["minimum_improvements"]
        and summary["candidate_pass_rate"] >= V1_THRESHOLDS["minimum_candidate_pass_rate"]
    )
    result = {
        "schema_version": RESULT_SCHEMA,
        "result_id": "RTS-SKILL-REGRESSION-RESULT-000001",
        "dataset_id": dataset["dataset_id"],
        "dataset_fingerprint": dataset["dataset_fingerprint"],
        "baseline_snapshot_fingerprint": baseline["snapshot_fingerprint"],
        "candidate_snapshot_fingerprint": candidate["snapshot_fingerprint"],
        "rollback_fingerprint": rollback["rollback_fingerprint"],
        "fixture_results": rows,
        "summary": summary,
        "recommendation": "RESEARCH_READY" if ready else "REJECT_CANDIDATE",
        "promotion_eligibility": PROMOTION,
    }
    result["result_fingerprint"] = sha256_value(result)
    return result
