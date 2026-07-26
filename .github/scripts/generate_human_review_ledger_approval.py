"""Generate the exact approval/start lifecycle candidate for RTS-FRZ-000009.

This file and its workflow are temporary and must be removed before merge.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import freezer.assessment_core as assessment_core
import freezer.cli as freezer_cli
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ITEM_ID = "RTS-FRZ-000009"
SELECTED_AT = "2026-07-26T04:30:00Z"
IN_PROGRESS_AT = "2026-07-26T04:31:00Z"
OUTPUT_ROOT = ROOT / "human-review-ledger-approval-candidate"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revise(changes: dict[str, object], at: str) -> dict[str, object]:
    freezer_cli.utc_now = lambda: at
    assessment_core.utc_now = lambda: at
    source = ROOT / ".human-review-ledger-lifecycle.json"
    write_json(source, changes)
    try:
        return freezer_cli.revise_item(ROOT, ITEM_ID, source)
    finally:
        source.unlink(missing_ok=True)


def generate() -> dict[str, object]:
    selected = revise(
        {
            "status": "SELECTED",
            "build_authority": "APPROVED",
        },
        SELECTED_AT,
    )
    in_progress = revise(
        {
            "status": "IN_PROGRESS",
            "build_authority": "APPROVED",
        },
        IN_PROGRESS_AT,
    )
    run = generate_run(ROOT)
    (ROOT / "governed_loop" / "runs" / "current.json").write_text(
        pretty_json(run), encoding="utf-8"
    )

    if selected["version"] != 2 or selected["status"] != "SELECTED":
        raise RuntimeError(f"unexpected selected lifecycle: {selected}")
    if in_progress["version"] != 3 or in_progress["status"] != "IN_PROGRESS":
        raise RuntimeError(f"unexpected active lifecycle: {in_progress}")
    if in_progress["build_authority"] != "APPROVED":
        raise RuntimeError("Human Review Ledger build authority was not approved")
    return {"selected": selected, "in_progress": in_progress, "run": run}


def write_doc(selected: dict[str, object], in_progress: dict[str, object], run: dict[str, object]) -> None:
    path = ROOT / "docs" / "implementation" / "HUMAN_REVIEW_LEDGER_V1_APPROVAL_TASK.md"
    path.write_text(
        "# Approve and Start Human Review Ledger v1\n\n"
        "## Human approval\n\n"
        "The operator explicitly instructed the governed loop-engine path to proceed without pausing after reviewing the current route. This record narrows that instruction to the repository-local `RTS-FRZ-000009 Human Review Ledger v1` implementation boundary defined by:\n\n"
        "- `RTS-BA-000009-001 / BUILD_NOW`;\n"
        "- `RTS-PF-000009-001 / PASS`.\n\n"
        "## Lifecycle\n\n"
        "```text\n"
        "v001 FROZEN / NOT_APPROVED\n"
        "-> v002 SELECTED / APPROVED\n"
        "-> v003 IN_PROGRESS / APPROVED\n"
        "```\n\n"
        "`RTS-FRZ-000009` becomes the only active item under WIP=1.\n\n"
        "## Approved implementation scope\n\n"
        "- standard-library repository-local `human_review_ledger` package;\n"
        "- strict decision, policy, reviewer-scope, chain, and current-summary schemas;\n"
        "- an initially empty append-only committed ledger contract;\n"
        "- deterministic `verify`, non-authorizing `summary`, and blank-template commands only;\n"
        "- exact proposal, pending-review, outcome, regression, rollback, policy, reviewer-scope, and prior-record fingerprints;\n"
        "- stale-source, chain-integrity, separation-of-duties, privacy, path-safety, and widened-authority rejection;\n"
        "- temporary `TEST_ONLY` fixtures in tests only;\n"
        "- governed-loop status linkage that does not interpret review as application authority;\n"
        "- focused tests, governed CI integration, and public documentation.\n\n"
        "## Not approved\n\n"
        "- creating, inferring, or impersonating a human reviewer, identity, signature, rationale, or decision;\n"
        "- committing a real `APPROVE` decision fixture;\n"
        "- Skill application, mutation, promotion, retirement, merge authorization, or automatic rollback;\n"
        "- adjacent-repository writes;\n"
        "- network, provider, subprocess, shell, scheduler, publication, deployment, messaging, or customer actions;\n"
        "- raw prompts, credentials, secrets, customer data, provider payloads, or private repository bodies.\n\n"
        "Any expansion requires a new Assessment, Preflight, and explicit human approval. A later human review decision remains review evidence only and requires a separately governed Promotion Application Preview before any application action is considered.\n\n"
        f"The coupled governed run is `{run['run_id']}` with fingerprint `{run['run_fingerprint']}`.\n",
        encoding="utf-8",
    )


def collect() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    paths = [
        "freezer/items/RTS-FRZ-000009/v002.json",
        "freezer/items/RTS-FRZ-000009/v003.json",
        "freezer/items/RTS-FRZ-000009/current.json",
        "freezer/index/items.json",
        "freezer/index/priority.json",
        "freezer/index/build_priority.json",
        "freezer/manifests/manifest.sha256",
        "governed_loop/runs/current.json",
        "docs/implementation/HUMAN_REVIEW_LEDGER_V1_APPROVAL_TASK.md",
    ]
    for relative in paths:
        source = ROOT / relative
        destination = OUTPUT_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=ROOT,
        check=True,
        stdout=(OUTPUT_ROOT / "base-tree-sha.txt").open("w", encoding="utf-8"),
    )


if __name__ == "__main__":
    generated = generate()
    write_doc(generated["selected"], generated["in_progress"], generated["run"])
    collect()
    print(generated["selected"]["item_id"], generated["selected"]["status"])
    print(generated["in_progress"]["item_id"], generated["in_progress"]["status"])
    print(generated["run"]["run_id"])
