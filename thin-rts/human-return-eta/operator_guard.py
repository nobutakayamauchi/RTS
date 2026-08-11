#!/usr/bin/env python3
"""Unified shadow-mode operator guard.

Active behavior:
- Human Return ETA remains driven by the existing evidence-weighted ETA model.
- Decision Sentinel emits advisory review pressure only.
- New amplification/launch features are logged for later validation but do not alter ETA yet.

This intentionally avoids promoting an under-validated formula into control authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import eta
from decision_sentinel import DecisionState, review_pressure
from operator_machine_model import launch_safe_orchestration


class OperatorGuardError(RuntimeError):
    pass


def advise(
    observations,
    *,
    task_class: str,
    decision_state: DecisionState,
    known_governed_stages: float = 0.0,
    target_chunks: float | None = None,
    prior_minutes_per_chunk: float | None = None,
) -> dict[str, object]:
    eta_result = eta.estimate(
        observations,
        task_class,
        target_chunks=target_chunks,
        prior_minutes_per_chunk=prior_minutes_per_chunk,
    )
    sentinel = review_pressure(decision_state)
    launch_stage_feature = launch_safe_orchestration(known_governed_stages)

    return {
        "goal": "OPERATOR_GUARD_SHADOW_V0_1",
        "mode": "SHADOW",
        "active_eta": eta_result,
        "decision_sentinel": sentinel,
        "shadow_features": {
            "known_governed_stages_at_launch": launch_stage_feature,
            "decision_severity": decision_state.severity,
            "evidence_quality": decision_state.evidence_quality,
            "axis_coverage": decision_state.axis_coverage,
            "recent_revision_load": decision_state.recent_revision_load,
            "recent_context_switch_load": decision_state.recent_context_switch_load,
            "unresolved_counterevidence": decision_state.unresolved_counterevidence,
            "irreversible": decision_state.irreversible,
        },
        "authority": {
            "eta_adjusted_by_shadow_features": False,
            "sentinel_can_auto_approve": False,
            "sentinel_can_auto_execute_irreversible_action": False,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Shadow-mode Human Return ETA + Decision Sentinel")
    p.add_argument("--history", required=True)
    p.add_argument("--task-class", required=True)
    p.add_argument("--severity", type=int, required=True, choices=(1, 2, 3))
    p.add_argument("--evidence-quality", type=float, required=True)
    p.add_argument("--axis-coverage", type=float, required=True)
    p.add_argument("--recent-revision-load", type=float, default=0.0)
    p.add_argument("--recent-context-switch-load", type=float, default=0.0)
    p.add_argument("--known-governed-stages", type=float, default=0.0)
    p.add_argument("--unresolved-counterevidence", action="store_true")
    p.add_argument("--irreversible", action="store_true")
    p.add_argument("--target-chunks", type=float)
    p.add_argument("--prior-minutes-per-chunk", type=float)
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        observations = eta.load_jsonl(Path(args.history))
        result = advise(
            observations,
            task_class=args.task_class,
            decision_state=DecisionState(
                severity=args.severity,
                evidence_quality=args.evidence_quality,
                axis_coverage=args.axis_coverage,
                recent_revision_load=args.recent_revision_load,
                recent_context_switch_load=args.recent_context_switch_load,
                unresolved_counterevidence=args.unresolved_counterevidence,
                irreversible=args.irreversible,
            ),
            known_governed_stages=args.known_governed_stages,
            target_chunks=args.target_chunks,
            prior_minutes_per_chunk=args.prior_minutes_per_chunk,
        )
    except Exception as exc:
        print(json.dumps({"goal": "ERROR", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
