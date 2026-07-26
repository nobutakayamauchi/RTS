# Human Review Ledger v1 Implementation Contract

## Governed item

- item: `RTS-FRZ-000009`
- Assessment: `RTS-BA-000009-001 / BUILD_NOW`
- Preflight: `RTS-PF-000009-001 / PASS`
- lifecycle during this implementation: `IN_PROGRESS / APPROVED`

## Purpose

Add a deterministic repository-local append-only ledger for separately authored human review decisions. Every record links exact proposal, pending-review, outcome, regression, rollback, policy, reviewer-scope, and prior-decision fingerprints.

## Committed state

The repository commits an empty ledger, current policy, reviewer scope, fail-closed schemas, and a blank input template. No real reviewer identity or human decision is manufactured by this implementation.

## Allowed commands

```text
python -m human_review_ledger.cli verify
python -m human_review_ledger.cli summary
python -m human_review_ledger.cli summary --as-of <ISO-8601>
python -m human_review_ledger.cli blank-template
```

There is no command to create, approve, apply, merge, mutate, publish, or send a decision.

## Required verification

- append-only sequence and prior-fingerprint chain
- manifest file digests and head linkage
- exact policy and reviewer-scope fingerprints
- explicit `HUMAN` authorship assertion and identity source
- reviewer differs from the proposer identity derived from the governed proposal and the implementer identity pinned by policy
- unmanifested decision files are rejected rather than ignored
- `APPROVE`, `REJECT`, `RETURN_FOR_REVISION`, `EXPIRE`, and `SUPERSEDE`
- elapsed approval expiry is evaluated during ordinary summary and verification, not only with an explicit test clock
- stale-source invalidation
- privacy and repository path safety
- all application, mutation, merge, adjacent-write, and external-action authority remains false
- governed-loop linkage remains read-only and `NOT_APPLIED`

## Permanent exclusions

No AI-created human identity, signature, rationale, or decision. No Skill application or mutation. No adjacent-repository write. No provider, network, subprocess, shell, scheduler, deployment, publication, messaging, customer action, or raw private-content storage.
