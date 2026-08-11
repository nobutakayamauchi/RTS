# AUTOPSY 0002 — Trust-Boundary Rotation

Observed CI run: `Cloud Custody Candidate Tests` run 14

Status: `PROTOTYPE_KILLED_AGAIN / PATCH_REQUIRED`

The original eight death causes stayed fixed, but a rotated WITNESS attack found a second class of failures.

## Material death causes

1. two apparent recovery recipients could be the primary fingerprint and subkey fingerprint of the same OpenPGP key family, defeating the intended two-recipient recovery separation;
2. free-form/newline authority text could enter custody metadata instead of a bounded opaque authority reference;
3. GCS target validation accepted generation fragments, query-like material and control characters;
4. upload did not bind provider transfer integrity to the local ciphertext through provider MD5 validation;
5. upload did not send the existing provider `--content-md5` integrity check;
6. restore attempted to read a receipt inside the public repository instead of rejecting the trust-boundary violation first.

## Surviving prior fixes

All eight failures from `AUTOPSY_0001.md` passed unchanged under the same workload.

This is the intended Darwin behavior: inherited death causes remain in the test corpus.

## Patch authorization

Only the demonstrated glue gaps above are authorized for patching.

No custom crypto, object store, key vault or broader platform surface is authorized.
