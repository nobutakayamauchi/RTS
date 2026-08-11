# Operator State Response Skill v0

Status: `/goal` prototype / Shadow Mode.

## Trigger

Use when the operator asks for `/goal`, work restart, return ETA, fatigue/state check, or when a meaningful deterioration/recovery signal appears during an active development session.

## Goal

Return a compact operational status without turning behavioral data into a medical diagnosis.

## Response shape

Prefer this compact order:

1. `RETURN <minutes> / LATE <minutes> / REWORK +<minutes>`
2. `FATIGUE_EST <0-100> <GREEN|AMBER|RED> (<confidence>, coverage)`
3. `RECOVERY <reported recovery events>` when present
4. `BAD <reported bad-status tags>` when present
5. `BEHAVIOR ↑ <personal-baseline anomalies>` only when calibrated
6. `VITAL_BASELINE Δ <personal-baseline deviations>` only when calibrated
7. `DECISION_REVIEW <GREEN|AMBER|RED>` when available
8. `MEDICAL <safety status>`
9. `ASK <at most 3 high-value missing questions>`

Do not inflate the answer with generic health advice when there is no material signal.

## High-value questions

Ask only missing information that can change the current response:

- total sleep in the last 24 h;
- subjective fatigue 0-10;
- recent recovery event(s) and subjective recovery 0-10;
- current bad-status symptoms (headache, nausea, dizziness, feverishness, collapse/fainting, etc.);
- optional vitals only when actually available;
- a short clarification when an unusual behavioral loop or reversal cannot be attributed to task difficulty/context.

If an emergency medical flag is present, do not continue optimization questioning before the safety action.

## Recovery logging

Record events such as:

- sleep / nap;
- meal;
- hydration;
- rest;
- symptom relief;
- medical assessment/treatment;
- other operator-reported recovery.

An event alone does NOT receive assumed recovery credit. Score credit requires reported recovery effect or later validated personal evidence.

## Bad-status logging

Record operator-reported tags without diagnostic reinterpretation. Examples:

- sleep_debt;
- headache;
- nausea;
- dizziness;
- weakness;
- feverish;
- pain;
- illness;
- fainted_or_collapsed;
- breathing_difficulty;
- altered_consciousness;
- seizure.

## Behavioral evidence

Derived signals may include typo rate, correction rate, loop rate and reversal rate.

Rules:

- compare to the same operator's rolling baseline;
- require at least 5 usable baseline samples before contribution;
- raw count alone is not fatigue evidence;
- task difficulty, device/input method and project context remain confounders;
- if a new pattern is material and attribution is unclear, ask one targeted question and log the answer as context.

## Vitals

Optional vitals are logged as values and personal-baseline deviations. v0 does not convert them into disease labels or universal fatigue points.

## Medical safety layer

This layer is separate from `FATIGUE_EST`.

Emergency/red-flag rules are based on official Japanese public triage guidance. When triggered, work optimization is subordinate to safety. The skill does not diagnose a cause.

## Privacy

Never commit runtime health/operator-state logs to the public repository. Do not store raw conversation text by default. Persist privacy-minimized derived metrics/tags in the private append-only log.

## Learning loop

After each useful run:

`predict -> observe human_required_at -> observe human_return_at -> outcome/revision taxonomy -> score error -> recalibrate or kill feature`

Promote a behavioral/vital feature only when held-out personal data improves ETA or review-pressure usefulness. Otherwise reduce its weight or drop it.
