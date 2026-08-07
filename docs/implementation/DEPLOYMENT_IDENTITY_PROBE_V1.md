# RTS Deployment Identity Probe v1

## Purpose

Prevent the debugger from classifying repository code as the implementation that is actually serving the observed runtime unless deployment identity has first been established.

## Canonical invariant

> Deployment Identity MUST be established before runtime implementation classification.

Corollary:

> Code existence != runtime evidence.

The probe is read-only and advisory. It grants no deployment, mutation, rollback, restart, or implementation authority.

## Problem

A debugger can observe a failure, find matching-looking source code, and incorrectly classify that source as runtime reality even when the observed service is running a stale checkout, another working directory, another process, another route, another artifact, or another deployed revision.

This is a provenance failure before it is a code-analysis failure.

## Identity fields

Each field is recorded as an evidence record containing `value`, `source`, and `observed_at`.

- host
- pid
- service/unit
- working directory
- executable
- entrypoint/module
- active route
- deployed commit/revision
- artifact SHA-256 and artifact path when supplied

## States

### ESTABLISHED

Required identity fields are present and at least one runtime anchor (`service_unit` or `active_route`) is present. Runtime implementation classification may proceed.

### PARTIAL

Some identity evidence exists, but the required identity cannot be established. Runtime implementation classification is forbidden.

### UNKNOWN

No meaningful identity can be established. Runtime implementation classification is forbidden.

### CONFLICT

Two or more deployment-identity sources conflict. Runtime implementation classification is forbidden until the conflict is resolved.

## Required establishment boundary

For v1, `ESTABLISHED` requires:

1. working directory;
2. executable;
3. entrypoint;
4. deployed revision; and
5. at least one of service/unit or active route.

Artifact SHA-256 strengthens identity evidence but does not replace a deployed revision in v1.

## Fail-closed rules

- Repository file existence MUST NOT set runtime classification authority.
- `runtime_classification_allowed` MUST be true only when status is `ESTABLISHED`.
- `PARTIAL`, `UNKNOWN`, and `CONFLICT` MUST block runtime implementation classification.
- Conflicting revision environment values MUST produce `CONFLICT`.
- Missing or unreadable requested artifacts MUST fail the probe.
- Snapshot validation MUST reject manufactured runtime authority.
- Snapshot validation MUST reject any representation that treats code existence as runtime evidence.

## Read-only collection

The probe may read:

- process working directory;
- Python executable and argv entrypoint;
- hostname and pid;
- explicitly supplied service/unit and route;
- bounded deployment-related environment variables;
- `.git/HEAD` or packed refs when available;
- a specifically supplied artifact for SHA-256 measurement.

The probe MUST NOT:

- modify source files;
- write deployment state;
- restart services;
- select or kill processes;
- change routes;
- change FREEZER state;
- grant build authority;
- claim that GitHub `main` is deployed merely because it exists.

## CLI

Collect a snapshot:

```bash
python -m deployment_identity.cli probe \
  --service-unit rts.service \
  --active-route https://example.invalid/health \
  --deployed-revision <commit> \
  --entrypoint app.py
```

Require a usable identity before continuing a debugger pipeline:

```bash
python -m deployment_identity.cli probe \
  --service-unit rts.service \
  --deployed-revision <commit> \
  --entrypoint app.py \
  --require-established
```

Validate a stored snapshot:

```bash
python -m deployment_identity.cli verify deployment_identity.json --require-established
```

Exit codes:

- `0`: valid snapshot and requested gate passed;
- `1`: invalid input or invalid snapshot;
- `2`: valid snapshot, but identity is not `ESTABLISHED` while `--require-established` was requested.

## Debugger integration contract

The required order is:

```text
Observation
→ Deployment Identity Probe
→ ESTABLISHED?
    ├─ no  → runtime implementation = UNKNOWN; stop classification
    └─ yes → evidence correlation
            → code mapping
            → root-cause analysis
            → patch proposal
            → retest against the same or newly established deployment identity
```

A retest MUST establish deployment identity again when service, route, working directory, executable, artifact, or revision may have changed.

## Acceptance tests

The v1 implementation must prove:

1. an explicit runtime anchor plus revision can establish identity;
2. repository code existence without deployed revision remains `PARTIAL`;
3. deployed revision without service/unit or route remains `PARTIAL`;
4. active route may serve as the runtime anchor;
5. conflicting revision environment values produce `CONFLICT`;
6. artifact hashing does not substitute for revision identity;
7. manufactured runtime-classification permission is rejected;
8. code existence cannot be promoted into runtime evidence;
9. a missing requested artifact fails closed.

## Future integration

A later bounded change may connect this probe to the RTS debugger/flight-recorder pipeline and require an `ESTABLISHED` snapshot before any runtime-to-source implementation classification. That integration is intentionally separate from this v1 probe so the probe can first be validated as an independent read-only component.
