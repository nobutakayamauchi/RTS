# METEOR RESULT — RTS-FRZ-000024

Date: 2026-08-28  
Item: `RTS-FRZ-000024 Catalog Cost False-Green Repair v1`

## Why this item exists

K2 (`RTS-FRZ-000023`) was created because a zero-failure result is not evidence of a literal zero defect rate.

Core quality invariant:

```text
0 observed defects != 0% defect probability
```

The K2 held-out lane then found a real false green, `FRZ-000023-FG-001`:

```text
A cost-efficient creative model is described for routine media drafts.
```

Before this repair:

```text
K0 classification          = HUMAN_NOW
K0 problem-solving paths   = []
K1 recovered route         = RECALIBRATE_LIMIT_OR_BUDGET
K1 disposition             = AI_CONTINUE
expected disposition       = WAIT_SAFE_DEFER
```

The historical finding remains preserved. FRZ-000024 does not rewrite the fact that K0/K1 previously produced that false green.

## Root cause

The defect had two independent layers.

### K0 over-classification

`limits_usage` treated bare `cost` wording as a potentially concrete operational signal. The catalog sentence also contained performance-positioning language, but did not match the bounded descriptive-capability patterns. As a result, K0 assigned too much causal reach and classified the descriptive sentence as `HUMAN_NOW`.

### K1 over-recovery

K1 second-pass recovery accepted a bare `cost` token as enough to manufacture `RECALIBRATE_LIMIT_OR_BUDGET`, turning descriptive catalog text into active AI work.

Fixing only K1 would have changed the case from `AI_CONTINUE` to `HUMAN_CANDIDATE`, which would still be the wrong attention allocation. Therefore the smallest complete repair required bounded changes in both K0 descriptive recognition and K1 operational-cost route recovery.

## Repair

### K0

Descriptive patterns now recognize bounded catalog/positioning forms such as:

- `cost-efficient`, `cost-effective`, `cost-optimized`, `price-friendly`;
- a model/engine/product described, positioned, marketed, or presented as/for a use;
- `described/positioned/marketed/presented for ...`.

These forms do not by themselves become a concrete operational contract.

### K1

Bare `cost` or `price` wording no longer opens `RECALIBRATE_LIMIT_OR_BUDGET`.

The route is retained for explicit operational pricing/billing language and for price/cost text coupled to observable operational context such as:

- amount/currency;
- per-unit pricing;
- increase/decrease/change;
- budget, cap, or limit.

This is a boundary repair, not a literal special case for the FG-001 sentence.

## Counter-DA: avoid the opposite false negative

The following operational controls still recover `RECALIBRATE_LIMIT_OR_BUDGET` after the repair:

```text
Pricing for input tokens is $5 per million tokens.
API cost increases from $5 to $7 per million tokens.
Billing changed and the budget cap must be recalibrated before rollout.
The token price is 7 USD per million input tokens.
```

So the repair does not solve the false positive by globally suppressing pricing/cost work.

## Post-repair result

Resolution evidence in `docs/implementation/frz000024_resolution.json` records:

```text
K0 classification                = HUMAN_LATER
K0 explicit contract signal      = false
K0 DA problem-solving paths      = []
K0 Counter-DA paths              = []
K1 recovered escape routes       = []
K1 residual routes               = []
K1 disposition                   = WAIT_SAFE_DEFER
```

FG-001 is therefore resolved without changing its held-out expected outcome.

## An important secondary failure during repair

The first candidate repair exposed a stale test oracle: an older K1 DA test explicitly expected low-cost catalog wording to recover a budget route even while remaining deferred. That expectation represented the behavior now being repaired and was corrected.

After that correction, K0 and K1 regressions passed, but K2 still stopped the repair because mutation M06 (`LOW_PRIORITY_HEURISTIC_PROMOTION`) survived.

The old low-cost test had also been the effective sentinel proving that K1 cannot promote a lower-priority K0 item merely because second-pass recovery finds a route. Removing the bare cost route accidentally removed that sentinel.

The production repair was not reverted. Instead, the M06 oracle was restored with an independent lower-priority identity case:

```text
Legacy models remain available during a transition window;
map the effective model identity before assuming equivalent behavior.
```

Normal behavior:

```text
K0 lower priority
K1 can recover MAP_ENGINE_IDENTITY_CATALOG
but active recovery is suppressed
=> WAIT_SAFE_DEFER
```

Under M06, lower-priority suppression is removed and the test fails. M06 is therefore killed again.

This yields another quality invariant:

```text
fixing a defect can reduce detector sensitivity
```

Repair validation must therefore test both the repaired behavior and continued ability to detect seeded faults.

## K2 after repair

Post-repair K2 evidence:

```text
critical mutants       7 / 7 KILLED
mutation lane          PASS
harness controls       PASS
known-bad lane         PASS
held-out lane          PASS
metamorphic lane       PASS
production source      unchanged by mutation harness
status                 ADEQUATE
```

Equivalent control still survives. Invalid syntax control remains `INVALID_MUTANT` and does not count as a kill.

## What ADEQUATE means

`ADEQUATE` is deliberately bounded:

```text
ADEQUATE = no failure detected by the currently defined K2 mandatory lanes
ADEQUATE != literal zero defect probability
```

It does not prove that no unknown semantic boundary remains anywhere in the system.

In quality-control terms, the result is now closer to:

> The current sample passed, and the inspection system still detects all currently seeded critical defects.

—not:

> The manufacturing process has a 0% defect rate.

For a simple independent binomial thought experiment, even observing zero defects in 76 samples would not imply a 0% population rate; the common “rule of three” gives a rough 95% upper bound near `3/76 ~= 3.9%`. That approximation is not an RTS defect-rate estimate because RTS cases are not assumed to be independent random production samples. It is included only to make the zero-observation distinction explicit.

## Verification history

- governed start first attempt `33131318153`: failed safely on invalid Build Assessment reuse-mode enum; no WIP commit landed;
- governed start repaired run `33131410344`: SUCCESS, FRZ-000024 entered governed WIP;
- first bounded repair run `33131591658`: K0 PASS, K1 FAIL on stale low-cost oracle; no repair commit landed;
- K1 diagnostic `33131627629`: confirmed FG-001 and all operational pricing controls behaved correctly under the candidate repair;
- second repair run `33131800051`: K0/K1 PASS, K2 stopped on M06 survivor (6/7); no repair commit landed;
- K2 diagnostic `33131839612`: confirmed M06 was the sole critical survivor;
- final bounded repair run `33131933464`: K0 PASS, K1 PASS, K2 PASS, FG-001 resolution assertion PASS, repair committed;
- post-repair evidence run `33131992451`: resolution evidence generated from the committed repair;
- persistent A-K2 full-stack run `33132084820`: SUCCESS;
- canonical FREEZER completion run `33132138773`: pre-validation SUCCESS, `VERIFIED -> COMPLETED`, post-validation SUCCESS, completion committed;
- temporary start/repair/diagnostic/evidence/completion workflows, repair script, and diagnostic dumps removed after completion.

## Authority boundary

The repair grants no authority for:

- execution;
- profile application;
- promotion;
- Canon mutation;
- semantic truth declaration.

All remain `NONE`.

## Final state

```text
RTS-FRZ-000024              = COMPLETED
FRZ-000023-FG-001            = RESOLVED by bounded repair
K2 current defined lanes     = ADEQUATE
critical mutation detection  = 7 / 7
zero defect claim            = FALSE
WIP                           = CLEAR
```

**COMPLETED / bounded adequacy restored.**

The next model or corpus should still be treated as a new sample. A future zero-failure result remains a trigger to ask whether the detector has enough independent coverage, not permission to infer a permanent 0% defect rate.
