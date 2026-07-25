# Approve Outcome Learning Proposal v1 — Lifecycle Task

## Purpose

Record the explicit human approval and governed lifecycle start for `RTS-FRZ-000007 Outcome Learning and Skill Promotion`.

## Approval boundary

The operator explicitly approved continuing on 2026-07-25 (Asia/Tokyo). This approval authorizes only the proposal-only v1 implementation ground described by `RTS-PF-000007-001`.

It does not authorize:

- Skill promotion, publication, retirement, mutation, application, or automatic rollback
- writes to RTS-Skills or any adjacent repository
- self-approval by the proposal generator
- network, provider API, subprocess, shell, deployment, messaging, scheduling, customer action, or external side effects
- treating `SIMULATED_ONLY` evidence as external business or user success
- ingestion of private prompts, credentials, customer data, provider payloads, or repository bodies

## Gate evidence

Before lifecycle transition:

- current Build Assessment: `RTS-BA-000007-002 / BUILD_NOW`
- current Implementation Preflight: `RTS-PF-000007-001 / PASS`
- WIP limit: `1`
- active `IN_PROGRESS` item count: `0`
- auto-start: `false`

## Lifecycle records

Append, without rewriting prior versions:

```text
v002 FROZEN / NOT_APPROVED
→ v003 SELECTED / APPROVED
→ v004 IN_PROGRESS / APPROVED
```

The final current pointer for this PR is v004.

## Implementation separation

This lifecycle PR contains no proposal-engine code. The proposal-only v1 implementation must be delivered in a separate PR and must remain inside the approved Preflight boundary.

## Completion conditions

- append-only v003 and v004 records exist
- current pointer resolves to v004
- Assessment and Preflight remain current
- exactly one item is `IN_PROGRESS`
- priority and build-priority indexes exclude the active item
- FREEZER SHA manifest is current
- all governed verification, stale-index checks, unit tests, and Unicode Guard pass
