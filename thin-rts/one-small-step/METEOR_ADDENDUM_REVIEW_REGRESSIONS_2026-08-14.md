# ONE SMALL STEP v0.1 — METEOR Addendum: PR Review Regressions

Date: **2026-08-14 JST**

Status: `REVIEW_FINDINGS_REPAIRED / REGRESSIONS_RETAINED / MERGE-CANDIDATE`

Codex PR review identified four material failure modes after the initial pre-merge candidate was marked ready.

## Death 1 — bounded fear experiment could authorize a larger action

Original failure class:

`BOUNDED_EXPERIMENT != AUTHORIZED_ACTION_BOUND`

A small declared experiment could coexist with an unrelated larger `step_plan.action`, and an irreversible experiment could still pass when the four fear fields were merely non-empty.

Repair:

- fear-gate normal passage now requires `reversibility=REVERSIBLE`;
- when `step_plan.action` exists it must exactly match `fear.bounded_experiment`;
- mismatch or irreversible risk returns `RISK_BOUNDING`.

Permanent regression cases:

- irreversible fear experiment fails closed;
- bounded experiment cannot authorize a larger unrelated action.

## Death 2 — goal success definition could masquerade as observed measure

Original failure class:

`SUCCESS_MEASURE_DEFINITION != OBSERVED_SUCCESS_MEASUREMENT`

Repair:

Gold-success maturity no longer falls back from `attempt.measure` to the goal's `success_measure`. Success maturity advances only from an observed attempt-level measure.

Permanent regression:

- a success with explanation/reproduction/transfer/method/evidence but no observed attempt measure remains `SUCCESS_1`, not Gold.

## Death 3 — null evidence reference could become the string "None"

Original failure class:

`STRINGIFIED_NULL != EVIDENCE_REFERENCE`

Repair:

`_evidence_refs` now accepts only actual non-empty strings. Arbitrary JSON values are not stringified into apparent evidence.

Permanent regressions:

- `[null]` cannot grant Gold Success;
- `[null]` cannot grant Gold Failure.

## Death 4 — string "false" could become boolean True

Original failure class:

`TRUTHY_STRING != PROGRESS`

Repair:

Progress axes accept JSON booleans only. Non-boolean values become false for progress accounting and add `INVALID_PROGRESS_VALUE`, preserving fail-closed behavior and the effort/effect gap.

Permanent regression:

- `"outcome": "false"` cannot certify outcome progress or suppress `EFFORT_EFFECT_GAP`.

## Final local replay

The current branch-equivalent test composition was replayed after all review repairs:

- baseline: **9/9 PASS**;
- original destructive METEOR: **12/12 PASS**;
- choice/autonomy gate: **6/6 PASS**;
- fear/risk gate including review deaths: **4/4 PASS**;
- canonical guidance routing: **4/4 PASS**;
- PR review regressions: **4/4 PASS**;
- total: **39/39 PASS**.

Python syntax compilation for the evaluator and composed gates also passed.

## Verdict

`39/39 PASS`

`KNOWN REVIEW DEATHS RETAINED AS REGRESSION MEMORY`

`MERGE-CANDIDATE UNDER CURRENT EVIDENCE`
