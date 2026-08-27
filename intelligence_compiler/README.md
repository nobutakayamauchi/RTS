# Incremental / Resumable Intelligence Compiler v1

Completed main work is persisted as raw outcome/evidence before learning begins. Learning is deterministic and chunked. Each successful chunk commits independently; later failures retry or quarantine only the failed chunk. Replays skip completed work by idempotency identity, and an orphan result can be adopted after a crash between result-write and manifest-update.

`LEARNING FAILURE != MAIN TASK FAILURE`

`RESUME != RECOMPUTE SUCCESSFUL CHUNKS`

`COMPILER OUTPUT = PROPOSAL ONLY`
