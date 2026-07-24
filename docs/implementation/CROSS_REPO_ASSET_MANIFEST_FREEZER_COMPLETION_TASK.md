# Cross-Repo Asset Manifest v1 — FREEZER Completion Task

## Purpose

PR #228 merged the Cross-Repo Asset Manifest runtime, seed inventory, indexes, tests, and CI, but the governed FREEZER registration for the parent initiative and its four children did not reach `main`. This task completes that missing governance layer without changing the already-merged asset-manifest design.

## Scope

Implement only the FREEZER completion for the already-built Cross-Repo Asset Manifest v1.

Create and verify these records using the existing append-only FREEZER, Build Assessment, and Implementation Preflight contracts:

- `RTS-FRZ-000003` — Governed Execution and Learning Loop (parent)
  - type: `architecture`
  - status: `FROZEN`
  - build authority: `NOT_APPROVED`
  - Preflight outcome: `DECOMPOSE_REQUIRED`
  - preserve children 000004–000007 in dependencies, preserved value, source refs, destinations, or another existing validated field without adding unvalidated schema fields
- `RTS-FRZ-000004` — Cross-Repo Asset Manifest
  - type: `architecture`
  - status: `COMPLETED`
  - build authority: `APPROVED`
  - current Build Assessment recommendation: `BUILD_NOW`
  - current Implementation Preflight outcome: `PASS`
  - evidence must reference the merged `asset_manifest/` implementation and PR #228 / merge commit `9bafaa74ff56e5765060408c133ac106337a4574`
- `RTS-FRZ-000005` — Read-Only Loop Core
  - type: `feature`
  - status: `FROZEN` or `READY`
  - build authority: `NOT_APPROVED`
  - depends on 000004
- `RTS-FRZ-000006` — Governed Execution Controller
  - type: `architecture`
  - status: `FROZEN`
  - build authority: `NOT_APPROVED`
  - depends on 000004 and 000005
- `RTS-FRZ-000007` — Outcome Learning and Skill Promotion
  - type: `feature`
  - status: `FROZEN`
  - build authority: `NOT_APPROVED`
  - depends on 000004–000006

Only 000004 is approved/completed. Do not implement 000005–000007.

## Required updates

- add immutable item versions and `current.json` pointers for 000003–000007
- add the required immutable Build Assessment and Preflight records/pointers for 000003 and 000004
- use the current item fingerprints produced by the repository code; do not hand-wave stale fingerprints
- regenerate `freezer/index/items.json`, `freezer/index/priority.json`, `freezer/index/build_priority.json`, and `freezer/manifests/manifest.sha256`
- update brittle tests that assume exactly two FREEZER items or a fixed next ID
- add focused tests proving:
  - 000003 is decomposed and not approved
  - 000004 is completed with current BUILD_NOW assessment and PASS Preflight
  - 000005–000007 remain unapproved and unimplemented
  - WIP=1 and human approval gates are unchanged
- keep `asset_manifest/` behavior unchanged unless a genuine integration defect is found

## Validation

Run and report the exact results of:

```text
python -m asset_manifest.cli verify
python -m freezer.cli verify
python -m freezer.build_assessment verify
python -B -m unittest discover -s tests -v
```

Also run the existing semantic stale-index check or an equivalent temporary-copy rebuild check so committed generated outputs are proven current.

## Boundaries

- no external publication, contact, or customer action
- no mutation of adjacent repositories
- no private repository bodies, secrets, customer data, prompts, or credentials
- no auto-start of 000005–000007
- do not weaken Build Assessment, Preflight, explicit human approval, or WIP=1
- do not add temporary transfer bundles, workflow hacks, or diagnostic files to the final diff

## Completion evidence

The append-only current records now bind completion to the already-merged implementation and conform to the published string-list item contract:

- parent item: `freezer/items/RTS-FRZ-000003/v002.json`
- completed child item: `freezer/items/RTS-FRZ-000004/v006.json`
- Build Assessment: `freezer/assessments/RTS-FRZ-000004/ba003.json`
- parent Implementation Preflight: `freezer/preflights/RTS-FRZ-000003/pf002.json`
- completed child Implementation Preflight: `freezer/preflights/RTS-FRZ-000004/pf003.json`
- implementation PR: `#228`
- implementation merge commit: `9bafaa74ff56e5765060408c133ac106337a4574`

The current records for 000003–000007 use arrays of strings for `preserved_value` and the other published list fields. Runtime validation and focused tests now reject scalar strings. Earlier item, assessment, and Preflight versions remain immutable; current pointers select the schema-compliant evidence-complete versions.

## Completion condition

The task is complete only when CI is green, review findings are resolved, the final diff contains only the required governed records/tests/generated outputs, and `main` can verify all three systems: FREEZER, Build Assessment, and Asset Manifest.
