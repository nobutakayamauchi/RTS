# Operator–Machine Development Hypothesis v0.1

Status: `/goal` PROVISIONAL CONCLUSION UNDER CURRENT EVIDENCE — NOT PROMOTED

## Question

What was the human actually doing over time, what was delegated to AI/Codex/Kernel, and how much machine work followed each human judgment?

Raw commit count cannot answer this after automation. The evidence requires separate human-load, human-hinge, governed-stage, machine-output, and return-time layers.

## Canonical human load

For project `p` and window `W`:

`L[p,W] = (E, J, O, R, X)`

where `E` is direct execution/intervention evidence, `J` decision load, `O` orchestration, `R` rework/adversarial repair, and `X` within-session context switching.

The existing saturated `OLT_100` scalar remains secondary. Unknown axes remain UNOBSERVED, not semantic zero.

## Human hinge -> machine lineage

For a human decision hinge `h_i` and machine stage `s_j`, a STRONG binding requires:

1. `time(s_j) > time(h_i)`;
2. semantic agreement with the human decision;
3. patch/content evidence supporting the agreement.

Timestamp proximity alone is insufficient. A semantically attractive stage that occurred before the hinge is rejected.

Let `S_W` be the count (or confidence-weighted count) of machine stages bound to human decisions in window `W`.
Let `Y_W` be machine-visible output in an explicitly named unit. Commits may be used only as an output proxy, never as human-effort units.

## Primary hypothesis equation

Human-to-machine visible-output amplification is factorized as:

`Lambda_W = Y_W / J_W = (S_W / J_W) * (Y_W / S_W)`

Define:

`Gamma_J(W) = S_W / J_W`

= governed/bound machine stages per human decision-load unit.

`Gamma_M(W) = Y_W / S_W`

= machine-visible output per governed stage.

Therefore:

`Lambda_W = Gamma_J(W) * Gamma_M(W)`

This factorization matters because the system can evolve in two different ways:

- one human judgment can launch more machine stages;
- each machine stage can itself become a much larger agent/CI work bundle.

Those mechanisms must not be collapsed into raw commit count.

## Timing hypothesis

For each direct lineage, define:

`T_first(i) = first_bound_machine_stage_time - human_hinge_time`

and, when the evidence identifies the next human-required point:

`T_return(i) = next_human_required_time - human_hinge_time`

Human Return ETA should ultimately estimate:

`P80(T_return | task_class, L, Gamma_J, Gamma_M, evidence_quality)`

rather than machine compute time alone.

## Binding quality

Exploratory evidence weights may reuse the ETA convention:

- STRONG = 1.0
- MEDIUM = 0.6
- WEAK = 0.25
- REJECTED = 0

Then a confidence-weighted stage count is:

`S*_W = sum(q_ij)`

but raw and weighted counts must both remain inspectable. The weights are modeling choices, not facts.

## March strong micro-pilot

The first clean causal slice is 2026-03-03.

Hinge 1 at 09:03:16 JST:
- decision: move the long README to `docs/technical_overview.md` without changing its contents;
- PR #97 created 42 s later;
- PR #98 removes the long README body;
- PR #99 places the same long body in `docs/technical_overview.md`;
- PR #100 occurs in the same temporal interval but changes the README beyond the narrow move decision, so it is not counted as a STRONG binding for hinge 1.

Hinge 2 at 09:11:59 JST:
- decision: restrict the replacement README to the approved opening/Why-RTS reinforcement;
- PR #101 created 54 s later and its patch directly matches that bounded decision.

Observed strong micro-pilot:

- decision hinges = 2
- decision units = 2
- STRONG bound PR stages = 4
- `Gamma_J = 4 / 2 = 2.0 stages per DLU`
- first-stage latencies = 42 s, 54 s
- median first-stage latency = 48 s

This is proof of method, not a March-wide estimate.

## Negative controls

The 2026-03-06 Boundary Discipline decision demonstrates why semantic search alone is unsafe.
PR #90/#91/#92 look semantically attractive, but they predate the exact human hinge by more than two days. They are explicitly REJECTED as causal descendants.

PR #123 occurs 13m40s after the second March 6 hinge, but its small `rts_core` initialization patch is not specific enough to prove Boundary Discipline causality. It remains MEDIUM-or-lower candidate evidence.

The March 13 two-layer logging decision is visibly inherited by later run artifacts, but PR #181/#182 are roughly 25 hours later; they are phase corroboration, not a direct one-hinge lineage.

The March 16 boundary-semantics decision is followed about one hour later by AGENTS/spec/organization/fix contracts (#185-#188) that encode explicit role, scope, direction, and separation boundaries. This is principle-level MEDIUM evidence until the missing causal bridge is recovered.

## Later governed windows

Using existing evidence-bounded RTS windows and commits only as a machine-visible output proxy:

### 2026-07-27

- machine-visible output proxy `Y = 226 commits`
- governed stages `S = 16`
- decision load `J >= 10 DLU`

Thus:

- `Gamma_J = 16 / 10 = 1.6 stages/DLU`
- `Gamma_M = 226 / 16 = 14.125 commit-proxy/stage`
- `Lambda = 226 / 10 = 22.6 commit-proxy/DLU`

### 2026-08-11

- machine-visible output proxy `Y = 107 commits`
- governed stages `S = 3`
- decision load `J >= 4 DLU`

Thus:

- `Gamma_J = 3 / 4 = 0.75 stages/DLU`
- `Gamma_M = 107 / 3 = 35.6667 commit-proxy/stage`
- `Lambda = 107 / 4 = 26.75 commit-proxy/DLU`

The important change is not simply 'more commits'. The observed later system uses fewer, larger governed stages per decision unit while each stage contains much more machine-visible work.

## Observed control-pressure proxy

For windows where `E` is observed, define only as a descriptive observed-data proxy:

`K_obs(W) = (J + O + R) / E`

It is NOT coverage-invariant, NOT a fatigue score, and missing components must not be invented as zero.

Using the current monthly lower-bound table as recorded:

- Feb: 0.154
- Mar: 0.826
- Jun: 1.476
- Jul: 6.367
- Aug 1-12: 26.085

Because historical axis coverage differs by month, this sequence is evidence for a role-shape hypothesis, not a calibrated longitudinal physiological/workload scale.

## Provisional final conclusion

The surviving evidence rejects the model:

`human effort ~= commits`

and increasingly supports the model:

`human = control-plane judgment / architecture / orchestration / adversarial review`

`machine = implementation / expansion / repeated execution / verification bundles`

The best current historical hypothesis is therefore:

`Human role: Implementation -> Architecture -> Orchestration -> Adversarial Judgment`

while machine-visible work becomes increasingly compressed behind each governed stage.

A more precise statement is:

**The operator did not simply do less implementation over time. The unit of human contribution moved upward in abstraction: from touching implementation toward selecting structure, defining boundaries, delegating bounded work, judging results, and attacking failures. Simultaneously, the amount of machine-visible output inside one governed stage increased materially.**

The final measurement object should therefore be the tuple:

`D_W = (L_W, Gamma_J, Gamma_M, Lambda, T_return, Q)`

not commit count alone.

## What would falsify or revise this hypothesis

The hypothesis must be revised if broader exact-chat/PR binding shows that:

- most apparent machine bursts actually required dense hidden manual intervention;
- later high `Gamma_M` is mostly merge/rebase/bot artifact rather than real agent work;
- missing early `O/R` evidence erases the apparent role-shape change;
- strong held-out lineages do not reproduce the hinge -> stage -> human-return structure;
- a different simpler model predicts Human Return ETA materially better.

Until then this is the strongest evidence-bounded model recovered from the current history, not a universal law and not a clinical workload claim.
