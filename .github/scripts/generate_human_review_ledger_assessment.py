#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CREATED_AT = "2026-07-25T23:45:00Z"
ITEM_ID = "RTS-FRZ-000009"
REF = "b75e3cc55c7c9754e3c0c914ee53c06e1f91cf86"
OUT = ROOT / "human-review-ledger-assessment-candidate"

assessment_input = {
    "assessor": "ChatGPT 5.6 Thinking with GitHub connector",
    "rationale": "The repository already contains the exact pending review request, proposal fingerprints, regression and rollback evidence, governed-loop source linkage, JSON validation patterns, and FREEZER gates needed for a repository-local append-only human review ledger. The remaining work is a narrow decision schema, immutable history verification, stale-input detection, separation-of-duties checks, and focused fail-closed tests. No approval, application, merge, adjacent-repository write, or Skill mutation authority is required.",
    "expected_effect": {
        "impact": 5,
        "strategic_fit": 5,
        "revenue_leverage": 3.5,
        "risk_reduction": 5,
        "recurrence": 5,
        "confidence": 4.5
    },
    "implementation": {
        "from_scratch_hours": 60,
        "integration_hours": 5,
        "validation_hours": 5,
        "unknown_buffer_hours": 2
    },
    "github_scan": {
        "performed": True,
        "repositories": ["nobutakayamauchi/RTS"],
        "queries": [
            "pending human review proposal exact fingerprints separation of duties",
            "append-only immutable governance records stale source detection",
            "skill regression rollback proposal review schema governed loop"
        ],
        "assets": [
            {"repository":"nobutakayamauchi/RTS","path":"learning_proposals/schemas/human_review.schema.json","ref":REF,"kind":"schema","reuse_mode":"DIRECT","license_status":"OWNED","estimated_hours_saved":10,"notes":"Existing fail-closed pending review contract and authority fields."},
            {"repository":"nobutakayamauchi/RTS","path":"learning_proposals/reviews/feature-build-v1.pending.json","ref":REF,"kind":"data","reuse_mode":"DIRECT","license_status":"OWNED","estimated_hours_saved":8,"notes":"Exact pending review request and separation-of-duties baseline."},
            {"repository":"nobutakayamauchi/RTS","path":"learning_proposals/proposals/feature-build-v1.json","ref":REF,"kind":"data","reuse_mode":"DIRECT","license_status":"OWNED","estimated_hours_saved":8,"notes":"Exact proposal, evidence, regression, and rollback references."},
            {"repository":"nobutakayamauchi/RTS","path":"learning_proposals/common.py","ref":REF,"kind":"code","reuse_mode":"ADAPT","license_status":"OWNED","estimated_hours_saved":6,"notes":"Canonical JSON, hashing, privacy-key, and path-safety helpers."},
            {"repository":"nobutakayamauchi/RTS","path":"governed_loop/","ref":REF,"kind":"code","reuse_mode":"REFERENCE","license_status":"OWNED","estimated_hours_saved":6,"notes":"Exact source linkage and non-authorizing run verification patterns."},
            {"repository":"nobutakayamauchi/RTS","path":"skill_regression/","ref":REF,"kind":"code","reuse_mode":"REFERENCE","license_status":"OWNED","estimated_hours_saved":6,"notes":"Regression, rollback, and stale fingerprint verification patterns."},
            {"repository":"nobutakayamauchi/RTS","path":"freezer/","ref":REF,"kind":"code","reuse_mode":"REFERENCE","license_status":"OWNED","estimated_hours_saved":4,"notes":"Append-only lifecycle, manifest, WIP, Assessment, and Preflight gates."}
        ],
        "gaps": [
            "No append-only decision ledger currently distinguishes approve, reject, return, expire, and supersede.",
            "No current verifier invalidates decisions after reviewed-input or reviewer-scope drift.",
            "No current decision record proves reviewer identity and separation of duties without granting application authority.",
            "The first version must not create a human decision or apply a Skill."
        ]
    },
    "risks": [
        "A stored decision could be mistaken for Skill application or merge authority.",
        "An AI-generated reviewer identity, rationale, or approval would be false authority.",
        "Mutable or reordered history could hide supersession or expiry.",
        "A decision could remain apparently valid after proposal, evidence, regression, rollback, policy, or reviewer-scope drift.",
        "Private prompts, credentials, customer data, provider payloads, or private repository bodies could leak into rationale fields."
    ]
}

with tempfile.TemporaryDirectory() as td:
    input_path = Path(td) / "assessment.json"
    input_path.write_text(json.dumps(assessment_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "freezer.build_assessment", "create", ITEM_ID, "--input", str(input_path)], cwd=ROOT, check=True)

run = subprocess.run([sys.executable, "-m", "governed_loop.cli", "generate"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
(ROOT / "governed_loop/runs/current.json").write_text(run, encoding="utf-8")
subprocess.run([sys.executable, "-m", "freezer.cli", "verify"], cwd=ROOT, check=True)
subprocess.run([sys.executable, "-m", "freezer.build_assessment", "verify"], cwd=ROOT, check=True)
subprocess.run([sys.executable, "-m", "governed_loop.cli", "verify"], cwd=ROOT, check=True)

if OUT.exists():
    shutil.rmtree(OUT)
for rel in [
    "freezer/assessments/RTS-FRZ-000009/ba001.json",
    "freezer/assessments/RTS-FRZ-000009/current.json",
    "freezer/index/build_priority.json",
    "freezer/manifests/manifest.sha256",
    "governed_loop/runs/current.json",
]:
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / rel, dst)

doc = OUT / "docs/implementation/HUMAN_REVIEW_LEDGER_V1_ASSESSMENT_TASK.md"
doc.parent.mkdir(parents=True, exist_ok=True)
doc.write_text("""# Human Review Ledger v1 — Build Assessment\n\nThis assessment evaluates only whether a repository-local append-only human review ledger should proceed to Implementation Preflight. It grants no reviewer identity, decision, approval, application, merge, adjacent-repository write, external execution, or Skill mutation authority.\n\nThe assessment reuses the exact pending review request, proposal, regression, rollback, governed-loop, privacy, hashing, and FREEZER gate contracts already committed in RTS.\n""", encoding="utf-8")
print(OUT)
