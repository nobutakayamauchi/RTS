# Stage 0 out-of-band validator runbook

Status: `EXPERIMENT_ONLY / VALIDATOR_SIDE / NEVER_SOLVER_CONTEXT`

Parent: issue #353 / PR #354.

## Frozen inputs

- dataset: `SWE-bench-Live/MultiLang`
- dataset revision: `608f7ae9ab8ea1f9f0d030fe04562cf6bd1a0c8b`
- evaluator: `microsoft/SWE-bench-Live`
- evaluator revision: `70ec57e852e3f2d195790fe71f553e272c691833`
- Stage 0 splits: `c`, `go`
- seed SHA-256: `050b40668443f667bcc5eabb7ff6c0ea3db5f2e962ac2178ce8e95d4e9e7921b`

Do not substitute `main` for either pinned revision after the run begins.

## Namespace boundary

The validator may access raw dataset rows, gold `patch`, `test_patch`, hidden evaluation fields, and the benchmark evaluator because it is outside Ultimate Loop solver context.

The solver may receive none of those materials.

`VALIDATOR KNOWS GOLD != SOLVER MAY KNOW GOLD`

## Candidate ordering

For each selected split, load the raw rows only in the validator namespace and call `stage0_control.candidate_order(...)` with the frozen seed. Validate candidates strictly in that resulting order.

Do not skip a valid earlier candidate because a later task looks easier, smaller, more familiar, or more convenient.

For the first candidate, run the official gold evaluation three independent times. If it does not pass 3/3, record the invalidity and continue to the next candidate in deterministic order. The first 3/3 candidate is admitted for that split.

## Gold validity execution

Use the pinned evaluator checkout and its official evaluation path. Each attempt must have a separate output location or otherwise prove an actual new evaluation rather than reusing cached success.

Conceptually, for candidate `<INSTANCE_ID>`:

```text
python -m evaluation.evaluation \
  --dataset SWE-bench-Live/MultiLang \
  --split <c-or-go> \
  --instance_ids <INSTANCE_ID> \
  --platform linux \
  --patch_dir gold \
  --output_dir logs/furnace-gold/<INSTANCE_ID>/run-1 \
  --workers 1 \
  --overwrite 1

# repeat as run-2 and run-3 with fresh output paths
```

If the pinned evaluator expects a local pinned dataset file to guarantee the exact Hugging Face revision, materialize that revision outside solver context and pass the local dataset path instead of silently resolving current `main`.

## Resource preflight

Before counting any failed execution, record CPU and memory availability. The benchmark's ordinary guidance is approximately 4 CPUs / 16 GiB per instance, and some large C++ repositories may require much more memory.

A task blocked by insufficient host resources, image pull failure, benchmark drift, sandbox corruption, or validator failure is not an Ultimate Loop solver failure.

`RESOURCE_BLOCKED != SOLVER_FAILED`

## Admission

After 3/3 gold PASS:

1. call `build_validator_provenance`;
2. generate the opaque ID with `stage0_control.opaque_task_id`;
3. call `sanitize_for_solver`;
4. call `verify_solver_envelope`;
5. recursively scan the solver bootstrap namespace with `forbidden_key_scan`;
6. retain raw/gold validator artifacts outside the solver workspace;
7. prepare the sandbox;
8. remove outbound solution-lookup capability where practical;
9. start TRACE only after the clean envelope and prepared sandbox cross the boundary.

If any forbidden benchmark field is present in solver input or TRACE bootstrap, classify the run as `EXPERIMENT_INVALID`.

## Stage 0 completion gate

Stage 0 begins only when one C task and one Go task have independently passed gold validation 3/3 and each has a clean solver envelope.

Stage 0 itself passes the instrumentation gate only when both tasks produce sequenceable TRACE with acceptable observer overhead and no contamination. Solver success is not required for the instrumentation gate; a cleanly observed solver failure remains useful data.
