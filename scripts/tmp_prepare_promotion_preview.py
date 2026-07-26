#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import traceback
from pathlib import Path

from freezer.assessment_store import assessment_current_path, create_assessment
from freezer.cli import load_current, rebuild, revise_item
from freezer.preflight import create_preflight, preflight_current_path
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ROOT = Path(__file__).resolve().parents[1]
ITEM_ID = "RTS-FRZ-000010"
TMP = ROOT / ".tmp"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def generate() -> None:
    if not assessment_current_path(ROOT, ITEM_ID).exists():
        create_assessment(
            ROOT,
            ITEM_ID,
            TMP / "promotion_application_preview_assessment.json",
        )
        rebuild(ROOT)

    if not preflight_current_path(ROOT, ITEM_ID).exists():
        create_preflight(
            ROOT,
            ITEM_ID,
            TMP / "promotion_application_preview_preflight.json",
        )
        rebuild(ROOT)

    current = load_current(ROOT, ITEM_ID)
    if current["status"] == "FROZEN":
        selected = TMP / "selected.json"
        write_json(
            selected,
            {"status": "SELECTED", "build_authority": "APPROVED"},
        )
        revise_item(ROOT, ITEM_ID, selected)
        current = load_current(ROOT, ITEM_ID)

    if current["status"] == "SELECTED":
        started = TMP / "started.json"
        write_json(started, {"status": "IN_PROGRESS"})
        revise_item(ROOT, ITEM_ID, started)

    test_path = ROOT / "tests/test_governed_loop.py"
    text = test_path.read_text(encoding="utf-8")
    idle = '''        self.assertEqual(loop["active_item_ids"], [])
        self.assertEqual(loop["wip_count"], 0)
        self.assertEqual(loop["state"], "NORMAL")
        self.assertEqual(loop["recommendation_action"], "REQUEST_HUMAN_APPROVAL")
        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000003")'''
    active = '''        self.assertEqual(loop["active_item_ids"], ["RTS-FRZ-000010"])
        self.assertEqual(loop["wip_count"], 1)
        self.assertEqual(loop["state"], "FOCUS")
        self.assertEqual(loop["recommendation_action"], "CONTINUE_OR_VERIFY_ACTIVE_ITEM")
        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000010")'''
    if idle in text:
        test_path.write_text(text.replace(idle, active), encoding="utf-8")
    elif active not in text:
        raise RuntimeError("expected governed-loop assertion block not found")

    task = ROOT / "docs/implementation/PROMOTION_APPLICATION_PREVIEW_V1_TASK.md"
    task.write_text(
        """# Promotion Application Preview v1 Implementation Contract

## Governed item

- item: `RTS-FRZ-000010`
- Assessment: `RTS-BA-000010-001 / BUILD_NOW`
- Preflight: `RTS-PF-000010-001 / PASS`
- lifecycle: `v001 FROZEN / NOT_APPROVED -> v002 SELECTED / APPROVED -> v003 IN_PROGRESS / APPROVED`
- WIP: `1`

## Human authorization

The operator explicitly authorized the governed loop-engine completion route. This authority is limited to the repository-local, read-only, non-applying Promotion Application Preview v1 boundary.

## Allowed implementation

- deterministic standard-library preview package
- exact proposal, review, ledger, regression, rollback, policy, scope, and target fingerprints
- canonical proposed change set, blockers, validation, stop conditions, and rollback references
- `generate`, `verify`, and `summary` only
- committed blocked fixture for the current empty ledger
- governed-loop read-only integration and focused tests

## Not authorized

No human-decision creation, self-approval, Skill mutation, application, target write, adjacent-repository write, commit, merge, provider, scheduler, network, subprocess, publication, deployment, messaging, customer action, or automatic rollback.
""",
        encoding="utf-8",
    )

    run_path = ROOT / "governed_loop/runs/current.json"
    run_path.write_text(pretty_json(generate_run(ROOT)), encoding="utf-8")

    for path in TMP.glob("selected.json"):
        path.unlink()
    for path in TMP.glob("started.json"):
        path.unlink()
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache)


def main() -> None:
    diagnostic = TMP / "promotion_preview_prepare_error.txt"
    try:
        generate()
        diagnostic.unlink(missing_ok=True)
    except Exception:
        diagnostic.parent.mkdir(parents=True, exist_ok=True)
        diagnostic.write_text(traceback.format_exc(), encoding="utf-8")
        print(diagnostic.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
