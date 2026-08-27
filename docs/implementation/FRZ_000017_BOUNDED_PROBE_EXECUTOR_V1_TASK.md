# FRZ-000017 — Bounded Probe Executor + Profile Application Gate v1

Goal: turn F's advisory probe matrix into a fingerprint-approved, budget-bounded, resumable background campaign without embedding provider credentials or automatically mutating runtime routing.

Hard boundaries: approval before adapter invocation; fail closed on queue/attempt/cost overflow; completed jobs are never replayed on resume; engine mismatch stops; hidden/raw text is rejected; only same-engine STABLE profiles may produce an application preview; application materializes a local rollback artifact only.
