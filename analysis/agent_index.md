# RTS Agent Analyze ZERO — Index

- generated_at_utc: 2026-03-15T05:05:17+00:00
- runs_count: 2

RTS observes agent execution structure only. No semantics. No judging.

## Summary
- FAIL: 0
- DRIFT: 0
- SPAGHETTI: 0
- OK: 1
- VERIFIED: 1

## Runs
| Run | Class | Spans | fail | drift | warn | miss_status | spaghetti_reason_codes |
|---|---:|---:|---:|---:|---:|---:|---|
| [RUN_TEMPLATE.md](../runs/RUN_TEMPLATE.md) | OK | 0 | 0 | 0 | 0 | 0.0 |  |
| [RUN_VERIFIED_GOLD.md](../runs/RUN_VERIFIED_GOLD.md) | VERIFIED | 2 | 0 | 0 | 0 | 0.0 |  |

## Operator Notes
- VERIFIED only upgrades OK. It never overrides FAIL/DRIFT/SPAGHETTI.
- SPAGHETTI triggers are fixed: DUP_SPAN_ID / MISSING_PARENT / HIGH_MISSING_STATUS (+ PARSE_ERROR).
- Unknown status tokens are treated as missing (to avoid false OK).
