# Human Return ETA — observed pilot

Status: `REAL TIMESTAMP PILOT / LOW SAMPLE COUNT`

This pilot uses two observed Cloud Custody Meteor repair intervals from 2026-08-11 JST:

| round | start | human hinge | duration |
|---|---|---|---:|
| Meteor repair 1 | 22:19:46 | 22:23:08 | 3m22s |
| Meteor repair 2 | 22:25:15 | 22:29:05 | 3m50s |

Task class for the pilot: `meteor_custody_repair`.

Under the v0 rule:

- samples: `2`
- confidence: `LOW`
- median: about `3.60 min`
- P80 by nearest-rank: about `3.83 min`
- `COME_BACK_AFTER_MINUTES = 4`
- observed range rounds to about `3–4 min`
- `LATE_AFTER_MINUTES = 6`

Interpretation:

> For another materially similar round, the current low-confidence advice is: **come back in about 4 minutes; treat 6 minutes as unusually long; wake immediately on ERROR / APPROVAL_REQUIRED / HUMAN_ACTION_REQUIRED.**

This is not a universal estimate. It is a first real-history binding and must change as more observations accumulate.

## What this does not prove

- Two samples are not enough for stable distribution estimates.
- Commit timestamps are only acceptable here because the selected commits were already identified as the relevant attack and human-hinge points. Arbitrary adjacent commits must not be automatically treated as a task duration.
- Future runs may contain provider waits or a new death class and take materially longer.
- Notification delivery is not implemented here; it remains an external integration responsibility.
