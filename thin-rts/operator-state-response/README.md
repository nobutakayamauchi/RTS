# Operator State Response v0

A small `/goal` response skill that sits beside Human Return ETA and Decision Sentinel.

It is designed for one operator's longitudinal use. It is NOT a medical diagnosis system.

## What it returns

Example:

```text
RETURN 7m / LATE 10m / REWORK +2m
FATIGUE_EST 58.0/100 AMBER (LOW, cov=61%)
RECOVERY nap, meal
BAD headache, sleep_debt
BEHAVIOR ↑ correction_rate z=2.1, loop_rate z=1.9
DECISION_REVIEW AMBER
MEDICAL no reported red flag
ASK 直近24時間の睡眠は合計何時間くらい？
```

## Core separation

- `RETURN/LATE/REWORK`: work timing.
- `FATIGUE_EST`: operational heuristic, not clinical fatigue.
- `BEHAVIOR`: deviation from personal longitudinal baseline only.
- `VITAL_BASELINE`: personal trend/deviation only.
- `DECISION_REVIEW`: advisory review pressure from the parent prototype.
- `MEDICAL`: separate official-guidance safety layer.

A medical red flag overrides optimization advice but does not become a fatigue-score feature.

## Fatigue prior v0

Positive burden components:

- sleep shortfall relative to the MHLW adult rough target of >=6 h, with individual-difference caveat;
- subjective fatigue;
- reported non-emergency symptom burden;
- personal-baseline behavioral anomaly;
- current launch-safe workload pressure.

Recovery is subtractive only when the operator reports actual recovery effect. A meal, water or nap event is logged even when its effect is unknown.

All weights are heuristic priors. They are expected to be recalibrated or deleted under dogfood evidence.

## Behavioral features

v0 supports derived:

- typo rate;
- correction rate;
- loop rate;
- reversal rate.

At least five personal baseline samples are required before a behavior feature contributes. Device/input method and task context are confounders; raw counts are never portable fatigue units.

## Vitals

Optional values:

- heart rate;
- temperature;
- SpO2;
- systolic/diastolic blood pressure;
- respiratory rate.

v0 only computes personal-baseline robust z deviations. These values do not diagnose disease and do not directly change the fatigue score.

## Private logging

The public repository must never contain runtime health logs.

Default private location:

```text
~/.local/share/rts-private/operator-state/state.jsonl
```

The file is append-only JSONL and owner-only (`0600`) where supported. Raw chat text is not part of the default record.

## CLI

Feed a JSON payload through stdin or `--input`. Add `--log` to append the privacy-minimized record.

The CLI is deliberately boring: no daemon, cloud service, database or autonomous medical behavior.

## Shadow Mode

Use this as a logging/advisory layer first. Evaluate whether fatigue/behavior/vital features improve held-out return-time prediction or identify useful review-pressure states. If they do not, kill or down-weight them.
