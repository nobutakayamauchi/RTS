# ONE SMALL STEP — Adaptive Progress Guidance Loop Specification v0.1

Date: **2026-08-14 JST**

Status: `PROVISIONAL / PRE-MERGE CANDIDATE`

## 1. Purpose

Provide a bounded guidance/evaluation contract that can take a person from **"I do not know what to do"** toward a meaningful next action while preserving evidence, partial progress, learning, and restartability.

The system is specifically designed not to assume that a person has stable capacity, a correct initial goal, a valid metric, enough evidence to explain success/failure, or one universally correct way to live.

ONE SMALL STEP does **not** define the right life for a person. It helps make the person's own choices more informed, more reversible where possible, more evidence-aware, and more likely to become choices the person can continue to own as circumstances and values change.

## 2. Non-goals

v0 is not:

- a universal life planner;
- a source of a single correct way to live;
- a system that turns the user's current choice into unquestioned doctrine;
- a guarantee of a regret-free outcome;
- a therapist or clinical decision system;
- an automated employment decision system;
- a personality classifier;
- an LLM runtime;
- a task scheduler;
- a browser/search platform;
- an autonomous action engine;
- a truth oracle for causality.

## 3. Canonical flow

```text
ORIENT
  SELF_PROFILE
  RESOURCE_MAP
  BRAIN_DUMP
  CURRENT_STATE
→ PAIN_AND_GOAL_DISCOVERY
→ TEMPORARY_GOAL
→ MEASURE
→ LIGHT
→ CHOICE_REVIEW WHEN MATERIAL
→ ONE_SMALL_STEP
→ ACT
→ TRACE
→ EVALUATE
→ REFINE
→ EXPERIENCE
→ NEXT_LIGHT
→ repeat
```

### 3.1 No-capacity branch

```text
CAPACITY=NONE or DO_NOT_PUSH
→ PRESERVE_AND_RESTART
→ CHECKPOINT_ONLY
```

The system must not convert inability to act into a moral or productivity failure.

## 4. Orientation contract

A fully lost user starts with current reality, not a grand goal.

Minimum orientation fields:

- capabilities;
- constraints;
- current state;
- usable resources;
- unstructured brain dump.

Unknown and omitted facts remain unknown. Sensitive self-disclosure is not required merely to satisfy schema completeness; an implementation may explicitly record `UNKNOWN`/`DECLINED` rather than forcing disclosure.

## 5. Goal contract

Goals are mutable hypotheses.

States:

- `EXPLORING`
- `HYPOTHESIS`
- `CONFIRMED`
- `INVALIDATED`

`SUNK EFFORT != GOAL AUTHORITY`

An invalidated goal reopens pain/need discovery.

The first useful goal may simply reduce the user's most immediate pain or blocker. The system optimizes for movement toward a better state, not loyalty to the first wording of the goal.

## 5.1 Choice autonomy and informed-ownership contract

ONE SMALL STEP must not present a universal answer to how a person should live. Different people may rationally value different gains, accept different losses, and choose different paths under the same external facts.

For a material choice, the system should make visible at minimum:

- the person's stated values or priorities relevant to the choice;
- expected gains or possibilities;
- accepted costs or losses;
- credible alternatives;
- reversibility;
- severe or irreversible downside risk;
- counterevidence or conditions that would justify stopping/changing course.

The canonical decision owner remains the user/human. The system may challenge the reasoning, surface alternatives, identify missing evidence, or refuse to normalize unresolved severe/irreversible harm as an ordinary next step; it does not certify one life path as universally correct.

`USER CHOICE != SYSTEM ENDORSEMENT`

`USER CHOICE != CONFIRMATION-ONLY ANALYSIS`

A previously chosen path remains challengeable. Sunk cost, identity, pride, or earlier commitment do not create authority to continue when material evidence changes.

The system does not promise "no regret." Its narrower objective is to reduce **avoidable regret caused by missing information, hidden trade-offs, unexamined alternatives, or preventable catastrophic downside**, while helping the user retain ownership of the final choice.

### 5.1.1 Safety boundary

Low-consequence, reversible choices must not be buried in a full life-review process.

For material/high-stakes choices, unresolved severe or irreversible harm is not routed as a normal action step. The next step becomes reducing irreversibility, gathering discriminating evidence, finding a smaller bounded experiment, or obtaining qualified external review where the domain requires it.

`AUTONOMY != NORMALIZE CATASTROPHIC RISK`

`SAFETY REVIEW != LIFE DECISION AUTHORITY`

## 6. Measurement contract

A goal should have an observable success measure before effort can be strongly evaluated.

Metric validity is itself challengeable:

- `UNKNOWN`
- `HYPOTHESIS`
- `SUPPORTED`
- `VERIFIED`
- `INVALID`

A provisional metric may guide an experiment, but cannot certify strong outcome progress.

`METRIC MOVED != REAL GOAL MOVED`

## 7. Step contract

A meaningful step may be small, but it may not be unbounded.

When a concrete `step_plan` exists it should contain:

- `action` — what will be done;
- `expected_signal` — what result would be informative;
- `review_boundary` — when to stop and evaluate;
- `stop_or_change_rule` — what result triggers a method change, pause, or reframe.

This prevents endless effort from being mistaken for commitment.

## 8. Effort vs effect

The system may acknowledge effort without certifying its usefulness.

`EFFORT DESERVES RECOGNITION`

`EFFORT DOES NOT CREATE EFFECT`

If effort is present but no supported progress axis moves, the evaluator returns `EFFORT_EFFECT_GAP` and the method or measurement must be reconsidered before simply increasing volume.

## 9. Progress axes

Progress is multi-axis:

1. `outcome`
2. `capability`
3. `knowledge`
4. `uncertainty_reduction`
5. `risk_reduction`
6. `preservation`

A final goal can fail while meaningful capability/knowledge progress is real.

## 10. Failure analysis contract

Failure analysis starts from evidence and reconstruction:

```text
INTENDED
→ ACTUAL ACTION
→ OBSERVED EVENT
→ EXPECTED/OBSERVED GAP
→ EVIDENCE
→ CAUSE HYPOTHESIS
→ PREVENTION METHOD
→ PREVENTION TEST
```

Allowed cause confidence:

- `UNKNOWN`
- `HYPOTHESIS`
- `SUPPORTED`
- `VERIFIED`

Unknown cause labels fail closed.

`FAILURE OBSERVED != CAUSE KNOWN`

When the cause is unknown, the next step is evidence collection or a discriminating experiment, not a confident story.

## 11. Success analysis contract

Success is refined by measurement, explanation, reproduction, transfer, and retention.

Gold Success requires:

- measured outcome;
- explanation;
- verified personal reproduction;
- verified transfer reproduction;
- reusable method;
- boundary conditions;
- evidence reference(s).

A lucky or one-off success remains a lower Success level.

## 12. Failure Gold Experience

Gold Failure requires a repeat-prevention method that has survived a test and is tied to verified causal evidence plus retained evidence references.

A prevention technique that appears to work but does not validate the claimed cause remains `FAILURE_5`, not Gold.

## 13. Gold revocation

Gold is evidence status, not a permanent title.

Any contradictory evidence or regression reopens the experience as:

`EXPERIENCE_REVIEW_REQUIRED`

## 14. External blockers

External blockage is not proof of insufficient effort.

The system asks:

1. Must the blocker actually be removed?
2. Can the goal be reached with substitute evidence?
3. Is there a bypass or delegation route?
4. Should the goal be reframed?
5. Is preservation/waiting the correct next state?

## 15. Restartability

Stopping is classified before it is corrected.

Possible stop causes include avoidable friction, depleted capacity, external dependency, safety, deliberate pause, or goal invalidation.

The design target is:

> **Not "never stop". "Never lose the place you reached."**

## 16. Human-development use

For training/coaching, evaluate observable learning behavior and task performance, not fixed personality labels.

Examples of useful learning-profile evidence:

- needs overview before detail;
- benefits from worked examples;
- needs written vs spoken instruction;
- freezes under ambiguous instructions;
- benefits from frequent vs delayed feedback.

MBTI/typology-like labels may be user-supplied context but are not authoritative routing evidence.

A manager/trainer should be evaluated too: if an intervention did not work, the training hypothesis is also challengeable.

## 17. Cause vs accountability

`CAUSE_ANALYSIS != ACCOUNTABILITY_DECISION`

Analyze contributing conditions first. Accountability may then be considered separately with appropriate evidence, authority, and context.

## 18. Evaluation-depth rule

Evaluation cost should scale with risk, irreversibility, and consequence. A five-minute low-risk task should not require a thirty-minute postmortem.

v0 leaves depth selection to the calling layer; future versions may formalize risk tiers.

## 19. Acceptance scenarios

v0 must handle at minimum:

A. user does not know what to do;
B. goal exists but first step is unclear;
C. high effort, low/no outcome;
D. fear prevents trying;
E. failure with unknown cause;
F. success with unknown/non-reproducible cause;
G. goal missed despite intermediate growth;
H. stopped and later resumed;
I. external blocker;
J. trainer onboarding a learner;
K. success method being transferred;
L. organization preventing repeated failure;
M. material personal choice with different gains/losses depending on the user's values;
N. high-stakes or irreversible choice with unresolved severe downside risk.

## 20. Hard invariants

`PERSON != FAILURE MODE`

`EFFORT != EFFECT`

`GOAL != PERMANENT`

`METRIC != TRUTH`

`SYSTEM != UNIVERSAL LIFE AUTHORITY`

`USER CHOICE != SYSTEM ENDORSEMENT`

`CHOICE SUPPORT != CHOICE OWNERSHIP`

`INFORMED CHOICE != GUARANTEED NO REGRET`

`MATERIAL SEVERE/IRREVERSIBLE RISK != NORMAL NEXT STEP`

`FAILURE != EXPERIENCE UNTIL USABLE LEARNING REMAINS`

`SUCCESS != GOLD UNTIL REPRODUCIBLE + TRANSFERABLE + RETAINED`

`FAILURE != GOLD UNTIL REPEAT-PREVENTION IS VERIFIED`

`UNKNOWN != EXPLANATION`

`GOLD != PERMANENT`

`STOPPED != LOST`

`GOOD EVALUATION -> NEXT STEP OR EXPLICIT PRESERVE/UNKNOWN/SAFETY STATE`
