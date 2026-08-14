# ONE SMALL STEP v0.1

Status: `PROVISIONAL / PRE-MERGE CANDIDATE / METEOR-SURVIVED-UNDER-CURRENT-EVIDENCE`

Formal name: **Adaptive Progress Guidance Loop**

Common name: **ONE SMALL STEP**

Tagline: **A light for the next step.**

ONE SMALL STEP is a thin, evidence-aware guidance contract for people who do not know what to do next, cannot reliably sustain full capacity, or are working hard without knowing whether the effort is actually moving them toward a better state.

It does not promise a perfect life plan or claim one correct way to live. It makes the current state visible, treats goals as revisable hypotheses, turns work into bounded experiments, separates effort from effect, surfaces trade-offs and alternatives for material choices, and requires evaluation to produce a next step whenever the evidence supports one.

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
→ CHOICE REVIEW WHEN MATERIAL
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

## Choice / autonomy rule

ONE SMALL STEP does not tell a person how they must live. Different people may value different outcomes, accept different losses, and rationally choose different paths from the same facts.

For a material choice, the system helps expose:

- what matters to the person;
- what the choice may make possible;
- what it may cost;
- credible alternatives;
- reversibility;
- severe or irreversible downside risk;
- evidence or outcomes that should trigger reconsideration.

The system may challenge the reasoning, but the final choice remains the user's unless an external law, safety rule, professional boundary, or other legitimate authority governs the action.

`SYSTEM != UNIVERSAL LIFE AUTHORITY`

`USER CHOICE != SYSTEM ENDORSEMENT`

`CHOICE SUPPORT != CHOICE OWNERSHIP`

It also does not promise a regret-free future. The narrower aim is to reduce avoidable regret caused by missing information, hidden trade-offs, unexamined alternatives, or preventable catastrophic downside.

If a material/high-stakes choice still carries unresolved severe or irreversible harm, the normal action route pauses. The next step becomes a smaller reversible experiment, more evidence, or qualified external review rather than a confident life directive.

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

Fear is not treated as a character flaw or a command to "be brave". Before an unstarted action, `fear_gate.py` requires the feared loss, an explicitly reversible bounded experiment, cost of inaction, and—when a concrete action exists—an exact binding between that action and the bounded experiment. Earlier gates such as orientation, capacity preservation, invalid goal, measurement repair, external blockers, and material-choice safety review remain dominant.

`UNBOUNDED FEAR != COMMAND TO ACT`

`BOUNDED EXPERIMENT != AUTHORITY FOR A LARGER ACTION`

`BOUNDED REVERSIBLE EXPERIMENT MAY BECOME THE NEXT SMALL STEP`

## Scope

The v0 core is deliberately small. `one_small_step.py` is the pure evaluator/router, `choice_gate.py` adds material-choice autonomy/safety review, `fear_gate.py` adds bounded pre-action fear decomposition, and `guidance.py` is the canonical entrypoint that composes them. They do not:

- provide medical, legal, financial, or employment decisions;
- diagnose a person;
- define one correct life path;
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
python -m unittest -v test_one_small_step.py test_meteor_one_small_step.py test_choice_gate.py test_fear_gate.py test_guidance.py test_review_regressions.py
```

Current branch-equivalent pre-merge replay: **39/39 PASS**.

## Canonical records

- `SPEC.md` — current contract and invariants.
- `GOAL_RESULT_V0_1.md` — `/goal` scope/destruction result.
- `DA_COUNTER_DA_2026-08-14.md` — adversarial design review.
- `DA_COUNTER_DA_CHOICE_AUTONOMY_2026-08-14.md` — autonomy, confirmation-bias, regret, and severe-risk review.
- `METEOR_RESULT_2026-08-14.md` — destructive test record and retained deaths.
- `METEOR_ADDENDUM_FEAR_GATE_2026-08-14.md` — fear/risk acceptance extension.
- `METEOR_ADDENDUM_CHOICE_AUTONOMY_2026-08-14.md` — material-choice autonomy/safety extension.
- `METEOR_ADDENDUM_REVIEW_REGRESSIONS_2026-08-14.md` — Codex review deaths, repairs, and permanent regression memory.

## Provisional verdict

The current thin evaluator survives the frozen v0 workload under current evidence. It is not a complete coaching product, not a universal human evaluation theory, not a universal answer to how to live, and not permanently immune from challenge.
