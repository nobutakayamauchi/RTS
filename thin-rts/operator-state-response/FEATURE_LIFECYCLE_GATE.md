# Feature Lifecycle Gate — Operator State Response

Status: `/goal` / WITNESS lifecycle rule.

## Principle

Optional data sources are not implementation commitments.

A candidate may remain documented and frozen until current low-cost dogfood can answer whether the missing data is likely to improve held-out prediction, verification, or safety usefulness.

The active v0 loop stays intentionally small:

`manual check-in -> optional screenshot-derived values -> work outcome -> held-out validation`

No wearable purchase, vendor API, continuous location collection, microphone capture, or dedicated environmental sensor is required for v0.

## Lifecycle verdicts

Every optional feature must eventually receive one of three verdicts:

### ROTATE
Return the candidate to experiment/prototype only when evidence shows a repeated information gap and there is a plausible measurable benefit.

Examples of qualifying evidence:
- ETA error remains materially higher when the candidate variable is absent;
- rework / correction / loop prediction improves on held-out personal samples when the candidate is present;
- Decision Review Pressure becomes more useful without unacceptable false alerts;
- a safety-relevant blind spot cannot be resolved by cheaper/manual evidence.

ROTATE authorizes a bounded experiment, not production adoption.

### PERMAFREEZE
Keep the idea and interface notes but do not implement it when:
- value remains plausible but unproven;
- the missing-data problem is rare;
- the acquisition/privacy/cost burden is not currently justified;
- manual check-in or screenshot evidence is already good enough.

PERMAFREEZE means "preserve the option; spend nothing now."

### DELETE
Remove the candidate from the active design when evidence shows that it adds no useful information or creates more burden/risk than value.

Examples:
- no held-out improvement after enough comparable samples;
- the feature is redundant with cheaper signals;
- vendor score duplicates raw physiology and causes double counting;
- location/audio collection creates privacy burden without measurable gain;
- the signal is too noisy, too sparse, or too confounded to support the intended use.

Deletion is a success if it prevents unnecessary system growth.

## Frozen candidates at this stage

The following are design options, not active requirements:

- fitness ring / smartwatch purchase;
- HealthKit / Health Connect / Samsung Health automated ingestion;
- direct Oura or other vendor API integration;
- continuous weather/location adapter;
- microphone-derived ambient-noise adapter;
- dedicated cabin temperature/humidity/CO2 hardware.

Current default verdict for each: `PERMAFREEZE_PENDING_EVIDENCE`.

They may move to ROTATE only through the evidence rule below.

## Evidence rule for unfreezing

A candidate must answer all of these before ROTATE:

1. What repeated prediction/verification gap exists in the current manual loop?
2. Which exact variable is expected to reduce that gap?
3. Can the same information be obtained more cheaply from check-in or screenshot evidence?
4. What held-out metric will determine success?
5. What privacy, cost, maintenance, and vendor-lock-in burden is introduced?
6. What result sends the candidate back to PERMAFREEZE or DELETE?

If these cannot be stated, do not build.

## Suggested evaluation metrics

Use predeclared metrics appropriate to the candidate:

- Human Return ETA absolute error;
- early-return waste;
- late-return waste;
- rework minutes;
- loop/correction/reversal detection usefulness;
- Decision Review Pressure false-alert / useful-alert rate;
- evidence coverage improvement;
- operator burden per useful observation.

A feature must improve at least one target without unacceptable degradation elsewhere.

## Current /goal verdict

`CHECK-IN + SCREENSHOT + OUTCOME` = ROTATE / ACTIVE DOGFOOD

`AUTOMATED WEARABLE / LOCATION / NOISE / CABIN SENSOR STACK` = PERMAFREEZE_PENDING_EVIDENCE

`PURCHASE AS A PREREQUISITE` = DELETE

The next decision is not "which gadget should be bought?".

The next decision is "does the active low-cost loop reveal a repeated missing-data gap worth paying to close?"
