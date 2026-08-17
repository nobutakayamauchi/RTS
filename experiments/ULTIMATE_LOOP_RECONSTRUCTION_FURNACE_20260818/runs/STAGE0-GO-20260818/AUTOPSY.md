# Stage 0 Go Autopsy — FURNACE-02-6F812634AF9D173B

Status: `SOLVER_FAIL / CLEAN_BLIND_RUN / TRACE_COMPLETE / OBSERVER_OVERHEAD_PARTIAL`

## Admission

- split: Go
- deterministic candidate rank: 1
- gold validity: 3/3 out-of-band before solver admission
- solver dataset access: false
- solver gold access: false
- hidden evaluator details exposed: false
- network policy during solver sandbox: offline after prepare

## Public task reconstruction

The unknown repository reconstructed as a Go project with platform adapters and a self-contained WeCom WebSocket path. Repository rules required focused fixes and regression tests.

The first actionable model was that WebSocket text ingress forwarded raw mention-bearing text directly into the core message handler.

## Reproduction

A test-only patch was applied before implementation.

Observed public regression:

- mention at prefix: FAIL
- mention in middle: FAIL
- mention at suffix: FAIL
- no mention: PASS

Failure class: `INGRESS_NORMALIZATION_MISSING`.

## Candidate

The bounded candidate added package-local mention normalization at the WeCom WebSocket text-ingress boundary plus a regression test.

Public verification:

- targeted regression: PASS, 4/4
- existing `platform/wecom` suite: PASS
- full repository `go test ./... -count=1`: PASS

No hidden benchmark material was used to construct or refine the candidate.

## Final sealed evaluation

Exactly one official hidden evaluation was executed against the frozen candidate.

Safe aggregate result:

```text
submitted:  1
success:    0
failure:    1
error:      0
incomplete: 0
empty_patch:0
```

Final task result: `FAIL`.

Hidden test names, logs, expected outputs, gold patch, and fixing-PR material were not exposed. No repair was attempted after the hidden failure.

## What this proves

It proves that the current loop could enter an unfamiliar Go repository, reconstruct a plausible local architecture, reproduce the public failure, build a small candidate, and preserve existing public regressions.

It does **not** prove repair generalization. The candidate failed unseen evaluation despite complete public regression success.

`PUBLIC REGRESSION GREEN != UNSEEN GENERALIZATION`

That statement remains a held candidate rather than a newly promoted canonical rule because this is one task.

## Method memory carried forward

Allowed carryover to the next task:

- reproduce before editing;
- isolate the smallest likely responsibility surface before widening scope;
- distinguish public-regression confidence from unseen-generalization evidence;
- stop rather than using hidden evaluation as an iterative oracle.

Not carried forward:

- repository name;
- file paths;
- symbols;
- issue wording;
- mention-specific implementation details;
- candidate patch;
- any hidden-test information.

## Observer result

TRACE contains 29 sequenceable events with contiguous sequence IDs, monotonic event order, one run/task binding, all required event categories, `TASK_START` first, and `TASK_END` last.

TRACE completeness: `COMPLETE`.

Observer overhead measurement is incomplete for Stage 0 purposes: write volume is retained, but no separately calibrated baseline run exists for wall/CPU overhead. This is an instrumentation debt to measure on the C task without altering the solving method.

## Verdict

`FAILURE WITH CLEAN TRACE`

The run is valid and useful. Do not rescue or retroactively tune it.
