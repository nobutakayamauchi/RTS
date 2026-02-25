# RTS Agent Analyze ZERO — Index

- generated_at_utc: 2026-02-25T03:51:16+00:00
- runs_count: 1

RTS observes agent execution structure only. No semantics. No judging.

## Summary
- FAIL: 0
- DRIFT: 0
- SPAGHETTI: 1
- OK: 0
- VERIFIED: 0

## Runs
| Run | Class | Spans | fail | drift | warn | miss_status | spaghetti_reason_codes |
|---|---:|---:|---:|---:|---:|---:|---|
| [RUN_TEMPLATE.md](../runs/RUN_TEMPLATE.md) | SPAGHETTI | 2 | 0 | 0 | 0 | 1.0 | HIGH_MISSING_STATUS |

## Operator Notes
- VERIFIED only upgrades OK. It never overrides FAIL/DRIFT/SPAGHETTI.
- SPAGHETTI triggers are fixed: DUP_SPAN_ID / MISSING_PARENT / HIGH_MISSING_STATUS (+ PARSE_ERROR).
- Unknown status tokens are treated as missing (to avoid false OK).
