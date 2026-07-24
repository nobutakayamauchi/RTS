from __future__ import annotations

from pathlib import Path
from typing import Any

from .adapters import get_adapter, validate_script_response
from .budgets import _append, _budget_excess, _project_usage
from .models import (
    AUTHORITY,
    TERMINAL_STATES,
    ControllerError,
    load_json,
    validate_authorization,
    validate_usage,
    zero_usage,
)
from .planning import plan_execution
from .store import checkpoint_path, verify_checkpoint


def _execution_record(plan: dict[str, Any], state: str, timestamp: str) -> dict[str, Any]:
    identifiers = plan["execution_identifiers"]
    return {
        "skill_id": identifiers["skill_id"],
        "drive_id": identifiers["drive_id"],
        "pack_id": identifiers["pack_id"],
        "trigger": identifiers["trigger"],
        "result": {
            "controller_state": state,
            "verification": "SIMULATED_ONLY",
            "plan_id": plan["plan_id"],
        },
        "timestamp": timestamp,
    }


def _result_payload(plan: dict[str, Any], checkpoint: dict[str, Any], timestamp: str) -> dict[str, Any]:
    payload = {
        "schema_version": "RTS-CONTROLLER-RESULT-V1",
        "authority": AUTHORITY,
        "external_execution_performed": False,
        "plan_id": plan["plan_id"],
        "run_id": plan["plan_id"],
        "state": checkpoint["state"],
        "attempt": checkpoint["attempt"],
        "usage": checkpoint["usage"],
        "checkpoint": checkpoint,
    }
    if checkpoint["state"] in TERMINAL_STATES:
        payload["execution_record"] = _execution_record(plan, checkpoint["state"], timestamp)
    else:
        payload["execution_record"] = None
    return payload


def _load_script(path: Path) -> dict[str, Any]:
    raw = load_json(path.resolve())
    if isinstance(raw, dict) and "responses" in raw:
        responses = raw["responses"]
        if not isinstance(responses, list) or not responses:
            raise ControllerError("script.responses must be a non-empty array")
        raw = responses[0]
    return validate_script_response(raw)


def _execute_attempt(
    plan: dict[str, Any],
    authorization: dict[str, Any],
    state_dir: Path,
    script: dict[str, Any],
    current_checkpoint: dict[str, Any],
) -> dict[str, Any]:
    adapter = get_adapter(plan["adapter_id"])
    response = adapter.execute(script)
    current_usage = validate_usage(current_checkpoint["usage"])
    attempt = current_checkpoint["attempt"] + 1
    projected = _project_usage(current_usage, attempt=True, delta=response["usage"], event=True)
    excess = _budget_excess(projected, plan["budgets"])
    timestamp = response["timestamp"]
    if excess:
        escalated_usage = _project_usage(current_usage, event=True)
        if _budget_excess(escalated_usage, plan["budgets"]):
            raise ControllerError("budget exhausted before escalation event could be recorded")
        _append(
            state_dir,
            plan,
            authorization,
            event_type="BUDGET_ESCALATION",
            before=current_checkpoint["state"],
            after="ESCALATED",
            attempt=current_checkpoint["attempt"],
            usage=escalated_usage,
            timestamp=timestamp,
            summary=f"Projected adapter usage exceeded: {', '.join(excess)}",
        )
        _, checkpoint = verify_checkpoint(state_dir, plan["plan_id"])
        return _result_payload(plan, checkpoint, timestamp)

    if response["kind"] == "success":
        verify_usage = dict(projected)
        success_usage = _project_usage(verify_usage, event=True)
        terminal_excess = _budget_excess(success_usage, plan["budgets"])
        if terminal_excess:
            _append(
                state_dir,
                plan,
                authorization,
                event_type="BUDGET_ESCALATION",
                before="RUNNING",
                after="ESCALATED",
                attempt=attempt,
                usage=verify_usage,
                timestamp=timestamp,
                summary=(
                    "Projected successful verification exceeded: "
                    + ", ".join(terminal_excess)
                ),
            )
        else:
            _append(
                state_dir,
                plan,
                authorization,
                event_type="ADAPTER_SUCCESS",
                before="RUNNING",
                after="VERIFYING",
                attempt=attempt,
                usage=verify_usage,
                timestamp=timestamp,
                summary=response["summary"],
            )
            _append(
                state_dir,
                plan,
                authorization,
                event_type="DRY_RUN_VERIFIED",
                before="VERIFYING",
                after="SUCCEEDED",
                attempt=attempt,
                usage=success_usage,
                timestamp=timestamp,
                summary="Dry-run result verified as simulated-only output",
            )
    elif response["kind"] == "stop":
        _append(
            state_dir,
            plan,
            authorization,
            event_type="ADAPTER_STOP",
            before="RUNNING",
            after="STOPPED",
            attempt=attempt,
            usage=projected,
            timestamp=timestamp,
            summary=response["summary"],
        )
    elif response["retryable"]:
        remaining = (
            attempt < plan["budgets"]["max_attempts"]
            and projected["events"] < plan["budgets"]["max_events"]
        )
        after = "RUNNING" if remaining else "ESCALATED"
        event_type = "RETRYABLE_FAILURE" if remaining else "ATTEMPT_BUDGET_ESCALATION"
        _append(
            state_dir,
            plan,
            authorization,
            event_type=event_type,
            before="RUNNING",
            after=after,
            attempt=attempt,
            usage=projected,
            timestamp=timestamp,
            summary=response["summary"],
        )
    else:
        _append(
            state_dir,
            plan,
            authorization,
            event_type="NON_RETRYABLE_FAILURE",
            before="RUNNING",
            after="FAILED",
            attempt=attempt,
            usage=projected,
            timestamp=timestamp,
            summary=response["summary"],
        )
    _, checkpoint = verify_checkpoint(state_dir, plan["plan_id"])
    return _result_payload(plan, checkpoint, timestamp)


def run_execution(root: Path, authorization_path: Path, state_dir: Path, script_path: Path) -> dict[str, Any]:
    plan = plan_execution(root, authorization_path)
    authorization = validate_authorization(load_json(authorization_path.resolve()))
    script = _load_script(script_path)
    run_checkpoint = checkpoint_path(state_dir, plan["plan_id"])
    if run_checkpoint.exists():
        raise ControllerError("run already exists; use resume or inspect")
    usage = zero_usage()
    timestamp = authorization["as_of"]
    for event_type, before, after, summary in (
        ("AUTHORIZATION_ACCEPTED", "PLANNED", "AUTHORIZED", "Explicit authorization fingerprint accepted"),
        ("ADAPTER_DISPATCHED", "AUTHORIZED", "DISPATCHED", "Deterministic dry-run adapter selected"),
        ("RUN_STARTED", "DISPATCHED", "RUNNING", "Local bounded dry-run started"),
    ):
        usage = _project_usage(usage, event=True)
        _append(
            state_dir,
            plan,
            authorization,
            event_type=event_type,
            before=before,
            after=after,
            attempt=0,
            usage=usage,
            timestamp=timestamp,
            summary=summary,
        )
    _, checkpoint = verify_checkpoint(state_dir, plan["plan_id"])
    return _execute_attempt(plan, authorization, state_dir, script, checkpoint)


def resume_execution(root: Path, authorization_path: Path, state_dir: Path, script_path: Path) -> dict[str, Any]:
    plan = plan_execution(root, authorization_path)
    authorization = validate_authorization(load_json(authorization_path.resolve()))
    _, checkpoint = verify_checkpoint(state_dir, plan["plan_id"])
    if checkpoint["plan_id"] != plan["plan_id"] or checkpoint["plan_fingerprint"] != plan["plan_id"]:
        raise ControllerError("resume plan fingerprint mismatch")
    if checkpoint["authorization_fingerprint"] != authorization["authorization_fingerprint"]:
        raise ControllerError("resume authorization fingerprint mismatch")
    if checkpoint["state"] in TERMINAL_STATES:
        raise ControllerError("terminal run cannot be resumed")
    if checkpoint["state"] != "RUNNING":
        raise ControllerError(f"resume supports RUNNING checkpoints only, got {checkpoint['state']}")
    return _execute_attempt(plan, authorization, state_dir, _load_script(script_path), checkpoint)


def _runtime_plan_from_checkpoint(
    authorization: dict[str, Any], checkpoint: dict[str, Any]
) -> dict[str, Any]:
    plan_id = checkpoint["plan_id"]
    if checkpoint["run_id"] != plan_id or checkpoint["plan_fingerprint"] != plan_id:
        raise ControllerError("checkpoint plan identity mismatch")
    return {
        "plan_id": plan_id,
        "budgets": dict(authorization["budgets"]),
        "execution_identifiers": {
            "skill_id": authorization["skill_id"],
            "drive_id": authorization["drive_id"],
            "pack_id": authorization["pack_id"],
            "trigger": authorization["trigger"],
        },
    }


def _find_authorized_run(
    state_dir: Path, authorization: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]] | None:
    if not state_dir.exists():
        return None
    if not state_dir.is_dir():
        raise ControllerError("state_dir must be a directory")
    matching: list[tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]] = []
    active_other: list[str] = []
    for child in sorted(state_dir.iterdir(), key=lambda path: path.name):
        if not child.is_dir() or not (child / "checkpoint.json").exists():
            continue
        events, checkpoint = verify_checkpoint(state_dir, child.name)
        if checkpoint["run_id"] != checkpoint["plan_id"]:
            raise ControllerError(f"{child.name}: checkpoint run/plan identity mismatch")
        if checkpoint["authorization_fingerprint"] == authorization["authorization_fingerprint"]:
            matching.append(
                (_runtime_plan_from_checkpoint(authorization, checkpoint), events, checkpoint)
            )
        elif checkpoint["state"] not in TERMINAL_STATES:
            active_other.append(child.name)
    if len(matching) > 1:
        raise ControllerError("multiple runs match the supplied authorization")
    if matching:
        return matching[0]
    if active_other:
        raise ControllerError(
            "another non-terminal run exists under state_dir; refusing ambiguous operation"
        )
    return None


def stop_execution(root: Path, authorization_path: Path, state_dir: Path, timestamp: str) -> dict[str, Any]:
    authorization = validate_authorization(load_json(authorization_path.resolve()))
    existing = _find_authorized_run(state_dir.resolve(), authorization)
    if existing is None:
        plan = plan_execution(root, authorization_path)
        usage = _project_usage(zero_usage(), event=True)
        _append(
            state_dir,
            plan,
            authorization,
            event_type="HUMAN_EMERGENCY_STOP",
            before="PLANNED",
            after="STOPPED",
            attempt=0,
            usage=usage,
            timestamp=timestamp,
            summary="Explicit human emergency stop before dispatch",
        )
        _, current = verify_checkpoint(state_dir, plan["plan_id"])
        return _result_payload(plan, current, timestamp)

    plan, _, checkpoint = existing
    if checkpoint["state"] in TERMINAL_STATES:
        raise ControllerError("terminal run cannot be stopped again")
    usage = _project_usage(checkpoint["usage"], event=True)
    if _budget_excess(usage, plan["budgets"]):
        raise ControllerError("event budget exhausted before emergency stop could be recorded")
    _append(
        state_dir,
        plan,
        authorization,
        event_type="HUMAN_EMERGENCY_STOP",
        before=checkpoint["state"],
        after="STOPPED",
        attempt=checkpoint["attempt"],
        usage=usage,
        timestamp=timestamp,
        summary="Explicit human emergency stop",
    )
    _, current = verify_checkpoint(state_dir, plan["plan_id"])
    return _result_payload(plan, current, timestamp)


def inspect_run(root: Path, authorization_path: Path, state_dir: Path) -> dict[str, Any]:
    authorization = validate_authorization(load_json(authorization_path.resolve()))
    existing = _find_authorized_run(state_dir.resolve(), authorization)
    if existing is None:
        raise ControllerError("no run matches the supplied authorization")
    plan, events, checkpoint = existing
    return {
        "schema_version": "RTS-CONTROLLER-INSPECTION-V1",
        "authority": AUTHORITY,
        "external_execution_performed": False,
        "plan": plan,
        "checkpoint": checkpoint,
        "events": events,
    }
