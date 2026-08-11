# Thin RTS Reference Run 0002 — Decision Boundary Replacement

Timestamp: **2026-08-11 18:59 JST**

## Legacy responsibility under test

Legacy implementation: `scripts/decision_boundary_append.py`.

The old script accepts decision id, actor, role, scope, justification, and a state hash, then appends a timestamped `decision.boundary` JSON object to a repository-local monthly JSONL file.

The responsibility is **not** "run this Python file".
The responsibility is:

> preserve an explicit, timestamped, reconstructable authority boundary tied to a repository/system state.

## Destroy / replacement attempt

External composition used instead of legacy custom runtime logic:

- GitHub commit identity/history provides durable timestamped state history;
- this committed record provides actor/authority/scope/justification semantics;
- repository/branch/commit references provide state binding;
- human authority remains external to the record;
- Git history preserves subsequent corrections rather than requiring mutable hidden state.

No Python execution, RTS month variable, session directory, JSONL append runtime, daemon, or database is required for this workload.

## Actual boundary record

- `decision_id`: `RTS-REVIVAL-DECISION-0002`
- `actor`: repository owner/operator
- `actor_role`: project authority
- `scope`: authorize experiment-only construction and destructive testing on `revival/zero-cost-timeattack-20260811`; does **not** authorize merge/promotion to `main`.
- `justification`: measure whether the responsibilities of RTS can be reproduced by zero-additional-cost external composition plus thin reconstruction glue.
- `state_reference_before_boundary`: `a39bf71f0132cd7a42470a7bda27c61934b0b023`
- `record_timestamp_jst`: `2026-08-11 18:59`
- `promotion_authority`: `NONE_YET`

## Reconstruction check

An independent reader can recover:

1. who held authority;
2. the scope of that authority;
3. why the boundary existed;
4. the repository state immediately before this record;
5. the fact that branch experimentation did not grant merge/promotion authority.

## Result

`PASS`

The legacy `decision_boundary_append.py` implementation is **not required** for this responsibility under the current Git/GitHub workflow.

Initial classification:

- invariant/contract: `INHERIT_PRINCIPLE`
- legacy script: `ARCHIVE`
- durable storage/history: `EXTERNALIZE`
- semantic binding record: `GLUE_ONLY`

Next attack: mutate/correct this boundary record in a later commit and verify that the old boundary remains reconstructable from Git history rather than being silently overwritten.
