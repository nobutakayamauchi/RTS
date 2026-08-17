# Ultimate Loop Reconstruction Furnace — Experiment Preflight

Status: `EXPERIMENT_ONLY / NOT_CANONICAL / BLINDNESS_GATE_REQUIRED`

Parent experiment: issue #353.

## Purpose

This directory contains only the smallest repository-local glue required to keep the SWE-bench-Live experiment blind. It is not a benchmark platform and it is not canonical Ultimate Loop authority.

The first preflight attempt exposed a material trust-boundary failure: the ordinary dataset viewer presents solver-allowed task material adjacent to gold patches, test patches, hints, commit URLs, and hidden evaluation material.

Therefore the solver must never consume raw benchmark rows.

`SOLVER DIRECT DATASET ACCESS -> EXPERIMENT INVALID`

## Boundary

The data path is deliberately split:

```text
PINNED BENCHMARK DATASET
        |
        v
OUT-OF-BAND VALIDATOR
  - may access gold
  - runs gold evaluation exactly 3 times
  - retains validator-side provenance only
        |
        v
TASK ENVELOPE SANITIZER
  - explicit allowlist serializer
  - no raw-row copy / blacklist stripping
        |
        v
SOLVER-VISIBLE ENVELOPE
  - opaque task id
  - repo
  - base commit
  - problem statement
  - rebuild/test command contract
  - sandbox image identity
  - TASK_VALID=true
  - offline-after-prepare network policy
        |
        v
ULTIMATE LOOP + TRACE
```

The validator and solver namespaces must remain separate. A validator-side source fingerprint is provenance, not solver input.

## Files

- `task_envelope.py` — strict allowlist serializer, validator provenance helper, solver-envelope verifier, recursive forbidden-key scan.
- `test_task_envelope.py` — regression cases for gold leakage, schema drift, invalid tasks, hidden evaluation fields, trace leakage, and source mutation.

## Hard invariants

`CAN ACCESS TASK != CAN ACCESS TASK BLINDLY`

`COLUMN IGNORED AFTER RETRIEVAL != COLUMN NEVER ENTERED CONTEXT`

`DATASET VIEWER != SAFE SOLVER INPUT`

`GOLD VALIDATION != GOLD ACCESS BY SOLVER`

`GENERALIZED METHOD MEMORY != ANSWER CACHE`

`BROKEN EXPERIMENT HARNESS != SOLVER FAILURE`

## Required preflight before Stage 0

1. Pin the exact dataset revision.
2. Deterministically sample candidate rows outside solver context.
3. Validate each candidate with the benchmark gold path exactly three times.
4. Admit only 3/3 reproducibly valid tasks.
5. Generate an opaque task ID unrelated to the fixing PR number.
6. Serialize with `sanitize_for_solver`.
7. Verify the emitted object with `verify_solver_envelope`.
8. Scan the full solver-visible input/TRACE bootstrap namespace with `forbidden_key_scan`.
9. Prepare the sandbox, then remove outbound solution-lookup capability where practical.
10. Only then start the Ultimate Loop task clock.

Any inability to prove this separation is an experiment-integrity failure and should produce `EXPERIMENT_INVALID`, not a benchmark result.

## Scope

Do not promote this directory into the canonical method merely because the experiment uses it. After the furnace, Raison d'etre / DA / Counter-DA / METEOR decides whether any responsibility discovered here deserves a durable home.
