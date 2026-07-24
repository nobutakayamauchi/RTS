# Read-Only Loop Core v1

`loop_core` reads committed FREEZER and Asset Manifest indexes and emits one deterministic advisory recommendation.

## Boundary

- local files only
- no network, provider, subprocess, deployment, scheduling, publication, or tool calls
- normal evaluation writes only canonical JSON to stdout
- governed inputs are never changed
- authority is always `ADVISORY_ONLY`
- the evaluator never selects, approves, starts, executes, verifies, or completes an item

## State vocabulary

- `NORMAL`: no active item and the next governance step is clear
- `FOCUS`: exactly one item is selected or in progress
- `OVERLOAD`: more than one item is active and WIP=1 is violated
- `STALL`: no immediately actionable candidate is available
- `BLOCKED`: a required assessment or Preflight gate is missing

## Commands

```text
python -m loop_core.cli evaluate
python -m loop_core.cli verify
```

Optional execution/evidence JSON arrays are shape-validated and reported as **unverified**, because the current RTS core does not define full runtime evidence linkage.
