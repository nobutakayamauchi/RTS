# Thin RTS — Encrypted Cloud Custody v0 Candidate

Status: `IMPLEMENTED_CANDIDATE / NOT_YET_LIVE_VERIFIED`

This directory is the smallest custom orchestration surface currently allowed to survive the Destroy Loop for encrypted evidence custody.

It does **not** implement cryptography, cloud storage, key management, or a new backup engine.

External responsibilities:

- OpenPGP encryption/decryption: GnuPG (`gpg`)
- first object-storage adapter: Google Cloud CLI (`gcloud storage`)
- cloud authentication, transport, retries, IAM, provider durability: provider/tool responsibility
- private recovery-key custody: separate operator-controlled trust boundary

Thin RTS owns only:

- deterministic evidence packaging;
- SHA-256 binding before and after encryption;
- explicit recipient/key-epoch binding;
- refusal to encrypt when the selected recipient has a secret-key record on the producer;
- opaque object naming;
- upload + remote generation/size observation;
- recovery receipt/card generation;
- download/decrypt/manifest verification;
- PASS / ERROR / APPROVAL_REQUIRED boundaries.

## `/goal` semantics

The `goal` subcommand intentionally runs until one of three boundaries:

- `ERROR` — a required invariant/tool/key/target check failed;
- `APPROVAL_REQUIRED` — local bundle + ciphertext were created and verified enough to show the exact planned remote write, but no cloud write was executed;
- `LIVE_UPLOAD_VERIFIED` — an explicitly approved upload completed and the remote object generation/size were observed.

A verified upload is **not** full completion. The next hard gate is a fresh-environment restore with a separated recovery identity.

## Required separation

The producer must have the public recipient keys but must not have secret-key records for those selected recipients.

The candidate requires at least two recipient fingerprints for `/goal` so the first live experiment cannot silently collapse to one irreplaceable recovery path.

Recovery identities must be created and stored outside the producer/server and outside the evidence-cloud trust boundary.

## Input contract

`--input` points at a completed evidence-bundle directory. This layer does not decide legal relevance. The input should already contain the originals/derivatives/custody/reproduction material required by the upstream legal-evidence gate.

Symlinks are rejected. File paths are sorted. Tar metadata is normalized. The archive contains `RTS_BUNDLE_MANIFEST.json` with each source path, byte size and SHA-256.

## Private runtime paths

`--work` and `--recovery-dir` must point outside the public repository.

Do not commit:

- evidence originals;
- tar/gzip bundles;
- ciphertext generated for real evidence;
- recovery receipts/cards tied to real cases;
- public or private recovery-key exports;
- provider credentials;
- account/project/bucket identifiers unless intentionally approved for publication.

## GCS target contract

The first provider adapter requires a dedicated prefix such as:

`gs://<user-selected-bucket>/<dedicated-private-prefix>`

Bucket root is rejected.

Existing unrelated render/build buckets are **not automatically authorized** as evidence-custody destinations merely because they are visible to the current credential.

## Local validation

Run the pure unit tests before a live experiment:

`python3 -m unittest thin-rts/cloud-custody/test_custody.py`

Run tool/recipient/target checks using `doctor`.

Run `goal` without `--approve-live-upload` first. That produces the exact planned object URI and an `APPROVAL_REQUIRED` boundary without mutating the cloud.

Only after the target and recovery-key separation are deliberately accepted should the same invocation be repeated with `--approve-live-upload`.

## Fresh recovery

`restore` requires a recovery receipt that records the expected provider object generation, ciphertext SHA-256, and plaintext bundle SHA-256.

The restore path:

`download -> verify ciphertext digest -> verify remote generation -> decrypt -> verify plaintext bundle digest -> safe extract -> verify internal manifest`

Opening a decrypted file without those checks is not PASS.

## Known incomplete gates

This candidate does not yet prove:

- real live upload/write authority to a dedicated evidence-custody prefix;
- fresh-environment recovery;
- alternate recovery recipient success;
- wrong-key failure;
- one-byte ciphertext mutation detection;
- truncated/missing/stale object handling in a live provider workload;
- anti-zubora scheduling/retry automation;
- provider replacement with a second transport;
- integration with automatic evidence triage/event/legal-watch layers.

Therefore:

`ENCRYPTED_CLOUD_CUSTODY = NOT_COMPLETE`

`PROMOTION = NOT_AUTHORIZED`
