from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from statistics import median
from typing import Any, Iterable


class ProfileError(ValueError):
    pass


PROFILE_STATES = {
    "UNCHARACTERIZED",
    "PROVISIONAL",
    "STABLE",
    "DRIFT_SUSPECTED",
    "DRIFT_CONFIRMED",
    "QUARANTINED",
}
OUTCOME_STATES = {"SUCCESS", "FAILURE", "UNKNOWN"}
AUTHORITY_NONE = {
    "execution_authority": "NONE",
    "profile_application_authority": "NONE",
    "promotion_authority": "NONE",
}
CONFIG_VALUES = {
    "context_mode": {"minimal", "selective", "expanded"},
    "recall_mode": {"off", "light", "selective"},
    "instruction_density": {"low", "medium", "high"},
    "autonomy": {"bounded", "medium", "high"},
    "reasoning_tier": {"low", "medium", "high", "xhigh"},
    "tool_strategy": {"bounded", "adaptive", "autonomous"},
}
FORBIDDEN_OBSERVATION_FIELDS = {
    "chain_of_thought",
    "hidden_reasoning",
    "reasoning_text",
    "scratchpad",
    "prompt_text",
    "response_text",
}
NUMERIC_METRICS = {
    "wall_clock_seconds",
    "retry_count",
    "human_intervention_count",
    "tool_call_count",
    "quality_score",
}


def conservative_config() -> dict[str, str]:
    return {
        "context_mode": "selective",
        "recall_mode": "light",
        "instruction_density": "medium",
        "autonomy": "bounded",
        "reasoning_tier": "medium",
        "tool_strategy": "bounded",
    }


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def validate_engine(engine: dict[str, Any]) -> None:
    if not isinstance(engine, dict):
        raise ProfileError("engine must be an object")
    required = {"provider", "model", "adapter_version"}
    missing = sorted(required - set(engine))
    if missing:
        raise ProfileError(f"engine missing fields: {missing}")
    for key, value in engine.items():
        if value is not None and not isinstance(value, str):
            raise ProfileError(f"engine.{key} must be string or null")
    if not engine["provider"] or not engine["model"] or not engine["adapter_version"]:
        raise ProfileError("provider/model/adapter_version must be non-empty")


def engine_key(engine: dict[str, Any]) -> str:
    validate_engine(engine)
    digest = hashlib.sha256(_canonical(engine).encode()).hexdigest()[:16]
    revision = engine.get("model_revision") or "unknown-revision"
    return f"{engine['provider']}:{engine['model']}@{revision}#{digest}"


def validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise ProfileError("config must be an object")
    if set(config) != set(CONFIG_VALUES):
        raise ProfileError(f"config fields must equal {sorted(CONFIG_VALUES)}")
    for field, allowed in CONFIG_VALUES.items():
        if config[field] not in allowed:
            raise ProfileError(f"invalid {field}={config[field]!r}")


def validate_observation(observation: dict[str, Any]) -> None:
    if not isinstance(observation, dict):
        raise ProfileError("observation must be an object")
    forbidden = sorted(FORBIDDEN_OBSERVATION_FIELDS & set(observation))
    if forbidden:
        raise ProfileError(f"hidden/raw text fields are forbidden: {forbidden}")
    required = {
        "observation_id",
        "engine",
        "domain",
        "task_id",
        "variant_id",
        "config",
        "outcome",
        "metrics",
        "provenance",
    }
    missing = sorted(required - set(observation))
    if missing:
        raise ProfileError(f"observation missing fields: {missing}")
    for field in ("observation_id", "domain", "task_id", "variant_id"):
        if not isinstance(observation[field], str) or not observation[field]:
            raise ProfileError(f"{field} must be a non-empty string")
    validate_engine(observation["engine"])
    validate_config(observation["config"])
    outcome = observation["outcome"]
    if not isinstance(outcome, dict) or outcome.get("status") not in OUTCOME_STATES:
        raise ProfileError(f"outcome.status must be one of {sorted(OUTCOME_STATES)}")
    metrics = observation["metrics"]
    if not isinstance(metrics, dict):
        raise ProfileError("metrics must be an object")
    unknown_metric_keys = sorted(set(metrics) - NUMERIC_METRICS)
    if unknown_metric_keys:
        raise ProfileError(f"unsupported metrics: {unknown_metric_keys}")
    for key, value in metrics.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProfileError(f"metrics.{key} must be numeric or null")
        if value < 0:
            raise ProfileError(f"metrics.{key} must be non-negative")
        if key == "quality_score" and value > 1:
            raise ProfileError("quality_score must be within [0,1]")
    provenance = observation["provenance"]
    if not isinstance(provenance, dict):
        raise ProfileError("provenance must be an object")
    if not isinstance(provenance.get("run_id"), str) or not provenance.get("run_id"):
        raise ProfileError("provenance.run_id is required")
    if any(key in provenance for key in FORBIDDEN_OBSERVATION_FIELDS):
        raise ProfileError("provenance cannot contain hidden reasoning or raw prompt/response bodies")


def validate_observations(observations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = list(observations)
    seen: set[str] = set()
    for row in rows:
        validate_observation(row)
        oid = row["observation_id"]
        if oid in seen:
            raise ProfileError(f"duplicate observation_id: {oid}")
        seen.add(oid)
    return rows


def wilson_lower_bound(successes: int, total: int, z: float = 1.96) -> float | None:
    if total <= 0:
        return None
    phat = successes / total
    denominator = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return max(0.0, (centre - margin) / denominator)


def _median_metric(rows: list[dict[str, Any]], name: str) -> float | None:
    values = [float(row["metrics"][name]) for row in rows if row["metrics"].get(name) is not None]
    return median(values) if values else None


def aggregate_variants(observations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = validate_observations(observations)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["variant_id"], _canonical(row["config"]))].append(row)
    result = []
    for (variant_id, _), group in sorted(groups.items()):
        known = [row for row in group if row["outcome"]["status"] != "UNKNOWN"]
        successes = sum(row["outcome"]["status"] == "SUCCESS" for row in known)
        tasks = {row["task_id"] for row in known}
        n = len(known)
        success_rate = (successes / n) if n else None
        result.append({
            "variant_id": variant_id,
            "config": group[0]["config"],
            "known_outcomes": n,
            "unknown_outcomes": len(group) - n,
            "successes": successes,
            "success_rate": success_rate,
            "success_lower_bound": wilson_lower_bound(successes, n),
            "distinct_tasks": len(tasks),
            "quality_median": _median_metric(known, "quality_score"),
            "human_intervention_median": _median_metric(known, "human_intervention_count"),
            "retry_median": _median_metric(known, "retry_count"),
            "wall_clock_median": _median_metric(known, "wall_clock_seconds"),
            "tool_call_median": _median_metric(known, "tool_call_count"),
            "eligible": n >= 3 and len(tasks) >= 2,
        })
    return result


def _rank_variant(row: dict[str, Any]) -> tuple:
    def lower_is_better(value: float | None) -> float:
        return -value if value is not None else float("-inf")
    return (
        1 if row["eligible"] else 0,
        row["success_lower_bound"] if row["success_lower_bound"] is not None else -1.0,
        row["success_rate"] if row["success_rate"] is not None else -1.0,
        row["quality_median"] if row["quality_median"] is not None else -1.0,
        lower_is_better(row["human_intervention_median"]),
        lower_is_better(row["retry_median"]),
        lower_is_better(row["wall_clock_median"]),
    )


def build_profile(observations: Iterable[dict[str, Any]], engine: dict[str, Any], domain: str) -> dict[str, Any]:
    validate_engine(engine)
    if not domain:
        raise ProfileError("domain is required")
    rows = validate_observations(observations)
    key = engine_key(engine)
    relevant = []
    for row in rows:
        if row["domain"] != domain:
            continue
        if engine_key(row["engine"]) != key:
            raise ProfileError("mixed engine identity inside requested domain profile")
        relevant.append(row)
    variants = aggregate_variants(relevant)
    eligible = [row for row in variants if row["eligible"]]
    if not eligible:
        return {
            "engine": engine,
            "engine_key": key,
            "domain": domain,
            "state": "UNCHARACTERIZED",
            "confidence": "LOW",
            "reason": "INSUFFICIENT_DISTINCT_TASK_EVIDENCE",
            "recommended_config": conservative_config(),
            "selected_variant_id": None,
            "evidence": {"observations": len(relevant), "variants": variants},
            "apply_mode": "ADVISORY_ONLY",
            "authority": dict(AUTHORITY_NONE),
            "architecture_claim": "NONE",
        }
    best = max(eligible, key=_rank_variant)
    stable = (
        best["known_outcomes"] >= 10
        and best["distinct_tasks"] >= 5
        and (best["success_lower_bound"] or 0.0) >= 0.60
    )
    state = "STABLE" if stable else "PROVISIONAL"
    confidence = "HIGH" if stable else "MEDIUM"
    return {
        "engine": engine,
        "engine_key": key,
        "domain": domain,
        "state": state,
        "confidence": confidence,
        "reason": "OBSERVED_OUTCOME_PROFILE",
        "recommended_config": best["config"],
        "selected_variant_id": best["variant_id"],
        "evidence": {"observations": len(relevant), "selected": best, "variants": variants},
        "apply_mode": "ADVISORY_ONLY",
        "authority": dict(AUTHORITY_NONE),
        "architecture_claim": "NONE",
    }


def resolve_operating_policy(profile: dict[str, Any] | None, current_engine: dict[str, Any]) -> dict[str, Any]:
    validate_engine(current_engine)
    current_key = engine_key(current_engine)
    if not profile:
        return {
            "state": "NEW_ENGINE",
            "inheritance": "NONE",
            "config": conservative_config(),
            "reason": "NO_PROFILE",
            "apply_mode": "ADVISORY_ONLY",
            "authority": dict(AUTHORITY_NONE),
        }
    if profile.get("engine_key") != current_key:
        return {
            "state": "NEW_ENGINE",
            "inheritance": "PRIOR_ONLY",
            "config": conservative_config(),
            "reason": "ENGINE_IDENTITY_CHANGED_REPROFILE_REQUIRED",
            "apply_mode": "ADVISORY_ONLY",
            "authority": dict(AUTHORITY_NONE),
        }
    if profile.get("state") in {"DRIFT_CONFIRMED", "QUARANTINED", "UNCHARACTERIZED"}:
        return {
            "state": profile.get("state"),
            "inheritance": "BOUNDED",
            "config": conservative_config(),
            "reason": "PROFILE_NOT_SAFE_FOR_REUSE",
            "apply_mode": "ADVISORY_ONLY",
            "authority": dict(AUTHORITY_NONE),
        }
    validate_config(profile["recommended_config"])
    return {
        "state": profile["state"],
        "inheritance": "SAME_ENGINE_EVIDENCE",
        "config": profile["recommended_config"],
        "reason": "PROFILE_RECOMMENDATION",
        "apply_mode": "ADVISORY_ONLY",
        "authority": dict(AUTHORITY_NONE),
    }


def plan_probe_matrix(
    engine: dict[str, Any],
    domain: str,
    prior_profile: dict[str, Any] | None = None,
    max_probes: int = 8,
) -> dict[str, Any]:
    validate_engine(engine)
    if not domain:
        raise ProfileError("domain is required")
    if isinstance(max_probes, bool) or not isinstance(max_probes, int) or not 1 <= max_probes <= 8:
        raise ProfileError("max_probes must be an integer in [1,8]")
    key = engine_key(engine)
    inheritance = "NONE"
    baseline = conservative_config()
    if prior_profile:
        if prior_profile.get("engine_key") == key and prior_profile.get("state") in {"PROVISIONAL", "STABLE"}:
            baseline = dict(prior_profile["recommended_config"])
            validate_config(baseline)
            inheritance = "SAME_ENGINE_EVIDENCE"
        else:
            inheritance = "PRIOR_ONLY"
    probes = [{"probe_id": "baseline", "changed_dimension": None, "config": baseline}]
    variations = [
        ("context_mode", "minimal"),
        ("context_mode", "expanded"),
        ("recall_mode", "off"),
        ("recall_mode", "selective"),
        ("instruction_density", "low"),
        ("autonomy", "high"),
        ("reasoning_tier", "xhigh"),
        ("tool_strategy", "adaptive"),
    ]
    seen = {_canonical(baseline)}
    for field, value in variations:
        if len(probes) >= max_probes:
            break
        candidate = dict(baseline)
        candidate[field] = value
        fingerprint = _canonical(candidate)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        probes.append({
            "probe_id": f"probe-{len(probes):02d}",
            "changed_dimension": field,
            "config": candidate,
        })
    return {
        "engine": engine,
        "engine_key": key,
        "domain": domain,
        "inheritance": inheritance,
        "design": "ONE_DIMENSION_AT_A_TIME",
        "probe_count": len(probes),
        "probes": probes,
        "execution": "NOT_PERFORMED",
        "apply_mode": "ADVISORY_ONLY",
        "authority": dict(AUTHORITY_NONE),
    }


def detect_drift(profile: dict[str, Any], recent_observations: Iterable[dict[str, Any]], current_engine: dict[str, Any]) -> dict[str, Any]:
    validate_engine(current_engine)
    if profile.get("engine_key") != engine_key(current_engine):
        return {
            "state": "NEW_ENGINE",
            "reason": "ENGINE_IDENTITY_CHANGED",
            "action": "CONSERVATIVE_REPROFILE",
            "architecture_claim": "NONE",
            "authority": dict(AUTHORITY_NONE),
        }
    rows = validate_observations(recent_observations)
    selected_config = profile.get("recommended_config")
    validate_config(selected_config)
    domain = profile.get("domain")
    relevant = [
        row for row in rows
        if row["domain"] == domain
        and engine_key(row["engine"]) == profile["engine_key"]
        and row["config"] == selected_config
        and row["outcome"]["status"] != "UNKNOWN"
    ]
    tasks = {row["task_id"] for row in relevant}
    if len(relevant) < 3 or len(tasks) < 3:
        return {
            "state": "INSUFFICIENT_EVIDENCE",
            "reason": "NEED_MORE_DISTINCT_TASKS",
            "action": "KEEP_OBSERVING",
            "architecture_claim": "NONE",
            "authority": dict(AUTHORITY_NONE),
        }
    recent_success = sum(row["outcome"]["status"] == "SUCCESS" for row in relevant) / len(relevant)
    baseline = profile.get("evidence", {}).get("selected", {})
    baseline_success = baseline.get("success_rate")
    if baseline_success is None:
        return {
            "state": "INSUFFICIENT_EVIDENCE",
            "reason": "BASELINE_SUCCESS_UNKNOWN",
            "action": "REPROFILE",
            "architecture_claim": "NONE",
            "authority": dict(AUTHORITY_NONE),
        }
    score = 0
    success_drop = float(baseline_success) - recent_success
    if success_drop >= 0.20:
        score += 2
    elif success_drop >= 0.10:
        score += 1
    recent_human = _median_metric(relevant, "human_intervention_count")
    recent_retry = _median_metric(relevant, "retry_count")
    baseline_human = baseline.get("human_intervention_median")
    baseline_retry = baseline.get("retry_median")
    if recent_human is not None and baseline_human is not None and recent_human - baseline_human >= 1:
        score += 1
    if recent_retry is not None and baseline_retry is not None and recent_retry - baseline_retry >= 2:
        score += 1
    if score >= 2 and len(tasks) >= 5:
        state, action = "DRIFT_CONFIRMED", "CONSERVATIVE_REPROFILE"
    elif score >= 1:
        state, action = "DRIFT_SUSPECTED", "CAP_PROBES"
    else:
        state, action = "STABLE", "KEEP_PROFILE"
    return {
        "state": state,
        "reason": "OBSERVED_OUTCOME_CHANGE",
        "action": action,
        "recent": {
            "known_outcomes": len(relevant),
            "distinct_tasks": len(tasks),
            "success_rate": recent_success,
            "success_drop": success_drop,
            "human_intervention_median": recent_human,
            "retry_median": recent_retry,
        },
        "architecture_claim": "NONE",
        "authority": dict(AUTHORITY_NONE),
    }
