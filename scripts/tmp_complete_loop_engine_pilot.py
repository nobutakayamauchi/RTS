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

# Parent completion changes only lifecycle state. The exact integrated child and
# pilot-entry evidence is recorded in the separate completion document so the
# existing evidence-backed Assessment remains current.
parent_verified = revise("RTS-FRZ-000003", "parent-verified.json", {"status": "VERIFIED"})
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

## Completion evidence

The parent is closed by the independently verified child packages and the canonical eight-stage governed-loop fixture. The parent item body is not substantively rewritten during completion, preserving the current Build Assessment fingerprint. This document records the integrated result and practical-test entry point.

## Preserved boundary

Completion grants no provider, scheduler, publication, target or adjacent-repository write, Skill mutation, automatic approval, merge, contract, outreach, or external-execution authority. The prepared CASE-001 project is now eligible to enter a governed practical test; the test result itself remains unobserved.
'''
(ROOT / "docs/implementation/LOOP_ENGINE_GOVERNED_PILOT_V1_COMPLETION.md").write_text(completion, encoding="utf-8")
