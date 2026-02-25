# RTS Agent Analyze ZERO — Index

- generated_at_utc: 2026-02-25T04:10:17+00:00
- runs_count: 1

RTS observes agent execution structure only. No semantics. No judging.

## Summary
- FAIL: 0
- DRIFT: 0
- SPAGHETTI: 0
- OK: 1
- VERIFIED: 0

## Runs
| Run | Class | Spans | fail | drift | warn | miss_status | spaghetti_reason_codes |
|---|---:|---:|---:|---:|---:|---:|---|
| [RUN_VERIFIED_GOLD.md](../runs/RUN_VERIFIED_GOLD.md) | OK | 2 | 0 | 0 | 0 | 0.0 |  |

## Operator Notes
- VERIFIED only upgrades OK. It never overrides FAIL/DRIFT/SPAGHETTI.
- SPAGHETTI triggers are fixed: DUP_SPAN_ID / MISSING_PARENT / HIGH_MISSING_STATUS (+ PARSE_ERROR).
- Unknown status tokens are treated as missing (to avoid false OK).
