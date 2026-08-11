# Thin RTS — Encrypted Cloud Custody & Recovery Requirement

Timestamp: **2026-08-11 19:46 JST**

Status: `HARD_COMPLETION_REQUIREMENT / NOT_YET_PASSED`

This requirement extends `LEGAL_EVIDENCE_COMPLETION_GATE.md`.
A future `PASS_FOR_ENGINEERING_EVIDENCE_GATE` is invalid unless this requirement also passes.

## User model

The system MUST be designed on the assumption that the primary operator:

- is poor at manual evidence filing and preservation;
- may forget recurring backup work;
- does not have legal/evidence-management expertise;
- may lose or replace a phone/computer;
- may make mistakes under stress;
- still needs to recover and explain the evidence later.

The correct response is automation and fail-closed recovery design, not a longer checklist for the operator.

## Outcome

Given a user-selected supported cloud/storage destination, Thin RTS must be able to automatically preserve a dispute-ready evidence bundle so that:

1. the cloud receives **ciphertext, not readable evidence**;
2. theft or unauthorized access to the cloud object alone does not disclose the evidence contents;
3. the encryption/decryption secret is not stored in the same trust boundary as the ciphertext merely for convenience;
4. the operator can recover the evidence after device/server loss using a deliberately separated recovery path;
5. recovery does not depend on remembering the original AI chat or manually reconstructing command history;
6. the restored bundle can be independently verified against its evidence manifest and custody history.

## External-first architecture

Thin RTS MUST NOT invent its own cryptography.

Preferred shape:

`EVIDENCE ORIGINALS + MANIFEST + CUSTODY LOG + REPRODUCTION MATERIAL`
→ `DETERMINISTIC BUNDLE LAYOUT`
→ `COMPRESSION`
→ `CLIENT-SIDE ENCRYPTION USING OFF-THE-SHELF CRYPTO`
→ `CIPHERTEXT DIGEST + UPLOAD EVENT`
→ `USER-SELECTED CLOUD/OBJECT STORAGE VIA EXTERNAL ADAPTER`
→ `REMOTE EXISTENCE / SIZE / ID CHECK`
→ `PERIODIC DOWNLOAD + DECRYPT + VERIFY DRILL`

The cloud/provider is a storage/transport dependency, not the trust root for plaintext confidentiality.

## Key separation

The unattended producer/uploader SHOULD require only encryption capability, not decryption capability.

For a public-key encryption implementation this means:

- the server/automation may retain public recipient material;
- the private decryption identity MUST NOT be stored beside the evidence ciphertext merely because it is convenient;
- compromise of the server or cloud must not automatically reveal the long-term decryption secret.

## Recovery design for a forgetful operator

A single irreplaceable key copy is NOT acceptable.

The completion test requires at least:

- one primary recovery identity held outside the evidence cloud/server trust boundary;
- one separately stored recovery copy or separately authorized recovery recipient;
- clear labels that identify which evidence generation/key epoch the recovery material covers;
- a human-readable `RECOVERY_CARD` that states what to retrieve, what tool is required, and how to verify success;
- a successful recovery drill from a fresh location using only the recovery package plus the encrypted cloud bundle.

If recovery key material is itself stored remotely, it must be independently protected (for example by a passphrase-encrypted identity file or another already-trusted secret store) and must not collapse back into the same credential boundary as the ciphertext.

## Provider adapter

The storage destination MUST be replaceable.

Thin RTS owns only a narrow upload/download contract such as:

- `put ciphertext object`
- `get ciphertext object`
- `list/version/stat object`
- `record provider object/version/reference`

Cloud-specific authentication, transport, retries, and provider APIs are externalized to an existing tool/adapter wherever possible.

No provider is mandatory merely because it was used for the first test.

## Evidence semantics

Before encryption/upload, the bundle must already contain or reference the legal-evidence structures required by `LEGAL_EVIDENCE_COMPLETION_GATE.md`.

The custody record must preserve at least:

- plaintext evidence/bundle digest before encryption;
- encryption tool + version/format identity;
- recipient/key epoch identifier without exposing the private key;
- ciphertext digest;
- upload timestamp;
- provider/object/version reference;
- actor/tool and authority;
- verification result.

Encryption is a custody transformation. It must not erase the ability to prove what protected plaintext bundle it was created from.

## Privacy and theft-resistance target

A stolen cloud archive or copied remote object should reveal as little as practical beyond unavoidable storage metadata.

The minimum requirement is encrypted content. Filename/path metadata should also be minimized or encrypted when the selected external transport/storage design supports that without creating a worse recovery burden.

Secrets, private identities, provider credentials, and plaintext evidence MUST NOT be committed to the public RTS repository.

## Automation / anti-zubora rule

For routine preservation, the normal operator action should approach **zero manual filing steps**.

The system should automatically:

- detect/accept a completed evidence bundle;
- package it;
- encrypt it;
- upload it;
- record custody/provenance;
- verify remote presence;
- surface a clear PASS / FAIL / UNKNOWN result;
- retain failure evidence and retry safely where authorized.

A workflow that is secure only when the operator remembers many manual steps FAILS this requirement.

## Restore / repair rule

The operator must be able to recover after loss of the original working machine/server.

A successful restore must demonstrate:

`FRESH ENVIRONMENT`
→ `obtain ciphertext from selected cloud`
→ `obtain separated recovery identity`
→ `decrypt`
→ `decompress/extract`
→ `recompute evidence digests`
→ `verify manifest/custody links`
→ `produce PASS / FAIL / UNKNOWN report`

A restore that merely opens files but cannot verify evidence integrity is not a PASS.

## Adversarial test set

Before completion, this layer must survive at least:

1. cloud ciphertext copied by an unauthorized party — plaintext remains unavailable without recovery secret;
2. original server/device lost — recovery succeeds from fresh environment;
3. primary recovery key unavailable — designated recovery path succeeds;
4. wrong key / wrong key epoch — fail closed;
5. ciphertext one-byte mutation — detected during decrypt/authentication or subsequent digest verification;
6. truncated/missing cloud object — detected;
7. stale but valid older ciphertext substituted for current bundle — detected as stale through evidence/custody identity;
8. cloud upload reports success but remote object is missing/wrong size/wrong identity — no PASS;
9. decryption succeeds but manifest verification fails — FAIL, not success;
10. provider changed — same evidence format remains recoverable through a different supported transport adapter;
11. public repository leak attempt containing private key/provider secret/plaintext evidence — blocked by gate/test;
12. operator performs no manual evidence-filing action after source capture — automated preservation still completes or clearly fails.

The workload must not be weakened after failure.

## Current likely external composition

Current design hypothesis, still subject to WITNESS/Meteor testing:

- compression/archive: existing standard tooling;
- client-side public-key file encryption: existing external encryption tool;
- cloud transport: provider-neutral existing transfer tool where supported;
- hashes/manifests: standard cryptographic hash tooling + Thin RTS record contract;
- private-key/recovery custody: separate user-controlled trust boundary;
- Thin RTS custom surface: only the bounded orchestration, evidence manifest/custody binding, verification report, and provider adapter glue that survives testing.

No custom cipher, KDF, key vault, cloud storage engine, or bespoke crypto protocol is authorized.

## Completion verdict

`NOT_COMPLETE`

Completion requires a real encrypted cloud round trip plus fresh-environment recovery and adversarial verification. Architecture text alone cannot pass this gate.
