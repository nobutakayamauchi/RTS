# Read-Only Governed Loop Orchestrator v1 — Implementation Task

## Purpose

Implement the approved `RTS-FRZ-000008` scope as a deterministic repository-local one-shot orchestrator.

## Composition

The package invokes current public verification contracts in this fixed order:

1. Asset Manifest;
2. Read-Only Loop Core;
3. Governed Execution Controller local self-verification;
4. Outcome Evidence;
5. Skill Regression and rollback;
6. Proposal-Only Outcome Learning.

It emits one canonical loop-run record linking exact source, evaluation, controller, outcome, regression, rollback, proposal, and pending-review fingerprints.

## Commands

```text
python -m governed_loop.cli generate
python -m governed_loop.cli verify
python -m governed_loop.cli summary
```

Normal commands write only to stdout. Verification is read-only and hashes all governed sources before and after composition.

## Safety boundary

The implementation is not a scheduler or runtime dispatcher. It grants no provider, external execution, adjacent-repository write, Skill mutation, approval, application, publication, messaging, or automatic rollback authority.

All current outcomes remain `SIMULATED_ONLY`. The learning proposal remains `REVIEW_REQUIRED / NOT_APPROVED / NOT_APPLIED`, and the review remains `PENDING`.

## Validation

CI must run all existing governed package verifiers, the governed-loop verifier and focused tests, full unit-test discovery, stale-index checks, and Unicode Guard.

The committed run fixture is generated from exact governed inputs and must be byte-for-byte reproducible.
