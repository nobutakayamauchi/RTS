# Stage 0 TRACE — DA / Counter-DA result

Status: `EXPERIMENT_ONLY / TRACE_V2_TORTURE_GREEN / REAL_STAGE0_REQUIRED`

Parent experiment: #353. Candidate PR: #354.

## Frozen question

Can the observer retain the material state transitions of Ultimate Loop while the loop is moving quickly, without silently dropping, reordering, fabricating, or contaminating evidence?

This review attacks the observer contract itself before using it to judge Ultimate Loop.

## DA — deaths found in TRACE v1

TRACE v1 was not strong enough to call a run complete.

### Death 1 — presence could masquerade as completeness

The validator required one occurrence of every named event type, but did not require meaningful payloads. A trace containing empty payloads could satisfy the shape of a complete run.

`EVENT NAME EXISTS != MATERIAL EVIDENCE CAPTURED`

### Death 2 — normal first-pass success forced fake failure history

`FAILURE_SIGNATURE`, `HYPOTHESIS_REOPEN`, `FALSE_TRANSFER`, `METHOD_MEMORY_REUSE`, and `HUMAN_TOUCH` were globally mandatory even when the real count was zero. That incentivized synthetic placeholder events merely to satisfy completeness.

`ZERO REAL EVENTS != MISSING EVENTS`

### Death 3 — event counts were not reconciled

A task summary could not prove that the number of patch attempts, tests, reopens, tool invocations, transfers, or human touches matched the retained event stream.

`SUMMARY COUNT != OBSERVED COUNT`

### Death 4 — causal order was under-specified

Sequence continuity alone did not prevent logically impossible traces such as patching before Counter-DA or a test result bound to an attempt that had no prior patch.

`SEQUENCED != CAUSALLY COHERENT`

### Death 5 — TRACE itself could become a contamination path

TRACE payloads were not independently checked for benchmark-forbidden field names. A nested `patch`, `test_patch`, hint, fixing URL, or hidden evaluation field could enter retained logs.

`BLIND SOLVER INPUT != BLIND TRACE`

### Death 6 — caller mutation could rewrite retained evidence

A recorder that stores caller-owned nested payload objects by reference can have old events changed after emission.

`EMITTED != IMMUTABLE`

### Death 7 — timing noise could report negative observer cost

A noisy baseline could produce a negative overhead percentage and make the observer appear to speed up the workload.

`NOISY NEGATIVE DELTA != NEGATIVE OBSERVER COST`

## Repair — TRACE v2

The experiment-local TRACE contract now:

- requires event-specific material payload keys;
- distinguishes always-required lifecycle evidence from conditional counted events;
- binds `TASK_END.event_counts` to exact observed event counts;
- enforces the causal spine from task start through discovery, model, hypothesis, evidence, DA and Counter-DA;
- rejects patch-before-Counter-DA and test-without-prior-patch-for-the-same-attempt;
- requires exactly one `TASK_START` and one final `TASK_END`;
- recursively rejects benchmark-forbidden TRACE keys;
- validates patch SHA-256 shape and key enum values;
- freezes nested payloads at emission time;
- serializes concurrent writes through one sequence authority;
- clamps negative timing noise to zero reported overhead;
- supports JSONL replay for captured traces.

## Counter-DA — attacks retained as regressions

The hardened test set attacks the repair with:

1. empty-payload completeness spoof;
2. declared-vs-observed event count mismatch;
3. patch-before-Counter-DA reorder;
4. sequence gap;
5. cross-task trace mixing;
6. negative timing noise;
7. nested forbidden benchmark field leakage;
8. duplicate/early `TASK_END`;
9. test result bound to an attempt with no prior patch;
10. post-emission mutation of nested caller payload;
11. clean first-pass success with zero fake failure events;
12. burst capture: 8 concurrent threads x 250 tool events, followed by disk replay and exact sequence/count verification.

Local isolated replay result after repair:

`12 / 12 PASS`

The burst test retains 2,000 concurrent `TOOL_INVOCATION` events with no observed loss in the test process, strict sequence continuity, memory/disk row equality, and a complete replayable trace.

## Counter-DA residuals

This is not yet proof that the observer survives a real Ultimate Loop run.

Remaining live risks include:

- the synthetic burst does not reproduce every real Codex/tool scheduling pattern;
- OS/process crash durability beyond per-write flush is not proven;
- observer overhead on a real repository repair remains unmeasured;
- evidence references are structurally required but their external truth must still be bound by the real experiment;
- a real solver could expose a new event class not represented in TRACE v2;
- resource pressure/OOM must remain an experiment or environment classification unless causally attributable to the solver.

Therefore the correct promotion state is:

`TRACE_V2_TORTURE_GREEN`

not:

`OBSERVER_PROVEN`

## Gate to Ultimate Loop validation

Proceed to the two-task Stage 0 smoke only when:

1. the pinned dataset/evaluator pair remains fixed;
2. each task passes the out-of-band gold path 3/3 on the actual runner;
3. resource preflight admits the runner;
4. only the sanitized solver envelope enters Ultimate Loop context;
5. TRACE v2 is active before `TASK_START`;
6. no forbidden benchmark field enters solver-visible input or TRACE;
7. after each task, emitted/captured counts, order, replay and observer overhead are checked before interpreting solver performance.

If TRACE becomes incomplete under real load, classify the run as observer failure rather than Ultimate Loop failure.

`TRACE TORTURE PASS != REAL OBSERVER PROOF`

`OBSERVER FAILURE != SOLVER FAILURE`

`FAILURE WITH CLEAN TRACE > CONTAMINATED PASS`
