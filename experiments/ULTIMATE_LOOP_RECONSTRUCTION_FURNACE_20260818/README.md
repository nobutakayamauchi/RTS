# Ultimate Loop Reconstruction Furnace — Experiment Preflight

Status: `EXPERIMENT_ONLY / NOT_CANONICAL / STAGE0_VALIDATOR_RUNNING`

Parent experiment: issue #353. Draft integration vehicle: PR #354.

## Purpose

This directory contains only the smallest experiment-local glue required to run the SWE-bench-Live reconstruction furnace without contaminating Ultimate Loop with benchmark answers or evaluator-only metadata. It is not a benchmark platform and it is not canonical Ultimate Loop authority.

The first preflight attempt exposed a material trust-boundary failure: the ordinary dataset surface presents solver-allowed task material adjacent to gold patches, test patches, hints, commit URLs, hidden evaluation metadata, and task identities that can point back to fixing work.

The second DA pass against the pinned official evaluator found that `rebuild_cmds`, `test_cmds`, `print_cmds`, `log_parser`, hidden pass/fail lists, and sandbox image identity belong to the evaluator/runner boundary rather than the blind solver boundary.

Therefore the solver never consumes raw benchmark rows or evaluator metadata.

`SOLVER DIRECT DATASET ACCESS -> EXPERIMENT INVALID`

`EVALUATOR METADATA != SOLVER INPUT`

## Frozen Stage 0

- dataset: `SWE-bench-Live/MultiLang`
- dataset revision: `608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b`
- evaluator: `microsoft/SWE-bench-Live`
- evaluator revision: `70ec57e852e3f2d195790fe71f553e272c691833`
- seed SHA-256: `050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b`
- deterministic Stage 0 splits: `c`, `go`
- admission: first deterministic candidate in each split that passes official gold evaluation `3/3`

No candidate is manually selected for ease.

## Boundary

```text
PINNED RAW BENCHMARK DATASET
        |
        v
OUT-OF-BAND VALIDATOR / RUNNER
  - raw instance identity allowed
  - gold patch / hidden test patch allowed
  - evaluator commands allowed
  - sandbox image identity allowed
  - official gold evaluation exactly 3x
  - raw stdout/stderr sealed from solver/operator model
        |
        v
STRICT ALLOWLIST SANITIZER v2
        |
        v
SOLVER-VISIBLE ENVELOPE
  - opaque task id
  - repo
  - base commit
  - public problem statement
  - platform
  - TASK_VALID=true
  - offline-after-prepare policy
        |
        v
ULTIMATE LOOP + TRACE
```

The validator and solver namespaces remain separate. Validator provenance is retained runner-side and is never solver input.

## Files

- `task_envelope.py` — v2 allowlist serializer and forbidden-key scanner.
- `stage0_control.py` — pinned deterministic split/candidate ordering, opaque IDs, resource preflight, first-valid admission.
- `trace_contract.py` — sequenceable fail-closed TRACE contract.
- `gold_validator.py` — sealed out-of-band 3x gold validator; emits only solver-safe artifacts.
- `STAGE0_RUN_MANIFEST.json` — frozen Stage 0 revisions, seed and admission rule.
- `VALIDATOR_RUNBOOK.md` — exact namespace and validity procedure.
- `test_*.py` — regression coverage for blindness, deterministic admission, resource classification and TRACE integrity.

## TRACE Stage 0 gate

A trace is not accepted merely because an event file exists. It must preserve contiguous sequence numbers, monotonic timestamps, run/task binding, material event categories, `TASK_START` first, and `TASK_END` last. Missing required categories produce `TRACE_INCOMPLETE`; sequence gaps, reordering or cross-task mixing fail closed.

Stage 0 measures observer overhead separately from solver performance.

`TRACE EXISTS != TRACE COMPLETE`

`OBSERVER FAILURE != SOLVER FAILURE`

## Hard invariants

`CAN ACCESS TASK != CAN ACCESS TASK BLINDLY`

`COLUMN IGNORED AFTER RETRIEVAL != COLUMN NEVER ENTERED CONTEXT`

`DATASET VIEWER != SAFE SOLVER INPUT`

`GOLD VALIDATION != GOLD ACCESS BY SOLVER`

`EVALUATOR COMMAND != PUBLIC TASK CONTRACT`

`RAW INSTANCE ID != REQUIRED SOLVER IDENTITY`

`GENERALIZED METHOD MEMORY != ANSWER CACHE`

`BROKEN EXPERIMENT HARNESS != SOLVER FAILURE`

`RESOURCE_BLOCKED != SOLVER_FAILURE`

`FAILURE WITH CLEAN TRACE > CONTAMINATED PASS`

## Stage 0 admission and execution

1. Use the frozen dataset/evaluator revisions and seed.
2. Deterministically order C and Go candidates outside solver context.
3. Evaluate each candidate's gold patch exactly three times on the experiment machine.
4. Continue in deterministic order until the first `3/3` candidate is found; never skip an earlier valid candidate for convenience.
5. Build only the v2 solver envelope.
6. Scan the complete solver bootstrap namespace for forbidden keys.
7. Prepare the sandbox runner-side and remove outbound solution lookup where practical.
8. Start the task clock only after the clean boundary is proven.
9. Run two telemetry-torture tasks through normal Ultimate Loop reasoning without benchmark-specific method changes.
10. Proceed to the eight-world Stage 1 gauntlet only if TRACE completeness and observer overhead survive Stage 0.

If no valid candidate can be established, resources are insufficient, or the boundary cannot be proven, stop as a validator/experiment-integrity result rather than inventing a solver failure.

## Scope

Do not promote any mechanism in this directory into the canonical Development Sequence Loop merely because the furnace needs it. After the experiment, Raison d'etre / DA / Counter-DA / METEOR decides whether any discovered responsibility deserves a durable home.
