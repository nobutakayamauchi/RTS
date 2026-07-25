"""Generate the exact RTS-FRZ-000009 Build Assessment candidate.

This file and its workflow step are temporary and must be removed before merge.
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
import freezer.assessment_store as assessment_store
import freezer.cli as freezer_cli
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ITEM_ID = "RTS-FRZ-000009"
ASSESSED_AT = "2026-07-25T23:45:00Z"
OUTPUT_ROOT = ROOT / "human-review-ledger-assessment-candidate"

ASSESSMENT = {
    "assessor": "ChatGPT 5.6 Thinking with GitHub connector",
    "rationale": "The repository already contains a deterministic pending review request, exact proposal and evidence fingerprints, regression and rollback records, privacy and path-safety validators, append-only FREEZER storage patterns, and the one-shot governed-loop run. Human Review Ledger v1 can therefore be implemented mainly by adapting current standard-library validation and immutable-record patterns. The remaining work is a strict decision schema, append-only chain verification, reviewer and separation-of-duties fields, stale-decision detection, non-authorizing summaries, CLI verification, focused tests, and governed-loop linkage. No review decision, reviewer identity, Skill application, adjacent-repository write, or external authority is required to build the ledger contract.",
    "expected_effect": {
        "impact": 5,
        "strategic_fit": 5,
        "revenue_leverage": 3,
        "risk_reduction": 5,
        "recurrence": 4.5,
        "confidence": 4.5
    },
    "implementation": {
        "from_scratch_hours": 48,
        "integration_hours": 5,
        "validation_hours": 5,
        "unknown_buffer_hours": 2
    },
    "github_scan": {
        "performed": True,
        "repositories": ["nobutakayamauchi/RTS"],
        "queries": [
            "pending human review proposal reviewer separation of duties",
            "append-only immutable decision chain stale fingerprint validation",
            "skill regression rollback proposal evidence exact linkage",
            "FREEZER assessment preflight lifecycle manifest governed loop"
        ],
        "assets": [
            {
                "repository": "nobutakayamauchi/RTS",
                "path": "learning_proposals/",
                "ref": "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86",
                "kind": "code",
                "reuse_mode": "DIRECT",
                "license_status": "OWNED",
                "estimated_hours_saved": 10,
                "notes": "Provides deterministic proposal generation, exact provenance, privacy rejection, path safety, pending-review semantics, and non-authorizing validation patterns."
            },
            {
                "repository": "nobutakayamauchi/RTS",
                "path": "learning_proposals/schemas/human_review.schema.json",
                "ref": "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86",
                "kind": "schema",
                "reuse_mode": "ADAPT",
                "license_status": "OWNED",
                "estimated_hours_saved": 6,
                "notes": "Supplies the current pending-review vocabulary and separation-of-duties boundary to extend into append-only decisions."
            },
            {
                "repository": "nobutakayamauchi/RTS",
                "path": "learning_proposals/proposals/feature-build-v1.json and learning_proposals/reviews/feature-build-v1.pending.json",
                "ref": "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86",
                "kind": "data",
                "reuse_mode": "DIRECT",
                "license_status": "OWNED",
                "estimated_hours_saved": 6,
                "notes": "Provides exact proposal and pending-review fingerprints for deterministic ledger fixtures without inventing a human decision."
            },
            {
                "repository": "nobutakayamauchi/RTS",
                "path": "governed_loop/",
                "ref": "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86",
                "kind": "code",
                "reuse_mode": "DIRECT",
                "license_status": "OWNED",
                "estimated_hours_saved": 8,
                "notes": "Provides fixed-order source verification, canonical fingerprints, privacy boundaries, CLI patterns, and read-only non-authorizing summaries."
            },
            {
                "repository": "nobutakayamauchi/RTS",
                "path": "skill_regression/results/feature-build-v1.json and skill_regression/rollback/feature-build-v1.json",
                "ref": "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86",
                "kind": "data",
                "reuse_mode": "DIRECT",
                "license_status": "OWNED",
                "estimated_hours_saved": 6,
                "notes": "Provides exact regression and rollback evidence that a review decision must bind without granting application eligibility."
            },
            {
                "repository": "nobutakayamauchi/RTS",
                "path": "freezer/",
                "ref": "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86",
                "kind": "code",
                "reuse_mode": "REFERENCE",
                "license_status": "OWNED",
                "estimated_hours_saved": 4,
                "notes": "Supplies append-only version history, exact current pointers, manifest integrity, Assessment, Preflight, approval, and WIP gates."
            }
        ],
        "gaps": [
            "No append-only decision record schema currently distinguishes APPROVE, REJECT, RETURN_FOR_REVISION, EXPIRE, and SUPERSEDE.",
            "No current validator proves that reviewer identity and separation-of-duties fields are human-supplied and bound to exact reviewed inputs.",
            "No current ledger invalidates a decision after proposal, evidence, regression, rollback, policy, or reviewer-scope drift.",
            "No first-version command may apply a Skill, write an adjacent repository, merge a change, or infer a human decision.",
            "Promotion Application Preview remains a separate future child and must consume only an explicitly human-authored current decision."
        ]
    },
    "risks": [
        "A ledger record could be misread as application or merge authority rather than review evidence.",
        "An AI-generated reviewer identity, rationale, signature, or approval could impersonate human authorization.",
        "Mutable or reorderable decision records could erase rejection history or silently replace conditions.",
        "A decision could remain apparently current after one of its exact reviewed inputs drifts.",
        "The ledger could accidentally persist raw prompts, credentials, customer data, provider payloads, or private repository bodies."
    ]
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate() -> dict[str, object]:
    assessment_store.utc_now = lambda: ASSESSED_AT
    assessment_core.utc_now = lambda: ASSESSED_AT
    freezer_cli.utc_now = lambda: ASSESSED_AT
    source = ROOT / ".human-review-ledger-assessment.json"
    write_json(source, ASSESSMENT)
    try:
        record = assessment_store.create_assessment(ROOT, ITEM_ID, source)
    finally:
        source.unlink(missing_ok=True)
    freezer_cli.rebuild(ROOT)
    run = generate_run(ROOT)
    (ROOT / "governed_loop" / "runs" / "current.json").write_text(
        pretty_json(run), encoding="utf-8"
    )
    if record["derived"]["recommendation"] != "BUILD_NOW":
        raise RuntimeError(f"unexpected recommendation: {record['derived']}")
    return {"record": record, "run": run}


def write_doc(record: dict[str, object], run: dict[str, object]) -> None:
    derived = record["derived"]
    path = ROOT / "docs" / "implementation" / "HUMAN_REVIEW_LEDGER_V1_ASSESSMENT_TASK.md"
    path.write_text(
        "# Human Review Ledger v1 — Build Assessment\n\n"
        f"- Assessment: `{record['assessment_id']}`\n"
        f"- recommendation: `{derived['recommendation']}`\n"
        f"- decision score: `{derived['decision_score']}`\n"
        f"- reuse hours saved: `{derived['reuse_hours_saved']}`\n"
        f"- net hours: `{derived['net_hours']}`\n"
        f"- implementation efficiency: `{derived['implementation_efficiency']}`\n"
        f"- item fingerprint: `{record['item_fingerprint']}`\n\n"
        "The Assessment evaluates repository-local implementation value only. It does not create a human decision, approve the Skill proposal, grant build authority, satisfy Implementation Preflight, authorize application, or permit adjacent-repository writes.\n\n"
        f"The coupled read-only run is `{run['run_id']}` with fingerprint `{run['run_fingerprint']}` and WIP remains `0`.\n",
        encoding="utf-8",
    )


def collect() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    paths = [
        "freezer/assessments/RTS-FRZ-000009/ba001.json",
        "freezer/assessments/RTS-FRZ-000009/current.json",
        "freezer/index/items.json",
        "freezer/index/priority.json",
        "freezer/index/build_priority.json",
        "freezer/manifests/manifest.sha256",
        "governed_loop/runs/current.json",
        "docs/implementation/HUMAN_REVIEW_LEDGER_V1_ASSESSMENT_TASK.md",
    ]
    for relative in paths:
        source = ROOT / relative
        destination = OUTPUT_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, check=True, stdout=(OUTPUT_ROOT / "base-tree-sha.txt").open("w", encoding="utf-8"))


if __name__ == "__main__":
    generated = generate()
    write_doc(generated["record"], generated["run"])
    collect()
    print(generated["record"]["assessment_id"])
    print(generated["record"]["derived"])
    print(generated["run"]["run_id"])
