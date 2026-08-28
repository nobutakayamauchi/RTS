# False-Green Test Adequacy Gate v1

K2 validates the **ability of the K1 test surface to detect faults**. It does not claim that green tests prove bug absence.

## Residual-defect quality doctrine

K2 treats a zero-failure observation as a property of the **current sample and current detector**, not as proof of a literal zero defect probability.

```text
0 observed defects != 0% defect probability
TEST PASS          != defect absence
ADEQUATE           != zero-defect certification
```

In an open-world, adaptive system, better design, better tooling, better models, better procedures, and better tests can drive observed defect rates lower and lower. They do not justify silently collapsing residual unknown risk to exactly zero.

A run with no detected defect is therefore allowed to increase confidence, but it must not erase the possibility of:

- a defect outside the sampled surface;
- a defect outside the currently modeled failure modes;
- a detector blind spot;
- a stale or overfit oracle;
- a repair that accidentally reduces detector sensitivity.

This is an operational quality invariant, not a claim that a statistical defect rate can be inferred from the RTS corpus. RTS cases are not assumed to be independent random production samples.

## Mandatory independent lanes

- known-bad injection;
- critical mutation testing;
- held-out cases;
- metamorphic properties;
- mutation-harness controls.

These lanes exist because a detector can look healthy while missing a different class of defect. Passing one lane cannot compensate for failing another.

## Mutation rules

Mutation rules are fail-closed:

- a critical mutant must match the source exactly once;
- it must import successfully before it can be counted as a behavioral kill;
- syntax/import failure is `INVALID_MUTANT`, not `KILLED`;
- an equivalent/no-op control must survive;
- mutation execution happens in a temporary package copy and the production K1 source hash must remain unchanged.

## Repair must preserve inspection sensitivity

A defect repair is not complete merely because the original failing case turns green.

After a repair, K2 must also re-check that the inspection system still detects the seeded faults it detected before the repair. A repair that fixes behavior while causing a critical mutant to survive is not an adequate repair.

```text
fixing a defect can reduce detector sensitivity
```

The FRZ-000024 repair demonstrated this directly: the original false green was corrected, but mutation `M06_LOW_PRIORITY_HEURISTIC_PROMOTION` temporarily survived because the old sentinel had been removed with the defective behavior. The production repair was kept, while an independent sentinel restored detection of M06.

## Meaning of ADEQUATE

`ADEQUATE` requires every currently mandatory lane to pass. A high mutation-kill percentage cannot mask a failed held-out, known-bad, metamorphic, or harness-control lane.

The term is deliberately bounded:

```text
ADEQUATE = no failure detected by the currently defined mandatory K2 lanes
ADEQUATE != literal zero defect probability
```

The next model, corpus, provider surface, architecture generation, or materially different operating condition is a new sample surface. A future zero-failure result remains a reason to ask whether independent detector coverage is sufficient, not permission to infer permanent zero risk.

## Authority boundary

K2 has no semantic truth, execution, profile-application, promotion, Canon, or evidence-drop authority.
