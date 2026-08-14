# ONE SMALL STEP v0.1

Status: `PROVISIONAL / PRE-MERGE CANDIDATE / METEOR-SURVIVED-UNDER-CURRENT-EVIDENCE`

Formal name: **Adaptive Progress Guidance Loop**

Common name: **ONE SMALL STEP**

Tagline: **A light for the next step.**

ONE SMALL STEP is a thin, evidence-aware guidance contract for people who do not know what to do next, cannot reliably sustain full capacity, or are working hard without knowing whether the effort is actually moving them toward a better state.

It does not promise a perfect life plan. It makes the current state visible, treats goals as revisable hypotheses, turns work into bounded experiments, separates effort from effect, and requires evaluation to produce a next step whenever the evidence supports one.

## Core idea

```text
SELF PROFILE
→ RESOURCE MAP
→ BRAIN DUMP
→ CURRENT STATE
→ PAIN / NEED
→ TEMPORARY GOAL
→ MEASURE
→ LIGHT
→ ONE SMALL STEP
→ ACT
→ TRACE
→ EVALUATE
→ REFINE
→ EXPERIENCE
→ NEXT LIGHT
```

If the person cannot act now:

```text
NO CAPACITY / DO NOT PUSH
→ PRESERVE CURRENT STATE
→ CREATE RESTART POINT
→ RESUME LATER WITHOUT STARTING OVER
```

Stopping is not automatically failure. The system optimizes for **restartability**, not endless motion.

## Experience rule

> **場数や経験年数が経験なのではない。その後も使える形で残ったものが経験である。**

Operational form:

> **Experience is what remains usable.**

### Success path

A success is not Gold merely because the outcome was good.

```text
SUCCESS_1  outcome happened
SUCCESS_2  outcome can be measured and explained
SUCCESS_3  the person can reproduce it
SUCCESS_4  another person can reproduce it through transfer/training
GOLD       evidence-backed reusable method + boundary conditions are retained
```

### Failure path

A failure is not Gold merely because someone suffered through it.

```text
FAILURE_1  failure happened
FAILURE_2  failure is observed/measured
FAILURE_3  a cause hypothesis exists
FAILURE_4  a prevention method exists
FAILURE_5  the prevention method survives a test
GOLD       verified cause + retained evidence establish a repeat-prevention method
```

A Gold Experience is revocable when new evidence contradicts it.

## Human rule

`BREAK THE THEORY, NOT THE PERSON.`

The evaluator separates causal analysis from accountability. It does not turn a process failure into a personality judgment, and it does not erase legitimate responsibility merely because the analysis is blameless.

## Progress rule

Goal completion is not the only valid progress axis.

ONE SMALL STEP can retain:

- outcome progress;
- capability progress;
- knowledge gained;
- uncertainty reduced;
- risk reduced;
- preservation/restartability gained.

`GOAL NOT REACHED != NO PROGRESS`

`EFFORT SPENT != PROGRESS PROVEN`

## Fear / risk rule

Fear is not treated as a character flaw or a command to "be brave". Before an unstarted action, `fear_gate.py` can require the feared loss, reversibility, cost of inaction, and a bounded experiment. Earlier gates such as orientation, capacity preservation, invalid goal, measurement repair, and external blockers remain dominant.

`UNBOUNDED FEAR != COMMAND TO ACT`

`BOUNDED REVERSIBLE EXPERIMENT MAY BECOME THE NEXT SMALL STEP`

## Scope

The v0 core is deliberately small. `one_small_step.py` is the pure evaluator/router, `fear_gate.py` adds bounded pre-action risk decomposition, and `guidance.py` is the canonical entrypoint that composes them. They do not:

- provide medical, legal, financial, or employment decisions;
- diagnose a person;
- use personality typologies as decision authority;
- crawl the web;
- store private profiles;
- act as an employee surveillance or ranking system;
- send messages, spend money, hire/fire, or take external action;
- claim that an AI-generated causal story is evidence.

AI or human reasoning may supply structured inputs around the evaluator. External systems may own search, storage, communication, calendars, evidence collection, and action execution.

## Run

Use the composed entrypoint for normal execution so acceptance gates are not bypassed:

```bash
python guidance.py example_case.json
python -m unittest -v test_one_small_step.py test_meteor_one_small_step.py test_fear_gate.py test_guidance.py
```

Current locally replayed repository-intended workload: **25/25 PASS**.

## Canonical records

- `SPEC.md` — current contract and invariants.
- `GOAL_RESULT_V0_1.md` — `/goal` scope/destruction result.
- `DA_COUNTER_DA_2026-08-14.md` — adversarial design review.
- `METEOR_RESULT_2026-08-14.md` — destructive test record and retained deaths.
- `METEOR_ADDENDUM_FEAR_GATE_2026-08-14.md` — final fear/risk acceptance extension.

## Provisional verdict

The current thin evaluator survives the frozen v0 workload under current repository evidence. It is not a complete coaching product, not a universal human evaluation theory, and not permanently immune from challenge.
