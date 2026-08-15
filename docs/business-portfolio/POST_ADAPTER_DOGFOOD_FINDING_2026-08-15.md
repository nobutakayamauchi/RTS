# Post Adapter v0 Dogfood Finding — 2026-08-15

Status: `DOGFOOD_BLOCKER_RESOLVED / NO_AUTO_PUBLISH`

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

No unsupported fact is required for this reproduction.

## Original failure

The first dogfood run emitted:

```text
project + summary
+ every verified fact as one bullet
+ CTA
```

as a single X draft of approximately 493 Unicode code points before platform-specific counting.

Evidence binding was working, but channel shaping was missing.

## Implemented correction

The adapter now separates:

```text
Evidence Binding
-> CHANNEL_POLICY
-> CONTENT_BUDGET
-> FACT_PRIORITY
-> OVERFLOW_STRATEGY
-> channel draft
```

### CHANNEL_POLICY

X has a replaceable adapter policy rather than a permanent platform rule inside the normalized source contract.

Current v0 policy records:

```text
must_keep_fields = project_name / summary / call_to_action
thread_allowed = true
max_thread_blocks = 6
cta_placement = primary
overflow_strategy = thread
```

### CONTENT_BUDGET

The current X adapter uses:

```text
unit = unicode_codepoints
max_per_post = 260
```

This is a conservative **internal draft budget**, not a claim that 260 is X's permanent or exact platform character-count rule. It can be replaced in the channel policy without rewriting the normalized source contract.

### FACT_PRIORITY

Optional fact hints are now supported:

```text
critical > high > normal > low
must_keep facts rank before non-must-keep facts
```

Priority never changes whether a claim is verified. Evidence binding still decides whether the claim is eligible to appear at all.

For the BridgePatch fixture:

- public-sale state = `critical / must_keep`;
- exact v2 line item / quantity / JPY 10,000 = `critical / must_keep`;
- v2 active state and legacy-link retirement = `high`;
- Pages build = `normal`;
- no billing/social auto-post side effect = `low`.

### OVERFLOW_STRATEGY

The X strategy is `thread`.

The primary post reserves room for:

```text
project + summary
+ highest-priority facts that fit
+ CTA
```

Lower-priority verified facts move to explicit continuation blocks.

No arbitrary character truncation or claim paraphrase is performed by the shaping layer.

If a required field or a single verified fact exceeds the configured per-post budget by itself, generation fails closed with `human rewrite required` rather than silently cutting the claim.

## BridgePatch dogfood result

The real fixture now produces:

```text
X post blocks: 2
max observed body size: 251 Unicode code points
configured internal budget: 260
verified claims in fixture: 6
verified claims emitted: 6
claim duplication: 0
claim loss: 0
external publication: false
```

Primary contains:

- project + summary;
- both `critical / must_keep` facts;
- CTA.

Continuation contains the remaining four evidence-bound facts in priority order.

## Regression result

Isolated execution against the updated implementation:

```text
10/10 unit tests PASS
```

Coverage includes:

- original four-channel behavior;
- evidence fail-closed behavior;
- approval blocking when warnings remain;
- replaceable channel policy recorded in the manifest;
- BridgePatch two-post dogfood;
- every BridgePatch claim emitted exactly once;
- budget compliance;
- oversized single-claim fail-closed behavior;
- invalid priority fail-closed behavior;
- fifth-channel extension without rewriting the normalized source contract.

## Required invariant after correction

```text
Evidence binding decides WHAT may be claimed.
Channel policy decides WHAT FITS in the primary channel surface.
Fact priority decides ORDER OF ATTENTION, not truth.
Overflow strategy preserves verified claims without silent deletion.
```

## Safety boundary

The correction does not:

- weaken evidence requirements;
- auto-compress or paraphrase factual claims;
- add direct X posting;
- add X credentials or OAuth;
- publish the generated draft;
- treat the internal 260-codepoint budget as permanent platform truth.

## Current verdict

```text
BRIDGEPATCH_SALES_BLOCKERS: CLOSED
POST_ADAPTER_CORE_EVIDENCE_GATE: PASS
POST_ADAPTER_X_CHANNEL_POLICY: PASS
POST_ADAPTER_BRIDGEPATCH_DOGFOOD: PASS
EXTERNAL_POSTING: NOT_PERFORMED
NEXT_GATE: PR_REVIEW_AND_MERGE
```
