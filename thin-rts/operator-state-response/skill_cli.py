#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from private_log import append_private_record
from response_skill import ResponseContext, evaluate_response
from state_model import BehaviorMetrics, OperatorStateInput
from vitals_model import Vitals


class SkillCLIError(RuntimeError):
    pass


def _load_json(path: str | None) -> dict:
    try:
        if path:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        return json.load(sys.stdin)
    except (OSError, json.JSONDecodeError) as exc:
        raise SkillCLIError(str(exc)) from exc


def _tuple_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise SkillCLIError("list field must be an array")
    return tuple(str(item).strip() for item in value if str(item).strip())


def build_state(payload: dict) -> tuple[OperatorStateInput, ResponseContext]:
    state_raw = payload.get("state", {})
    ctx_raw = payload.get("context", {})
    if not isinstance(state_raw, dict) or not isinstance(ctx_raw, dict):
        raise SkillCLIError("state and context must be objects")

    behavior_raw = state_raw.get("behavior")
    behavior = BehaviorMetrics(**behavior_raw) if isinstance(behavior_raw, dict) else None
    vitals_raw = ctx_raw.get("vitals")
    vitals = Vitals(**vitals_raw) if isinstance(vitals_raw, dict) else None
    bad_status = _tuple_strings(state_raw.get("bad_status"))

    state = OperatorStateInput(
        sleep_hours_24h=state_raw.get("sleep_hours_24h"),
        subjective_fatigue_0_10=state_raw.get("subjective_fatigue_0_10"),
        subjective_recovery_0_10=state_raw.get("subjective_recovery_0_10"),
        bad_status=bad_status,
        bad_status_assessed=bool(state_raw.get("bad_status_assessed", bool(bad_status))),
        recovery_events=_tuple_strings(state_raw.get("recovery_events")),
        behavior=behavior,
        behavior_baseline=state_raw.get("behavior_baseline", {}),
        workload_pressure_0_1=state_raw.get("workload_pressure_0_1"),
    )
    ctx = ResponseContext(
        eta_return_minutes=ctx_raw.get("eta_return_minutes"),
        eta_late_after_minutes=ctx_raw.get("eta_late_after_minutes"),
        rework_minutes=ctx_raw.get("rework_minutes"),
        decision_review_level=ctx_raw.get("decision_review_level"),
        heat_exposure=bool(ctx_raw.get("heat_exposure", False)),
        cannot_drink=bool(ctx_raw.get("cannot_drink", False)),
        vitals=vitals,
        vitals_baseline=ctx_raw.get("vitals_baseline", {}),
    )
    return state, ctx


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact operator state / return-clock response skill")
    parser.add_argument("--input", help="JSON input file; stdin when omitted")
    parser.add_argument("--log", action="store_true", help="append privacy-minimized record to private JSONL")
    parser.add_argument("--log-path", help="optional private JSONL destination outside repository")
    args = parser.parse_args()
    try:
        payload = _load_json(args.input)
        state, ctx = build_state(payload)
        result = evaluate_response(state, ctx)
        if args.log:
            append_private_record(result.log_record, Path(args.log_path) if args.log_path else None)
    except Exception as exc:
        print(json.dumps({"goal": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
