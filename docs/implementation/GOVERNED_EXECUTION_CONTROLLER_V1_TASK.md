# Governed Execution Controller v1 — Implementation Task

## Purpose

Implement `RTS-FRZ-000006` as a bounded local execution controller that converts an already governed and explicitly authorized work item into a reconstructable execution run with deterministic planning, strict budgets, append-only checkpoints, emergency stop, resume, structured failure, and human escalation.

This is the third child of `RTS-FRZ-000003`. It consumes the completed Cross-Repo Asset Manifest and Read-Only Loop Core. It must not implement outcome learning or Skill promotion (`RTS-FRZ-000007`).

## Ground survey result

The implementation is feasible because the ecosystem already contains:

- FREEZER Build Assessment, PASS Preflight, human authority and WIP=1 gates
- Read-Only Loop Core advisory evaluation
- canonical minimal `execution_record` and `evidence_ref` contracts
- RTS-AGE typed provider-adapter and deterministic local dry-run patterns
- RTS-Hermes-Drive orchestration responsibility boundaries
- RTS-MCP-Packs read/write permission-separation principles
- append-only and SHA-manifest patterns in RTS

The ground passes only for a local controller with no network, subprocess, provider API, deployment, publication, messaging, scheduling, adjacent-repository mutation, or autonomous start.

## Human approval

The operator explicitly approved moving to the next child on 2026-07-24. This approval authorizes implementation of `RTS-FRZ-000006` only. It does not authorize live external execution, publication, deployment, messaging, customer contact, scheduling, repository mutation outside this PR, or implementation of `RTS-FRZ-000007`.

## Required package

Create a top-level Python package:

```text
execution_controller/
```

Suggested minimum structure:

```text
execution_controller/
  __init__.py
  cli.py
  controller.py
  adapters.py
  models.py
  store.py
  README.md
  schemas/
    authorization.schema.json
    execution_plan.schema.json
    event.schema.json
    checkpoint.schema.json
  examples/
    authorization.json
    execution_plan.json
```

Equivalent names are acceptable only when the public boundary remains explicit.

## Architectural boundary

The controller belongs to the execution/Harness layer, not the RTS trust core.

It may:

- read governed RTS records
- validate an independently supplied execution authorization
- create a deterministic execution plan
- invoke an explicitly selected in-process adapter
- write append-only local run events/checkpoints only to an explicitly supplied state directory
- stop, resume and escalate a local run
- emit reconstructable records suitable for later handoff to RTS

It must not:

- grant its own approval or execution authority
- select a FREEZER item by itself
- weaken Build Assessment, Preflight, WIP=1 or human gates
- modify FREEZER, Asset Manifest or Loop Core governed inputs
- call networks, provider APIs, subprocesses or shell commands
- publish, deploy, message, schedule, invoice or contact anyone
- mutate adjacent repositories or external systems
- auto-retry without consuming an explicit budget
- implement learning, Skill mutation or promotion

## Governed inputs

By default, planning must read:

- `freezer/index/items.json`
- `freezer/index/build_priority.json`
- `asset_manifest/index/assets.json`

It may call or reuse Read-Only Loop Core functions in-process, but must not parse human-facing stdout.

A target item is eligible only when all are true:

- status is `SELECTED` or `IN_PROGRESS`
- `build_authority` is `APPROVED`
- current Build Assessment is `BUILD_NOW`
- current Implementation Preflight is `PASS`
- WIP=1 is satisfied
- the supplied authorization matches the exact item ID and item version
- the authorization permits the chosen adapter and capabilities

The controller must fail closed when any gate is missing, stale, malformed or ambiguous.

## Execution authorization

The controller consumes, but never creates or approves, an explicit authorization document.

Minimum fields:

- `authorization_id`
- `item_id`
- `item_version`
- `issued_by`
- `issued_at`
- `as_of`
- `adapter_id`
- `skill_id`
- `drive_id`
- `pack_id`
- `trigger`
- `allowed_capabilities`
- `budgets`
- `stop_conditions`
- `authorization_fingerprint`

Minimum budget fields:

- `max_attempts`
- `max_elapsed_seconds`
- `max_changed_files`
- `max_changed_bytes`
- `max_events`

For v1, the only permitted capability is:

```text
LOCAL_CHECKPOINT_WRITE
```

Any undeclared capability, including network, subprocess, repository write, publish, deploy, message, schedule or external tool use, must be rejected.

The authorization fingerprint must be deterministically recomputed and verified. The controller may not silently accept changed authorization content.

## State machine

Use a small explicit state machine:

```text
PLANNED
→ AUTHORIZED
→ DISPATCHED
→ RUNNING
→ VERIFYING
→ SUCCEEDED | FAILED | STOPPED | ESCALATED
```

Rules:

- state transitions must be enumerated and validated
- terminal states cannot transition further
- `STOPPED` can be reached from any non-terminal state by explicit emergency-stop command
- retry creates a new attempt event and consumes `max_attempts`
- budget exhaustion produces `ESCALATED`, not an implicit retry
- adapter failure must be structured as retryable or non-retryable
- non-retryable failure produces `FAILED`
- retryable failure with no remaining attempt budget produces `ESCALATED`
- resume requires a valid checkpoint chain and unchanged authorization fingerprint

## Adapter boundary

Define a typed adapter protocol inspired by `RTS-AM-A0012` without copying provider-specific assumptions.

Minimum result variants:

- success
- structured failure with `retryable` boolean
- explicit stop request

Implement only a deterministic in-process adapter in v1:

```text
adapter_id: dry-run
```

The dry-run adapter must:

- make no network or subprocess calls
- not change repositories or external systems
- produce deterministic results from explicit inputs
- support scripted success/failure/stop responses for tests
- report measured attempts, elapsed seconds, changed files and changed bytes supplied by the script rather than inspecting or editing a real worktree

No live OpenAI, Anthropic, Claude, Codex, Hermes, MCP or shell adapter is allowed in this PR.

## Planning

Planning must produce canonical JSON containing at least:

- schema/version
- deterministic plan ID
- target item ID and version
- exact governed-input paths and SHA-256 fingerprints
- authorization ID and fingerprint
- adapter ID
- requested execution identifiers (`skill_id`, `drive_id`, `pack_id`, `trigger`)
- allowed capabilities
- budgets
- initial state `PLANNED`
- required human/gate evidence
- stop conditions
- authority statement

For identical input bytes and arguments, the plan must be byte-for-byte reproducible. Do not add current wall-clock time to canonical planning output.

## Append-only event log and checkpoint

An executing command may write only below an explicitly supplied local `--state-dir`.

Required layout:

```text
<state-dir>/<run-id>/
  events.jsonl
  checkpoint.json
```

Each event must contain:

- sequence number
- event ID
- previous-event hash
- event hash
- state before and after
- attempt number
- cumulative budget usage
- event type
- deterministic or explicitly supplied timestamp
- safe summary without prompts, secrets or private payloads

The event hash must cover the canonical event content and previous hash. Verification must detect deletion, insertion, reordering or mutation.

`checkpoint.json` is a derived current pointer and must include the latest sequence, latest event hash, current state, attempt, cumulative usage, authorization fingerprint and plan fingerprint. The event log is the source of truth.

The controller must refuse to append when the chain or checkpoint is invalid.

## Canonical execution record

On terminal completion, emit a minimal execution record compatible with the existing canonical fields:

- `skill_id`
- `drive_id`
- `pack_id`
- `trigger`
- `result`
- `timestamp`

Additional controller metadata may be nested under a documented extension object, not by redefining the canonical schema.

No result may be presented as an externally verified outcome merely because the dry-run adapter succeeded.

## CLI

Provide at least:

```text
python -m execution_controller.cli plan --authorization PATH
python -m execution_controller.cli run --authorization PATH --state-dir PATH --script PATH
python -m execution_controller.cli resume --authorization PATH --state-dir PATH --script PATH
python -m execution_controller.cli stop --authorization PATH --state-dir PATH --timestamp VALUE
python -m execution_controller.cli inspect --authorization PATH --state-dir PATH
python -m execution_controller.cli verify
```

Behavior:

- `plan` writes canonical JSON to stdout only
- `run`, `resume` and `stop` require explicit `--state-dir`
- no command chooses a target item or creates authorization
- no command performs an external action
- errors return non-zero and fail closed

## Budget enforcement

Before and after every adapter event, enforce all budgets.

At minimum test:

- attempts cannot exceed `max_attempts`
- cumulative elapsed seconds cannot exceed `max_elapsed_seconds`
- cumulative changed files cannot exceed `max_changed_files`
- cumulative changed bytes cannot exceed `max_changed_bytes`
- total events cannot exceed `max_events`
- negative or decreasing usage is rejected
- adapter-reported usage is explicit data, not trusted as verified worktree measurement

Any projected budget overrun must stop before the prohibited transition and produce `ESCALATED`.

## Emergency stop and resume

Emergency stop must:

- be an explicit command
- append a `STOPPED` terminal event
- preserve prior events
- never delete checkpoints or logs

Resume must:

- reject terminal runs
- verify the complete hash chain
- verify checkpoint agreement
- verify plan and authorization fingerprints
- preserve sequence and cumulative budgets
- continue with the next attempt only when budget remains

## Privacy and evidence boundary

Do not persist:

- prompts
- secrets or credentials
- customer data
- private repository paths or bodies
- provider raw payloads
- tool arguments that may contain private content

Persist only safe identifiers, hashes, counters, states and bounded summaries.

## FREEZER lifecycle for RTS-FRZ-000006

Use append-only records and current pointers. Do not rewrite existing immutable versions.

Required final state:

- item status `COMPLETED`
- build authority `APPROVED`
- current Build Assessment recommendation `BUILD_NOW`
- current Implementation Preflight outcome `PASS`

Preserve a lifecycle history showing:

```text
FROZEN / NOT_APPROVED
→ SELECTED / APPROVED
→ IN_PROGRESS / APPROVED
→ VERIFIED / APPROVED
→ COMPLETED / APPROVED
```

The Build Assessment must cite actual inspected assets including at least:

- `RTS-AM-A0001` — FREEZER governance
- `RTS-AM-A0002` — execution-record contract
- `RTS-AM-A0003` — evidence-reference contract
- `RTS-AM-A0006` — append-only audit concepts, adapt only
- `RTS-AM-A0009` — minimal reconstructable runtime flow
- `RTS-AM-A0010` — feature-build sequence
- `RTS-AM-A0011` — verification runner
- `RTS-AM-A0012` — typed provider adapter
- `RTS-AM-A0013` — local deterministic dry-run
- `RTS-AM-A0016` — orchestration responsibility
- `RTS-AM-A0017` — connector permission separation

The Preflight must explicitly record:

- no live external adapter
- no network/subprocess/tool execution
- no adjacent-repository mutation
- no data migration
- explicit state directory is the only runtime write boundary
- rollback by reverting this PR and deleting uncommitted local runtime state
- `RTS-FRZ-000007` remains `FROZEN / NOT_APPROVED`

Regenerate all affected FREEZER indexes and SHA manifests.

## Tests

Add focused tests for at least:

- deterministic plan for identical inputs
- all FREEZER gates are required and stale gates fail closed
- authorization fingerprint mismatch fails closed
- unknown capability and unknown adapter are rejected
- state-transition legality
- terminal-state immutability
- append-only event hash-chain integrity
- checkpoint/event-log disagreement detection
- emergency stop
- resume with unchanged authorization
- resume rejection after authorization change
- retryable vs non-retryable failures
- attempt, elapsed-time, changed-file, changed-byte and event budgets
- projected budget overrun escalates before an illegal transition
- writes stay inside the explicit state directory
- prompts/private payloads are not persisted
- minimal execution record fields are emitted
- dry-run success is not labelled external verification
- `RTS-FRZ-000007` remains `FROZEN / NOT_APPROVED`

Avoid brittle fixed-count assumptions.

## CI

Update the governed workflow so changes limited to the controller or its tests trigger CI.

The workflow `push.paths` and `pull_request.paths` must include at least:

- `execution_controller/**`
- `tests/test_execution_controller.py`
- `docs/implementation/GOVERNED_EXECUTION_CONTROLLER_V1_TASK.md`
- the workflow file itself

CI must run:

```text
python -m asset_manifest.cli verify
python -m freezer.cli verify
python -m freezer.build_assessment verify
python -m loop_core.cli verify
python -m execution_controller.cli verify
python -B -m unittest discover -s tests -v
```

Retain semantic stale-index checks and Unicode Guard.

## Required validation

Run and report exact results for:

```text
python -m asset_manifest.cli verify
python -m freezer.cli verify
python -m freezer.build_assessment verify
python -m loop_core.cli verify
python -m execution_controller.cli verify
python -B -m unittest discover -s tests -v
```

Also run semantic regenerated-output freshness verification and verify the final changed-file list contains no caches, local state, transfer bundles, logs, diagnostic dumps or workflow hacks.

## Boundaries

- do not implement `RTS-FRZ-000007`
- do not add live provider adapters
- do not call networks, subprocesses, shell commands or external tools
- do not publish, deploy, send, schedule, invoice or contact anyone
- do not mutate adjacent repositories
- do not persist private prompts, credentials, customer data or private repository content
- do not weaken WIP=1, Build Assessment, Preflight or human approval
- do not add generated runtime state, Python caches, transfer bundles, diagnostic dumps or temporary workflow hacks
- do not rewrite immutable FREEZER records

## Completion condition

The task is complete only when:

- deterministic planning and bounded dry-run execution work
- all state, budget, authorization, stop, resume and hash-chain checks fail closed
- runtime writes are confined to an explicit local state directory
- no external capability is present
- `RTS-FRZ-000006` is append-only completed with current `BUILD_NOW` and `PASS` evidence
- `RTS-FRZ-000007` remains unapproved and unimplemented
- all CI is green
- all review findings are resolved
- the final diff contains no forbidden generated or temporary files
