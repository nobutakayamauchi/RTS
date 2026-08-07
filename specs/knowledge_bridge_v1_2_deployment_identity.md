# RTS Design Knowledge Bridge v1.2 — Deployment Identity Gate

**Status:** IMPLEMENTED / VALIDATED / PASS  
**Base:** V1 dogfood completion record  
**Scope:** One dogfood-discovered defect only

## Problem

V1 dogfood showed that source-code existence can be mistaken for runtime reality when multiple working trees, legacy UIs, or deployment generations coexist.

A stale/non-deployed source tree was initially inspected and could have produced a false `BROKEN` classification before the active deployment was identified from the running service and route surface.

## Invariant

> Deployment Identity MUST be established before runtime implementation classification.

And:

> Code existence != runtime evidence.

## V1.2 behavior

`dogfood-start` creates an explicit `deployment_identity` block before observations are recorded.

A new dogfood run starts in:

```text
AWAITING_DEPLOYMENT_IDENTITY
```

The identity may record:

- service / unit
- working directory
- entrypoint / loaded module
- deployed revision
- active route or runtime surface
- supporting evidence

`debug-link` refuses non-empty runtime observations unless:

1. `deployment_identity.verified == true`
2. at least one concrete deployment identifier is present
3. deployment evidence is present

An empty observation set may still be linked while deployment identity is unresolved; all tracked nodes remain `UNOBSERVED`.

## Output propagation

Lifecycle output uses schema `1.2` and carries the normalized `deployment_identity` forward so later human review and City Release can see which runtime was classified.

## Safety boundary

This change does not add automatic environment discovery, repair, code modification, approval, or release execution.

Deployment verification remains evidence supplied or gathered by the dogfood operator. The gate prevents runtime classification from proceeding before that evidence boundary is satisfied.

## Validation evidence — 2026-08-07

Focused regression suite on `feature/obsidian-freezer-knowledge-bridge-v1.2`:

```text
76 passed in 1.02s
```

Real-project dogfood reused the Vlog request `REQ-d1226cff8801` and confirmed both sides of the gate:

1. Non-empty runtime observations without `deployment_identity` were rejected with:

```text
PermissionError: runtime classification requires deployment_identity; code existence is not runtime evidence
```

2. After recording and verifying deployment identity from the actual runtime, the same observations linked successfully.

Verified runtime identity included:

```text
service: rts-video-flow-web.service
working_directory: /home/ubuntu/rts-video-flow-segment-test
entrypoint: web_console.app_v5:app
active_surface: app_v5 with inherited app_v4/app_v3 routes
```

Supporting evidence came from systemd inspection and active runtime-route inspection.

Lifecycle classification remained stable after the gate:

```text
planned: 6
AS_BUILT: 3
BROKEN: 0
STALE: 1
UNOBSERVED: 2
status: AWAITING_HUMAN_DECISION
```

City Release also remained stable:

```text
decision: V1_SCOPE_COMPLETE_WITH_KNOWN_ISSUES
next_city: DOGFOODING
human_decision_required: true
```

No autonomous implementation, repair, approval, or release execution was introduced.

## Definition of Done

V1.2 is complete because:

1. dogfood observations contain an explicit deployment identity placeholder
2. new runs begin at `AWAITING_DEPLOYMENT_IDENTITY`
3. debug-link rejects runtime observations without verified deployment identity
4. verified identity requires a concrete identifier and evidence
5. lifecycle output preserves deployment identity
6. empty/unobserved runs remain legal without fabricating deployment evidence
7. existing Human Approval Boundary remains unchanged
8. focused knowledge-bridge tests pass
9. the real-project reject-then-pass dogfood sequence passes
10. City Release behavior remains unchanged after deployment verification

No additional feature work belongs in V1.2.
