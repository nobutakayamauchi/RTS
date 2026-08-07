# RTS Design Knowledge Bridge v1.2 — Deployment Identity Gate

**Status:** IMPLEMENTED / VALIDATION PENDING  
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

## Definition of Done

V1.2 is complete when:

1. dogfood observations contain an explicit deployment identity placeholder
2. new runs begin at `AWAITING_DEPLOYMENT_IDENTITY`
3. debug-link rejects runtime observations without verified deployment identity
4. verified identity requires a concrete identifier and evidence
5. lifecycle output preserves deployment identity
6. empty/unobserved runs remain legal without fabricating deployment evidence
7. existing Human Approval Boundary remains unchanged
8. focused knowledge-bridge tests pass

No additional feature work belongs in V1.2.
