"""Generate the exact RTS-FRZ-000009 Implementation Preflight candidate.

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
import freezer.preflight as preflight
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ITEM_ID = "RTS-FRZ-000009"
PREFLIGHT_AT = "2026-07-26T00:20:00Z"
OUTPUT_ROOT = ROOT / "human-review-ledger-preflight-candidate"

PREFLIGHT = {
    "outcome": "PASS",
    "assessor": "ChatGPT 5.6 Thinking with GitHub connector",
    "rationale": "The current BUILD_NOW Assessment and completed proposal, outcome, regression, rollback, FREEZER, and governed-loop components support a narrow repository-local implementation. Human Review Ledger v1 can add schemas, an initially empty append-only ledger, deterministic chain and source-fingerprint verification, non-authorizing summaries, a blank human-input template, and focused tests without creating a reviewer identity or decision. The package must reject stale or reordered decisions and preserve the pending proposal state. No command may approve, apply, merge, mutate a Skill, write an adjacent repository, call a provider, or perform an external action.",
    "affected_boundaries": [
        "repository-local human review decision schemas and append-only record layout",
        "exact proposal, pending-review, outcome, regression, rollback, policy, and reviewer-scope fingerprint linkage",
        "decision chain ordering, previous-record linkage, supersession, expiry, and stale-input validation",
        "reviewer identity fields and separation-of-duties assertions without AI identity inference",
        "non-authorizing ledger summary, verification, and blank template commands",
        "privacy, path safety, forbidden-import, manifest, CI, and governed-loop integration boundaries"
    ],
    "existing_assumptions": [
        "RTS remains the canonical repository-local structural ledger.",
        "The Skill proposal and pending review remain REVIEW_REQUIRED / PENDING / NOT_APPROVED / NOT_APPLIED.",
        "A human reviewer, not the package or AI, supplies any reviewer identity, rationale, conditions, and decision.",
        "Repository authentication may show who committed a record, but the first version does not claim cryptographic identity proof.",
        "An approval decision is review evidence only and cannot itself apply a Skill, authorize merge, or write an adjacent repository.",
        "Promotion Application Preview remains a separate future child with its own Assessment, Preflight, and approval."
    ],
    "data_migration": {
        "required": False,
        "notes": "No migration is authorized. The implementation may add a new package, schemas, an empty ledger manifest or current summary, templates, tests, and documentation. It must not rewrite the existing proposal, pending review, outcomes, regression result, rollback record, Assessments, Preflights, completed item histories, or adjacent repositories."
    },
    "external_interfaces": [
        "repository-local filesystem reads of committed governed proposal, evidence, regression, rollback, policy, and ledger records",
        "repository-local append-only ledger file contract for later human-authored records",
        "stdout for deterministic verify, summary, and blank-template commands"
    ],
    "approval_changes": [
        "This Preflight grants no review decision, reviewer identity, approval, application, merge, Skill mutation, adjacent-repository write, scheduling, provider, or external-action authority.",
        "A separate explicit human lifecycle revision is required before RTS-FRZ-000009 may become SELECTED or IN_PROGRESS.",
        "The implementation PR may contain no real APPROVE record; committed ledger state begins empty or pending-only.",
        "Any later human-authored decision is separately reviewed and does not authorize application without Promotion Application Preview and its own human gate.",
        "Any live identity provider, signature service, adjacent-repository operation, or automated application requires a new Assessment, Preflight, and approval."
    ],
    "public_documents": [
        "docs/implementation/HUMAN_REVIEW_LEDGER_V1_REGISTRATION_TASK.md",
        "docs/implementation/HUMAN_REVIEW_LEDGER_V1_ASSESSMENT_TASK.md",
        "learning_proposals/README.md",
        "learning_proposals/schemas/human_review.schema.json",
        "docs/core/operation_loop.md"
    ],
    "regression_tests": [
        "An empty committed ledger verifies deterministically and reports NO_DECISIONS without changing the pending proposal.",
        "Temporary test-only records cover APPROVE, REJECT, RETURN_FOR_REVISION, EXPIRE, and SUPERSEDE semantics without committing a real human decision.",
        "Records require explicit HUMAN authorship fields, non-empty reviewer identity source, rationale, reviewed-at time, and exact reviewed-source fingerprints.",
        "Reviewer, proposer, and implementer identities must satisfy declared separation-of-duties rules; self-review is rejected.",
        "Sequence numbers, previous-record fingerprints, decision fingerprints, and current pointers are recomputed; deletion, reordering, overwrite, fork, and silent supersession are rejected.",
        "Proposal, pending-review, outcome, regression, rollback, policy, reviewer-scope, and prior-record drift makes a decision stale or invalid.",
        "APPROVE remains non-authorizing: application status is NOT_APPLIED and all merge, mutation, adjacent-write, provider, scheduler, and external-action flags remain false.",
        "Raw prompts, credentials, secrets, customer data, provider payloads, private repository bodies, path escape, and forbidden private markers are rejected.",
        "The CLI exposes verify, summary, and blank-template only; no create-decision, approve, apply, merge, publish, send, network, subprocess, or shell command exists.",
        "All existing FREEZER, Assessment, Preflight, component, governed-loop, stale-index, full-unit, and Unicode checks remain green."
    ],
    "hidden_dependencies": [
        "The existing pending human-review schema models a request rather than a final append-only decision and must not be silently widened in place.",
        "The ledger needs its own policy fingerprint defining decision types, separation-of-duties, expiry, and non-authorizing constants.",
        "A current summary must distinguish no decision, current human decision, expired decision, stale decision, and superseded history.",
        "A human-authored record can assert identity provenance, but the repository-local first version cannot independently prove real-world identity.",
        "Governed-loop integration must report ledger status without interpreting an approval as application eligibility.",
        "CI path filters must include the package, schemas, ledger records, policy, focused tests, and public implementation documentation."
    ],
    "rollback_boundary": "The future implementation must be revertible by its merge commit and delete no existing governed data. The committed ledger begins empty or pending-only, and later decision records are append-only. No automatic rollback, record deletion, Skill restoration, application, adjacent-repository mutation, merge, or external action is authorized.",
    "completion_conditions": [
        "A standard-library repository-local human_review_ledger package exposes deterministic verify, summary, and blank-template commands only.",
        "A fail-closed decision schema defines APPROVE, REJECT, RETURN_FOR_REVISION, EXPIRE, and SUPERSEDE while fixing application and external-authority fields to non-authorizing values.",
        "A separate policy record pins decision vocabulary, reviewer roles, separation-of-duties, expiry rules, source requirements, and authority constants.",
        "The committed ledger starts with no real human decision and reports NO_DECISIONS or PENDING_REVIEW without fabricating reviewer data.",
        "Decision records bind exact proposal, pending-review, outcome evidence, regression result, rollback, policy, reviewer scope, and previous-record fingerprints.",
        "Append-only verification rejects overwrite, deletion, reordering, forked chains, sequence gaps, duplicate current decisions, and silent supersession.",
        "Stale-source detection prevents an old decision from remaining current after any reviewed input or policy changes.",
        "Focused tests use temporary TEST_ONLY records for all decision states, chain failures, self-review, stale inputs, privacy, path safety, and widened authority.",
        "The governed loop can verify and summarize ledger status but keeps proposal approval NOT_APPROVED and application NOT_APPLIED until a real human record and later application gate exist.",
        "CI and public documentation include the new package and explicitly state that no AI-generated decision, real approval fixture, Skill application, merge, or adjacent-repository write is included.",
        "RTS-FRZ-000009 advances through append-only SELECTED, IN_PROGRESS, VERIFIED, and COMPLETED lifecycle records only after separate human build approval."
    ],
    "decomposition": {
        "required": False,
        "child_candidates": []
    },
    "risks": [
        "A schema-valid HUMAN authorship assertion could be mistaken for independently verified identity.",
        "An APPROVE decision could be misread as Skill application or merge authority.",
        "Chain verification could miss deleted or forked records if the manifest and current pointer are not independently recomputed.",
        "Supersession or expiry rules could accidentally hide rejection history.",
        "A stale decision could survive source or policy drift if every reviewed fingerprint is not mandatory.",
        "A template or test fixture could be mistaken for a real human decision unless clearly blank or TEST_ONLY and excluded from committed ledger state.",
        "Private review rationale or source content could be persisted instead of bounded summaries and fingerprints."
    ]
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate() -> dict[str, object]:
    preflight.utc_now = lambda: PREFLIGHT_AT
    freezer_cli.utc_now = lambda: PREFLIGHT_AT
    assessment_core.utc_now = lambda: PREFLIGHT_AT
    source = ROOT / ".human-review-ledger-preflight.json"
    write_json(source, PREFLIGHT)
    try:
        record = preflight.create_preflight(ROOT, ITEM_ID, source)
    finally:
        source.unlink(missing_ok=True)
    freezer_cli.rebuild(ROOT)
    run = generate_run(ROOT)
    (ROOT / "governed_loop" / "runs" / "current.json").write_text(
        pretty_json(run), encoding="utf-8"
    )
    if record["outcome"] != "PASS":
        raise RuntimeError(f"unexpected preflight outcome: {record['outcome']}")
    return {"record": record, "run": run}


def write_doc(record: dict[str, object], run: dict[str, object]) -> None:
    path = ROOT / "docs" / "implementation" / "HUMAN_REVIEW_LEDGER_V1_PREFLIGHT_TASK.md"
    path.write_text(
        "# Human Review Ledger v1 — Implementation Preflight\n\n"
        f"- Preflight: `{record['preflight_id']}`\n"
        f"- outcome: `{record['outcome']}`\n"
        f"- item fingerprint: `{record['item_fingerprint']}`\n"
        "- item remains: `FROZEN / NOT_APPROVED`\n"
        "- WIP remains: `0`\n\n"
        "The approved implementation ground is schemas, an empty append-only ledger contract, deterministic verification, non-authorizing summary, blank human-input template, temporary TEST_ONLY fixtures, tests, CI, and documentation. No real reviewer identity or decision is created.\n\n"
        "This Preflight grants no build authority and no Skill application, merge, adjacent-repository write, provider, scheduler, network, subprocess, publication, deployment, messaging, or external-action authority.\n\n"
        f"The coupled read-only run is `{run['run_id']}` with fingerprint `{run['run_fingerprint']}`.\n",
        encoding="utf-8",
    )


def collect() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    paths = [
        "freezer/preflights/RTS-FRZ-000009/pf001.json",
        "freezer/preflights/RTS-FRZ-000009/current.json",
        "freezer/index/items.json",
        "freezer/index/priority.json",
        "freezer/index/build_priority.json",
        "freezer/manifests/manifest.sha256",
        "governed_loop/runs/current.json",
        "docs/implementation/HUMAN_REVIEW_LEDGER_V1_PREFLIGHT_TASK.md",
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
    write_doc(generated["record"], generated["run"])
    collect()
    print(generated["record"]["preflight_id"])
    print(generated["record"]["item_fingerprint"])
    print(generated["run"]["run_id"])
