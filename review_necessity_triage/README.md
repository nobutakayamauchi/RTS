# Review Necessity Triage v1

`review_necessity_triage` consumes a valid J semantic-refinement report and ranks **human attention**, not semantic truth.

For every unresolved J finding it preserves the exact source anchor and produces two separately inspectable cases:

- `RETAIN_ATTENTION_DA_V1` — strongest bounded case for why ignoring or misreading the finding could matter.
- `DEFER_ATTENTION_COUNTER_DA_V1` — strongest bounded case for why the finding may be non-actionable, noisy, redundant, or safe to schedule later.

The lenses score different questions and are never averaged into hidden consensus.

## Required axes

- `impact`: immediate operational consequence if wrong/ignored, 0..5.
- `causal_reach`: plausible downstream reach into H/F/G or engine-routing decisions, 0..5. This is a heuristic path score, **not a measured probability**.
- `perspective_gap`: absolute difference between the lenses' human-review-importance estimates, 0..5. Material disagreement increases review priority.

## Classes

- `HUMAN_NOW`
- `HUMAN_LATER`
- `DEFER_LOW_VALUE`
- `REVIEW_BLOCKED`

There is no automatic `DROP` authority.

## Hard boundary

Triage does not create or verify documentation claims, infer hidden model architecture, execute a provider/model, apply an engine profile, mutate runtime routing, promote memory, or grant Canon authority. All authority fields remain `NONE`.
