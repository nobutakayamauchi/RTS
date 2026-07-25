"""Generate the exact RTS-FRZ-000009 registration candidate for CI validation.

This file and its workflow step are temporary and must be removed before merge.
"""
from __future__ import annotations

import json
import shutil
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
REGISTERED_AT = "2026-07-25T23:09:00Z"
OUTPUT_ROOT = ROOT / "human-review-ledger-registration-candidate"

ITEM = {
    "item_id": ITEM_ID,
    "title": "Human Review Ledger v1",
    "type": "architecture",
    "status": "FROZEN",
    "summary": "Add a deterministic repository-local append-only ledger for human review decisions linked to exact proposal, evidence, regression, rollback, reviewer, and policy fingerprints without granting application or mutation authority.",
    "original_problem": "RTS can generate a pending human-review request, but it has no governed append-only record that distinguishes approval, rejection, return-for-revision, expiry, and supersession while preserving reviewer identity, separation of duties, exact reviewed inputs, and non-authorizing boundaries.",
    "why_it_matters": "Without an immutable review ledger, later application previews cannot prove who reviewed which exact proposal and evidence set, whether the reviewer was independent, or whether the decision remained current after source drift.",
    "reason_frozen": "A review record could be mistaken for execution authority or silently rewritten. A current BUILD_NOW Assessment, PASS Implementation Preflight, explicit human approval, and WIP=1 transition are required before implementation.",
    "preserved_value": [
        "Append-only human review decisions with exact source fingerprints.",
        "Explicit APPROVE, REJECT, RETURN_FOR_REVISION, EXPIRE, and SUPERSEDE semantics.",
        "Reviewer identity, role, separation-of-duties, rationale, conditions, and expiry evidence.",
        "Fail-closed stale-decision detection without Skill application or adjacent-repository mutation."
    ],
    "priority": {
        "impact": 5,
        "urgency": 4,
        "strategic_fit": 5,
        "readiness": 4,
        "revenue_value": 3,
        "dependency_value": 5,
        "risk_reduction": 5,
        "confidence": 4,
        "effort": 2,
        "uncertainty": 2
    },
    "trigger_conditions": [
        "RTS-FRZ-000007 and RTS-FRZ-000008 are COMPLETED with current governed records.",
        "The pending review request remains REVIEW_REQUIRED / PENDING / NOT_APPROVED / NOT_APPLIED.",
        "Review decisions can link exact proposal, evidence, regression, rollback, policy, and reviewer fingerprints.",
        "The ledger remains repository-local, deterministic, append-only, and human-authored."
    ],
    "negative_triggers": [
        "An AI creates or infers a human approval, reviewer identity, signature, rationale, or decision.",
        "A review decision directly mutates or applies a Skill, writes to an adjacent repository, or authorizes merge.",
        "Existing decision records can be overwritten, deleted, reordered, or silently superseded.",
        "A stale decision remains valid after proposal, evidence, regression, rollback, policy, or reviewer-scope drift.",
        "Raw prompts, credentials, customer data, provider payloads, or private repository bodies are persisted."
    ],
    "dependencies": [
        "RTS-FRZ-000007",
        "RTS-FRZ-000008"
    ],
    "source_refs": [
        "learning_proposals/proposals/feature-build-v1.json",
        "learning_proposals/reviews/feature-build-v1.pending.json",
        "learning_proposals/schemas/human_review.schema.json",
        "governed_loop/runs/current.json",
        "skill_regression/results/feature-build-v1.json",
        "skill_regression/rollback/feature-build-v1.json"
    ],
    "possible_destinations": [
        "RTS repository-local human_review_ledger package",
        "RTS governance review-decision records",
        "future human-approved promotion application preview"
    ],
    "estimated_hours": {
        "minimum": 12,
        "maximum": 22
    },
    "tags": [
        "human-review",
        "ledger",
        "append-only",
        "separation-of-duties",
        "approval",
        "evidence",
        "governance"
    ],
    "build_authority": "NOT_APPROVED",
    "recall_mode": "MANUAL"
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_item() -> None:
    if freezer_cli.next_item_id(ROOT) != ITEM_ID:
        raise RuntimeError(f"unexpected next item id: {freezer_cli.next_item_id(ROOT)}")
    freezer_cli.utc_now = lambda: REGISTERED_AT
    assessment_core.utc_now = lambda: REGISTERED_AT
    source = ROOT / ".human-review-ledger-item.json"
    write_json(source, ITEM)
    try:
        freezer_cli.add_item(ROOT, source)
    finally:
        source.unlink(missing_ok=True)


def rebuild_governed_run() -> dict[str, object]:
    run = generate_run(ROOT)
    (ROOT / "governed_loop" / "runs" / "current.json").write_text(
        pretty_json(run), encoding="utf-8"
    )
    loop = run["components"]["read_only_loop"]
    if loop["wip_count"] != 0 or loop["active_item_ids"] != []:
        raise RuntimeError("registration widened WIP state")
    if loop["recommendation_item_id"] != "RTS-FRZ-000003":
        raise RuntimeError("registration changed the current advisory target")
    return run


def write_registration_doc(run: dict[str, object]) -> None:
    path = ROOT / "docs" / "implementation" / "HUMAN_REVIEW_LEDGER_V1_REGISTRATION_TASK.md"
    path.write_text(
        "# Human Review Ledger v1 — FREEZER Registration\n\n"
        "## Registered scope\n\n"
        "- item: `RTS-FRZ-000009`\n"
        "- initial status: `FROZEN / NOT_APPROVED`\n"
        "- Assessment: `MISSING`\n"
        "- Preflight: `MISSING`\n"
        "- recall mode: `MANUAL`\n"
        "- priority score: `84.26`\n\n"
        "## Intended boundary\n\n"
        "The item is limited to deterministic repository-local append-only human review-decision records. Registration does not create a decision, identify a reviewer, approve a proposal, authorize application, mutate a Skill, write to an adjacent repository, merge a change, or perform any external action.\n\n"
        "## Coupled governed run\n\n"
        f"- run: `{run['run_id']}`\n"
        f"- fingerprint: `{run['run_fingerprint']}`\n"
        "- WIP: `0`\n"
        "- current advisory target remains `RTS-FRZ-000003`\n\n"
        "A separate current Build Assessment and Implementation Preflight are required before selection or implementation.\n",
        encoding="utf-8",
    )


def collect_candidate() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    paths = [
        f"freezer/items/{ITEM_ID}/v001.json",
        f"freezer/items/{ITEM_ID}/current.json",
        "freezer/index/items.json",
        "freezer/index/priority.json",
        "freezer/index/build_priority.json",
        "freezer/manifests/manifest.sha256",
        "governed_loop/runs/current.json",
        "docs/implementation/HUMAN_REVIEW_LEDGER_V1_REGISTRATION_TASK.md",
    ]
    for relative in paths:
        source = ROOT / relative
        destination = OUTPUT_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


if __name__ == "__main__":
    register_item()
    run = rebuild_governed_run()
    write_registration_doc(run)
    collect_candidate()
    print(run["run_id"])
    print(run["run_fingerprint"])
