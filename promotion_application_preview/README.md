# Promotion Application Preview v1

This package converts the committed promotion proposal, pending review, Human Review Ledger, regression result, rollback snapshot, and baseline/candidate snapshots into one deterministic **read-only, non-applying preview**.

The current repository state intentionally produces:

```text
state: BLOCKED
approval_status: NOT_APPROVED
application_status: NOT_APPLIED
target_write_authorized: false
adjacent_repository_write_authorized: false
```

The preview describes one proposed target-file replacement, its expected before/after hashes, prerequisites, blockers, validation steps, stop conditions, and rollback reference. It never writes, patches, commits, merges, publishes, deploys, messages, schedules, or mutates a target.

## Commands

```text
python -m promotion_application_preview.cli generate
python -m promotion_application_preview.cli verify
python -m promotion_application_preview.cli summary
```

`generate` prints a deterministic proposal-only preview. `verify` and `summary` verify the committed preview and all exact governed inputs before returning a summary.
