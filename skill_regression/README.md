# Governed Skill Regression Dataset v1

This package supplies the baseline/candidate comparison and rollback evidence required by the readiness work that precedes `RTS-FRZ-000007`.

It is deliberately **not** a Skill promotion engine.

## Pinned baseline

The baseline is a repository-local snapshot of:

```text
nobutakayamauchi/RTS-Skills-
commit: 66991529519795e62d61874d6a6197ae14e01967
path: rts-skills/bundles/feature-build.md
```

The copied content, source metadata, structured contract, and SHA-256 fingerprint are immutable evaluation inputs.

## Candidate fixture

The candidate is local to this repository. It adds:

- a `rollback-snapshot-writer` step
- an immutable rollback output
- explicit human-approval and rollback safety rules

It is an evaluation fixture only. It is not published to `RTS-Skills-` and is never promotion eligible.

## Deterministic comparison

The dataset is explicitly linked to `RTS-OUTCOME-000001` through `RTS-OUTCOME-000003`, then applies six fixed fixtures:

- standard feature-build compatibility
- rollback-ready feature build
- promotion authority boundary
- adjacent-repository boundary
- tiny one-step non-applicability
- urgent break/fix non-applicability

The immutable v1 thresholds are:

```text
regressions: 0
safety failures: 0
minimum improvements: 2
candidate applicable pass rate: 1.0
rollback snapshot: required
```

The committed result is recomputed from structured contracts. No model judgment, network call, provider call, subprocess, shell command, or adjacent-repository mutation is used.

## Result boundary

A passing evaluation produces:

```text
recommendation: RESEARCH_READY
promotion_eligibility: NOT_ELIGIBLE
```

`RESEARCH_READY` means only that the candidate fixture, deterministic regression set, and rollback evidence are suitable inputs for a future FREEZER reassessment. It does not authorize promotion, publication, mutation, or an Implementation Preflight.

## Commands

```text
python -m skill_regression.cli verify
python -m skill_regression.cli evaluate
python -m skill_regression.cli summary
```

`verify` is read-only. It checks exact schemas, source and content hashes, canonical fingerprints, path containment, privacy-sensitive keys, cross-artifact references, fixed thresholds, deterministic fixture outcomes, rollback integrity, and the permanent `NOT_ELIGIBLE` boundary.
