# ONE SMALL STEP v0.1 — METEOR Addendum: Fear / Risk Gate

Date: **2026-08-14 JST**

Status: `SURVIVES / PRE-MERGE CANDIDATE`

A final implementation-to-spec DA found one uncovered acceptance path after the original 21-test suite: a person who is afraid to try could reach the general next-step route without an explicit risk-decomposition gate.

This was treated as an implementation gap, not deferred as motivational copy.

## Added contract

`fear_gate.py` runs only before an unstarted action and only after earlier core gates (orientation, capacity preservation, goal validity, measurement, and external blocker review) have cleared.

Unbounded fear requires four explicit fields:

- feared loss;
- reversibility;
- cost of inaction;
- bounded experiment.

If they are missing, the system returns:

`RISK_BOUNDING -> DECOMPOSE_FEAR_AND_BOUND_RISK`

It does not return "be brave", "try harder", or a personality judgment.

If the risk has been bounded and the underlying step already has an expected signal, review boundary, and stop/change rule, the small experiment may proceed.

## Exact tests

- unbounded fear routes to risk decomposition;
- bounded fear may proceed to a one-step experiment.

The two tests were replayed against the exact pre-gate core behavior represented by the repository implementation and passed **2/2** locally.

Combined current local validation of the repository core workload plus this acceptance extension:

- original baseline + METEOR: **21/21 PASS**;
- fear/risk extension: **2/2 PASS**;
- total repository-intended acceptance workload: **23/23 PASS**.

## Invariant

`FEAR != CHARACTER FLAW`

`UNBOUNDED FEAR != COMMAND TO ACT`

`BOUNDED REVERSIBLE EXPERIMENT MAY BECOME THE NEXT SMALL STEP`
