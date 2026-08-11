# Operator Load Timeline and Operator-Machine Amplification

## Evidence-bounded provisional conclusion for PR #315

**Status:** PROVISIONAL CONCLUSION REACHED.  
**Promotion authority:** none. PR #315 remains Draft; this document is research consolidation, not merge approval.  
**Core evidence base:** recovered Operator Load Timeline workbooks up to v0.5/v0.6, PR #315 body, and exact human-hinge recovery notes.

### Abstract

This note formalizes the result of an evidence-bounded reconstruction of RTS development history. The original question was whether GitHub timestamps could estimate how much human work was performed. The surviving conclusion is stronger and narrower: visible GitHub output is not a direct measure of human effort. Instead, the measurable object is a chain from human decision load to governed machine stages to machine-visible output.

The provisional model separates human load shape, machine-stage activation, stage-level output amplification, return timing, and evidence quality. The current evidence supports a role migration hypothesis: human work shifted from direct implementation toward architecture, orchestration, and adversarial judgment, while machine-side work absorbed expansion, repeated execution, and verification. This remains a falsifiable historical hypothesis, not a clinical or capacity claim.

### 1. Why commit count failed

A raw commit or PR count collapses at least three different quantities:

1. human judgment or authorization;
2. governed machine stages launched by that judgment;
3. machine-visible output produced by those stages.

The OLT recovery therefore rejects:

```text
human effort = commits
```

and keeps the load vector:

```text
L_W = (E_W, J_W, O_W, R_W, X_W)
```

where:

- `E`: direct exact-human execution/activity evidence;
- `J`: evidence-bound decision load, in Decision Load Units (DLU);
- `O`: governed-stage orchestration burden;
- `R`: repair/adversarial/rework burden;
- `X`: context-switch burden, currently a low-recovery lower bound.

Blank or missing axes mean `UNOBSERVED`, not semantic zero.

### 2. Final surviving factorization

The central surviving equation is:

```text
Lambda_W = Y_W / J_W = (S_W / J_W) * (Y_W / S_W)
```

or:

```text
Lambda_W = Gamma_J * Gamma_M
```

Definitions:

- `J_W`: evidence-bound human decision load, measured in DLU.
- `S_W`: governed or strongly bound machine stages associated with the decision window.
- `Y_W`: explicitly named machine-visible output proxy, such as commits or PR stages. It is not human effort.
- `Gamma_J = S_W / J_W`: stages activated per unit of human decision load.
- `Gamma_M = Y_W / S_W`: machine-visible output per governed machine stage.
- `Lambda_W = Y_W / J_W`: total visible-output amplification per decision-load unit.

Because current historical evidence often proves only `J_true >= J_lower`, decision-normalized quantities are usually upper-bound proxies:

```text
Gamma_J_true <= S_W / J_lower
Lambda_true <= Y_W / J_lower
```

The robust comparison should therefore prioritize `Gamma_M` when stage and output definitions are stable.

### 3. Strong pilot: March 3

A small STRONG-binding pilot on 2026-03-03 produced the first direct hinge-to-stage chain.

- 09:03:16 JST: README move decision strongly binds PR #97, #98, #99.
- First bound stage latency: 42 seconds.
- 09:11:59 JST: bounded README reinforcement decision strongly binds PR #101.
- First bound stage latency: 54 seconds.
- Pilot total: 2 decision hinges -> 4 strongly bound PR stages.

```text
Gamma_J = 4 / 2 = 2.0 stages/DLU
median T_first = 48 seconds
```

PR #100 was intentionally excluded: it was temporally close but exceeded the narrow decision content. Similarly, semantically attractive pre-hinge stages from 3/6 were rejected when their timestamps preceded the decision. This killed the naive rule `similar words imply causality`.

### 4. Cross-window results

| Window | Y proxy | S stages | J evidence | Gamma_J bound | Gamma_M proxy | Lambda bound |
|---|---:|---:|---:|---:|---:|---:|
| 2026-03-03 micro-pilot | 4 bound PR stages | 4 | 2 | 2.0 | 1.0 | 2.0 |
| 2026-07-27 RTS | 226 commits | 16 | J >= 10 | <= 1.6 | 14.125 | <= 22.6 |
| 2026-08-11 WITNESS | 107 commits | 3 | J >= 4 | <= 0.75 | 35.6667 | <= 26.75 |

The important observation is not that `Gamma_J` monotonically rises. It does not. The stronger observation is:

```text
later governed stages can contain much larger machine-visible work bundles
```

or:

```text
Gamma_M increased materially between the July and August samples.
```

### 5. Cascade compression

Trigger-aligned cascade analysis compared two D2 structural decisions in March.

| Metric | 3/2 Decision Boundary | 3/6 Boundary Discipline |
|---|---:|---:|
| First PR latency | 165.5 min | 15.6 min |
| PRs in 6h | 4 | 39 |
| PRs in 24h | 33 | 49 |
| PR/hour over 6h | 0.67 | 6.50 |
| 6h/24h compression | 12.1% | 79.6% |

Derived comparisons:

```text
first-output speedup ~= 10.6x
6h cascade-rate multiplier = 9.75x
cascade-compression multiplier ~= 6.57x
```

This is association, not proof of causality. However, it supports the narrower hypothesis that after some upstream design decisions, machine-visible output starts faster and is more heavily front-loaded.

### 6. Human role migration hypothesis

The provisional surviving historical hypothesis is:

```text
Human role:
Implementation -> Architecture -> Orchestration -> Adversarial Judgment
```

while the machine side increasingly absorbs:

```text
Machine role:
Implementation -> Expansion -> Repeated Execution -> Verification
```

The strongest plain-language conclusion is:

> Human work did not simply decrease. The unit of human work moved upward into more abstract control-plane decisions, while the amount of implementation and verification contained inside each machine stage grew.

### 7. Control-plane ratio

A descriptive secondary index is:

```text
K_obs = (J + O + R) / E
```

It should not be read as `fatigue` or as a coverage-invariant productivity metric. It indicates how much of the observed evidence is control-plane load relative to direct exact-human execution evidence. In the current reconstruction it rises sharply across later windows, consistent with the role migration hypothesis, but coverage differences prevent clean longitudinal comparison.

### 8. Final measurement object

The durable object should not be a single score. The proposed state vector is:

```text
D_W = (L_W, Gamma_J_bounds, Gamma_M_proxy, Lambda_bounds, T_return, Q)
```

with:

```text
L_W = (E, J, O, R, X)
```

For Human Return ETA, the target should use the first defensible human-required time, not the observed operator return time:

```text
T_return_hat = P80(T_required | task_class, L_launch, Gamma_J, Gamma_M, Q)
```

### 9. Falsification and calibration agenda

The formula should now be treated as frozen unless new STRONG evidence falsifies it. The next phase is calibration:

1. Recover more exact human hinges for March, July, and August.
2. Bind each hinge to stages only when temporal, semantic, and scope compatibility all hold.
3. Measure `T_first`, `T_required`, `T_observed`, early-return waste, late-return waste, and overshoot.
4. Estimate medians and P20/P80/P90 intervals for each task class.
5. Kill any model that requires post-hoc leakage or does not outperform simpler timestamp-only baselines.

### 10. /goal verdict

```text
PROVISIONAL CONCLUSION REACHED
THEORY FROZEN - CALIBRATION / FALSIFICATION PHASE
```

The unfinished work is not the formula. The unfinished work is increasing the STRONG evidence sample size and narrowing the confidence intervals.
