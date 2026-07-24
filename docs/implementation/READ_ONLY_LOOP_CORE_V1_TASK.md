# Read-Only Loop Core v1 — Implementation Task

## Purpose

Implement `RTS-FRZ-000005` as a deterministic, local, advisory-only evaluator that reads current governed RTS records and asset metadata, evaluates the repository's operational/governance state, and emits one reconstructable recommendation without modifying its inputs or receiving implementation authority.

This is the second child of `RTS-FRZ-000003`. It must be completed before any execution controller (`RTS-FRZ-000006`) or outcome-learning runtime (`RTS-FRZ-000007`) is considered.

## Ground survey result

The implementation is feasible as a bounded local package because the repository already contains:

- canonical FREEZER indexes, Build Assessment, Preflight and WIP=1 boundaries
- the canonical Cross-Repo Asset Manifest
- minimal `execution_record` and `evidence_ref` contracts
- a legacy repository state detector that may be adapted but not promoted unchanged
- a reconstructable minimal-runtime flow reference
- verification-runner guidance that separates verified, unverified and assumed claims
- read-only observer/report patterns and explicit permission separation in adjacent public repositories

The scope passes Preflight only when it remains local, deterministic, read-only against governed inputs, and advisory-only.

## Human approval

The operator explicitly approved continuing with the next remaining child on 2026-07-24. This approval applies only to `RTS-FRZ-000005`. It does not approve or start `RTS-FRZ-000006` or `RTS-FRZ-000007`.

## Required package

Create a new top-level Python package:

```text
loop_core/
```

Suggested minimum structure:

```text
loop_core/
  __init__.py
  cli.py
  core.py
  models.py
  README.md
  schemas/
    evaluation.schema.json
  examples/
    evaluation.json
```

Equivalent names are acceptable only when the public CLI and boundaries below remain clear.

## Default governed inputs

The evaluator must read these repository-local files by default:

- `freezer/index/items.json`
- `freezer/index/build_priority.json`
- `asset_manifest/index/assets.json`

It may optionally accept caller-supplied local files containing execution records and evidence references, but those inputs must be shape-validated against the required fields in:

- `schemas/execution_record.schema.yaml`
- `schemas/evidence_ref.schema.yaml`

Do not redefine those canonical contracts. Do not add a hidden linkage model that the repository does not currently define.

## Read-only boundary

The evaluator must not mutate:

- FREEZER items, assessments, Preflights, pointers, indexes or manifests
- Asset Manifest snapshots, pointers, indexes or manifests
- execution/evidence input files
- adjacent repositories
- external systems

The normal evaluation command must write only to stdout. A deterministic checkpoint hash must be included inside the output payload instead of creating an implicit checkpoint file.

No network calls, subprocess execution, provider calls, deployment, publication, messaging, scheduling, or tool invocation may occur.

## Determinism

For identical input bytes and identical explicit CLI arguments, the canonical evaluation payload must be byte-for-byte reproducible.

Do not insert current wall-clock time into the canonical payload. An `as_of` value may be:

- supplied explicitly by the caller, or
- deterministically derived from committed input metadata

Canonical JSON serialization must use stable key ordering and stable list ordering where order is not semantically supplied by an input contract.

## Evaluation output

The evaluator must emit a JSON object with, at minimum:

- schema/version identifier
- deterministic `evaluation_id` or checkpoint hash
- exact input paths and SHA-256 fingerprints
- `as_of`
- current WIP count and active item IDs
- evaluated state
- audit level
- evidence summary separated into:
  - verified
  - unverified
  - assumed
- exactly one advisory next action
- rationale tied to governed input fields
- measurable success condition
- fallback action
- stop conditions
- explicit authority value `ADVISORY_ONLY`
- explicit statement that no implementation/write authority was granted

The output schema must reject additional undeclared fields unless a documented extension object is intentionally provided.

## State and recommendation rules

Use small deterministic rules. Do not create an opaque scoring model.

At minimum:

1. More than one `SELECTED` or `IN_PROGRESS` FREEZER item is an overload/governance violation and must recommend reducing WIP before any other work.
2. Exactly one active item should recommend continuing or verifying that item, depending on status.
3. With no active item, the highest-ranked actionable candidate from `build_priority.json` should drive the recommendation.
4. `ASSESSMENT_REQUIRED` must recommend Build Assessment, not implementation.
5. `BUILD_NOW` without human approval must recommend approval, not implementation.
6. A non-PASS or missing Preflight must never produce an implementation recommendation.
7. Completed items must not be recommended for implementation.
8. The evaluator itself never selects, approves, edits, starts, executes or completes an item.

The public state vocabulary may adapt the legacy operation-loop vocabulary, but it must be fully documented and covered by tests. Suggested values are `NORMAL`, `FOCUS`, `OVERLOAD`, `STALL`, and `BLOCKED`.

## Evidence-state boundary

Use the verification-runner principle:

- `verified`: facts proven by validated governed input files and deterministic checks
- `unverified`: optional local inputs that pass shape validation but lack a defined full evidence linkage
- `assumed`: explicit absence/default assumptions, such as no runtime outcome feed being supplied

Do not present optional execution records as verified outcomes merely because their JSON shape is valid.

## CLI

Provide at least:

```text
python -m loop_core.cli evaluate
python -m loop_core.cli verify
```

Useful explicit options may include:

```text
--root PATH
--execution-records PATH
--evidence-refs PATH
--as-of VALUE
```

`evaluate` prints canonical JSON to stdout.

`verify` must:

- validate all default governed inputs
- validate the output schema and committed example
- run the evaluator twice and prove deterministic equality
- hash governed input files before and after evaluation and prove no mutation
- confirm authority is always `ADVISORY_ONLY`
- confirm the evaluator cannot auto-start or mutate a FREEZER item

## FREEZER lifecycle for RTS-FRZ-000005

Use append-only records and current pointers. Do not rewrite existing immutable versions.

Required final governed state:

- current item status: `COMPLETED`
- current build authority: `APPROVED`
- current Build Assessment recommendation: `BUILD_NOW`
- current Implementation Preflight outcome: `PASS`

Preserve a lifecycle history showing human-approved selection before completion, either through separate immutable item versions or an equivalent already-supported append-only sequence.

The Build Assessment must cite the actual reusable assets inspected, including at least:

- `RTS-AM-A0001` — FREEZER governance
- `RTS-AM-A0002` — execution-record contract
- `RTS-AM-A0003` — evidence-reference contract
- `RTS-AM-A0004` — legacy state detection, adapt only
- `RTS-AM-A0009` — minimal reconstructable runtime flow
- `RTS-AM-A0011` — verification-runner
- one or more read-only observer/report or permission-separation references when materially reused

The Preflight must explicitly record:

- no adjacent-repository mutation
- no external interface or credential requirement
- no data migration
- no controller/write authority
- rollback by reverting this PR
- `RTS-FRZ-000006` and `RTS-FRZ-000007` remain unapproved and unimplemented

Regenerate all affected FREEZER indexes and SHA manifests using repository commands.

## Tests

Add focused tests for at least:

- deterministic output for identical inputs
- input hashes unchanged after evaluation
- WIP > 1 produces overload/governance stop recommendation
- one active item is handled without starting another item
- missing assessment recommends assessment
- missing/non-PASS Preflight blocks implementation recommendation
- completed items are not proposed for implementation
- optional record shape validation
- verified/unverified/assumed separation
- canonical output matches the JSON schema
- malformed governed inputs fail closed
- authority is always advisory-only
- `RTS-FRZ-000006` and `RTS-FRZ-000007` remain `NOT_APPROVED`

Avoid brittle fixed-count assumptions where possible.

## CI

Add or update GitHub Actions so CI runs:

```text
python -m asset_manifest.cli verify
python -m freezer.cli verify
python -m freezer.build_assessment verify
python -m loop_core.cli verify
python -B -m unittest discover -s tests -v
```

The workflow `push.paths` and `pull_request.paths` filters must explicitly include at least:

- `loop_core/**`
- `tests/test_loop_core.py`
- `docs/implementation/READ_ONLY_LOOP_CORE_V1_TASK.md`
- the workflow file itself

A change limited to `loop_core/**` or its focused tests must trigger the governed validation workflow without relying on an unrelated FREEZER or Asset Manifest change.

Retain the existing semantic stale-index check and Unicode Guard behavior.

## Required validation

Run and report exact results for:

```text
python -m asset_manifest.cli verify
python -m freezer.cli verify
python -m freezer.build_assessment verify
python -m loop_core.cli verify
python -B -m unittest discover -s tests -v
```

Also run the existing semantic generated-output freshness check or an equivalent temporary-copy rebuild comparison.

## Boundaries

- do not implement `RTS-FRZ-000006` or `RTS-FRZ-000007`
- do not add execution, write, deployment, provider, scheduling or external-action capability
- do not mutate adjacent repositories
- do not copy private repository bodies, paths, prompts, credentials, customer data or secrets
- do not weaken WIP=1, human approval, Build Assessment or Preflight gates
- do not change Asset Manifest behavior unless a genuine integration defect is proven
- do not add generated Python caches, transfer bundles, diagnostic dumps or temporary workflow hacks
- do not rewrite existing immutable FREEZER records

## Completion condition

The task is complete only when:

- the read-only evaluator is deterministic and input-preserving
- its output is schema-validated and explicitly advisory-only
- `RTS-FRZ-000005` is append-only completed with current `BUILD_NOW` and `PASS` evidence
- `RTS-FRZ-000006` and `RTS-FRZ-000007` remain untouched except for regenerated derived indexes if required
- all CI is green
- all review findings are resolved
- the final diff contains no forbidden generated or temporary files
