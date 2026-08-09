# Deployment Identity v1 — Completion Task

## Problem

RTS observation can misclassify stale or non-deployed source code as runtime reality.

The governing invariant is:

```text
Code existence != runtime evidence.
```

Runtime implementation classification MUST NOT occur until Deployment Identity is established.

## Required identity surface

Deployment Identity v1 requires explicit evidence for:

1. service/unit/container/job identity;
2. working directory;
3. executable/module/entrypoint;
4. active route/command/worker/interface surface;
5. deployed commit/revision/image digest;
6. expected source revision;
7. timezone-aware observation timestamp.

## Establishment rule

All required observations MUST be present.

`deployed_revision` MUST exactly equal `source_revision`.

Only then may the verifier emit:

```text
DEPLOYMENT_IDENTITY_ESTABLISHED
runtime_classification_authorized: true
```

Every missing field, invalid timestamp, or revision mismatch fails closed. No repository-path inference, branch-name inference, source-code existence, or best-effort guess may substitute for runtime observation.

## Evidence chain

```text
Source Identity
    -> Deployment Identity
    -> Runtime Observation
    -> Outcome Evidence
```

Deployment Identity does not claim that an outcome is correct. It proves the runtime subject of the claim before outcome classification begins.

## v1 implementation

- `deployment_identity/core.py` — deterministic validator and fingerprinting
- `deployment_identity/cli.py` — read-only verification CLI
- `deployment_identity/README.md` — operator contract and boundary
- `tests/test_deployment_identity.py` — fail-closed invariants

## Prohibited behavior

Deployment Identity v1 MUST NOT:

- execute shell commands;
- inspect a live host itself;
- call a network or provider;
- deploy or restart services;
- mutate another repository;
- infer deployment state from source presence;
- authorize runtime classification after partial identity evidence.

Those observations must be collected by a separately governed observer/adapter and supplied as evidence.

## Acceptance criteria

- deterministic fingerprints;
- exact revision binding;
- missing identity fields fail closed;
- mismatched source/deployed revision fails closed;
- timezone-less observations fail closed;
- code/source evidence alone cannot establish runtime identity;
- successful proof explicitly authorizes runtime classification and nothing beyond it.

## Completion boundary

Deployment Identity v1 closes the previously observed classification gap at the proof boundary. It does not yet provide privileged live-host collection. Any future collector requires a separate authority, privacy, and execution-safety review.
