# METEOR ATTACK 0001 — Encrypted Cloud Custody Prototype

Timestamp: **2026-08-11 JST**

Status: `ACTIVE / PROTOTYPE MUST DIE BEFORE IMPLEMENTATION`

Method authority: WITNESS Meteor Gate.

This candidate is deliberately treated as a **prototype under `/goal`**, not as an implementation entitled to survive.

The burden of proof is on the candidate. Green happy-path CI is insufficient.

## Frozen outcome

Preserve a dispute-ready evidence bundle using existing crypto and cloud capabilities with the smallest surviving glue surface, while keeping long-term decryption secrets outside the producer/cloud trust boundary and preserving independently verifiable recovery.

## Witness ordering

`OUTCOME -> NECESSITY -> EXTERNAL FIRST -> REALITY -> EVIDENCE -> BUILD LAST -> RETEST`

Per-responsibility verdicts remain limited to:

`DROP / EXTERNALIZE / GLUE / IRREDUCIBLE_BUILD`

No existing code receives a survival right because it has already been written.

## Candidate under attack

Current prototype composition:

- deterministic packaging: Python stdlib glue;
- content digests: SHA-256;
- public-key encryption: external GnuPG;
- first provider adapter: external `gcloud storage`;
- Thin RTS glue: manifest/custody binding, approval boundary, provider metadata observation, recovery verification.

## Attack set A — package identity

The prototype must fail closed when:

1. the evidence directory is empty;
2. source evidence collides with the reserved internal manifest name;
3. a manifest entry attempts `..` / absolute-path escape;
4. duplicate manifest paths exist;
5. restored output contains unmanifested extra files;
6. extraction is attempted into a dirty/non-empty destination that could mix stale data with restored evidence;
7. deterministic packaging cannot reproduce identical bytes from identical input.

A verifier that only checks listed files but silently accepts extra or escaping material is dead.

## Attack set B — provider race / stale substitution

Cloud Storage metadata and object data are separate observations. The prototype must not claim that an unconditioned download is the recorded generation merely because a later metadata request reports that generation.

Required surviving behavior:

- new-object upload uses a generation precondition equivalent to `ifGenerationMatch=0`, not a best-effort existence check;
- restore binds the data retrieval itself to the recorded immutable generation, rather than downloading an unconstrained latest object and checking metadata afterward;
- stale/replaced generation produces FAIL/ERROR, never PASS.

## Attack set C — trust-boundary collapse

Before live `/goal` can reach cloud mutation:

- producer has public recipient material only for selected recovery recipients;
- producer must not hold corresponding secret-key records;
- at least two recovery recipients remain required for the first experiment;
- real recovery-package paths and work paths must be outside the public repository;
- provider credentials, recovery secrets, plaintext evidence and live receipts must never become tracked repository artifacts.

## Attack set D — authority

Prototype construction and local destructive testing are authorized under `/goal`.

The following remain separate authority boundaries:

- live cloud mutation;
- key generation/import of private recovery material onto the producer;
- merge/promotion;
- publication of account/bucket/project/evidence identifiers.

If a boundary is reached, `/goal` must stop with `APPROVAL_REQUIRED` rather than silently cross it.

## Initial verdict

`PROTOTYPE_SURVIVAL = UNPROVEN`

`LIVE_UPLOAD = NOT_AUTHORIZED_BY_THIS_DOCUMENT`

`PROMOTION = NOT_AUTHORIZED`

The test suite is intentionally expanded with red-team expectations. A red CI result is **successful Meteor evidence**, not a development failure.
