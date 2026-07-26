# Acceptance Criteria v1

## Functional

- Loads only the fixed RTS source set.
- Produces at least 10 candidate records.
- Produces contribution and value records for each candidate.
- Builds a review queue and one NOT_PUBLISHED draft.

## Evidence integrity

- Every candidate links to exact sources.
- Missing or drifted source fails closed.
- VERIFIED cannot be assigned from generated prose alone.
- Conflicts are preserved.

## Human authority

- No automatic approval.
- Draft generation uses approved records only.
- Publication, outreach, contracts, and external action are absent.

## Privacy

- Public RTS evidence only.
- Credentials and sensitive CASE data are rejected.
- Third-party personal details are not copied into output drafts.

## Determinism

- Canonical JSON and SHA-256 fingerprints.
- Same source/config reproduces the same pre-review candidates.
- Manifest detects extra, missing, or changed governed files.

## Scope and cost

- WIP=1.
- No multi-repository adapter.
- No platform or matching subsystem.
- Governance does not exceed the bounded implementation without an explicit warning.

## Usability

- Human can understand evidence, contribution, value, uncertainty, and action required without rereading the full PR history.
