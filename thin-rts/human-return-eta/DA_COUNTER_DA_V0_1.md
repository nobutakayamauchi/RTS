# DA / Counter-DA v0.1 — Human Return ETA + Decision Sentinel

Status: `/goal` PROTOTYPE HARDENING — advisory only, not promoted.

## DA attacks

1. **Denominator-bound inversion**
   - Historical `J>=k` is a lower bound.
   - Therefore `S/J_lower` and `Y/J_lower` are upper bounds on the corresponding true ratios, not point estimates and not lower bounds.
   - July `22.6` and Aug `26.75` commit-proxy/DLU are therefore `Lambda_upper` values under current J evidence.

2. **Prediction leakage from post-hoc O**
   - Historical `O = governed_stage_count + known_gate_elapsed/15` is useful for retrospective load-shape analysis.
   - It is unsafe as a launch-time ETA feature because gate elapsed is future information and can correlate directly with the target return time.
   - Launch-time prediction must use only features known at launch. The safe orchestration feature begins with governed stages known/planned at launch; realized elapsed belongs in the outcome record.

3. **Observed human return != machine-ready time**
   - If the operator comes back late, learning the observed return timestamp can teach oversleep/overshoot rather than the correct wake-up point.
   - When available, store `machine_ready_at` / `human_required_at` separately from `observed_human_return_at`.
   - ETA should target the first defensible human-required point, while actual human return is used to measure early/late waste.

4. **Revision != mistake**
   - A later revision can be caused by new evidence, scope change, or healthy iteration.
   - Do not train a wrong-decision detector on every revert/revise.
   - Outcome taxonomy must at least separate `CORRECTIVE_ERROR`, `NEW_EVIDENCE`, `SCOPE_CHANGE`, `ROUTINE_ITERATION`, and `UNKNOWN`.

5. **Machine-visible output is not stable effort currency**
   - Commit counts depend on repo practice, bot behavior, merges/rebases, and tooling era.
   - `Y` must always carry its explicit unit/proxy and should later become a multi-signal output vector or within-era standardized measure.

6. **Stage ontology drift**
   - `S` is only comparable when 'governed stage' means the same thing.
   - Stage definitions must be versioned or normalized by era/task class.

7. **Sparse-history / survivor bias**
   - Recovered history over-represents observable Git/Chat activity and under-represents silent thinking, abandoned work, and missing days.
   - Missing evidence remains UNOBSERVED; confidence must fall rather than silently imputing zero.

8. **Non-stationarity**
   - Tooling/model/project architecture changed materially across the history.
   - Old history should act as a prior; recent same-class evidence should dominate as it accumulates.

9. **Concurrency**
   - The operator may launch task A, switch to B, then return to A.
   - `T_return` must be tied to the task lineage, not simply the next human message globally.

10. **False authority risk**
   - A 'decision risk score' can become an unearned pseudo-authority.
   - v0.1 therefore emits `Decision Review Pressure` only. It does not claim a probability of being wrong and cannot autonomously approve irreversible actions.

## Counter-DA — what survives

The model survives if the following separations are enforced:

- retrospective load vector vs launch-time prediction vector;
- human decision load vs machine stage count vs machine-visible output;
- machine-ready time vs observed human return;
- corrective error vs legitimate revision;
- exact values vs lower/upper bounds vs proxies;
- evidence quality and axis coverage travel with every result.

The main amplification factorization remains useful:

`Lambda = (S/J) * (Y/S) = Y/J`

but each factor must carry bound semantics. With only `J>=J_lower`:

- `Gamma_J_true <= S/J_lower`;
- `Lambda_true <= Y/J_lower`;
- `Gamma_M = Y/S` remains a point proxy only to the extent Y and S are stable and correctly classified.

## Decision Sentinel v0.1

The first prototype computes a transparent heuristic **Decision Review Pressure (DRP)** from decision-time information only:

- decision severity D1/D2/D3;
- evidence quality Q;
- OLT axis coverage;
- recent revision load;
- recent context-switch load;
- unresolved counterevidence;
- irreversibility.

It returns GREEN / AMBER / RED guidance:

- GREEN: proceed and log;
- AMBER: require one independent check or DA;
- RED: hold irreversible action until evidence or authority is rechecked.

`DRP_100` is a prior heuristic and explicitly **not an error probability**. Its weights and thresholds must be replaced or recalibrated if real labeled outcomes show poor discrimination.

## Live dogfood loop

For each future run/decision, capture at minimum:

- task lineage / task class;
- human hinge time;
- launch-time observable features only;
- decision severity;
- Q and axis coverage;
- planned/known governed stages;
- bound machine stages and output unit after the fact;
- machine-ready / human-required time if observable;
- observed human return time;
- terminal state;
- later outcome label using the revision taxonomy;
- ETA prediction, actual target, early/late error;
- Sentinel level and whether the extra check changed the decision.

Then repeatedly compare:

- ETA absolute error;
- early-return waste;
- late-return waste;
- false-confidence rate;
- Sentinel alert precision/recall only after enough defensible labels exist;
- utility: prevented corrective errors minus unnecessary interruption cost.

## Kill conditions

Drop or simplify the prototype if:

- launch-safe OLT features do not improve held-out ETA over timestamp-only history;
- DRP alerts are not better than simple D3+low-Q rules;
- output-amplification metrics fail to reproduce across stable stage ontologies;
- the model adds more operator interruption than it saves;
- apparent accuracy depends on post-hoc leakage.
