# Adaptive Governance Compiler v1 — Implementation Contract

## Purpose

Compile the minimum deterministic governance plan required for an exact change context instead of applying maximum governance ceremony to every change.

## Implemented boundary

- strict change-context validation;
- deterministic G0 through G4 classification;
- fixed approval, independent-review, rollback, testing, and execution profiles;
- compressed planning workflow with per-profile step budgets;
- governance-to-implementation cost ratio and `BALANCED`, `HEAVY`, or `OVER_GOVERNED` status;
- exact context and plan fingerprints;
- fail-closed verification against tampering or context drift;
- non-authorizing CLI with `compile`, `verify`, and `profiles` only.

## Preserved constitutional boundary

The compiler cannot approve itself, widen authority, apply changes, mutate a repository or Skill, merge, publish, deploy, message, schedule, call a provider, or perform an external action. Emergency status never lowers the selected governance level.

## Integration state

`RTS-FRZ-000010` and its parent `RTS-FRZ-000003` are completed, WIP has returned to zero, and the CASE-001 pilot seed/run contract is committed. This compiler is rebased onto that completed loop-engine state and must pass its focused tests, the full repository suite, Unicode Guard, and independent review before merge.
