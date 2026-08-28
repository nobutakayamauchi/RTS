# METEOR RESULT — RTS-FRZ-000023

Date: 2026-08-28
Item: `RTS-FRZ-000023 False-Green Test Adequacy Gate v1`

## Scope

K2 validates the validator. It asks whether the K1 test surface can actually detect deliberately seeded semantic faults and independent held-out failures, rather than treating a green test run as proof that no problem exists.

Core invariant:

```text
TEST PASS != PROBLEM ABSENCE
```

K2 itself grants no semantic truth, execution, profile-application, promotion, Canon, or evidence-drop authority.

## Mandatory independent lanes

1. known-bad injection;
2. critical mutation testing against K1 targeted tests;
3. held-out cases not used to tune K1;
4. metamorphic properties;
5. mutation-harness controls.

No single percentage or lane can mask failure in another lane.

## Mutation validity boundary

A mutation counts as `KILLED` only when the mutated package first imports successfully and then K1 targeted behavioral tests fail.

- syntax/import failure => `INVALID_MUTANT`, not a kill;
- source-shape mismatch => `STALE_OPERATOR`, not silently skipped;
- equivalent/no-op control must survive;
- production K1 source hash must remain unchanged because mutations run in a temporary package copy.

## Initial destructive adequacy run

Initial K2 validation run `33129780597` failed at the adequacy baseline. That failure was investigated rather than normalized away.

Diagnostic run `33129849384` showed:

- 7 critical semantic mutants / 7 killed;
- equivalent control survived;
- invalid syntax control was classified invalid and did not count as a kill;
- production K1 source was unchanged;
- known-bad lane passed;
- metamorphic lane passed;
- held-out lane exposed two expectation mismatches.

One held-out mismatch (`legacy model identity`) was a fixture expectation error: K0 had already placed the case in a lower-priority class and K1 correctly preserved it as `WAIT_SAFE_DEFER` under the monotonicity boundary.

The second held-out mismatch was a real false green and remains preserved as finding `FRZ-000023-FG-001`.

## Real false-green finding — FRZ-000023-FG-001

Held-out anchor:

```text
A cost-efficient creative model is described for routine media drafts.
```

Expected K1 disposition:

```text
WAIT_SAFE_DEFER
```

Observed trace from run `33130122176`:

```text
K0 classification: HUMAN_NOW
K0 DA problem-solving paths: []
K0 Counter-DA problem-solving paths: []
        ↓
K1 second-pass recovered route:
RECALIBRATE_LIMIT_OR_BUDGET
        ↓
K1 disposition: AI_CONTINUE
```

This is a genuine cross-layer false green: catalog/product-description wording containing a cost cue is converted into active AI work even though the held-out expectation treats the sentence as low-priority descriptive material.

K2 does **not** repair completed K0/K1 production logic in-place. The finding is preserved for a separate governed repair after K2 closes.

## Why 7/7 mutation kill was still insufficient

The selected seven mutants covered important K1 branches:

- an open discriminating route incorrectly escalating;
- safe defer being ignored;
- human choice bypassing exhaustion evidence;
- pre-closure no-route search counting as exhaustion;
- duplicate probe replay being accepted;
- K1 heuristic recovery promoting K0 lower-priority work;
- closing a route that was never active.

All seven were killed by existing targeted K1 tests. Nevertheless, the independent held-out wording found a semantic boundary outside those selected mutation axes.

Therefore:

```text
7/7 MUTATION KILL != TEST ADEQUATE
```

This is the main K2 result.

## K2 self-DA

K2 initially trusted summary booleans such as `mutation_lane_pass` and `controls_pass`. A tampered report could therefore claim a green summary while underlying mutant rows contradicted it.

Repair run `33130076659` made K2 recompute mutation and lane truth from underlying evidence. Counter-DA passed after the repair.

K2 now rejects:

- a surviving critical mutant hidden behind `mutation_lane_pass=true`;
- a killed equivalent control hidden behind `controls_pass=true`;
- an invalid critical mutant counted as a kill;
- a failed held-out row hidden behind an `ADEQUATE` lane summary.

One intermediate repair workflow definition had invalid YAML and produced no jobs; it is excluded from semantic adequacy evidence and was replaced with a staged repository-local repair script. The temporary repair, diagnostic, finding, start, validation, and completion surfaces were removed after their evidence was folded into the persistent result.

## Persistent and FREEZER validation

Persistent A-K2 validation run `33130193219` passed K2 baseline/self-DA, K1 through A regressions, and FREEZER verification while K2 was in governed WIP.

Canonical completion run `33130235365` passed pre-completion validation, transitioned `RTS-FRZ-000023` through `VERIFIED -> COMPLETED`, passed post-completion validation, confirmed A-K2 `COMPLETED` with WIP clear, and committed only generated FREEZER completion state.

The permanent K2 workflow remains the cleaned-head validation surface after removal of temporary one-shot tooling.

## Current target adequacy state

The **K2 gate implementation is completed**, but the current K0/K1 target surface is intentionally:

```text
HOLD_FALSE_GREEN_RISK
```

because `FRZ-000023-FG-001` remains unresolved.

This distinction is mandatory:

```text
K2 COMPLETED != TARGET ADEQUATE
```

K2 completion means the false-green detector is implemented, adversarially tested, governed, and can correctly HOLD the target when a held-out failure survives. It does not certify K1 as bug-free.

## Current state

**COMPLETED / TARGET HOLD_FALSE_GREEN_RISK.**

Next repair, if authorized, belongs in a new FREEZER item and must address the cross-layer catalog/cost false-green without mutating the historical K2 result or pretending that 7/7 mutation kill proved adequacy.
