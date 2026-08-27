from __future__ import annotations

import copy
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable

from model_behavior_adaptation.core import (
    engine_key,
    validate_config,
    validate_engine,
    validate_observation,
)


class ProbeExecutionError(ValueError):
    pass


AUTHORITY_NONE = {
    "profile_application_authority": "NONE",
    "promotion_authority": "NONE",
}
FORBIDDEN_FIELDS = {
    "chain_of_thought",
    "hidden_reasoning",
    "reasoning_text",
    "scratchpad",
    "prompt_text",
    "response_text",
    "raw_prompt",
    "raw_response",
}
TERMINAL_JOB_STATES = {"COMPLETED", "QUARANTINED"}
BUDGET_LIMITS = {
    "max_jobs": (1, 64),
    "max_total_attempts": (1, 128),
    "max_parallel": (1, 4),
    "max_retries_per_job": (0, 2),
    "max_failures": (1, 64),
    "max_wall_clock_seconds": (30, 14400),
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def validate_budget(budget: dict[str, Any]) -> None:
    if not isinstance(budget, dict):
        raise ProbeExecutionError("budget must be an object")
    required = set(BUDGET_LIMITS) | {"max_estimated_cost_usd"}
    if set(budget) != required:
        raise ProbeExecutionError(f"budget fields must equal {sorted(required)}")
    for field, (lo, hi) in BUDGET_LIMITS.items():
        value = budget[field]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ProbeExecutionError(f"{field} must be integer in [{lo},{hi}]")
    cost = budget["max_estimated_cost_usd"]
    if cost is not None and (
        isinstance(cost, bool)
        or not isinstance(cost, (int, float))
        or cost <= 0
        or cost > 1000
    ):
        raise ProbeExecutionError("max_estimated_cost_usd must be null or within (0,1000]")
    if budget["max_failures"] > budget["max_jobs"]:
        raise ProbeExecutionError("max_failures cannot exceed max_jobs")


def validate_task(task: dict[str, Any]) -> None:
    required = {"task_id", "input_ref", "estimated_cost_usd", "timeout_seconds"}
    if not isinstance(task, dict) or set(task) != required:
        raise ProbeExecutionError(f"task fields must equal {sorted(required)}")
    if not isinstance(task["task_id"], str) or not task["task_id"]:
        raise ProbeExecutionError("task_id is required")
    if not isinstance(task["input_ref"], str) or not task["input_ref"]:
        raise ProbeExecutionError("input_ref is required")
    if any(field in task for field in FORBIDDEN_FIELDS):
        raise ProbeExecutionError("raw/hidden text cannot be embedded in task")
    cost = task["estimated_cost_usd"]
    if cost is not None and (
        isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0
    ):
        raise ProbeExecutionError("estimated_cost_usd must be non-negative or null")
    timeout = task["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 3600:
        raise ProbeExecutionError("timeout_seconds must be integer in [1,3600]")


def validate_probe_plan(plan: dict[str, Any]) -> None:
    required = {"engine", "engine_key", "domain", "probe_count", "probes", "execution"}
    if not isinstance(plan, dict) or not required <= set(plan):
        raise ProbeExecutionError("invalid probe plan")
    validate_engine(plan["engine"])
    if plan["engine_key"] != engine_key(plan["engine"]):
        raise ProbeExecutionError("probe plan engine_key mismatch")
    if not isinstance(plan["domain"], str) or not plan["domain"]:
        raise ProbeExecutionError("probe plan domain required")
    if plan["execution"] != "NOT_PERFORMED":
        raise ProbeExecutionError("probe plan must be unexecuted")
    probes = plan["probes"]
    if (
        not isinstance(probes, list)
        or not 1 <= len(probes) <= 8
        or plan["probe_count"] != len(probes)
    ):
        raise ProbeExecutionError("probe_count must match 1..8 probes")
    seen: set[str] = set()
    for probe in probes:
        if not isinstance(probe, dict) or not {"probe_id", "config"} <= set(probe):
            raise ProbeExecutionError("invalid probe")
        probe_id = probe["probe_id"]
        if not isinstance(probe_id, str) or not probe_id or probe_id in seen:
            raise ProbeExecutionError("probe_id must be unique")
        seen.add(probe_id)
        validate_config(probe["config"])


def _campaign_material(
    plan: dict[str, Any],
    tasks: list[dict[str, Any]],
    budget: dict[str, Any],
    adapter_kind: str,
) -> dict[str, Any]:
    return {
        "engine": plan["engine"],
        "engine_key": plan["engine_key"],
        "domain": plan["domain"],
        "probes": [
            {"probe_id": probe["probe_id"], "config": probe["config"]}
            for probe in plan["probes"]
        ],
        "tasks": tasks,
        "budget": budget,
        "adapter_kind": adapter_kind,
    }


def compile_campaign(
    plan: dict[str, Any],
    tasks: Iterable[dict[str, Any]],
    budget: dict[str, Any],
    adapter_kind: str = "fixture",
) -> dict[str, Any]:
    validate_probe_plan(plan)
    validate_budget(budget)
    rows = list(tasks)
    if not rows:
        raise ProbeExecutionError("at least one task is required")
    seen: set[str] = set()
    for task in rows:
        validate_task(task)
        if task["task_id"] in seen:
            raise ProbeExecutionError(f"duplicate task_id: {task['task_id']}")
        seen.add(task["task_id"])
    if adapter_kind not in {"fixture", "external"}:
        raise ProbeExecutionError("adapter_kind must be fixture or external")

    job_count = len(rows) * len(plan["probes"])
    if job_count > budget["max_jobs"]:
        raise ProbeExecutionError(
            f"campaign requires {job_count} jobs > max_jobs={budget['max_jobs']}; refusing silent truncation"
        )
    worst_attempts = job_count * (1 + budget["max_retries_per_job"])
    if worst_attempts > budget["max_total_attempts"]:
        raise ProbeExecutionError("worst-case retry attempts exceed max_total_attempts")

    unknown_cost = any(task["estimated_cost_usd"] is None for task in rows)
    base_cost = None
    if not unknown_cost:
        base_cost = sum(float(task["estimated_cost_usd"]) for task in rows) * len(plan["probes"])
    worst_cost = None if base_cost is None else base_cost * (1 + budget["max_retries_per_job"])

    if adapter_kind == "external":
        if budget["max_estimated_cost_usd"] is None:
            raise ProbeExecutionError("external campaigns require max_estimated_cost_usd")
        if worst_cost is None:
            raise ProbeExecutionError("external campaigns require per-task estimated_cost_usd")
    if (
        budget["max_estimated_cost_usd"] is not None
        and worst_cost is not None
        and worst_cost > float(budget["max_estimated_cost_usd"]) + 1e-9
    ):
        raise ProbeExecutionError("worst-case retry cost exceeds max_estimated_cost_usd")

    material = _campaign_material(plan, rows, budget, adapter_kind)
    fingerprint = _sha(material)
    jobs: list[dict[str, Any]] = []
    for task in rows:
        for probe in plan["probes"]:
            jobs.append(
                {
                    "job_id": _sha(
                        {
                            "campaign": fingerprint,
                            "task": task["task_id"],
                            "probe": probe["probe_id"],
                        }
                    )[:24],
                    "task_id": task["task_id"],
                    "input_ref": task["input_ref"],
                    "probe_id": probe["probe_id"],
                    "variant_id": probe["probe_id"],
                    "config": copy.deepcopy(probe["config"]),
                    "timeout_seconds": task["timeout_seconds"],
                    "estimated_cost_usd": task["estimated_cost_usd"],
                }
            )

    return {
        "campaign_id": f"campaign-{fingerprint[:16]}",
        "fingerprint": fingerprint,
        "engine": copy.deepcopy(plan["engine"]),
        "engine_key": plan["engine_key"],
        "domain": plan["domain"],
        "adapter_kind": adapter_kind,
        "budget": copy.deepcopy(budget),
        "job_count": len(jobs),
        "worst_case_attempts": worst_attempts,
        "worst_case_estimated_cost_usd": worst_cost,
        "jobs": jobs,
        "state": "PLANNED",
        "execution_authority": "NONE",
        "approval": "REQUIRED",
        "authority": dict(AUTHORITY_NONE),
    }


def authorize_campaign(campaign: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    if campaign.get("state") != "PLANNED" or campaign.get("execution_authority") != "NONE":
        raise ProbeExecutionError("campaign must be PLANNED and unauthorized")
    required = {"approved_by", "approved_fingerprint", "approved_at"}
    if not isinstance(approval, dict) or set(approval) != required:
        raise ProbeExecutionError(f"approval fields must equal {sorted(required)}")
    if not approval["approved_by"] or not approval["approved_at"]:
        raise ProbeExecutionError("approval requires approver and timestamp")
    if approval["approved_fingerprint"] != campaign["fingerprint"]:
        raise ProbeExecutionError("approval fingerprint mismatch")
    result = copy.deepcopy(campaign)
    result["state"] = "READY"
    result["execution_authority"] = "BOUNDED_CAMPAIGN_ONLY"
    result["approval"] = copy.deepcopy(approval)
    return result


def initialize_checkpoint(campaign: dict[str, Any]) -> dict[str, Any]:
    if campaign.get("state") != "READY" or campaign.get("execution_authority") != "BOUNDED_CAMPAIGN_ONLY":
        raise ProbeExecutionError("authorized READY campaign required")
    return {
        "campaign_id": campaign["campaign_id"],
        "fingerprint": campaign["fingerprint"],
        "state": "READY",
        "jobs": {
            job["job_id"]: {"state": "PENDING", "attempts": 0, "error_class": None}
            for job in campaign["jobs"]
        },
        "observations": [],
        "failure_count": 0,
        "attempt_count": 0,
        "started_chunks": 0,
        "stop_reason": None,
    }


def _unknown_observation(
    campaign: dict[str, Any], job: dict[str, Any], error: BaseException
) -> dict[str, Any]:
    return {
        "observation_id": f"obs-{job['job_id']}",
        "engine": copy.deepcopy(campaign["engine"]),
        "domain": campaign["domain"],
        "task_id": job["task_id"],
        "variant_id": job["variant_id"],
        "config": copy.deepcopy(job["config"]),
        "outcome": {"status": "UNKNOWN"},
        "metrics": {
            "wall_clock_seconds": None,
            "retry_count": None,
            "human_intervention_count": None,
            "tool_call_count": None,
            "quality_score": None,
        },
        "provenance": {
            "run_id": job["job_id"],
            "error_class": type(error).__name__,
        },
    }


def _validate_result(
    campaign: dict[str, Any], job: dict[str, Any], observation: dict[str, Any]
) -> None:
    validate_observation(observation)
    if engine_key(observation["engine"]) != campaign["engine_key"]:
        raise ProbeExecutionError("ENGINE_IDENTITY_MISMATCH")
    if observation["domain"] != campaign["domain"]:
        raise ProbeExecutionError("DOMAIN_MISMATCH")
    if observation["task_id"] != job["task_id"] or observation["variant_id"] != job["variant_id"]:
        raise ProbeExecutionError("JOB_RESULT_IDENTITY_MISMATCH")
    if observation["config"] != job["config"]:
        raise ProbeExecutionError("JOB_RESULT_CONFIG_MISMATCH")
    if observation["provenance"]["run_id"] != job["job_id"]:
        raise ProbeExecutionError("JOB_RESULT_RUN_ID_MISMATCH")


def run_campaign(
    campaign: dict[str, Any],
    adapter: Callable[[dict[str, Any]], dict[str, Any]],
    checkpoint: dict[str, Any] | None = None,
    *,
    max_jobs_this_chunk: int | None = None,
) -> dict[str, Any]:
    if campaign.get("state") != "READY" or campaign.get("execution_authority") != "BOUNDED_CAMPAIGN_ONLY":
        raise ProbeExecutionError("campaign execution requires exact human authorization")
    state = copy.deepcopy(checkpoint) if checkpoint is not None else initialize_checkpoint(campaign)
    if state.get("campaign_id") != campaign["campaign_id"] or state.get("fingerprint") != campaign["fingerprint"]:
        raise ProbeExecutionError("checkpoint campaign mismatch")
    if state.get("state") in {"STOPPED", "COMPLETED"}:
        return state

    budget = campaign["budget"]
    pending = [
        job
        for job in campaign["jobs"]
        if state["jobs"][job["job_id"]]["state"] not in TERMINAL_JOB_STATES
    ]
    if max_jobs_this_chunk is not None:
        if (
            isinstance(max_jobs_this_chunk, bool)
            or not isinstance(max_jobs_this_chunk, int)
            or max_jobs_this_chunk < 1
        ):
            raise ProbeExecutionError("max_jobs_this_chunk must be positive integer")
        pending = pending[:max_jobs_this_chunk]

    state["state"] = "RUNNING"
    state["started_chunks"] += 1
    started = time.monotonic()

    def invoke(job: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], int]:
        last_error: BaseException | None = None
        attempts = 0
        for _ in range(1 + budget["max_retries_per_job"]):
            attempts += 1
            try:
                observation = adapter(copy.deepcopy(job))
                _validate_result(campaign, job, observation)
                return (
                    observation,
                    {"state": "COMPLETED", "attempts": attempts, "error_class": None},
                    attempts,
                )
            except ProbeExecutionError as exc:
                if str(exc) == "ENGINE_IDENTITY_MISMATCH":
                    raise
                last_error = exc
            except Exception as exc:
                last_error = exc
        assert last_error is not None
        observation = _unknown_observation(campaign, job, last_error)
        validate_observation(observation)
        return (
            observation,
            {
                "state": "QUARANTINED",
                "attempts": attempts,
                "error_class": type(last_error).__name__,
            },
            attempts,
        )

    index = 0
    while index < len(pending):
        if state["failure_count"] >= budget["max_failures"]:
            state["state"] = "STOPPED"
            state["stop_reason"] = "FAILURE_BUDGET_REACHED"
            break
        if time.monotonic() - started >= budget["max_wall_clock_seconds"]:
            state["state"] = "STOPPED"
            state["stop_reason"] = "WALL_CLOCK_BUDGET_REACHED"
            break

        batch = pending[index : index + budget["max_parallel"]]
        index += len(batch)
        engine_mismatch = False
        with ThreadPoolExecutor(max_workers=budget["max_parallel"]) as pool:
            futures = {pool.submit(invoke, job): job for job in batch}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    observation, job_state, attempts = future.result()
                except ProbeExecutionError as exc:
                    if str(exc) == "ENGINE_IDENTITY_MISMATCH":
                        state["jobs"][job["job_id"]] = {
                            "state": "QUARANTINED",
                            "attempts": 1,
                            "error_class": "ENGINE_IDENTITY_MISMATCH",
                        }
                        state["attempt_count"] += 1
                        state["failure_count"] += 1
                        state["state"] = "STOPPED"
                        state["stop_reason"] = "ENGINE_IDENTITY_MISMATCH"
                        engine_mismatch = True
                        continue
                    raise

                state["attempt_count"] += attempts
                if state["attempt_count"] > budget["max_total_attempts"]:
                    raise ProbeExecutionError(
                        "attempt accounting exceeded authorized max_total_attempts"
                    )
                state["jobs"][job["job_id"]] = job_state
                if job_state["state"] == "QUARANTINED":
                    state["failure_count"] += 1
                state["observations"].append(observation)
        if engine_mismatch:
            break
        if state["failure_count"] >= budget["max_failures"] and index < len(pending):
            state["state"] = "STOPPED"
            state["stop_reason"] = "FAILURE_BUDGET_REACHED"
            break

    if state["state"] == "RUNNING":
        remaining = [
            job_state
            for job_state in state["jobs"].values()
            if job_state["state"] not in TERMINAL_JOB_STATES
        ]
        state["state"] = "COMPLETED" if not remaining else "PAUSED"
        state["stop_reason"] = None if not remaining else "CHUNK_LIMIT"
    return state


def observations_from_checkpoint(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    rows = copy.deepcopy(checkpoint.get("observations", []))
    seen: set[str] = set()
    for row in rows:
        validate_observation(row)
        if row["observation_id"] in seen:
            raise ProbeExecutionError("duplicate observation in checkpoint")
        seen.add(row["observation_id"])
    return rows


def build_application_preview(
    profile: dict[str, Any],
    current_engine: dict[str, Any],
    current_config: dict[str, Any],
) -> dict[str, Any]:
    validate_engine(current_engine)
    validate_config(current_config)
    if profile.get("engine_key") != engine_key(current_engine):
        return {
            "state": "BLOCKED",
            "reason": "ENGINE_IDENTITY_MISMATCH",
            "runtime_mutation": "NOT_PERFORMED",
            "authority": dict(AUTHORITY_NONE),
        }
    if profile.get("state") != "STABLE":
        return {
            "state": "BLOCKED",
            "reason": "PROFILE_NOT_STABLE",
            "runtime_mutation": "NOT_PERFORMED",
            "authority": dict(AUTHORITY_NONE),
        }
    proposed = copy.deepcopy(profile["recommended_config"])
    validate_config(proposed)
    changes = {
        key: {"from": current_config[key], "to": proposed[key]}
        for key in current_config
        if current_config[key] != proposed[key]
    }
    material = {
        "engine_key": profile["engine_key"],
        "domain": profile["domain"],
        "current": current_config,
        "proposed": proposed,
        "changes": changes,
    }
    fingerprint = _sha(material)
    return {
        "state": "REVIEW_REQUIRED",
        "fingerprint": fingerprint,
        "engine_key": profile["engine_key"],
        "domain": profile["domain"],
        "current_config": copy.deepcopy(current_config),
        "proposed_config": proposed,
        "changes": changes,
        "rollback_config": copy.deepcopy(current_config),
        "runtime_mutation": "NOT_PERFORMED",
        "authority": dict(AUTHORITY_NONE),
    }


def authorize_application(
    preview: dict[str, Any], approval: dict[str, Any]
) -> dict[str, Any]:
    if preview.get("state") != "REVIEW_REQUIRED":
        raise ProbeExecutionError("only REVIEW_REQUIRED preview can be approved")
    required = {"approved_by", "approved_fingerprint", "approved_at"}
    if not isinstance(approval, dict) or set(approval) != required:
        raise ProbeExecutionError(f"approval fields must equal {sorted(required)}")
    if approval["approved_fingerprint"] != preview["fingerprint"]:
        raise ProbeExecutionError("application approval fingerprint mismatch")
    if not approval["approved_by"] or not approval["approved_at"]:
        raise ProbeExecutionError("application approval requires approver and timestamp")
    result = copy.deepcopy(preview)
    result["state"] = "APPROVED_LOCAL_ARTIFACT"
    result["approval"] = copy.deepcopy(approval)
    result["authority"]["profile_application_authority"] = "LOCAL_POLICY_ARTIFACT_ONLY"
    return result


def materialize_policy_artifact(approved_preview: dict[str, Any]) -> dict[str, Any]:
    if approved_preview.get("state") != "APPROVED_LOCAL_ARTIFACT":
        raise ProbeExecutionError("approved local artifact preview required")
    return {
        "engine_key": approved_preview["engine_key"],
        "domain": approved_preview["domain"],
        "config": copy.deepcopy(approved_preview["proposed_config"]),
        "rollback_config": copy.deepcopy(approved_preview["rollback_config"]),
        "source_preview_fingerprint": approved_preview["fingerprint"],
        "runtime_mutation": "NOT_PERFORMED",
        "runtime_application_authority": "NONE",
        "promotion_authority": "NONE",
    }
