# Phase 6 — Implementation Council and Human Approval Gate

## Goal

Before approving a FREEZER draft, inspect the current codebase and FREEZER inventory, identify missing foundations, compare timing options, and generate a human-readable discussion report. Stop before approval.

## Inputs

- normalized knowledge record
- Challenge result
- FREEZER draft and review sidecar
- repository root
- FREEZER item directory

## Automated stages

1. Codebase inventory
2. FREEZER inventory
3. Dependency and overlap search
4. Missing Parts analysis
5. insertion-point candidates
6. timing and priority recommendation
7. human discussion report
8. stop at `AWAITING_HUMAN_DECISION`

## Decision classes

- `APPROVE_NOW`
- `APPROVE_AFTER_FOUNDATION`
- `BUNDLE_WITH_OTHER_ITEMS`
- `DEFER_OR_REJECT`

## Missing Part classes

- `blocking`: required before implementation
- `recommended`: reduces risk or rework
- `optional`: may be deferred without invalidating the implementation

## Safety boundary

Phase 6 must not:

- change `build_authority` to `APPROVED`
- add an item to FREEZER automatically
- edit source code
- execute implementation
- overwrite an existing council report

## Minimum completion criteria

- deterministic JSON report
- human-readable Markdown report
- code and FREEZER evidence references
- explicit opposing view
- explicit human questions
- `human_decision_required: true`
