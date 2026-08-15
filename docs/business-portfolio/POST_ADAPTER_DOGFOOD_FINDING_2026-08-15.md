# Post Adapter v0 Dogfood Finding — 2026-08-15

Status: `DOGFOOD_BLOCKER_FOUND / DO_NOT_AUTO_PUBLISH`

## Source under test

Real BridgePatch launch and payment-link correction:

```text
fixture:
post_adapter/fixtures/bridgepatch_launch_20260815.json

current X output capture:
post_adapter/fixtures/bridgepatch_launch_20260815_x_current.md
```

The source contains six evidence-bound verified facts covering:

- public-sale approval;
- dedicated Payment Link v2 active state;
- exact line-item name / JPY 10,000 / quantity 1;
- legacy Payment Link retirement;
- successful GitHub Pages hotfix build;
- no customer invoice or external social posting performed by the launch workflow.

No unsupported fact was required for this reproduction.

## Reproduction result

Using the deterministic behavior of the current committed `render_x()` implementation against the fixture produces a single X draft of approximately **493 Unicode code points** before any platform-specific counting rules are applied.

The current implementation does:

```text
project + summary
+ every verified fact as one bullet
+ CTA
```

It has no channel-rule object, no length budget, no priority/ranking step, and no thread-splitting decision.

## Why this is a real v0 dogfood failure

The frozen v0 specification requires the X adapter to produce:

- a concise primary post;
- optional thread continuation blocks when useful;
- platform constraints through a replaceable adapter rule rather than a permanent hard-coded limit.

The current renderer does not implement that replaceable rule layer. It simply emits every verified fact into one primary body.

Therefore a real evidence-rich development update can be factually safe yet operationally poor as an X draft.

This is not merely a request to hard-code `280` into the core. The missing capability is:

> `CHANNEL_POLICY / CONTENT_BUDGET / FACT_PRIORITY / OVERFLOW_STRATEGY`

## Required invariant

```text
Evidence binding decides WHAT may be claimed.
Channel policy decides HOW MUCH may enter the primary output.
Overflow must never be solved by silently deleting claim meaning or fabricating compression.
```

## Minimum correction candidate

Introduce a replaceable X adapter policy with at least:

```text
primary_budget
fact_priority
must_keep_fields
thread_allowed
max_thread_blocks
overflow_strategy
```

A possible flow is:

```text
verified facts
-> rank / select must-keep facts
-> render primary candidate
-> measure with selected channel policy
-> if over budget:
     move lower-priority verified facts to thread blocks
     OR require human rewrite
-> preserve source bindings for every emitted claim
```

The normalized source contract should remain unchanged.

## Safety boundary

Do not solve this by:

- dropping evidence requirements;
- marking unsupported summaries as verified;
- truncating arbitrary characters;
- rewriting a completed event into a stronger claim;
- adding direct X posting;
- hiding overflow from the reviewer.

## Current verdict

```text
BRIDGEPATCH_SALES_BLOCKERS: CLOSED
POST_ADAPTER_CORE_EVIDENCE_GATE: WORKING
POST_ADAPTER_X_CHANNEL_SHAPING: FAILED_DOGFOOD
EXTERNAL_POSTING: NOT PERFORMED
NEXT_AUTHORIZED_WORK: DESIGN/FIX CHANNEL POLICY LAYER
```

`/goal` stops here because the first real Post Adapter dogfood exposed a missing architectural layer rather than an external-account or human-approval blocker.
