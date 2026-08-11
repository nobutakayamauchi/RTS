# Human Return ETA — `/goal` prototype

Status: `PROTOTYPE / WITNESS-METEOR SUBJECT / NOT PROMOTED`

Purpose: free the human from staring at long-running development work without wasting a long block of time after the machine already needs attention.

This prototype predicts **when the human should come back**, not how long the underlying computation "really takes".

## Outcome

Given timestamped history for materially similar work, optionally combined with a weighted chunk estimate for the incoming work, produce a compact return recommendation:

- `COME_BACK_AFTER_MINUTES`
- `EXPECTED_RANGE_MINUTES`
- `LATE_AFTER_MINUTES`
- `SAMPLES`
- `CONFIDENCE`
- `WAKE_EARLY_ON = ERROR, APPROVAL_REQUIRED, HUMAN_ACTION_REQUIRED`

The terminal event is the first point where unattended execution has either completed or needs the human again. An early error is therefore valid timing evidence; it is not discarded merely because the job did not succeed.

## External-first boundary

External systems remain responsible for:

- CI/workflow execution;
- notification delivery;
- Git/GitHub event timestamps;
- provider/runtime timestamps;
- timers and schedulers;
- actual work execution.

Thin RTS owns at most bounded GLUE for:

- normalizing past start/human-hinge timestamps;
- keeping task classes separate;
- robust duration statistics;
- consuming an externally calculated weighted-chunk estimate;
- calibrating minutes-per-weighted-chunk from observed timestamps;
- consuming evidence-bounded Operator Load Timeline observations;
- conservative cold-start behavior;
- a return recommendation with explicit uncertainty.

No daemon, queue, scheduler, notification platform, telemetry platform, database, ML model, or custom time-series service is authorized by this prototype.

## Input contract

JSON Lines, one observation per line:

```json
{"task_class":"meteor_ci_repair","started_at":"2026-08-11T22:19:46+09:00","human_hinge_at":"2026-08-11T22:23:08+09:00","terminal":"READY_FOR_REVIEW","weighted_chunks":4.5,"evidence_strength":"STRONG","source":"paired-meteor-commits"}
```

Required fields:

- `task_class`: stable bounded label for materially similar work;
- `started_at`: timezone-aware ISO-8601 timestamp;
- `human_hinge_at`: timezone-aware ISO-8601 timestamp when unattended work stopped being useful without a human;
- `terminal`: observed terminal/handoff condition.

Optional fields:

- `weighted_chunks`: positive weighted chunk-equivalent produced by the chunk/load model;
- `evidence_strength`: `STRONG`, `MEDIUM`, or `WEAK`;
- `source`: bounded provenance label.

The estimator must not mix unrelated task classes merely to gain raw duration sample size.

## Hybrid model

The intended model is:

`OLD LOAD/CHUNK PRIOR + OLT + GIT/GITHUB/CI TIMESTAMPS -> OBSERVED CALIBRATION -> RECALIBRATED ETA -> MORE REAL RUNS -> HIGHER ACCURACY`

The historical chunk concept is treated as a **prior and workload-size signal**, not as unquestionable wall-clock truth. The exact historical chunk accounting formula was not found as canonical code in the current RTS repository, so this prototype does not invent a replacement formula. It accepts `weighted_chunks` as an input boundary and learns the wall-clock conversion from real timestamp evidence.

When enough comparable records contain `weighted_chunks`, the estimator calculates observed `minutes / weighted_chunk` and uses an evidence-weighted P80 rate. For a new task with a target weighted-chunk estimate, it scales the empirical task-class duration by relative chunk size and blends that with the learned chunk-rate estimate.

If same-class chunk history does not exist, global chunk-rate history may seed a **low-confidence prior**. An explicitly supplied historical `--prior-minutes-per-chunk` can bootstrap a cold start, but real observations should replace its influence over time.

## Operator Load Timeline v0.2

The recovered workload model is now represented primarily as:

`L[p,W] = (E, J, O, R, X)`

with:

- E: direct human activity;
- J: decision load;
- O: governed AI/CI/Kernel orchestration load;
- R: revision/rejection/adversarial repair load;
- X: active-window context switches.

The v0.2 evidence rule is strict: **blank means UNOBSERVED, not zero**. Partial vectors are preserved with `null` axes, `axis_coverage = observed_axes / 5`, and a display-only `OLT lower bound` calculated from observed axes only.

The current evidence-bounded actual corpus is stored in `olt_actual_v0_2.json` and documented in `OLT_ACTUAL_V0_2.md`. It includes RTS, RTS-minicompany, RTS-AGE and rts-video-flow windows. The current largest RTS lower-bound window is 2026-07-27 at about 52.2 with J/O/R observed and E/X still unknown.

Two secondary diagnostics are available:

- `Gamma = machine_visible_output / governed_stages` — output amplification, never human effort;
- `JPR = (J + R) / O` — observed workload-shape ratio, never a fatigue score and not guaranteed to be a lower bound when source axes are partial.

Complete-vector OLT similarity is already available as an optional ETA prior. Partial-vector ETA fusion is not yet authorized; it must first prove held-out accuracy improvement without imputing missing axes.

## Timestamp evidence tiers

Not all timestamps mean the same thing.

- `STRONG`: explicit run start -> first human hinge, or another semantically bound pair.
- `MEDIUM`: materially credible but incomplete binding.
- `WEAK`: approximate timing such as adjacent Git commit timestamps where active work duration is not proven.

Weak evidence may improve a prior but must not silently outweigh strong observations.

`git_history.py` can import bounded adjacent Git intervals as `WEAK` evidence. It deliberately drops gaps above a configured maximum and labels the provenance as `git-adjacent:*`. Arbitrary adjacent commits must never be promoted to proven active-work duration.

## Estimation rule v0.1

- Use only the most recent bounded sample window for the selected class.
- Raw task-class history remains the primary direct evidence.
- Evidence strength changes statistical weight; weak Git approximations have lower influence.
- Median remains a center diagnostic.
- Evidence-weighted P80 is the default direct-history return target.
- P90 defines `LATE_AFTER_MINUTES` with a small floor above the return target.
- Report an observed P20–P80 range.
- If target weighted chunks are available, scale same-class empirical timing by task size and blend it with the learned P80 minutes-per-chunk rate.
- Complete OLT vector-neighbor history may act as a sparse-data prior; direct task history removes that influence as samples mature.
- Cold start may use an explicit chunk prior; otherwise it returns a conservative fallback and `LOW` confidence instead of fake precision.
- High spread, weak evidence, very small sample count, or low axis coverage lowers confidence.

The P80 policy and the current blend are human-attention tradeoffs, not statistical truths. They remain replaceable under DARWIN ARENA if real use shows a better policy.

## Safety / truth rules

- Timestamps must be timezone-aware.
- Negative or zero durations are rejected.
- `weighted_chunks`, when present, must be positive and finite.
- Evidence strength must be explicit and bounded.
- Malformed observations do not silently become valid evidence.
- A currently running job is not fabricated into a completed duration.
- Historical observations are evidence of prior human-hinge time, not a guarantee of future completion.
- Adjacent Git timestamps are approximation evidence, not proof that the operator worked continuously between commits.
- Missing OLT axes remain unobserved and are never silently imputed to zero.
- Commit amplification is not human effort.
- JPR is descriptive workload shape, not fatigue or clinical evidence.
- Prediction output must expose sample count, effective sample weight, confidence, basis, and evidence mix.

## WITNESS gate

This file does not authorize survival.

The candidate must be attacked for at least:

1. outliers;
2. mixed task classes;
3. tiny sample counts;
4. malformed and naive timestamps;
5. negative durations;
6. long-tail runs;
7. stale/older observations versus recent observations;
8. early `ERROR` / `APPROVAL_REQUIRED` as legitimate return hinges;
9. identical timestamps and duplicate observations;
10. no-history cold start;
11. incorrect or zero chunk estimates;
12. weak Git evidence overwhelming strong observations;
13. large idle Git gaps being mistaken for active task duration;
14. unseen task classes using chunk priors with fake confidence;
15. target workload materially larger or smaller than historical runs;
16. missing OLT axes being silently converted to zero;
17. low-coverage lower bounds being compared as complete vectors;
18. extreme commits/stage being mistaken for human load;
19. partial-axis JPR being treated as a monotonic lower bound.

If existing CI/analytics already exposes an equal-or-better return ETA with lower burden, this GLUE should be dropped or externalized.
