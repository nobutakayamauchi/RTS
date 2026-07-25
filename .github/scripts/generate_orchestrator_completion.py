from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import freezer.assessment_core as assessment_core
import freezer.cli as freezer_cli
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ROOT = Path(__file__).resolve().parents[2]
ITEM_ID = "RTS-FRZ-000008"
VERIFIED_AT = "2026-07-25T12:10:00Z"
COMPLETED_AT = "2026-07-25T12:11:00Z"
OUTPUT_ROOT = ROOT / ".completion-candidate"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def build_item_versions() -> None:
    item_dir = ROOT / "freezer" / "items" / ITEM_ID
    current = json.loads((item_dir / "v003.json").read_text(encoding="utf-8"))

    verified = copy.deepcopy(current)
    verified["version"] = 4
    verified["status"] = "VERIFIED"
    verified["updated_at"] = VERIFIED_AT
    verified["supersedes"] = "v003"
    write_json(item_dir / "v004.json", verified)

    completed = copy.deepcopy(verified)
    completed["version"] = 5
    completed["status"] = "COMPLETED"
    completed["updated_at"] = COMPLETED_AT
    completed["supersedes"] = "v004"
    write_json(item_dir / "v005.json", completed)

    write_json(
        item_dir / "current.json",
        {
            "item_id": ITEM_ID,
            "current_version": 5,
            "path": f"freezer/items/{ITEM_ID}/v005.json",
            "updated_at": COMPLETED_AT,
        },
    )


def rebuild_governed_outputs() -> dict[str, object]:
    freezer_cli.utc_now = lambda: COMPLETED_AT
    assessment_core.utc_now = lambda: COMPLETED_AT
    freezer_cli.rebuild(ROOT)

    run = generate_run(ROOT)
    (ROOT / "governed_loop" / "runs" / "current.json").write_text(
        pretty_json(run), encoding="utf-8"
    )
    return run


def update_focused_test() -> None:
    path = ROOT / "tests" / "test_governed_loop.py"
    text = path.read_text(encoding="utf-8")
    old = '''        self.assertEqual(\n            run["components"]["read_only_loop"]["active_item_ids"],\n            ["RTS-FRZ-000008"],\n        )\n'''
    new = '''        loop = run["components"]["read_only_loop"]\n        self.assertEqual(loop["active_item_ids"], [])\n        self.assertEqual(loop["wip_count"], 0)\n        self.assertEqual(loop["state"], "NORMAL")\n        self.assertEqual(loop["recommendation_action"], "REQUEST_HUMAN_APPROVAL")\n        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000003")\n'''
    if old not in text:
        raise RuntimeError("governed-loop focused test block changed unexpectedly")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_completion_doc(run: dict[str, object]) -> None:
    path = (
        ROOT
        / "docs"
        / "implementation"
        / "READ_ONLY_GOVERNED_LOOP_ORCHESTRATOR_V1_COMPLETION_TASK.md"
    )
    path.write_text(
        f"""# Read-Only Governed Loop Orchestrator v1 — Completion\n\n"
        f"## Governed lifecycle\n\n"
        f"- `v003`: `IN_PROGRESS / APPROVED`\n"
        f"- `v004`: `VERIFIED / APPROVED`\n"
        f"- `v005`: `COMPLETED / APPROVED`\n"
        f"- current Assessment: `RTS-BA-000008-001 / BUILD_NOW`\n"
        f"- current Preflight: `RTS-PF-000008-001 / PASS`\n\n"
        f"## Verified implementation\n\n"
        f"- package: `governed_loop/`\n"
        f"- mode: `ONE_SHOT_READ_ONLY`\n"
        f"- committed run: `{run['run_id']}`\n"
        f"- run fingerprint: `{run['run_fingerprint']}`\n"
        f"- WIP after completion: `0`\n"
        f"- next advisory action: `REQUEST_HUMAN_APPROVAL` for `RTS-FRZ-000003`\n\n"
        f"## Preserved boundaries\n\n"
        f"No scheduler, polling, daemon, network, provider, subprocess, shell, publication, deployment, messaging, customer action, adjacent-repository write, Skill mutation, Skill application, automatic promotion, or automatic rollback authority was added. Outcome data remains `SIMULATED_ONLY`; the learning proposal remains `REVIEW_REQUIRED / NOT_APPROVED / NOT_APPLIED`.\n\n"
        f"## Completion evidence\n\n"
        f"The completion PR must pass strict committed-record verification, deterministic regeneration of the loop run, all focused and full tests, Unicode Guard, review-thread resolution, merge, and main re-verification.\n"
        f""",
        encoding="utf-8",
    )


def collect_candidate() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    paths = [
        f"freezer/items/{ITEM_ID}/v004.json",
        f"freezer/items/{ITEM_ID}/v005.json",
        f"freezer/items/{ITEM_ID}/current.json",
        "freezer/index/items.json",
        "freezer/index/priority.json",
        "freezer/index/build_priority.json",
        "freezer/manifests/manifest.sha256",
        "governed_loop/runs/current.json",
        "tests/test_governed_loop.py",
        "docs/implementation/READ_ONLY_GOVERNED_LOOP_ORCHESTRATOR_V1_COMPLETION_TASK.md",
    ]
    for relative in paths:
        source = ROOT / relative
        destination = OUTPUT_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


if __name__ == "__main__":
    build_item_versions()
    run = rebuild_governed_outputs()
    update_focused_test()
    write_completion_doc(run)
    collect_candidate()
    print(run["run_id"])
    print(run["run_fingerprint"])
