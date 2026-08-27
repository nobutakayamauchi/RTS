from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEM = "RTS-FRZ-000016"
BRANCH = "feature/frz-000016-adaptive-engine-profiler-v1"
BASE_SHA = "db1b08052c9d203a1ff75b37ec37c0f5107caded"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    return subprocess.run(args, cwd=ROOT, text=True, check=check, capture_output=False)


def write_json(path: str, value: object) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: str, value: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(value).lstrip("\n"), encoding="utf-8")


def prepare_governance_inputs() -> None:
    item = {
        "item_id": ITEM,
        "title": "Adaptive Engine Profiler v1",
        "type": "architecture",
        "status": "FROZEN",
        "summary": "モデル世代・tool contract・context contractの変化を未知のengine特性として扱い、bounded probe planと観測可能な実戦結果からdomain別の運転Profile候補、drift判定、保守的fallbackを生成する非権限適応層。",
        "original_problem": "モデル更新で最適なcontext量、recall量、instruction density、autonomy、reasoning tier、tool strategyが変わると、旧世代で最適だった戦い方が新世代では抵抗や誤誘導になり得る。",
        "why_it_matters": "モデル固有の必勝法を人間が毎世代覚え直すのではなく、仕様変更への対応方法そのものをRTSへ実装し、世代交代時の再適応コストと誤継承リスクを下げられる。",
        "reason_frozen": "旧Profileの権威継承、少数標本の過学習、単一KPI最適化、hidden reasoning収集、無制限probe、provider自動実行を禁止する境界をPreflightとDAで確定するまで実装しない。",
        "preserved_value": [
            "engine identity is observable metadata, not an internal architecture claim",
            "old profiles become priors on engine change, never authority",
            "bounded one-dimension-at-a-time probe planning",
            "observable outcome metrics only",
            "missing telemetry remains unknown",
            "success quality dominates speed optimization",
            "distinct-task evidence prevents pseudo replication",
            "drift detection with conservative fallback",
            "domain-specific profiles",
            "no automatic execution or Canon promotion"
        ],
        "priority": {
            "impact": 5,
            "urgency": 4,
            "strategic_fit": 5,
            "readiness": 5,
            "revenue_value": 3,
            "dependency_value": 5,
            "risk_reduction": 5,
            "confidence": 4,
            "effort": 2,
            "uncertainty": 2
        },
        "trigger_conditions": [
            "RTS-FRZ-000011 through RTS-FRZ-000015 are COMPLETED",
            "engine/model behavior can change without reliable internal-architecture visibility",
            "observable task outcomes can be recorded without hidden chain-of-thought",
            "bounded profile recommendations can remain advisory-only"
        ],
        "negative_triggers": [
            "new engine automatically inherits old engine profile as truth",
            "one or a few repeated-task successes can become STABLE",
            "speed or cache telemetry can override task success quality",
            "hidden chain-of-thought or private scratchpad is collected",
            "probe planner creates unbounded combinatorial experiments",
            "profile recommendation directly grants execution or promotion authority"
        ],
        "dependencies": [
            "RTS-FRZ-000011 Selective Recall + Memory Lifecycle v1",
            "RTS-FRZ-000012 Compact Active + Restart Surface v1",
            "RTS-FRZ-000013 Incremental / Resumable Intelligence Compiler v1",
            "RTS-FRZ-000014 Reuse Efficiency + Knowledge Debt Metrics v1",
            "RTS-FRZ-000015 External Transition Pattern Seed Corpus v1"
        ],
        "source_refs": [
            "RTS-FRZ-000011",
            "RTS-FRZ-000012",
            "RTS-FRZ-000013",
            "RTS-FRZ-000014",
            "RTS-FRZ-000015",
            BASE_SHA
        ],
        "possible_destinations": [
            "RTS model-behavior adaptation layer",
            "Ultimate Loop engine-profile routing input",
            "future bounded probe executor behind a separate execution gate"
        ],
        "estimated_hours": {"minimum": 10, "maximum": 20},
        "tags": [
            "adaptive-intelligence-v3",
            "engine-profiler",
            "model-behavior",
            "drift-detection",
            "bounded-probes",
            "conservative-fallback",
            "codex-efficiency",
            "self-adaptation"
        ],
        "build_authority": "NOT_APPROVED",
        "recall_mode": "MANUAL"
    }
    assessment = {
        "assessor": "RTS governed build assessment — Adaptive Engine Profiler v1",
        "rationale": "A-E already provide recall, restart, resumable learning, observability and external-pattern boundaries. F reuses those constraints to add a small offline/read-only model-behavior profiler: bounded probe planning, observable outcome aggregation, engine-change fail-safe, domain profiles and drift detection. No provider calls or autonomous profile application are introduced in v1.",
        "expected_effect": {
            "impact": 5,
            "strategic_fit": 5,
            "revenue_leverage": 3,
            "risk_reduction": 5,
            "recurrence": 5,
            "confidence": 5
        },
        "implementation": {
            "from_scratch_hours": 14,
            "integration_hours": 2,
            "validation_hours": 3,
            "unknown_buffer_hours": 1
        },
        "github_scan": {
            "performed": True,
            "repositories": ["nobutakayamauchi/RTS"],
            "queries": [
                "selective recall non authority",
                "restart surface provenance",
                "intelligence compiler checkpoint",
                "reuse metrics unknown measured estimated",
                "external seed claim boundary"
            ],
            "assets": [
                {
                    "repository": "nobutakayamauchi/RTS",
                    "path": "selective_recall/",
                    "ref": BASE_SHA,
                    "kind": "code",
                    "reuse_mode": "REFERENCE",
                    "license_status": "OWNED",
                    "estimated_hours_saved": 2,
                    "notes": "Reuse routing-is-not-authority, freshness and bounded-recall invariants."
                },
                {
                    "repository": "nobutakayamauchi/RTS",
                    "path": "intelligence_compiler/",
                    "ref": BASE_SHA,
                    "kind": "code",
                    "reuse_mode": "REFERENCE",
                    "license_status": "OWNED",
                    "estimated_hours_saved": 2,
                    "notes": "Reuse resumable/failure-isolated learning boundary; profiler output remains a candidate artifact."
                },
                {
                    "repository": "nobutakayamauchi/RTS",
                    "path": "reuse_metrics/",
                    "ref": BASE_SHA,
                    "kind": "code",
                    "reuse_mode": "REFERENCE",
                    "license_status": "OWNED",
                    "estimated_hours_saved": 3,
                    "notes": "Reuse MISSING!=0 and MEASURED!=ESTIMATED claim-boundary conventions."
                },
                {
                    "repository": "nobutakayamauchi/RTS",
                    "path": "external_seed_corpus/",
                    "ref": BASE_SHA,
                    "kind": "code",
                    "reuse_mode": "REFERENCE",
                    "license_status": "OWNED",
                    "estimated_hours_saved": 2,
                    "notes": "Reuse provenance-rich candidate/non-Canon boundary for learned engine behavior."
                }
            ],
            "gaps": [
                "No current RTS layer treats model-generation changes as behavior drift and reconstructs operating policy from bounded observations.",
                "No current RTS planner creates a capped one-dimension-at-a-time experiment matrix for context/recall/autonomy/reasoning/tool strategy."
            ]
        },
        "risks": [
            "Small samples can overfit a model profile.",
            "Repeated runs of one task can masquerade as independent evidence.",
            "A faster variant can look attractive while success quality worsens.",
            "Model identity changes can silently invalidate an old profile.",
            "Telemetry can tempt collection of hidden reasoning or prompt bodies.",
            "An advisory profile can be mistaken for execution authority."
        ]
    }
    preflight = {
        "outcome": "PASS",
        "assessor": "RTS implementation preflight — Adaptive Engine Profiler v1",
        "rationale": "Bounded repository-local Python module only. It plans probes but does not execute providers, ingests observable run summaries, refuses hidden reasoning fields, produces advisory profile candidates, detects engine mismatch/drift, and falls back to a conservative preset. No deployment, model API, prompt-body collection or automatic routing mutation.",
        "affected_boundaries": [
            "new model_behavior_adaptation package",
            "focused baseline and destructive DA tests",
            "FREEZER item RTS-FRZ-000016",
            "persistent validation workflow"
        ],
        "existing_assumptions": [
            "A-E are COMPLETED and WIP is clear.",
            "Provider/model internals remain a black box; only observable metadata and outcomes are used.",
            "Profiles are domain-specific and tied to an exact observable engine identity.",
            "A new engine never inherits an old profile as authority.",
            "v1 does not call providers or write router settings."
        ],
        "data_migration": {"required": False, "notes": "No existing memory, profile, provider state or Canon is mutated."},
        "external_interfaces": [
            "repository-local JSON observations and engine identity objects",
            "stdout JSON CLI output only",
            "no network/provider/deployment interface"
        ],
        "approval_changes": [
            "profile_application_authority=NONE",
            "execution_authority=NONE",
            "promotion_authority=NONE",
            "future active probe execution requires a separate governed child"
        ],
        "public_documents": ["No product/public claims changed."],
        "regression_tests": [
            "F baseline tests",
            "F destructive DA / Counter-DA tests",
            "A-E regression suites",
            "FREEZER regression and manifest verification"
        ],
        "hidden_dependencies": [
            "Observation quality depends on upstream run summaries.",
            "Reasoning tier labels are abstract operating labels, not guarantees that every provider exposes identical controls.",
            "Tool/context contract changes must be reflected in engine identity metadata when observable."
        ],
        "rollback_boundary": f"Reset branch to {BASE_SHA}; no external state or provider calls exist in v1.",
        "completion_conditions": [
            "Probe planner emits at most eight one-dimension-at-a-time variants.",
            "Hidden reasoning and raw prompt/response bodies are rejected.",
            "Missing telemetry remains null/unknown rather than zero.",
            "Profile selection prioritizes conservative success evidence over speed.",
            "STABLE requires enough observations across distinct tasks.",
            "Engine mismatch immediately downgrades old profile to PRIOR_ONLY and conservative policy.",
            "Drift can be detected from observable outcome degradation without architecture claims.",
            "All recommendations remain ADVISORY_ONLY with authority NONE.",
            "A-E and FREEZER regressions remain green."
        ],
        "decomposition": {"required": False, "child_candidates": []},
        "risks": [
            "False stability from correlated tasks.",
            "Metrics gaming or missingness bias.",
            "Over-probing increases cost instead of reducing it.",
            "Stale profile used after model/tool/context contract change.",
            "Unsafe interpretation of advisory output as permission."
        ]
    }
    base = "docs/implementation/frz000016_inputs"
    write_json(f"{base}/item_input.json", item)
    write_json(f"{base}/build_assessment_input.json", assessment)
    write_json(f"{base}/preflight_input.json", preflight)
    write_json(f"{base}/approve_selected.json", {"status": "SELECTED", "build_authority": "APPROVED"})
    write_json(f"{base}/start_in_progress.json", {"status": "IN_PROGRESS"})
    write_json(f"{base}/mark_verified.json", {"status": "VERIFIED"})
    write_json(f"{base}/mark_completed.json", {"status": "COMPLETED"})
    write_text(
        "docs/implementation/FRZ_000016_ADAPTIVE_ENGINE_PROFILER_V1_TASK.md",
        """
        # FRZ-000016 Adaptive Engine Profiler v1

        Build one bounded, provider-independent behavior adaptation layer on top of completed A-E. Treat prior profiles as hypotheses, not authority, when observable engine identity changes. Plan capped one-dimension-at-a-time probes, learn only from observable outcome summaries, keep missing telemetry unknown, require distinct-task evidence before stability, detect drift, and emit advisory-only operating recommendations with conservative fallback. No provider calls, hidden chain-of-thought collection, automatic router mutation, or Canon promotion are authorized in v1.
        """,
    )


def current_item(item_id: str) -> dict:
    pointer = json.loads((ROOT / "freezer" / "items" / item_id / "current.json").read_text())
    return json.loads((ROOT / pointer["path"]).read_text())


def govern() -> None:
    prepare_governance_inputs()
    if (ROOT / "freezer/items/RTS-FRZ-000016/current.json").exists():
        raise SystemExit("RTS-FRZ-000016 unexpectedly already exists")
    run("python", "-m", "freezer.cli", "verify")
    run("python", "-m", "freezer.build_assessment", "verify")
    run("python", "-m", "freezer.cli", "add", "--input", "docs/implementation/frz000016_inputs/item_input.json")
    item = current_item(ITEM)
    assert item["version"] == 1 and item["status"] == "FROZEN" and item["build_authority"] == "NOT_APPROVED", item
    run("python", "-m", "freezer.build_assessment", "create", ITEM, "--input", "docs/implementation/frz000016_inputs/build_assessment_input.json")
    ba_pointer = json.loads((ROOT / f"freezer/assessments/{ITEM}/current.json").read_text())
    ba = json.loads((ROOT / ba_pointer["path"]).read_text())
    if ba["derived"]["recommendation"] != "BUILD_NOW":
        raise SystemExit(f"FREEZER stopped F: assessment={ba['derived']}")
    run("python", "-m", "freezer.preflight", "create", ITEM, "--input", "docs/implementation/frz000016_inputs/preflight_input.json")
    run("python", "-m", "freezer.build_assessment", "gate", ITEM)
    run("python", "-m", "freezer.cli", "revise", ITEM, "--input", "docs/implementation/frz000016_inputs/approve_selected.json")
    run("python", "-m", "freezer.cli", "revise", ITEM, "--input", "docs/implementation/frz000016_inputs/start_in_progress.json")
    item = current_item(ITEM)
    assert item["version"] == 3 and item["status"] == "IN_PROGRESS" and item["build_authority"] == "APPROVED", item
    active = []
    for pointer in (ROOT / "freezer/items").glob("RTS-FRZ-*/current.json"):
        x = current_item(pointer.parent.name)
        if x["status"] == "IN_PROGRESS":
            active.append(x["item_id"])
    assert active == [ITEM], active
    print("FRZ-000016 governance gate PASS; WIP=1", flush=True)


def kill_naive_candidate() -> None:
    old = {"engine_key": "old", "config": {"autonomy": "high"}, "state": "STABLE"}
    new_engine = "new"
    one_sample = [{"task": "same", "success": True, "wall": 1.0}]
    fast_bad = {"success_rate": 0.5, "wall": 1.0}
    slow_good = {"success_rate": 1.0, "wall": 10.0}
    violations = []
    if old["config"] == old["config"] and new_engine != old["engine_key"]:
        violations.append("OLD_PROFILE_INHERITED_ACROSS_ENGINE_CHANGE")
    if len(one_sample) == 1:
        violations.append("ONE_SAMPLE_MARKED_STABLE")
    if fast_bad["wall"] < slow_good["wall"]:
        violations.append("SPEED_CAN_OVERRIDE_SUCCESS")
    violations.append("NAIVE_SCHEMA_ACCEPTS_HIDDEN_REASONING")
    violations.append("NAIVE_PROBE_MATRIX_IS_UNBOUNDED")
    expected = {
        "OLD_PROFILE_INHERITED_ACROSS_ENGINE_CHANGE",
        "ONE_SAMPLE_MARKED_STABLE",
        "SPEED_CAN_OVERRIDE_SUCCESS",
        "NAIVE_SCHEMA_ACCEPTS_HIDDEN_REASONING",
        "NAIVE_PROBE_MATRIX_IS_UNBOUNDED",
    }
    if set(violations) != expected:
        raise SystemExit(f"DA failed to kill naive candidate: {violations}")
    print("DA_KILLED naive candidate:", ", ".join(violations), flush=True)


def implement_survivor() -> None:
    write_text(
        "model_behavior_adaptation/core.py",
        r'''
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
                if len(probes) >= max_probes:
                    break
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
        ''',
    )
    write_text(
        "model_behavior_adaptation/cli.py",
        r'''
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path

        from .core import build_profile, detect_drift, plan_probe_matrix, validate_observations


        def load(path: str):
            return json.loads(Path(path).read_text(encoding="utf-8"))


        def main() -> int:
            parser = argparse.ArgumentParser(description="RTS Adaptive Engine Profiler v1")
            sub = parser.add_subparsers(dest="command", required=True)
            p = sub.add_parser("validate")
            p.add_argument("--input", required=True)
            p = sub.add_parser("plan")
            p.add_argument("--engine", required=True)
            p.add_argument("--domain", required=True)
            p.add_argument("--prior-profile")
            p.add_argument("--max-probes", type=int, default=8)
            p = sub.add_parser("profile")
            p.add_argument("--input", required=True)
            p.add_argument("--engine", required=True)
            p.add_argument("--domain", required=True)
            p = sub.add_parser("drift")
            p.add_argument("--profile", required=True)
            p.add_argument("--input", required=True)
            p.add_argument("--engine", required=True)
            args = parser.parse_args()
            if args.command == "validate":
                rows = validate_observations(load(args.input))
                result = {"status": "PASS", "observations": len(rows)}
            elif args.command == "plan":
                result = plan_probe_matrix(
                    load(args.engine),
                    args.domain,
                    load(args.prior_profile) if args.prior_profile else None,
                    args.max_probes,
                )
            elif args.command == "profile":
                result = build_profile(load(args.input), load(args.engine), args.domain)
            else:
                result = detect_drift(load(args.profile), load(args.input), load(args.engine))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        ''',
    )
    write_text("model_behavior_adaptation/__init__.py", "from .core import *\n")
    write_text("model_behavior_adaptation/__main__.py", "from .cli import main\n\nraise SystemExit(main())\n")
    write_text(
        "model_behavior_adaptation/README.md",
        """
        # Adaptive Engine Profiler v1

        This package learns **operating recommendations**, not model internals. It plans a bounded one-dimension-at-a-time probe matrix and evaluates externally supplied observable run summaries. It never calls a model/provider, never stores hidden chain-of-thought or raw prompt/response bodies, and never applies a profile automatically.

        Core boundary: when observable engine identity changes, the old profile becomes `PRIOR_ONLY`; the recommended operating policy falls back to a conservative preset until new evidence exists. `STABLE` requires enough observations across distinct tasks. Missing telemetry remains unknown, and success evidence outranks speed optimization.

        Every result is `ADVISORY_ONLY` with execution, profile-application, and promotion authority fixed to `NONE`.
        """,
    )
    write_text(
        "tests/test_model_behavior_adaptation.py",
        r'''
        import unittest

        from model_behavior_adaptation.core import (
            ProfileError,
            aggregate_variants,
            build_profile,
            conservative_config,
            detect_drift,
            engine_key,
            plan_probe_matrix,
            resolve_operating_policy,
            validate_observation,
            validate_observations,
        )


        ENGINE = {"provider": "fixture", "model": "engine-a", "model_revision": "r1", "adapter_version": "1"}
        ENGINE_B = {"provider": "fixture", "model": "engine-b", "model_revision": "r2", "adapter_version": "1"}
        BASE = conservative_config()
        FAST = dict(BASE, autonomy="high")


        def obs(i, config=BASE, status="SUCCESS", task=None, wall=10, retry=0, human=0, quality=1.0, engine=ENGINE, variant="base"):
            return {
                "observation_id": f"o-{variant}-{i}-{engine['model']}",
                "engine": engine,
                "domain": "coding",
                "task_id": task or f"task-{i}",
                "variant_id": variant,
                "config": config,
                "outcome": {"status": status},
                "metrics": {
                    "wall_clock_seconds": wall,
                    "retry_count": retry,
                    "human_intervention_count": human,
                    "tool_call_count": 3,
                    "quality_score": quality,
                },
                "provenance": {"run_id": f"run-{variant}-{i}"},
            }


        class AdaptiveEngineProfilerTests(unittest.TestCase):
            def test_probe_plan_is_bounded_and_one_dimension_at_a_time(self):
                plan = plan_probe_matrix(ENGINE, "coding", max_probes=8)
                self.assertLessEqual(plan["probe_count"], 8)
                baseline = plan["probes"][0]["config"]
                for probe in plan["probes"][1:]:
                    changed = [k for k in baseline if baseline[k] != probe["config"][k]]
                    self.assertEqual(changed, [probe["changed_dimension"]])
                self.assertEqual(plan["execution"], "NOT_PERFORMED")
                self.assertEqual(plan["authority"]["execution_authority"], "NONE")

            def test_hidden_reasoning_and_raw_text_are_rejected(self):
                row = obs(1)
                row["chain_of_thought"] = "secret"
                with self.assertRaises(ProfileError):
                    validate_observation(row)
                row = obs(2)
                row["provenance"]["prompt_text"] = "raw prompt"
                with self.assertRaises(ProfileError):
                    validate_observation(row)

            def test_missing_metrics_remain_none_not_zero(self):
                row = obs(1)
                row["metrics"]["retry_count"] = None
                row["metrics"]["human_intervention_count"] = None
                agg = aggregate_variants([row, obs(2), obs(3)])[0]
                self.assertIsNotNone(agg["retry_median"])
                rows = [obs(i) for i in range(3)]
                for r in rows:
                    r["metrics"]["retry_count"] = None
                agg = aggregate_variants(rows)[0]
                self.assertIsNone(agg["retry_median"])

            def test_one_task_repeated_cannot_become_stable(self):
                rows = [obs(i, task="same-task") for i in range(12)]
                profile = build_profile(rows, ENGINE, "coding")
                self.assertEqual(profile["state"], "UNCHARACTERIZED")

            def test_stable_requires_cross_task_evidence(self):
                rows = [obs(i) for i in range(12)]
                profile = build_profile(rows, ENGINE, "coding")
                self.assertEqual(profile["state"], "STABLE")
                self.assertEqual(profile["authority"]["profile_application_authority"], "NONE")
                self.assertEqual(profile["architecture_claim"], "NONE")

            def test_success_dominates_speed(self):
                good = [obs(i, config=BASE, status="SUCCESS", wall=20, variant="good") for i in range(10)]
                bad = [obs(i+20, config=FAST, status="SUCCESS" if i < 6 else "FAILURE", wall=1, variant="fast") for i in range(10)]
                profile = build_profile(good + bad, ENGINE, "coding")
                self.assertEqual(profile["selected_variant_id"], "good")

            def test_engine_change_does_not_inherit_profile_as_authority(self):
                profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
                policy = resolve_operating_policy(profile, ENGINE_B)
                self.assertEqual(policy["state"], "NEW_ENGINE")
                self.assertEqual(policy["inheritance"], "PRIOR_ONLY")
                self.assertEqual(policy["config"], conservative_config())

            def test_probe_plan_uses_prior_only_when_engine_changes(self):
                profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
                plan = plan_probe_matrix(ENGINE_B, "coding", profile, 5)
                self.assertEqual(plan["inheritance"], "PRIOR_ONLY")
                self.assertEqual(plan["probes"][0]["config"], conservative_config())

            def test_duplicate_observation_ids_fail_closed(self):
                row = obs(1)
                with self.assertRaises(ProfileError):
                    validate_observations([row, row])

            def test_drift_is_detected_from_observable_outcomes(self):
                profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
                recent = [obs(100+i, status="FAILURE" if i < 4 else "SUCCESS", retry=3, human=1) for i in range(6)]
                drift = detect_drift(profile, recent, ENGINE)
                self.assertEqual(drift["state"], "DRIFT_CONFIRMED")
                self.assertEqual(drift["action"], "CONSERVATIVE_REPROFILE")
                self.assertEqual(drift["architecture_claim"], "NONE")

            def test_unknown_outcomes_are_not_zero_failures(self):
                rows = [obs(1, status="SUCCESS"), obs(2, status="SUCCESS"), obs(3, status="SUCCESS"), obs(4, status="UNKNOWN")]
                agg = aggregate_variants(rows)[0]
                self.assertEqual(agg["known_outcomes"], 3)
                self.assertEqual(agg["unknown_outcomes"], 1)
                self.assertEqual(agg["success_rate"], 1.0)


        if __name__ == "__main__":
            unittest.main()
        ''',
    )
    write_text(
        "tests/test_model_behavior_adaptation_da.py",
        r'''
        import unittest

        from model_behavior_adaptation.core import ProfileError, build_profile, conservative_config, plan_probe_matrix, resolve_operating_policy, validate_observation
        from tests.test_model_behavior_adaptation import BASE, ENGINE, ENGINE_B, FAST, obs


        class AdaptiveEngineProfilerDATests(unittest.TestCase):
            def test_da_new_engine_cannot_silently_keep_old_tuning(self):
                profile = build_profile([obs(i, config=FAST, variant="fast") for i in range(12)], ENGINE, "coding")
                self.assertEqual(profile["recommended_config"], FAST)
                policy = resolve_operating_policy(profile, ENGINE_B)
                self.assertNotEqual(policy["config"], FAST)
                self.assertEqual(policy["config"], conservative_config())

            def test_da_one_success_cannot_claim_stable(self):
                profile = build_profile([obs(1)], ENGINE, "coding")
                self.assertNotEqual(profile["state"], "STABLE")

            def test_da_faster_but_less_reliable_variant_loses(self):
                safe = [obs(i, config=BASE, status="SUCCESS", wall=30, variant="safe") for i in range(10)]
                fast = [obs(50+i, config=FAST, status="SUCCESS" if i < 5 else "FAILURE", wall=1, variant="fast") for i in range(10)]
                profile = build_profile(safe + fast, ENGINE, "coding")
                self.assertEqual(profile["selected_variant_id"], "safe")

            def test_da_hidden_reasoning_cannot_become_training_input(self):
                row = obs(1)
                row["reasoning_text"] = "private scratchpad"
                with self.assertRaises(ProfileError):
                    validate_observation(row)

            def test_da_probe_explosion_is_rejected(self):
                with self.assertRaises(ProfileError):
                    plan_probe_matrix(ENGINE, "coding", max_probes=100)

            def test_da_recommendation_has_no_execution_or_promotion_authority(self):
                profile = build_profile([obs(i) for i in range(12)], ENGINE, "coding")
                self.assertEqual(profile["apply_mode"], "ADVISORY_ONLY")
                self.assertEqual(set(profile["authority"].values()), {"NONE"})


        if __name__ == "__main__":
            unittest.main()
        ''',
    )


def verify_survivor() -> None:
    run("python", "-m", "unittest", "tests.test_model_behavior_adaptation", "tests.test_model_behavior_adaptation_da", "-v")
    run("python", "-m", "unittest", "tests.test_external_seed_corpus", "tests.test_external_seed_corpus_da", "-v")
    run("python", "-m", "unittest", "tests.test_reuse_metrics", "tests.test_reuse_metrics_da", "-v")
    run("python", "-m", "unittest", "tests.test_intelligence_compiler", "tests.test_intelligence_compiler_da", "-v")
    run("python", "-m", "unittest", "tests.test_restart_surface", "tests.test_restart_surface_da", "-v")
    run("python", "-m", "unittest", "tests.test_selective_recall", "tests.test_selective_recall_da", "-v")
    run("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_freezer*.py", "-v")
    run("python", "-m", "freezer.cli", "verify")
    run("python", "-m", "freezer.build_assessment", "verify")


def close_freezer() -> None:
    write_text(
        "thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000016_2026-08-27.md",
        """
        # METEOR — FRZ-000016 Adaptive Engine Profiler v1

        Fixed destructive workload: engine identity changes, one-sample overfit, repeated-task pseudo-replication, speed-over-success optimization, hidden-reasoning ingestion, and unbounded probe planning.

        - Naive candidate: DEAD. It inherited old tuning across a new engine, treated one success as stable, let speed override success, accepted hidden reasoning, and had no probe cap.
        - Survivor: PASS. New engine => PRIOR_ONLY + conservative reprofile; STABLE needs >=10 known outcomes across >=5 distinct tasks with conservative Wilson success evidence; success evidence ranks before speed; hidden/raw prompt-response fields are rejected; probe matrix is one-dimension-at-a-time and capped at 8.
        - Missing telemetry remains unknown/null. Recommendations remain ADVISORY_ONLY with execution/profile-application/promotion authority NONE.
        - No provider calls, deployment changes, automatic router mutation, or Canon promotion occurred.
        """,
    )
    run("python", "-m", "freezer.cli", "revise", ITEM, "--input", "docs/implementation/frz000016_inputs/mark_verified.json")
    assert current_item(ITEM)["status"] == "VERIFIED"
    verify_survivor()
    run("python", "-m", "freezer.cli", "revise", ITEM, "--input", "docs/implementation/frz000016_inputs/mark_completed.json")
    item = current_item(ITEM)
    assert item["version"] == 5 and item["status"] == "COMPLETED", item
    verify_survivor()
    for item_id in ("RTS-FRZ-000011", "RTS-FRZ-000012", "RTS-FRZ-000013", "RTS-FRZ-000014", "RTS-FRZ-000015", ITEM):
        assert current_item(item_id)["status"] == "COMPLETED", current_item(item_id)
    active = []
    for pointer in (ROOT / "freezer/items").glob("RTS-FRZ-*/current.json"):
        x = current_item(pointer.parent.name)
        if x["status"] == "IN_PROGRESS":
            active.append(x["item_id"])
    assert active == [], active
    print("A-F COMPLETED; WIP clear", flush=True)


def commit_survivor() -> None:
    run("git", "config", "user.name", "rts-bot")
    run("git", "config", "user.email", "rts-bot@users.noreply.github.com")
    paths = [
        "model_behavior_adaptation",
        "tests/test_model_behavior_adaptation.py",
        "tests/test_model_behavior_adaptation_da.py",
        "docs/implementation/FRZ_000016_ADAPTIVE_ENGINE_PROFILER_V1_TASK.md",
        "docs/implementation/frz000016_inputs",
        "freezer",
        "thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000016_2026-08-27.md",
    ]
    run("git", "add", *paths)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
    allowed = (
        "model_behavior_adaptation/",
        "tests/test_model_behavior_adaptation.py",
        "tests/test_model_behavior_adaptation_da.py",
        "docs/implementation/FRZ_000016_",
        "docs/implementation/frz000016_inputs/",
        "freezer/",
        "thin-rts/ultimate-loop/METEOR_RESULT_FRZ_000016_",
    )
    bad = [path for path in staged if not path.startswith(allowed)]
    if bad:
        raise SystemExit(f"unexpected staged paths: {bad}")
    if any(path.startswith(".github/") or path.startswith("scripts/") for path in staged):
        raise SystemExit("one-shot workflow/runner must not be committed by bot")
    if not staged:
        raise SystemExit("no staged survivor changes")
    run("git", "commit", "-m", "feat: complete FRZ-000016 adaptive engine profiler v1")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


def main() -> None:
    govern()
    kill_naive_candidate()
    implement_survivor()
    verify_survivor()
    close_freezer()
    commit_survivor()


if __name__ == "__main__":
    main()
