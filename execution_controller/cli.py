from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from freezer.assessment_core import item_fingerprint as assessment_item_fingerprint
from freezer.preflight import item_fingerprint as preflight_item_fingerprint

from .controller import (
    ControllerError,
    inspect_run,
    plan_execution,
    resume_execution,
    run_execution,
    stop_execution,
)
from .models import (
    authorization_material,
    pretty_json,
    sha256_value,
    validate_plan,
)
from .store import verify_checkpoint

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = PACKAGE_DIR.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTS Governed Execution Controller v1")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--authorization", type=Path, required=True)

    run = sub.add_parser("run")
    run.add_argument("--authorization", type=Path, required=True)
    run.add_argument("--state-dir", type=Path, required=True)
    run.add_argument("--script", type=Path, required=True)

    resume = sub.add_parser("resume")
    resume.add_argument("--authorization", type=Path, required=True)
    resume.add_argument("--state-dir", type=Path, required=True)
    resume.add_argument("--script", type=Path, required=True)

    stop = sub.add_parser("stop")
    stop.add_argument("--authorization", type=Path, required=True)
    stop.add_argument("--state-dir", type=Path, required=True)
    stop.add_argument("--timestamp", required=True)

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--authorization", type=Path, required=True)
    inspect.add_argument("--state-dir", type=Path, required=True)

    sub.add_parser("verify")
    return parser


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _verification_fixture(root: Path) -> tuple[Path, Path]:
    item_id = "RTS-FRZ-999999"
    item = {
        "item_id": item_id,
        "title": "Controller Verification Fixture",
        "type": "test",
        "status": "SELECTED",
        "summary": "Synthetic local verification item.",
        "original_problem": "Verify the bounded controller without external actions.",
        "why_it_matters": "The package must prove its gates and deterministic state.",
        "reason_frozen": "fixture",
        "preserved_value": ["deterministic local verification"],
        "priority": {
            "impact": 1, "urgency": 1, "strategic_fit": 1, "readiness": 1,
            "revenue_value": 1, "dependency_value": 1, "risk_reduction": 1,
            "confidence": 1, "effort": 1, "uncertainty": 1,
        },
        "trigger_conditions": ["explicit test"],
        "negative_triggers": ["external action"],
        "dependencies": [],
        "source_refs": ["execution_controller"],
        "possible_destinations": ["local fixture"],
        "estimated_hours": {"minimum": 1, "maximum": 1},
        "tags": ["fixture"],
        "build_authority": "APPROVED",
        "recall_mode": "MANUAL",
        "version": 1,
        "created_at": "2026-07-24T00:00:00Z",
        "updated_at": "2026-07-24T00:00:00Z",
        "supersedes": None,
    }
    item_path = f"freezer/items/{item_id}/v001.json"
    _write_json(root / item_path, item)
    _write_json(
        root / f"freezer/items/{item_id}/current.json",
        {
            "item_id": item_id,
            "current_version": 1,
            "path": item_path,
            "updated_at": "2026-07-24T00:00:00Z",
        },
    )
    assessment_path = f"freezer/assessments/{item_id}/ba001.json"
    assessment = {
        "assessment_id": "RTS-BA-999999-001",
        "item_id": item_id,
        "assessment_version": 1,
        "item_version_snapshot": 1,
        "item_fingerprint": assessment_item_fingerprint(item),
        "derived": {"recommendation": "BUILD_NOW"},
    }
    _write_json(root / assessment_path, assessment)
    _write_json(
        root / f"freezer/assessments/{item_id}/current.json",
        {
            "item_id": item_id,
            "current_assessment_version": 1,
            "path": assessment_path,
            "assessment_id": assessment["assessment_id"],
            "recommendation": "BUILD_NOW",
            "decision_score": 100.0,
            "item_fingerprint": assessment["item_fingerprint"],
            "updated_at": "2026-07-24T00:00:00Z",
        },
    )
    preflight_path = f"freezer/preflights/{item_id}/pf001.json"
    preflight = {
        "preflight_id": "RTS-PF-999999-001",
        "item_id": item_id,
        "preflight_version": 1,
        "item_version_snapshot": 1,
        "item_fingerprint": preflight_item_fingerprint(item),
        "outcome": "PASS",
    }
    _write_json(root / preflight_path, preflight)
    _write_json(
        root / f"freezer/preflights/{item_id}/current.json",
        {
            "item_id": item_id,
            "current_preflight_version": 1,
            "path": preflight_path,
            "outcome": "PASS",
            "item_fingerprint": preflight["item_fingerprint"],
            "updated_at": "2026-07-24T00:00:00Z",
        },
    )
    _write_json(
        root / "freezer/index/items.json",
        {
            "generated_at": "2026-07-24T00:00:00Z",
            "count": 1,
            "items": [{
                "item_id": item_id,
                "version": 1,
                "title": item["title"],
                "type": "test",
                "status": "SELECTED",
                "priority_score": 1.0,
                "estimated_hours": {"minimum": 1, "maximum": 1},
                "tags": ["fixture"],
                "build_authority": "APPROVED",
                "preflight_state": "PASS",
                "updated_at": "2026-07-24T00:00:00Z",
            }],
        },
    )
    _write_json(
        root / "freezer/index/build_priority.json",
        {
            "generated_at": "2026-07-24T00:00:00Z",
            "count": 1,
            "policy": {},
            "items": [{
                "item_id": item_id,
                "version": 1,
                "title": item["title"],
                "status": "SELECTED",
                "priority_score": 1.0,
                "assessment_state": "CURRENT",
                "build_score": 100.0,
                "ranking_score": 100.0,
                "recommendation": "BUILD_NOW",
                "net_hours": 1.0,
                "reuse_hours_saved": 1.0,
                "implementation_efficiency": 1.0,
                "build_authority": "APPROVED",
            }],
        },
    )
    _write_json(
        root / "asset_manifest/index/assets.json",
        {
            "schema_version": "fixture",
            "generated_at": "2026-07-24T00:00:00Z",
            "count": 1,
            "assets": [{"asset_id": "RTS-AM-TEST"}],
        },
    )
    authorization = {
        "authorization_id": "RTS-AUTH-VERIFY-001",
        "item_id": item_id,
        "item_version": 1,
        "issued_by": "human-verification-fixture",
        "issued_at": "2026-07-24T00:00:00Z",
        "as_of": "2026-07-24T00:00:00Z",
        "adapter_id": "dry-run",
        "skill_id": "verify-skill",
        "drive_id": "verify-drive",
        "pack_id": "verify-pack",
        "trigger": "explicit-local-verification",
        "allowed_capabilities": ["LOCAL_CHECKPOINT_WRITE"],
        "budgets": {
            "max_attempts": 2,
            "max_elapsed_seconds": 10,
            "max_changed_files": 0,
            "max_changed_bytes": 0,
            "max_events": 10,
        },
        "stop_conditions": [
            "adapter_failure",
            "budget_exceeded",
            "human_stop",
            "unexpected_side_effect",
        ],
        "authorization_fingerprint": "0" * 64,
    }
    authorization["authorization_fingerprint"] = sha256_value(authorization_material(authorization))
    auth_path = root / "authorization.json"
    _write_json(auth_path, authorization)
    script_path = root / "script.json"
    _write_json(
        script_path,
        {
            "kind": "success",
            "summary": "deterministic local dry-run",
            "retryable": False,
            "usage": {"elapsed_seconds": 1, "changed_files": 0, "changed_bytes": 0},
            "result": {"fixture": "ok"},
            "timestamp": "2026-07-24T00:00:01Z",
        },
    )
    return auth_path, script_path


def command_verify() -> None:
    with tempfile.TemporaryDirectory(prefix="rts-controller-verify-") as temporary:
        fixture_root = Path(temporary) / "repo"
        state_dir = Path(temporary) / "state"
        auth_path, script_path = _verification_fixture(fixture_root)
        first = plan_execution(fixture_root, auth_path)
        second = plan_execution(fixture_root, auth_path)
        validate_plan(first)
        if pretty_json(first) != pretty_json(second):
            raise ControllerError("deterministic planning verification failed")
        result = run_execution(fixture_root, auth_path, state_dir, script_path)
        if result["state"] != "SUCCEEDED":
            raise ControllerError("dry-run success verification failed")
        events, checkpoint = verify_checkpoint(state_dir, first["plan_id"])
        if len(events) != 5 or checkpoint["state"] != "SUCCEEDED":
            raise ControllerError("event/checkpoint verification failed")
        persisted = (state_dir / first["plan_id"] / "events.jsonl").read_text(encoding="utf-8")
        for forbidden in ("prompt", "credential", "customer_data", "private_payload"):
            if forbidden in persisted:
                raise ControllerError(f"privacy verification failed: {forbidden}")
        import ast
        forbidden_modules = {"subprocess", "socket", "urllib.request", "requests"}
        for path in sorted(PACKAGE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = {alias.name for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    names = {node.module or ""}
                else:
                    continue
                if any(name in forbidden_modules or name.split(".")[0] in forbidden_modules for name in names):
                    raise ControllerError(f"forbidden external-action dependency found in {path.name}")
    print("Governed Execution Controller verification passed")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "plan":
            payload = plan_execution(root, args.authorization)
        elif args.command == "run":
            payload = run_execution(root, args.authorization, args.state_dir, args.script)
        elif args.command == "resume":
            payload = resume_execution(root, args.authorization, args.state_dir, args.script)
        elif args.command == "stop":
            payload = stop_execution(root, args.authorization, args.state_dir, args.timestamp)
        elif args.command == "inspect":
            payload = inspect_run(root, args.authorization, args.state_dir)
        elif args.command == "verify":
            command_verify()
            return 0
        else:
            raise ControllerError(f"unknown command: {args.command}")
        sys.stdout.write(pretty_json(payload))
    except ControllerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
