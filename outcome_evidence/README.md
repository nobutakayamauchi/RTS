# Governed Outcome Evidence Corpus v1

This package supplies a local, privacy-safe research corpus for the readiness work that precedes `RTS-FRZ-000007`.

It is deliberately **not** a Skill-learning or promotion engine.

## Boundary

The committed bundles are:

- deterministic local fixtures
- `SIMULATED_ONLY`
- reconstructable from canonical execution records and evidence references
- never eligible for Skill promotion
- free of network, provider, subprocess, publish, deploy, send, schedule, or adjacent-repository mutation

A `VERIFIED` classification means only that the specific bounded controller claim is verified by committed local evidence. It never means external business or user success was verified.

## Scenarios

The corpus includes at least:

- `SUCCESS`: a locally reconstructed successful controller path, classified `UNVERIFIED`
- `ESCALATION`: a verified bounded budget escalation
- `RECOVERY`: a stopped run preserved for a rollback-relevant hypothesis, classified `ASSUMED`

## Commands

```text
python -m outcome_evidence.cli verify
python -m outcome_evidence.cli list
python -m outcome_evidence.cli show RTS-OUTCOME-000001
```

`verify` is read-only. It checks exact schemas, canonical fingerprints, evidence-file hashes, cross-record agreement, required scenario variation, privacy-sensitive keys, path containment, no external-execution claims, and the permanent `NOT_ELIGIBLE` promotion boundary.

## What this unlocks

This satisfies only the evidence-corpus research prerequisite. It does not create:

- a baseline/candidate Skill regression dataset
- acceptance or rejection thresholds
- an immutable rollback snapshot
- a promotion proposal or human decision record
- an Implementation Preflight for `RTS-FRZ-000007`
- build authority or a lifecycle transition
