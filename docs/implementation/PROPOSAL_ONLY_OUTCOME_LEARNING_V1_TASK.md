# Proposal-Only Outcome Learning v1 — Implementation Contract

## Purpose

Implement the bounded repository-local proposal generator authorized for `RTS-FRZ-000007`. It may transform governed evidence into a deterministic request for human review. It may not approve or apply a Skill change.

## Required artifacts

- exact proposal schema and validator
- exact review-record schema and validator
- deterministic generator linking all source fingerprints
- committed `REVIEW_REQUIRED` proposal
- committed `PENDING` review request
- read-only verifier and CLI
- fail-closed privacy, authority, self-review, determinism, and source-drift tests
- governed CI coverage

## Permanent v1 boundaries

- all outcome evidence remains `SIMULATED_ONLY`
- the regression result remains `RESEARCH_READY / NOT_ELIGIBLE`
- proposal approval remains `NOT_APPROVED`
- application remains `NOT_APPLIED`
- the generator cannot emit an approved decision
- a final decision requires a separately authored explicit human identity
- even a human review record cannot authorize Skill mutation or adjacent-repository writes in v1
- no network, provider, subprocess, shell, external execution, publication, deployment, messaging, scheduling, customer action, or automatic rollback
- no raw prompts, credentials, customer data, provider payloads, or private repository bodies

## Verification

```text
python -m learning_proposals.cli verify
python -B -m unittest tests.test_learning_proposals -v
python -B -m unittest discover -s tests -v
```

## Completion meaning

Completion means the proposal-only package is reconstructable and review-ready. It does not mean the candidate Skill is approved, applied, published, externally verified, or promoted.
