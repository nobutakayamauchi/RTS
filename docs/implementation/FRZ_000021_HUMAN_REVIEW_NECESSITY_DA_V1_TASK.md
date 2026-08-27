# RTS-FRZ-000021 — Adversarial Human Review Necessity Triage v1

## Goal

Take the unresolved review surface left by J and determine **why a human should or should not spend attention on each item** before any later model-assisted semantic proposer is introduced.

Each unresolved exact anchor is evaluated through two deliberately different lenses:

- **DA / retain-attention lens** — strongest plausible case that misreading or ignoring the item could alter operating strategy, transition classification, probe selection, or future model adaptation.
- **Counter-DA / defer-attention lens** — strongest plausible case that the item is non-actionable, marketing/navigation noise, redundant, or causally too remote to justify immediate human attention.

The two lenses are never averaged into false consensus. Their disagreement is itself a review signal.

## User-required decision axes

1. **Impact** — how large the operational consequence could be if this item is interpreted incorrectly or ignored.
2. **Causal reach** — whether the item can plausibly affect a later H/F/G decision even if it is not immediately actionable.
3. **Perspective gap** — whether DA and Counter-DA assign materially different importance, which increases the value of human adjudication.

## Output classes

- `HUMAN_NOW` — immediate human review is justified by high impact, high causal reach, or material perspective disagreement.
- `HUMAN_LATER` — relevant but not urgent; preserve in the review queue.
- `DEFER_LOW_VALUE` — both lenses support low immediate value; preserve evidence but do not consume current human attention.
- `REVIEW_BLOCKED` — input is incomplete/truncated/stale or cannot be safely triaged.

There is no automatic `DROP` authority in v1.

## Hard invariants

- exact source anchor and source identity are preserved;
- every unresolved J finding produces exactly one triage record;
- DA and Counter-DA outputs remain separately visible;
- high perspective disagreement can never be hidden by averaging;
- high causal reach can require human review even when immediate impact is low;
- marketing/noise signals cannot suppress an explicit execution-contract signal in the same anchor;
- any upstream truncation/incomplete intake fails closed;
- causal scores are heuristic/advisory, never measured probabilities;
- triage never creates a docs claim, model-behavior claim, hidden-architecture claim, execution authority, profile-application authority, promotion authority, or Canon authority.

## Destructive DA death conditions

1. A naive average of DA and Counter-DA scores downgrades a high-disagreement item.
2. An item with low immediate impact but a clear future migration/deprecation causal path is auto-deferred.
3. Marketing/noise wording causes a sentence containing an explicit execution-contract change to be auto-deferred.
4. Any unresolved J item disappears from triage output.
5. Upstream ambiguity truncation or stale fingerprint produces a normal triage result.
6. Triage output grants execution/profile/promotion authority.

## Live usefulness gate

Run current official OpenAI / Anthropic / Google docs through I → J → K0 and report:

- original J unresolved count;
- `HUMAN_NOW` count;
- `HUMAN_LATER` count;
- `DEFER_LOW_VALUE` count;
- `REVIEW_BLOCKED` count;
- DA/Counter-DA disagreement count;
- top causal-path categories.

Completion requires that the system differentiates attention priority without claiming that lower priority means semantic correctness.
