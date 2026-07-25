# Proposal-Only Outcome Learning v1

This package turns the governed outcome corpus and deterministic Skill regression result into a **review request**, not a Skill promotion.

## Inputs

The generator reads only committed repository-local records:

- `RTS-OUTCOME-000001` through `RTS-OUTCOME-000003`
- `RTS-SKILL-REGRESSION-000001`
- `RTS-SKILL-REGRESSION-RESULT-000001`
- `RTS-SKILL-ROLLBACK-000001`
- candidate snapshot `RTS-SKILL-SNAPSHOT-000002`

Every input is linked by its canonical fingerprint. All outcome inputs remain `SIMULATED_ONLY`; the regression result remains `RESEARCH_READY / NOT_ELIGIBLE`.

## Output boundary

The committed proposal is permanently bounded to:

```text
proposal_status: REVIEW_REQUIRED
recommendation: REQUEST_HUMAN_REVIEW
approval_status: NOT_APPROVED
application_status: NOT_APPLIED
```

The companion review record is `PENDING` and unassigned. It is a review request, not a human decision.

The package cannot:

- approve its own proposal
- mutate, publish, promote, retire, or roll back a Skill
- write to RTS-Skills or another adjacent repository
- claim external success from simulated evidence
- use network, provider, subprocess, shell, deploy, send, or schedule capabilities
- ingest raw prompts, credentials, customer data, provider payloads, or private repository bodies

## Commands

```text
python -m learning_proposals.cli verify
python -m learning_proposals.cli generate
python -m learning_proposals.cli review-template
python -m learning_proposals.cli summary
```

`generate` and `review-template` print deterministic records to stdout. They do not write files or create approved decisions. `verify` is read-only and fails closed on stale fingerprints, widened authority, self-review, private fields, forbidden imports, or source drift.
