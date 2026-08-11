# Operator Load Timeline v0.1 — canonical `/goal` input model

Status: `PROTOTYPE / WITNESS-METEOR SUBJECT / NOT PROMOTED`

The primary record is a vector, not a single score:

`L[p,W] = (E, J, O, R, X)`

where `p` is project and `W` is a bounded time window or session.

## E — direct activity load

`E = N_H + sum(tau_i) / 15`

For adjacent HUMAN events:

- `tau_i = delta_t_i` only when `delta_t_i < 30 min`;
- otherwise `tau_i = 0`.

Interpretation: one OLU is approximately one explicit human intervention or about 15 minutes of continuous activity.

Worked reconstruction: `17 HUMAN + 78.7 min / 15 = 22.25 OLU`.

Commit count is not activity load. AUTO events do not become HUMAN load merely because they exist in GitHub.

## J — decision load

`J = sum(d_j)` with:

- D1 = 1: local continue/approve/select decision;
- D2 = 2: architecture/specification/policy/authority-boundary decision;
- D3 = 3: freeze/abolish/irreversible/final-authority decision.

Decision count must be derived from semantic decision evidence, not commit count.

## O — orchestration / governed-stage load

`O = N_G + T_G / 15`

`N_G` is the number of independently governed AI/CI/Kernel stages. `T_G` is elapsed gate-open-to-result time in minutes.

This is ownership/supervision burden, not manual coding time.

Worked reconstruction for PR #283–#286: `4 stages + 56.2167 min / 15 = 7.75 OLU`.

The 66 commits in that historical package are not 66 OLU.

## R — revision / rejection load

`R = sum(r_k)` where the current bounded prior is:

- 1 = simple correction;
- 2 = redesign after failure;
- 3 = discard premise / rebuild.

Meteor, Devil's Advocate, re-investigation, rejection and rebuild can contribute here when semantically evidenced.

## X — context-switch load

`X = sum(1[p_i != p_(i-1) and delta_t_i < 30 min])`.

Only switches inside an active window count. Long inactive gaps do not become context-switch burden.

## Evidence quality

Actor classification quality:

`Q = (N_H + N_A) / (N_H + N_A + N_U)`.

Automation rate among classified events:

`A = N_A / (N_H + N_A)`.

Materialized post-Kernel sample supplied to this prototype: HUMAN=3, AUTO=7, UNKNOWN=5, giving `Q=66.7%` and `A=70.0%`.

A separate spreadsheet summary reportedly contains 3/8/8. That discrepancy is intentionally unresolved and must not be normalized away without source reconciliation.

## Allocation views

For projects `q`:

- work share: `P_work[p,W] = E[p,W] / sum_q E[q,W]`;
- decision share: `P_decision[p,W] = J[p,W] / sum_q J[q,W]`;
- orchestration share: `P_orch[p,W] = O[p,W] / sum_q O[q,W]`.

These are deliberately separate views.

## Optional display score

The vector is the primary truth-bearing representation. A display-only score may be calculated with saturation:

`n(x;s) = 1 - exp(-x/s)`

`OLT_100 = 100 * [0.30 n(E;20) + 0.35 n(J;8) + 0.20 n(O;10) + 0.10 n(R;5) + 0.05 n(X;4)]`.

The weights and scales are v0.1 priors. `OLT_100` must not replace `(E,J,O,R,X)` in evidence records or model comparison.

## Human Return ETA integration rule

Human Return ETA should consume the OLT vector directly when possible.

The initial safe integration is:

1. preserve observed wall-clock human-hinge timestamps;
2. attach `(E,J,O,R,X)` to comparable historical windows;
3. compare incoming work to historical work in normalized vector space;
4. use vector-near observations as a missing-data prior;
5. retain task-class timestamp history as direct evidence;
6. keep weak Git-only portfolio history below semantically bound observations;
7. measure held-out ETA error before promotion.

`OLT_100` is not used as the sole workload feature for ETA because different load shapes can collapse to similar display scores.

## WITNESS conditions

The model survives only if it improves useful predictions or reconstruction without creating a larger classification burden than the benefit it provides.

Required attacks include:

- AUTO commit flood must not inflate E as human work;
- commit count must not fabricate J;
- long idle gaps must not inflate continuous activity;
- long inactive project gaps must not inflate X;
- unknown actor rate must remain visible through Q;
- spreadsheet summary/materialized-row disagreement must remain explicit;
- display-score collisions must not erase vector differences;
- sparse historical classifications must not claim high-confidence ETA improvement.
