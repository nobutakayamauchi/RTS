# Manual Capture v0 — Check-in + Screenshot First

Status: `/goal` prototype / Shadow Mode.

The first usable version does NOT require a fitness ring, smartwatch, paid sensor, or vendor API.

## Minimum loop

1. Quick operator check-in.
2. Optional screenshot evidence when a device/app/measurement already exists.
3. Extract only the useful values and provenance.
4. Record the later work outcome: return timing, rework, loop/correction/reversal signals, and decision-review outcome.
5. Compare whether the extra screenshot-derived feature improves held-out prediction. If not, drop it.

## Check-in fields

Keep the interaction short. Typical fields:

- sleep hours in the last 24 h;
- subjective fatigue 0-10;
- subjective recovery 0-10;
- recovery events: sleep/nap/meal/hydration/rest/etc.;
- bad-status assessed + reported tags;
- optional continuous-awake duration when known;
- optional vehicle/outdoor sleep flag;
- optional environment consent;
- optional note that a screenshot measurement is available.

Unknown is not zero.

## Screenshot evidence

A screenshot may come from any already-available source: health app, wearable app, thermometer, pulse/SpO2 device, sleep app, weather app, or similar measurement surface.

Default handling:

- inspect the screenshot transiently;
- extract only named measurements needed by the current model;
- keep units, measurement time/window, source/app/device class when visible, and extraction confidence;
- do not infer a missing value;
- do not convert a vendor score directly into fatigue/impairment;
- do not persist the screenshot itself by default;
- do not commit screenshots or extracted personal-health records to the public repository.

Suggested normalized observation:

```json
{
  "source_type": "screenshot",
  "source_class": "health_app",
  "observed_window": "overnight",
  "measurements": {
    "sleep_minutes": 301,
    "resting_heart_rate_bpm": 62,
    "hrv_sdnn_ms": 44
  },
  "extraction_confidence": "HIGH",
  "image_persisted": false
}
```

Only include measurements actually visible and interpretable.

## Why screenshot-first

The purpose of v0 is not maximum sensor density. The purpose is to establish whether added state evidence improves:

- Human Return ETA error;
- early/late return waste;
- rework time;
- loop/correction/reversal detection;
- Decision Review Pressure usefulness.

If manual check-in + occasional screenshots are already sufficient, a wearable purchase is unnecessary for the model. A wearable becomes justified only when it fills a repeated missing-data gap or materially improves held-out prediction/verification.

## Promotion rule

`manual check-in -> screenshot-derived evidence -> personal outcome validation -> API/wearable only if justified`

No equipment purchase is a completion requirement for v0.
