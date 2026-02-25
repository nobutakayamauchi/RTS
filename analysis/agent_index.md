# RTS Agent Analyze Index

- generated_at_utc: 2026-02-25T03:03:05+00:00
- runs_dir: runs
- runs_count: 1

RTS observes agent execution paths. Structure only. No semantic judging.

## Summary

- VERIFIED: 0
- OK: 1
- DRIFT: 0
- SPAGHETTI: 0
- FAIL: 0

> Definitions: VERIFIED=explicit clean success. OK=clean. DRIFT=soft anomaly. SPAGHETTI=miracle alignment risk. FAIL=hard failure.

## Runs

| Run | Class | Spans | Fail | Drift | Warn | LoopScore | Mode | Updated(UTC) | Notes |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| [RUN_TEMPLATE.md](../runs/RUN_TEMPLATE.md) | OK | 2 | 0 | 0 | 0 | 0 | unknown | 2026-02-25T03:03:03+00:00 | no fail/drift detected |

## Operator Notes

- This report is structure-first. It does not assert correctness of outputs.
- If you need stronger auditability: attach evidence links or snapshot hashes per span/run.
- Use SPAGHETTI as a warning: it may pass once but likely fails on replay.
