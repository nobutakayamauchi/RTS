# Human Review Ledger v1

`human_review_ledger` is a deterministic, repository-local, append-only record contract for **human review evidence**.

It does not create a reviewer, infer a human identity, approve its own proposal, apply or mutate a Skill, authorize a merge, write another repository, or perform an external action.

## Committed v1 state

The committed ledger is intentionally empty:

- `record_count: 0`
- `state: NO_DECISIONS`
- `approval_status: NOT_APPROVED`
- `application_status: NOT_APPLIED`

A blank template is provided for a future separately authored human record. The CLI has no command that creates or commits a decision.

## Commands

```text
python -m human_review_ledger.cli verify
python -m human_review_ledger.cli summary
python -m human_review_ledger.cli summary --as-of 2026-12-31T00:00:00Z
python -m human_review_ledger.cli blank-template
```

`verify` checks policy and reviewer scope fingerprints, fail-closed JSON contracts, decision-file digests, sequence continuity, prior-record hash linkage, separation of duties, source fingerprints, privacy and path boundaries, committed summary freshness, and the permanent non-application authority boundary.

`summary` is read-only. A structurally valid `APPROVE` record is review evidence only; stale or expired evidence derives `NOT_APPROVED`, and every state remains `NOT_APPLIED`.

## Decision vocabulary

- `APPROVE`
- `REJECT`
- `RETURN_FOR_REVISION`
- `EXPIRE`
- `SUPERSEDE`

Existing records are immutable. `EXPIRE` and `SUPERSEDE` append a new record that links the immediately prior decision fingerprint; they never rewrite history.

## Identity boundary

The ledger records an asserted human identity and its declared source. Repository-local v1 does not claim cryptographic identity proof. The reviewer must differ from both the proposal generator and the implementation identity, and the allowed reviewer role must exist in the current policy and reviewer-scope records.

## Privacy boundary

The ledger stores identifiers, rationale, conditions, and fingerprints only. Raw prompts, credentials, secrets, customer data, provider payloads, and private repository bodies are rejected.
