# Adaptive Engine Profiler v1

This package learns **operating recommendations**, not model internals. It plans a bounded one-dimension-at-a-time probe matrix and evaluates externally supplied observable run summaries. It never calls a model/provider, never stores hidden chain-of-thought or raw prompt/response bodies, and never applies a profile automatically.

Core boundary: when observable engine identity changes, the old profile becomes `PRIOR_ONLY`; the recommended operating policy falls back to a conservative preset until new evidence exists. `STABLE` requires enough observations across distinct tasks. Missing telemetry remains unknown, and success evidence outranks speed optimization.

Every result is `ADVISORY_ONLY` with execution, profile-application, and promotion authority fixed to `NONE`.
