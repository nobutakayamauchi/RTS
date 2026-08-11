# Operator State Response v0 — METEOR GATE

Status: `/goal` GLUE_CANDIDATE — medical diagnosis capability rejected.

## Desired outcome

Give the operator a compact response that combines:

- Human Return ETA / return clock;
- operational fatigue estimate;
- recovery and bad-status log;
- behavioral deviation from the operator's own baseline;
- advisory decision-review pressure;
- separate medical red-flag handling;
- follow-up questions only when they materially improve evidence.

## Destroy loop

### DROP: medical diagnosis from chat/typing/vitals

The prototype MUST NOT diagnose fatigue syndromes, dehydration, infection, neurological disease, or any other condition from typo rate, loop behavior, self-report, or consumer vitals.

### DROP: raw typo count => fatigue

Typing/error behavior is affected by task, device, time of day, speed strategy, language/input method and individual baseline. Raw counts are not portable fatigue units.

### SURVIVES: personal-baseline behavioral anomaly

Typing/correction/loop/reversal features may contribute only after enough personal baseline observations exist. Until then they remain UNCALIBRATED and contribute zero to the score, not semantic evidence of normality.

### DROP: post-hoc leakage

The live score and ETA may use only information known at response time. Future gate elapsed, later revisions, later medical outcomes, or observed human-return delay are forbidden launch-time features.

### SURVIVES: separate retrospective and launch-time state

Retrospective analysis may retain post-hoc observations for calibration. The response skill uses launch-safe features only.

### DROP: health logs in the public repository

Runtime health/state logs are sensitive. The public repository stores only schemas, source registry, code, and synthetic tests. Runtime logs default outside the repository and must be mode 0600 where supported.

### SURVIVES: advisory medical safety layer

Official emergency/red-flag guidance is allowed as a separate rule layer. A medical red flag overrides optimization advice and asks the operator to use appropriate official triage/emergency care. The fatigue score never decides medical urgency.

## Verdict

`GLUE` — build a small, local-first, advisory response skill.

No daemon, no diagnosis engine, no autonomous medical decision, no cloud health-data upload, no irreversible-action authority.
