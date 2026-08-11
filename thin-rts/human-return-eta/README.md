# Human Return ETA — `/goal` prototype

Status: `PROTOTYPE / WITNESS-METEOR SUBJECT / NOT PROMOTED`

Purpose: free the human from staring at long-running development work without wasting a long block of time after the machine already needs attention.

This prototype predicts **when the human should come back**, not how long the underlying computation "really takes".

## Outcome

Given timestamped history for materially similar work, produce a compact return recommendation:

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
- conservative cold-start behavior;
- a return recommendation with explicit uncertainty.

No daemon, queue, scheduler, notification platform, telemetry platform, database, ML model, or custom time-series service is authorized by this prototype.

## Input contract

JSON Lines, one observation per line:

```json
{"task_class":"meteor_ci_repair","started_at":"2026-08-11T22:19:46+09:00","human_hinge_at":"2026-08-11T22:23:08+09:00","terminal":"READY_FOR_REVIEW"}
```

Required fields:

- `task_class`: stable bounded label for materially similar work;
- `started_at`: timezone-aware ISO-8601 timestamp;
- `human_hinge_at`: timezone-aware ISO-8601 timestamp when unattended work stopped being useful without a human;
- `terminal`: observed terminal/handoff condition.

The estimator must not mix unrelated task classes merely to gain sample size.

## Estimation rule v0

- Use only the most recent bounded sample window for the selected class.
- Median is the center estimate.
- P80 is the default `COME_BACK_AFTER_MINUTES` target.
- P90 defines `LATE_AFTER_MINUTES` with a small floor above P80.
- Report an observed P20–P80 range.
- Cold start returns a conservative fallback and `LOW` confidence instead of fake precision.
- High spread or very small sample count lowers confidence.

The choice of P80 is a human-attention tradeoff, not a statistical truth. It should itself remain replaceable under DARWIN ARENA if real use shows a better policy.

## Safety / truth rules

- Timestamps must be timezone-aware.
- Negative or zero durations are rejected.
- Malformed observations do not silently become valid evidence.
- A currently running job is not fabricated into a completed duration.
- Historical observations are evidence of prior human-hinge time, not a guarantee of future completion.
- Prediction output must expose sample count and confidence.

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
10. no-history cold start.

If existing CI/analytics already exposes an equal-or-better return ETA with lower burden, this GLUE should be dropped or externalized.
