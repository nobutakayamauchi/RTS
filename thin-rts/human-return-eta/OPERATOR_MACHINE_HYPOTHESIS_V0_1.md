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

A DA pass established an important prediction boundary:

- retrospective `L_post` may include realized orchestration elapsed time;
- live ETA must use a launch-time feature set containing only information already known at launch;
- future gate elapsed time is forbidden as a predictor of future return time.

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

### Bound semantics discovered by DA

If the evidence only establishes `J_true >= J_lower`, then division reverses the direction of uncertainty:

`Gamma_J_true = S/J_true <= S/J_lower`

and

`Lambda_true = Y/J_true <= Y/J_lower`.

Therefore ratios computed with a decision-load lower bound are **upper-bound proxies**, not point estimates and not lower bounds.

`Gamma_M = Y/S` is a point proxy only to the extent that both the output unit `Y` and governed-stage ontology `S` are stable and correctly classified.

## Timing hypothesis

For each direct lineage, define:

`T_first(i) = first_bound_machine_stage_time - human_hinge_time`

and, when the evidence identifies the first defensible human-required point:

`T_required(i) = human_required_time - human_hinge_time`.

Observed operator return is separate:

`T_observed(i) = observed_human_return_time - human_hinge_time`.

Human Return ETA should target `T_required`, not `T_observed`, otherwise operator overshoot/absence can be learned as if it were machine readiness.

The live prediction target is therefore:

`P80(T_required | task_class, launch_features, evidence_quality)`

with post-hoc load/outcome features retained for analysis and recalibration only.

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
- decision units = 2 exact DLU
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

## Later governed windows — corrected DA interpretation

Using existing evidence-bounded RTS windows and commits only as a machine-visible output proxy:

### 2026-07-27

- machine-visible output proxy `Y = 226 commits`
- governed stages `S = 16`
- decision load `J >= 10 DLU`

Thus:

- `Gamma_J_true <= 16 / 10 = 1.6 stages/DLU`
- `Gamma_M_proxy = 226 / 16 = 14.125 commit-proxy/stage`
- `Lambda_true <= 226 / 10 = 22.6 commit-proxy/DLU`

### 2026-08-11

- machine-visible output proxy `Y = 107 commits`
- governed stages `S = 3`
- decision load `J >= 4 DLU`

Thus:

- `Gamma_J_true <= 3 / 4 = 0.75 stages/DLU`
- `Gamma_M_proxy = 107 / 3 = 35.6667 commit-proxy/stage`
- `Lambda_true <= 107 / 4 = 26.75 commit-proxy/DLU`

The robust observation is therefore narrower than the earlier point-estimate wording: the measured machine-visible output per governed stage is substantially larger in the Aug 11 window than in Jul 27 under the current stage/output definitions. The decision-normalized ratios remain upper-bound proxies until J is more completely recovered.

## Observed control-pressure proxy

For windows where the components are observed, define only as a descriptive observed-data proxy:

`K_obs(W) = (J + O + R) / E`

It is NOT coverage-invariant, NOT a fatigue score, and missing components must not be invented as zero. Because both numerator and denominator can be partially observed, `K_obs` is not generally a lower bound or an upper bound.

Using the currently recorded observed-component table:

- Feb: 0.154
- Mar: 0.826
- Jun: 1.476
- Jul: 6.367
- Aug 1-12: 26.085

Because historical axis coverage differs by month, this sequence supports only a role-shape hypothesis, not a calibrated longitudinal physiological/workload scale.

## Decision Sentinel counter-DA result

A later revision is not automatically an error. Revisions must distinguish at least:

- `CORRECTIVE_ERROR`;
- `NEW_EVIDENCE`;
- `SCOPE_CHANGE`;
- `ROUTINE_ITERATION`;
- `UNKNOWN`.

The first Decision Sentinel prototype therefore does **not** output `P(wrong)`. It emits advisory Decision Review Pressure from decision-time evidence only and can ask for an extra independent check/DA before a high-impact or poorly supported decision.

## Provisional final conclusion

The surviving evidence rejects the model:

`human effort ~= commits`

and increasingly supports the model:

`human = control-plane judgment / architecture / orchestration / adversarial review`

`machine = implementation / expansion / repeated execution / verification bundles`

The best current historical hypothesis remains:

`Human role: Implementation -> Architecture -> Orchestration -> Adversarial Judgment`

while machine-visible work becomes increasingly bundled behind governed stages.

A more precise statement is:

**The operator did not simply do less implementation over time. The observed unit of human contribution moved upward in abstraction: from touching implementation toward selecting structure, defining boundaries, delegating bounded work, judging results, and attacking failures. Simultaneously, later observed governed stages can contain much larger machine-visible work bundles. Decision-normalized amplification is still only bound-constrained where J is incomplete.**

The final measurement object should therefore preserve uncertainty and timing semantics, conceptually:

`D_W = (L_post, L_launch, Gamma_J_bounds, Gamma_M_proxy, Lambda_bounds, T_required, T_observed, Q)`

not commit count alone.

## What would falsify or revise this hypothesis

The hypothesis must be revised if broader exact-chat/PR binding shows that:

- most apparent machine bursts actually required dense hidden manual intervention;
- later high `Gamma_M` is mostly merge/rebase/bot artifact rather than real agent work;
- stage definitions changed enough that cross-era `Gamma_M` is not comparable;
- missing early `O/R` evidence erases the apparent role-shape change;
- strong held-out lineages do not reproduce the hinge -> stage -> human-required structure;
- launch-safe OLT/amplification features do not improve held-out Human Return ETA;
- a simpler decision rule performs as well as Decision Sentinel with fewer interruptions.

Until then this is the strongest evidence-bounded model recovered from the current history, not a universal law and not a clinical workload claim.
