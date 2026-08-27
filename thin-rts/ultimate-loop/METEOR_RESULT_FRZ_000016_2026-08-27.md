# METEOR — FRZ-000016 Adaptive Engine Profiler v1

Fixed destructive workload: engine identity changes, one-sample overfit, repeated-task pseudo-replication, speed-over-success optimization, hidden-reasoning ingestion, and unbounded probe planning.

- Naive candidate: DEAD. It inherited old tuning across a new engine, treated one success as stable, let speed override success, accepted hidden reasoning, and had no probe cap.
- Survivor: PASS. New engine => PRIOR_ONLY + conservative reprofile; STABLE needs >=10 known outcomes across >=5 distinct tasks with conservative Wilson success evidence; success evidence ranks before speed; hidden/raw prompt-response fields are rejected; probe matrix is one-dimension-at-a-time and capped at 8.
- Missing telemetry remains unknown/null. Recommendations remain ADVISORY_ONLY with execution/profile-application/promotion authority NONE.
- No provider calls, deployment changes, automatic router mutation, or Canon promotion occurred.
