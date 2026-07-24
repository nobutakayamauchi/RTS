# Refresh Promotion Assets and Reassess RTS-FRZ-000007

## Decision

This change refreshes the stale promotion/verification asset references and appends Build Assessment `RTS-BA-000007-002`.

The reassessment recommendation is:

```text
BUILD_NOW
decision_score: 71.41
```

This is a build-value recommendation only. `RTS-FRZ-000007` remains `FROZEN / NOT_APPROVED`, has no Implementation Preflight, and is not selected for implementation by this change.

## Asset Manifest v2

The append-only snapshot:

- preserves Asset Manifest v1
- replaces stale `RTS-AM-A0011` with the canonical RTS `outcome_evidence/` verifier
- records `skill_regression/` as the canonical deterministic regression and rollback dataset
- records the current pinned RTS-Skills `skill_promotion_review` manifest as reference-only
- updates current pointers, derived indexes, and SHA manifests

The former RTS-Skills verification-runner locator is not silently rewritten in history. It remains visible in `v001`; `v002` records the inspected replacement.

## Reassessment evidence

Since `RTS-BA-000007-001`, RTS gained:

- three governed, privacy-safe, reconstructable outcome bundles
- exact VERIFIED / UNVERIFIED / ASSUMED classification
- deterministic baseline/candidate regression fixtures
- immutable acceptance thresholds
- immutable rollback snapshot
- fail-closed verification of fingerprints, evidence hashes, paths, privacy, and promotion ineligibility
- a pinned current promotion-review contract from RTS-Skills

## Hard boundary

This change does not:

- create an Implementation Preflight
- change FREEZER item status or build authority
- implement outcome learning or proposal generation
- promote, retire, publish, or mutate a Skill
- write to RTS-Skills or any adjacent repository
- authorize network, provider, subprocess, shell, publish, deploy, send, or schedule operations
- treat SIMULATED_ONLY results as external success
- ingest prompts, secrets, credentials, customer data, provider payloads, or private repository bodies

## Next gate

A separate explicitly approved task may create an Implementation Preflight for a proposal-only v1. That Preflight must preserve WIP limits, human approval, regression, rollback, privacy, and no-adjacent-write boundaries.
