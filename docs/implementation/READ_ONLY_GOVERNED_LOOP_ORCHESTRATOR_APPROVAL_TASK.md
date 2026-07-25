# Approve and Start Read-Only Governed Loop Orchestrator v1

## Human approval

The operator explicitly instructed the governed roadmap to continue after reviewing the staged plan. This record narrows that instruction to the repository-local `RTS-FRZ-000008` implementation boundary defined by:

- `RTS-BA-000008-001 / BUILD_NOW`;
- `RTS-PF-000008-001 / PASS`.

## Lifecycle

```text
v001 FROZEN / NOT_APPROVED
-> v002 SELECTED / APPROVED
-> v003 IN_PROGRESS / APPROVED
```

`RTS-FRZ-000008` is the only active item under WIP=1.

## Approved scope

- standard-library repository-local package;
- deterministic one-shot `generate`, `verify`, and `summary` commands;
- fixed child-verification order;
- canonical immutable loop-run schema and fixture;
- exact source and output fingerprints;
- fail-closed privacy, path-safety, source-drift, and authority checks;
- focused tests and governed CI integration.

## Not approved

- scheduler, polling, daemon, or unattended continuous operation;
- network or live provider execution;
- subprocess, shell, publication, deployment, messaging, or customer actions;
- Skill approval, mutation, application, promotion, retirement, or automatic rollback;
- adjacent-repository writes;
- real-run ingestion or external-success claims;
- raw prompts, credentials, customer data, provider payloads, or private repository bodies.

Any such expansion requires a new Assessment, Preflight, and explicit human approval.
