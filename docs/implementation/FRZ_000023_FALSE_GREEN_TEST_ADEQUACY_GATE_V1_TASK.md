# RTS-FRZ-000023 — False-Green Test Adequacy Gate v1

## Goal
Test whether the K1 validation surface can actually detect materially wrong behavior instead of merely reporting green.

## Core invariant
`TEST PASS != PROBLEM ABSENCE`.

A K1 result is test-adequate only when independent adversarial lanes show that the test surface can detect seeded semantic faults without treating harness crashes as successful kills.

## Required lanes
1. Known-bad injection corpus with explicit expected dispositions/invariants.
2. Critical mutation testing against K1 targeted tests.
3. Held-out cases not used to tune K1 heuristics.
4. Metamorphic properties where irrelevant representation changes preserve decisions and meaning-changing transformations change the expected result.
5. Harness controls: a behaviorally equivalent mutant must survive; invalid/import-breaking mutants are not counted as kills.

## Non-goals
- No claim that passing proves absence of all bugs.
- No provider/model execution.
- No mutation of K1 production files in-place.
- No semantic truth, execution, profile, promotion, Canon, or evidence-drop authority.

## Death conditions
- A critical valid mutant survives targeted tests.
- A known-bad case receives a normal/unsafe disposition.
- Import/syntax failure is counted as a mutation kill.
- Equivalent control mutant is killed.
- Held-out cases are silently excluded or reused as tuning fixtures.
- Metamorphic meaning-preserving transformation changes disposition unexpectedly.
- Meaning-changing adversarial transformation fails to change the required expectation.
- Adequacy is inferred only from mutation kill percentage or only from one lane.
- Any lane drops records or silently truncates failures.
