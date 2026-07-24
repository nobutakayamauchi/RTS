# RTS-FRZ-000007 Outcome Learning and Skill Promotion — Readiness Assessment

## Decision

`RESEARCH_REQUIRED`

`RTS-FRZ-000007` remains:

```text
FROZEN / NOT_APPROVED
```

No Implementation Preflight is created by this change, because the current Build Assessment does not recommend `BUILD_NOW`.

## Verified current state

- `RTS-FRZ-000004`, `RTS-FRZ-000005`, and `RTS-FRZ-000006` are completed.
- RTS has canonical minimal `execution_record` and `evidence_ref` contracts.
- The Governed Execution Controller can emit deterministic `SIMULATED_ONLY` execution results.
- Legacy evolution documents retain proposal-only behavior and human adoption authority.
- RTS-Talent-Registry promotion rules require repeated successful evaluations, rollback or retirement paths, evidence states, and governance approval.
- No committed privacy-safe corpus of at least three governed run outcomes linked to evidence was found.
- No canonical baseline/candidate regression dataset or immutable skill rollback snapshot was found.
- The Asset Manifest locator for the RTS-Skills verification runner currently returns `404` and must be refreshed before implementation relies on it.

## Why implementation does not start

The current FREEZER item explicitly requires:

1. At least three governed run outcomes.
2. Defined Skill promotion and rollback datasets.
3. Evidence-linked success rather than declaration.
4. Regression comparison before promotion.
5. Human approval for any promotion.

Those gates are not satisfied by unit-test fixtures or controller dry-run success. `SIMULATED_ONLY` output is not real-world verified success.

## Required evidence corpus

A future reassessment may proceed only after a local, privacy-safe corpus contains at least three reconstructable outcome bundles.

Each bundle must contain:

- a canonical `execution_record`
- one or more canonical `evidence_ref` records
- controller plan and authorization fingerprints
- terminal controller state and budget usage
- explicit outcome classification: `VERIFIED`, `UNVERIFIED`, or `ASSUMED`
- measurable success or failure criteria
- no prompts, secrets, credentials, customer data, provider payloads, or private repository bodies

The corpus should include variation rather than three copies of the same success path. At minimum it should exercise a successful outcome, a failed or escalated outcome, and a recovery or rollback-relevant outcome.

## Required comparison and promotion contracts

Before Implementation Preflight, define:

- immutable baseline Skill version
- candidate Skill version
- deterministic regression fixtures
- acceptance and rejection thresholds
- evidence completeness rules
- promotion proposal schema
- human decision record
- rollback snapshot and retirement path
- destination ownership and mutation boundary

## v1 boundary after reassessment

The first implementable version should remain proposal-only:

```text
governed outcome bundles
→ evidence completeness validation
→ deterministic classification
→ baseline/candidate comparison
→ learning proposal
→ human decision required
```

It must not:

- promote or mutate a Skill automatically
- write to adjacent repositories
- treat simulated output as verified success
- weaken evidence, regression, rollback, or approval gates
- call networks, providers, subprocesses, publish, deploy, send, or schedule
- rewrite RTS core rules
- ingest private payloads

## Reassessment trigger

Create a new append-only Build Assessment only when all are true:

- at least three governed outcome bundles exist
- outcome/evidence linkage verifies
- baseline and candidate datasets exist
- rollback snapshot exists
- the RTS-Skills verification-runner locator is refreshed or replaced with an inspected current asset
- human approval explicitly authorizes a proposal-only v1 assessment

Until then, `RTS-FRZ-000007` remains frozen.
