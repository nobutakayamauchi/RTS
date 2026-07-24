# Governed Skill Regression Dataset v1 — Implementation Contract

## Purpose

Create the second research prerequisite for `RTS-FRZ-000007 Outcome Learning and Skill Promotion`: an immutable baseline/candidate Skill comparison with deterministic fixtures and a rollback snapshot.

## Source baseline

The baseline is pinned to the public RTS-Skills asset:

```text
repository: nobutakayamauchi/RTS-Skills-
commit: 66991529519795e62d61874d6a6197ae14e01967
path: rts-skills/bundles/feature-build.md
```

The source repository remains unchanged.

## Candidate scope

The candidate is a repository-local fixture derived from the pinned baseline. It adds rollback-snapshot preparation and explicit human-approval boundaries. It is not a publication candidate and must remain `NOT_ELIGIBLE`.

## Required artifacts

- pinned baseline content and metadata
- local candidate content and metadata
- structured baseline and candidate contracts
- explicit references to the three governed outcome bundles
- deterministic functional and safety fixtures
- immutable acceptance/rejection thresholds
- rollback snapshot that restores the baseline content hash
- committed deterministic evaluation result
- read-only validator and CLI
- mutation and boundary tests
- governed CI coverage

## Acceptance policy

The candidate is `RESEARCH_READY` only when all are true:

- regressions equal zero
- candidate safety failures equal zero
- candidate improves at least two fixtures
- candidate passes all applicable fixtures
- rollback snapshot reconstructs the exact baseline
- all fingerprints and file hashes verify
- no external execution or adjacent-repository mutation is claimed

## Permanent prohibitions

This package must not:

- promote, publish, retire, or mutate a Skill
- write to RTS-Skills or any adjacent repository
- create a promotion proposal or human decision record
- create or pass the `RTS-FRZ-000007` Implementation Preflight
- change FREEZER status or build authority
- use network, provider, subprocess, shell, publish, deploy, send, or schedule
- ingest prompts, secrets, credentials, customer data, provider payloads, or private repository bodies
- weaken the committed v1 thresholds

## Verification

```text
python -m skill_regression.cli verify
python -B -m unittest tests.test_skill_regression -v
```
