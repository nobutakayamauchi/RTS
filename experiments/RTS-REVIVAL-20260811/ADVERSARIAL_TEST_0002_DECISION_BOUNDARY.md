# Thin RTS Adversarial Test 0002 — Decision Boundary Tamper/Recovery

Timestamp: **2026-08-11 19:00 JST**

## Target

Legacy responsibility formerly implemented by `scripts/decision_boundary_append.py`: preserve explicit authority boundary plus state linkage.

## Attack

The valid committed decision boundary created in commit:

`fce1160d072c4bf23e8cd95f4016be5f940dea29`

was deliberately replaced by an invalid broader-scope/self-asserted promotion fixture in:

`691b1ceb8685ca8599052751ebba0ab31ea52875`

The invalid mutation claimed only synthetic test values and was explicitly marked as an attack fixture.

## Verification

GitHub was queried at the pre-attack commit. The original boundary remained exactly recoverable, including:

- experiment-only scope;
- explicit statement that merge/promotion to `main` was not authorized;
- state reference before the boundary;
- `promotion_authority: NONE_YET`.

The current file was then restored from Git history in:

`d0d2da0de4d5a80223e2da63afbf424bc6324cb3`

The restored blob exactly matches the pre-attack blob:

`ce175e99da084d041d82ab1116c2f00cfcb978b9`

## Verdict

`PASS`

The authority record can be changed in a later Git commit, but the historical boundary cannot be silently erased from Git history by that ordinary mutation. Reconstruction can distinguish the valid earlier boundary, the attack mutation, and the later restoration.

For this workload, the legacy Python append script did not provide an irreducible capability beyond Git/GitHub history plus a thin semantic boundary record.

### Classification after attack

- authority-boundary invariant: `INHERIT_PRINCIPLE`
- Git/GitHub durable history: `EXTERNALIZE`
- semantic record: `GLUE_ONLY`
- `scripts/decision_boundary_append.py`: `ARCHIVE`
- new custom append service/runtime: `NOT_AUTHORIZED`
