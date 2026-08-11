# Human Return ETA — `/goal` prototype

Status: `PROTOTYPE / WITNESS-METEOR SUBJECT / NOT PROMOTED`

Purpose: free the human from staring at long-running development work without wasting a long block of time after the machine already needs attention.

This prototype predicts **when the human should come back**, not how long the underlying computation "really takes".

## Outcome

Given timestamped history for materially similar work, optionally combined with a weighted chunk estimate and Operator Load Timeline evidence for the incoming work, produce a compact return recommendation:

- `COME_BACK_AFTER_MINUTES`
- `EXPECTED_RANGE_MINUTES`
- `LATE_AFTER_MINUTES`
- `SAMPLES`
- `CONFIDENCE`
- `WAKE_EARLY_ON = ERROR, APPROVAL_REQUIRED, HUMAN_ACTION_REQUIRED`

The terminal event is the first point where unattended execution has either completed or needs the human again. An early error is therefore valid timing evidence; it is not discarded merely because the job did not succeed.

## External-first boundary

External systems remain responsible for CI/workflow execution, notification delivery, Git/GitHub/Chat timestamps, provider/runtime timestamps, timers, schedulers, and actual work execution.

Thin RTS owns at most bounded GLUE for timestamp normalization, task-class separation, robust duration statistics, chunk calibration, evidence-bounded OLT fusion, and return recommendations with explicit uncertainty.

No daemon, queue, scheduler, notification platform, telemetry platform, database, ML model, or custom time-series service is authorized by this prototype.

## Input contract

JSON Lines, one observation per line:

```json
{"task_class":"meteor_ci_repair","started_at":"2026-08-11T22:19:46+09:00","human_hinge_at":"2026-08-11T22:23:08+09:00","terminal":"READY_FOR_REVIEW","weighted_chunks":4.5,"evidence_strength":"STRONG","source":"paired-meteor-commits"}
```

The estimator keeps unrelated task classes separate and treats timestamp/evidence quality explicitly.

## Hybrid model

The intended model is:

`OLD LOAD/CHUNK PRIOR + OLT + GIT/GITHUB/CI/CHAT TIMESTAMPS -> OBSERVED CALIBRATION -> RECALIBRATED ETA -> MORE REAL RUNS -> HIGHER ACCURACY`

The historical chunk concept is a prior/workload-size signal, not unquestionable wall-clock truth. The ETA layer learns conversion from real timestamp evidence. Complete OLT vectors may act as sparse-history priors; partial daily OLT must remain calibration evidence until held-out validation proves a safe ETA fusion rule.

## Operator Load Timeline

The canonical workload representation is:

`L[p,W] = (E, J, O, R, X)`

with:

- `E`: confirmed direct-human intervention plus bounded active-time evidence;
- `J`: evidence-bound decision load;
- `O`: independently governed AI/CI/Kernel stages plus known non-double-counted gate time;
- `R`: revision/rejection/adversarial repair load;
- `X`: confirmed within-session project switches.

The strict rule is **blank/unknown means UNOBSERVED, not zero**. `OLT_100` remains a secondary evidence-bounded display lower bound; the vector plus axis coverage are primary.

`Gamma = machine_visible_output / governed_stages` is output amplification, never human effort. `JPR = (J + R) / O` is workload-shape diagnostics only, never fatigue evidence.

`olt.fuse_partial_vectors()` now sums observed project contributions axis-by-axis while preserving an axis as `None` if no source observed it. This is a lower-bound fusion operation.

## OLT v0.4 — ChatGPT timestamp fusion

The source-bound daily anchor corpus is `olt_daily_v0_4.json`, derived from `Operator_Load_Timeline_v0_4_chat_fused.xlsx` and reviewed in `OLT_V0_4_DIFF_REVIEW.md`.

Recovered anchors:

- 36 exact confirmed HUMAN events;
- 167.0667 minutes of eligible adjacent exact-human activity (`gap < 30 min`);
- Pre-Kernel split to real JST days: Feb 16 E=10.0956 and Feb 18 E=12.1511;
- Post-Kernel HUMAN/AUTO/UNKNOWN separation retained;
- Jul 27: 5 exact ChatGPT HUMAN events + 36.6667 active min -> E=7.4444;
- Jul 27 fused partial vector: `(E=7.4444, J=10, O=26.5, R=10, X=UNOBSERVED)`, 80% axis coverage, OLT lower bound 61.5299;
- ChatGPT-observed Jul 27 J=5 is treated as corroborating evidence inside the stronger governed J>=10 row and is not double-counted;
- Jul 23 exact reversal remains `UNRESOLVED_PROJECT`; no link is invented to later MiniCompany `PUBLIC_SALE_APPROVED`;
- Jan 20 through Aug 12 remains a partial daily materialization: missing days are `UNOBSERVED`, never zero-work days.

Some workbook daily tables render numeric zero in cells whose observation flags say the axis is unobserved. Repository machine-readable data canonicalizes those cells to `null`. Observed zero and unknown are different states.

## Evidence tiers

- `STRONG`: explicit human/run semantic binding;
- `MEDIUM`: materially credible but incomplete binding;
- `WEAK`: approximation such as adjacent Git intervals, PR density, or portfolio-surface proxies.

Weak evidence may improve missing-data priors but must never silently become direct HUMAN workload.

## Estimation rule

- use recent bounded direct task history first;
- evidence strength changes statistical influence;
- P80 is the current return target and P90 contributes to late-after guidance;
- weighted chunks may scale workload size;
- complete OLT-vector neighbors may help sparse-history estimation;
- direct task history progressively removes prior influence;
- cold starts remain explicitly low confidence;
- low coverage, weak evidence, and high spread reduce confidence.

## Safety / truth rules

- Timestamps used for E must be timezone-aware and confirmed HUMAN.
- Negative or zero duration artifacts are rejected where duration is required.
- `weighted_chunks`, when present, must be positive and finite.
- AUTO/UNKNOWN rows do not become human workload.
- Date-only semantic evidence may contribute J/R/O where supported but never fabricate E.
- Semantic duplicates must be deduplicated before rollup.
- Unresolved project attribution may remain unresolved.
- Commit count is not decision count or human effort.
- PR-density drops or long gaps do not prove fatigue/cognitive decline.
- Missing OLT axes remain unobserved and are never silently imputed to zero.
- Prediction output must expose sample count, confidence, basis, and evidence mix.

## WITNESS gate

This file does not authorize survival.

Required comparison before promotion:

`TIMESTAMP_ONLY` vs `CHUNK_ONLY` vs `PORTFOLIO_PRIOR` vs `OLT_VECTOR_PRIOR` vs `PARTIAL_OLT_PRIOR` vs `HYBRID`

using held-out real runs for absolute ETA error, early-return waste, late-return waste, and false-confidence rate.

Full 2026-01-20→present ChatGPT event-level materialization, complete context-switch X, safe partial-vector ETA fusion, automatic strong-history adapters, and notification delivery remain unproven or externalized.
