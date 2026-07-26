# Promotion Application Preview v1 Implementation Contract

## Governed item

- item: `RTS-FRZ-000010`
- Assessment: `RTS-BA-000010-001 / BUILD_NOW`
- Preflight: `RTS-PF-000010-001 / PASS`
- lifecycle: `v001 FROZEN / NOT_APPROVED -> v002 SELECTED / APPROVED -> v003 IN_PROGRESS / APPROVED`
- WIP: `1`

## Human authorization

The operator explicitly authorized the governed loop-engine completion route. This authority is limited to the repository-local, read-only, non-applying Promotion Application Preview v1 boundary.

## Allowed implementation

- deterministic standard-library preview package
- exact proposal, review, ledger, regression, rollback, policy, scope, and target fingerprints
- canonical proposed change set, blockers, validation, stop conditions, and rollback references
- `generate`, `verify`, and `summary` only
- committed blocked fixture for the current empty ledger
- governed-loop read-only integration and focused tests

## Not authorized

No human-decision creation, self-approval, Skill mutation, application, target write, adjacent-repository write, commit, merge, provider, scheduler, network, subprocess, publication, deployment, messaging, customer action, or automatic rollback.
