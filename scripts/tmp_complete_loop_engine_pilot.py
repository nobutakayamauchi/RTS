from __future__ import annotations

import json
from pathlib import Path

from freezer.cli import revise_item
from governed_loop.common import pretty_json
from governed_loop.generation import generate_run

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp"
TMP.mkdir(exist_ok=True)


def revise(item_id: str, name: str, changes: dict) -> dict:
    path = TMP / name
    path.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = revise_item(ROOT, item_id, path)
    path.unlink()
    return result


preview_verified = revise("RTS-FRZ-000010", "preview-verified.json", {"status": "VERIFIED"})
preview_completed = revise("RTS-FRZ-000010", "preview-completed.json", {"status": "COMPLETED"})

parent_changes = {
    "status": "VERIFIED",
    "summary": "Completed parent integration for the governed one-shot loop: deterministic asset discovery, advisory work selection, bounded dry-run control, outcome evidence, regression analysis, proposal generation, append-only human review, non-applying promotion preview, and a verified pilot seed/run contract.",
    "dependencies": [
        "RTS-FRZ-000004",
        "RTS-FRZ-000005",
        "RTS-FRZ-000006",
        "RTS-FRZ-000007",
        "RTS-FRZ-000008",
        "RTS-FRZ-000009",
        "RTS-FRZ-000010"
    ],
    "source_refs": [
        "asset_manifest/snapshots/current.json",
        "execution_controller/README.md",
        "governed_loop/runs/current.json",
        "human_review_ledger/ledger/current.json",
        "learning_proposals/proposals/feature-build-v1.json",
        "outcome_evidence/examples/success.json",
        "pilot_run_contract/examples/value-discovery-case-001.json",
        "promotion_application_preview/previews/current.json",
        "skill_regression/results/feature-build-v1.json"
    ],
    "possible_destinations": [
        "CASE-001 governed practical test",
        "RTS repository-local governed pilot loop",
        "future separately approved provider and repository adapters"
    ]
}
parent_verified = revise("RTS-FRZ-000003", "parent-verified.json", parent_changes)
parent_completed = revise("RTS-FRZ-000003", "parent-completed.json", {"status": "COMPLETED"})

# The completion state has no active WIP. Preserve safety assertions while avoiding
# coupling the test to whichever frozen item is recommended next.
test_path = ROOT / "tests/test_governed_loop.py"
text = test_path.read_text(encoding="utf-8")
before = '''        self.assertEqual(loop["active_item_ids"], ["RTS-FRZ-000010"])
        self.assertEqual(loop["wip_count"], 1)
        self.assertEqual(loop["state"], "FOCUS")
        self.assertEqual(loop["recommendation_action"], "CONTINUE_OR_VERIFY_ACTIVE_ITEM")
        self.assertEqual(loop["recommendation_item_id"], "RTS-FRZ-000010")'''
after = '''        self.assertEqual(loop["active_item_ids"], [])
        self.assertEqual(loop["wip_count"], 0)
        self.assertEqual(loop["state"], "NORMAL")
        self.assertIsInstance(loop["recommendation_action"], str)
        self.assertTrue(loop["recommendation_action"])
        if loop["recommendation_item_id"] is not None:
            self.assertIsInstance(loop["recommendation_item_id"], str)'''
if before not in text:
    raise SystemExit("expected active-loop assertion block was not found")
test_path.write_text(text.replace(before, after), encoding="utf-8")

(ROOT / "governed_loop/runs/current.json").write_text(
    pretty_json(generate_run(ROOT)), encoding="utf-8"
)

completion = f'''# Loop Engine Governed Pilot v1 Completion

## Lifecycle closed

- `RTS-FRZ-000010`: v003 IN_PROGRESS -> v{preview_verified['version']:03d} VERIFIED -> v{preview_completed['version']:03d} COMPLETED
- `RTS-FRZ-000003`: v002 FROZEN -> v{parent_verified['version']:03d} VERIFIED -> v{parent_completed['version']:03d} COMPLETED
- WIP after completion: `0`

## Completed governed path

```text
asset discovery
-> advisory work selection
-> bounded local dry-run control
-> outcome evidence
-> deterministic regression
-> proposal-only learning
-> append-only human review
-> non-applying promotion preview
-> verified pilot seed/run contract
```

## Practical-test entry

- seed: `pilot_run_contract/examples/value-discovery-case-001.json`
- state: `READY_FOR_PILOT`
- WIP: `1`
- human gate: required
- execution/provider/publication/target-write authority: not authorized

## Preserved boundary

Completion grants no provider, scheduler, publication, target or adjacent-repository write, Skill mutation, automatic approval, merge, contract, outreach, or external-execution authority. The prepared CASE-001 project is now eligible to enter a governed practical test; the test result itself remains unobserved.
'''
(ROOT / "docs/implementation/LOOP_ENGINE_GOVERNED_PILOT_V1_COMPLETION.md").write_text(completion, encoding="utf-8")
