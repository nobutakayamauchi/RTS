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

`OLD LOAD/CHUNK PRIOR + GIT/GITHUB/CI TIMESTAMPS -> OBSERVED MINUTES PER WEIGHTED CHUNK -> RECALIBRATED ETA -> MORE REAL RUNS -> HIGHER ACCURACY`

The historical chunk concept is treated as a **prior and workload-size signal**, not as unquestionable wall-clock truth. The earlier operational meaning was human attention/evaluation/choice/verification burden, with materially heavier judgments represented as multiple chunk-equivalents. The exact historical chunk accounting formula was not found as canonical code in the current RTS repository, so this prototype does not invent a replacement formula. It accepts `weighted_chunks` as an input boundary and learns the wall-clock conversion from real timestamp evidence.

When enough comparable records contain `weighted_chunks`, the estimator calculates observed `minutes / weighted_chunk` and uses an evidence-weighted P80 rate. For a new task with a target weighted-chunk estimate, it scales the empirical task-class duration by relative chunk size and blends that with the learned chunk-rate estimate.

If same-class chunk history does not exist, global chunk-rate history may seed a **low-confidence prior**. An explicitly supplied historical `--prior-minutes-per-chunk` can bootstrap a cold start, but real observations should replace its influence over time.

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
- Cold start may use an explicit chunk prior; otherwise it returns a conservative fallback and `LOW` confidence instead of fake precision.
- High spread, weak evidence, or very small sample count lowers confidence.

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
15. target workload materially larger or smaller than historical runs.

If existing CI/analytics already exposes an equal-or-better return ETA with lower burden, this GLUE should be dropped or externalized.
