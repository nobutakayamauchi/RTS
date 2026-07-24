# Cross-Repo Asset Manifest v1 — Implementation Contract

## Decision context

The governed execution and learning loop is feasible, but it must not be implemented as one giant integration. The parent initiative is decomposed into four independently verifiable FREEZER candidates:

1. Cross-Repo Asset Manifest
2. Read-Only Loop Core
3. Governed Execution Controller
4. Outcome Learning and Skill Promotion

This pull request implements **only candidate 1**. It may register all five records (one parent plus four children), but it must not implement candidates 2–4.

## Required FREEZER records

Create immutable FREEZER records using the existing CLI/storage rules:

- `RTS-FRZ-000003` — Governed Execution and Learning Loop (parent)
  - type: architecture
  - status: FROZEN
  - build authority: NOT_APPROVED
  - preserve the four-child decomposition
  - create a Preflight outcome of `DECOMPOSE_REQUIRED`
- `RTS-FRZ-000004` — Cross-Repo Asset Manifest
  - type: architecture
  - assess GitHub reuse and build value
  - current assessment must recommend `BUILD_NOW`
  - create a passing implementation Preflight
  - explicitly approve only this child for this implementation
  - record it as COMPLETED only after implementation and verification
- `RTS-FRZ-000005` — Read-Only Loop Core
  - type: feature
  - status: FROZEN or READY, but NOT_APPROVED
  - depends on 000004
- `RTS-FRZ-000006` — Governed Execution Controller
  - type: architecture
  - status: FROZEN
  - NOT_APPROVED
  - depends on 000004 and 000005
- `RTS-FRZ-000007` — Outcome Learning and Skill Promotion
  - type: feature
  - status: FROZEN
  - NOT_APPROVED
  - depends on 000004–000006

Do not weaken the existing gates: current BUILD_NOW assessment, current PASS Preflight, explicit human approval, and WIP limit 1.

## Goal

Create a deterministic, append-only, Git-native inventory that answers:

- Which repository owns each capability or asset?
- Which asset is canonical, reference-only, reusable, frozen, superseded, or unsafe to import?
- What exact repository/path/ref was inspected?
- What can be reused directly, adapted, or used only as design evidence?
- Are there ownership conflicts, stale refs, license gaps, visibility leaks, or duplicated canonical claims?

The system must help future development reuse prior work without flattening all repositories into RTS core.

## Architectural boundary

- RTS remains the canonical structural ledger and governance home.
- The asset manifest records **metadata and references**, not copied repository bodies.
- Private repository content must not be exposed in public records. For private repositories, store only safe metadata and intentionally approved asset descriptors; never store secrets, customer data, prompt bodies, raw private paths that reveal sensitive content, or connector credentials.
- Do not silently promote adjacent repository behavior into RTS core.
- Do not execute external tools or mutate other repositories.
- Do not auto-start future implementation.

## Package and storage model

Add a focused package such as `asset_manifest/` with standard-library-only runtime code. The exact naming may be adjusted if a clearer existing convention exists, but keep it isolated from `freezer/` implementation code.

Recommended structure:

```text
asset_manifest/
├── README.md
├── __init__.py
├── cli.py
├── store.py
├── validation.py
├── schemas/
│   └── snapshot.schema.json
├── templates/
│   └── snapshot_input.json
├── snapshots/
│   ├── v001.json
│   └── current.json
├── index/
│   ├── repositories.json
│   ├── assets.json
│   └── ownership.json
└── manifests/
    └── manifest.sha256
```

The implementation may use an equivalent layout when justified, but must preserve immutable versions plus rebuildable indexes.

## Snapshot contract

A snapshot must include at least:

- schema version
- snapshot version
- generated/observed timestamp
- source refs used for the survey
- repository records
- asset records
- known gaps and assumptions
- explicit public/private handling statement

Repository records should include:

- repository full name
- visibility (`public`, `private`, or `unknown`)
- default branch
- observed ref/commit when known
- ecosystem role
- lifecycle status (`ACTIVE`, `PARTS`, `FREEZE`, `INACTIVE`, etc.)
- canonical responsibility
- allowed reuse boundary

Asset records should include:

- stable asset ID
- repository full name
- path or safe logical locator
- asset kind (`code`, `schema`, `test`, `workflow`, `documentation`, `data`, `design`, `runtime`, `process`, or another validated enum)
- capability name
- source ref/commit
- canonicality (`CANONICAL`, `REFERENCE`, `REUSABLE`, `EXPERIMENTAL`, `FROZEN`, `SUPERSEDED`)
- reuse mode (`DIRECT`, `ADAPT`, `REFERENCE_ONLY`, `NO_REUSE`)
- license status (`COMPATIBLE`, `REVIEW_REQUIRED`, `INCOMPATIBLE`, `NOT_APPLICABLE`, `UNKNOWN`)
- sensitivity (`PUBLIC`, `PRIVATE_METADATA_ONLY`, `RESTRICTED`)
- consumer/destination candidates
- notes, risks, and evidence refs

Use strict validation and reject unknown enum values, duplicate asset IDs, impossible version relationships, and malformed refs.

## Derived indexes and checks

Rebuild deterministic indexes from the current immutable snapshot:

1. Repository index
2. Asset index
3. Ownership/capability index

Verification must detect at least:

- two or more assets claiming `CANONICAL` ownership of the same capability without an explicit relationship
- a public snapshot containing a restricted/private body or disallowed locator
- `DIRECT` reuse with incompatible/unknown license when a license is required
- missing repository for an asset
- stale or mismatched current pointer
- stale indexes
- manifest hash mismatch
- duplicate asset IDs
- invalid refs or missing required fields

Conflicts should be reported deterministically and should fail verification when they violate a hard rule. Advisory ambiguity may be represented separately, but do not hide it.

## CLI

Provide a small, documented CLI. Minimum commands:

```text
python -m asset_manifest.cli create --input <snapshot.json>
python -m asset_manifest.cli verify
python -m asset_manifest.cli list-repos
python -m asset_manifest.cli list-assets
python -m asset_manifest.cli show <asset-id-or-repository>
python -m asset_manifest.cli diff <old-version> <new-version>
python -m asset_manifest.cli reindex
```

`create` must append a new immutable version and update `current.json`, indexes, and manifest. Existing immutable versions must never be overwritten.

## Seed inventory

Seed `v001` from the current RTS ecosystem classification. Cover all currently owned repositories visible in the registry/listing, including the canonical, active, parts, frozen, and inactive/test shelves.

At minimum, represent the known roles of:

- RTS
- RTS-Minimal-Runtime
- RTS-AGE
- RTS-minicompany
- rts01-offer
- seminar-compass
- nobutakayamauchi
- RTS-Skills-
- RTS-MCP-Packs
- RTS-Hermes-Drive
- RTS-Design-Research
- rts-dev-protocol
- RTS-Talent-Registry
- RTS-Signal-Feeds
- rts-video-flow
- AIX
- codex-connector-test
- ryoushuushotesutoyou
- rts-lite

Use existing `docs/ecosystem/REPO_MAP.md`, `docs/ecosystem/PROJECT_REGISTRY.md`, repository position documents, and exact Git refs as evidence. Private repositories must be represented only through safe metadata.

Seed key reusable assets discovered in the feasibility survey, including:

- RTS FREEZER and Preflight/Build Assessment contracts
- RTS execution/evidence schemas and reconstruction rules
- RTS Kernel state/index/audit concepts, clearly marked as legacy/repair-required where appropriate
- RTS-Skills feature-build and verification-runner assets
- RTS-AGE provider adapter, local dry-run, decision log reader/report assets
- RTS-Minimal-Runtime reference flow
- RTS-Hermes-Drive orchestration responsibility
- RTS-MCP-Packs connector/permission responsibility
- RTS-minicompany trace and human-gated business workflow
- legacy evolution, self-audit, and success-replication specifications as reference assets, not automatically active runtime

Do not claim that a file was fully reviewed unless it was actually inspected. Preserve gaps explicitly.

## Tests

Add focused tests covering at least:

- valid seed snapshot and deterministic indexes
- immutable version creation
- duplicate asset ID rejection
- conflicting canonical ownership rejection
- private/restricted leakage rejection
- missing repository reference rejection
- invalid enum rejection
- stale current pointer/index rejection
- manifest verification
- deterministic diff output
- all seeded repositories represented
- FREEZER records 000003–000007 and their gates/states

Update old FREEZER tests that assumed only two seed items or a specific next ID. Prefer assertions based on discovered maximum IDs and explicit fixtures instead of brittle global counts.

## CI and verification

Integrate verification into the existing FREEZER workflow or add a narrowly scoped workflow only when necessary. Required final checks:

```text
python -m asset_manifest.cli verify
python -B -m unittest discover -s tests -v
python -m freezer.cli verify
python -m freezer.build_assessment verify
```

Also verify rebuilt indexes/manifests in a temporary copy or deterministic rebuild step so committed generated files cannot drift.

## Completion conditions

This child is complete only when:

- all five FREEZER records exist with correct parent/child boundaries
- parent 000003 is decomposed and not approved
- only 000004 is completed
- v001 covers all 19 known repositories without leaking private content
- CLI and deterministic indexes work
- hard conflict/privacy/license rules are enforced
- manifest verification passes
- full tests and CI pass
- review findings are resolved
- no candidate 000005–000007 implementation has begun
