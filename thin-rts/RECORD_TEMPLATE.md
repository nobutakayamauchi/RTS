# Thin RTS — Material Transition Record

> Record only material facts/references required for reconstruction. Do not copy unnecessary sensitive payloads.

- `record_id`:
- `timestamp_jst`:
- `intent_summary`:
- `source_fingerprint_or_reference`:
- `constraints`:
- `assumptions`:
- `authority_holder`:
- `authority_scope`:
- `action_reference`:
- `deployment_identity_reference`:
- `outcome_reference`:
- `classification`: `PASS / FAIL / BLOCKED / UNKNOWN / EVIDENCE_INSUFFICIENT`
- `learning_or_review_reference`:
- `promotion_authority_reference`:
- `next_state_reference`:
- `unknowns`:

## Reconstruction checks

- [ ] Intent can be distinguished from implementation.
- [ ] Authority and scope are explicit.
- [ ] Action/execution evidence exists.
- [ ] Runtime/deployment identity is proven when runtime claims are made.
- [ ] Outcome is bound to the relevant action/execution.
- [ ] Review/learning is not silently promoted into authority.
- [ ] State/capability change has separate authority when required.
- [ ] Stale/replayed/mismatched evidence is not accepted as current evidence.
- [ ] Raw secrets/private data are not retained merely for convenience.
- [ ] Missing material evidence remains UNKNOWN/BLOCKED/EVIDENCE_INSUFFICIENT.
