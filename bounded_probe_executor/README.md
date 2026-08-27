# Bounded Probe Executor + Profile Application Gate v1

This layer executes **approved bounded campaigns**, not arbitrary provider work.

- F owns probe planning and profile synthesis.
- G compiles `task × probe` into a deterministic queue and fails closed if jobs, worst-case attempts, retry-adjusted estimated cost, parallelism, failures, or wall-clock ceilings are outside the approved budget.
- Adapter invocation is impossible before a fingerprint-exact human approval.
- `max_parallel <= 4`, retry is bounded, and background chunks are resumable; completed/quarantined jobs are terminal and are not replayed.
- Adapter results must match the authorized engine/domain/task/variant/config and must pass F's observable-only schema. Hidden reasoning, scratchpads, raw prompts, and raw responses are rejected.
- Engine identity mismatch stops the campaign.
- Only same-engine `STABLE` profiles can produce an application preview. Human approval materializes a rollback-capable **local policy artifact**; runtime routing is never mutated by v1.

`EXECUTION AUTHORITY = BOUNDED_CAMPAIGN_ONLY` applies only to the exact campaign fingerprint. `RUNTIME APPLICATION AUTHORITY = NONE`.

## Background education pattern

A scheduler or worker can call `run_campaign(..., max_jobs_this_chunk=N)`, persist the returned checkpoint, and later call it again with the same authorized campaign. Already terminal jobs are skipped. This lets model-behavior education run in bounded background chunks without replaying completed work.

Provider-specific API adapters and credentials are deliberately outside v1. They must satisfy the callable adapter contract and remain behind a separate credential/runtime gate.
