# Governed Outcome Evidence Corpus v1 — Implementation Task

## Purpose

Create the first local, privacy-safe corpus required by the readiness assessment for `RTS-FRZ-000007 Outcome Learning and Skill Promotion`.

This is research infrastructure only. It must not implement outcome learning, Skill mutation, promotion, retirement, or adjacent-repository writes.

## Required corpus

Commit at least three reconstructable outcome bundles with distinct scenarios:

1. successful controller path
2. failed or escalated controller path
3. recovery or rollback-relevant controller path

Each bundle must include:

- canonical `execution_record`
- one or more canonical `evidence_ref` records
- controller plan and authorization fingerprints
- terminal state and cumulative budget usage
- `VERIFIED`, `UNVERIFIED`, or `ASSUMED` classification
- measurable success, failure, and observed criteria
- deterministic bundle fingerprint
- evidence-file SHA-256 integrity
- `SIMULATED_ONLY`
- `promotion_eligibility: NOT_ELIGIBLE`

## Classification semantics

Classification applies to the exact claim represented by the bundle.

- A simulated successful path cannot be `VERIFIED` as real-world success.
- A bounded safety behavior, such as deterministic budget escalation, may be `VERIFIED`.
- A rollback-relevant inference without an executed mutation or restore remains `ASSUMED`.

## Safety boundary

The package must:

- read committed local JSON only
- make no network or provider calls
- use no subprocess or shell execution
- perform no publish, deploy, send, schedule, billing, customer, or adjacent-repository operation
- reject path traversal
- reject external-execution claims
- reject private-content field names
- never mark a simulated bundle promotion eligible
- leave `RTS-FRZ-000007` `FROZEN / NOT_APPROVED`
- create no Implementation Preflight

## Required package

```text
outcome_evidence/
  __init__.py
  cli.py
  corpus.py
  models.py
  README.md
  schemas/outcome_bundle.schema.json
  examples/*.json
  evidence/*.json
tests/test_outcome_evidence.py
```

## CLI

```text
python -m outcome_evidence.cli verify
python -m outcome_evidence.cli list
python -m outcome_evidence.cli show BUNDLE_ID
```

## Verification

Test at minimum:

- committed corpus verifies
- at least three bundles and all required scenarios exist
- bundle fingerprint mutation fails closed
- evidence hash mutation fails closed
- external-execution claims fail closed
- simulated success cannot claim `VERIFIED`
- promotion eligibility cannot be widened
- private-content fields fail closed
- evidence path traversal fails closed
- duplicate bundle and evidence IDs fail closed
- verification is deterministic and read-only

## Next boundary

After this corpus is merged, the next research artifact is the immutable baseline/candidate Skill regression and rollback dataset. `RTS-FRZ-000007` must not be reassessed until the remaining readiness conditions are satisfied.
