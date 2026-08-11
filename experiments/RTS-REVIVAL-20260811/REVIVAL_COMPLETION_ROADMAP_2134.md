# RTS Revival — Completion Roadmap and Cloud-Custody Progress

Observed checkpoint: **2026-08-11 21:34 JST**

Branch: `revival/zero-cost-timeattack-20260811`

This checkpoint preserves the measured earlier candidate result while tracking the broader completion gates added later.

## Current state

### 1. Thin RTS external-first candidate

`PASS_FOR_EXERCISED_REFERENCE_WORKLOADS`

The earlier candidate proved that multiple historical RTS responsibilities could be reproduced with external systems plus a thin reconstructive contract without authorizing a custom RTS Runtime / Controller / Governance Kernel.

The original 15-minute candidate measurement remains preserved and is not rewritten by later work.

### 2. Persistent-service Deployment Identity

`PASS_FOR_BOUNDED_RUNTIME_RECONSTRUCTION_WITH_EXPLICIT_UNKNOWN`

Reference Run 0005 reached a live project-specific outcome while preserving:

`LOADED_SOURCE_REVISION = NOT_PROVEN`

This closes the previously unexercised long-lived-service Deployment Identity workload without falsely equating current Git state with complete runtime reality.

### 3. Encrypted cloud custody — existing-tool Destroy Loop

`IN_PROGRESS`

Observed existing tools/capabilities:

- `age`: not found in current PATH;
- `gpg`: present at `/usr/bin/gpg`;
- GnuPG: `2.4.4`;
- public-key capability advertised by tool;
- modern cipher/hash families available at tool level;
- `rclone`: not found in current PATH;
- `gsutil`: present;
- `scp`, `sftp`, `rsync`, `curl`: present;
- `aws`, `az`, `restic`, `duplicity`, `borg`: not found in current PATH;
- `gsutil` is using the installed Google Cloud SDK;
- `gcloud auth list --filter=status:ACTIVE --format='value(status)'` returned a non-empty active marker (`*`), establishing that at least one active Cloud SDK credential is configured without recording the account identity in the public evidence record.

Current interpretation:

`EXISTING_CRYPTO_TOOL = GPG`

`EXISTING_OBJECT_STORAGE_TRANSPORT_CANDIDATE = GSUTIL / GCLOUD STORAGE`

`ACTIVE_CLOUD_SDK_CREDENTIAL = OBSERVED`

This does **not** yet prove bucket/object access, write authority, encrypted round trip, key separation, fresh-environment recovery, or anti-zubora automation.

## Completion roadmap

### Gate A — provider access proof

Read-only first:

- prove whether the active credential can see any usable Google Cloud Storage surface;
- distinguish `NO BUCKET / NO ACCESS / AUTH FAILURE / ACCESSIBLE STORAGE`;
- do not publish account, bucket, project, credential, or object identities into the public evidence record unless materially necessary.

If no usable GCS surface exists, return to the external-first transport comparison (`scp/sftp/rsync/curl` or another justified provider) before adding new software.

### Gate B — encryption/key-separation proof

Prove with off-the-shelf tooling that the producer can encrypt while holding **no long-term decryption secret**.

Required direction:

`SERVER/PRODUCER -> PUBLIC ENCRYPTION MATERIAL ONLY`

`RECOVERY SIDE -> PRIVATE DECRYPTION MATERIAL OUTSIDE SERVER/CLOUD TRUST BOUNDARY`

Need at least one separately recoverable path and a labeled key epoch/generation.

### Gate C — real encrypted cloud round trip

Exercise:

`evidence bundle -> manifest/digest -> encrypt -> ciphertext digest -> upload -> remote existence/size/identity check -> download -> decrypt -> recompute hashes -> verify manifest/custody`

The cloud object alone must not disclose plaintext.

### Gate D — fresh-environment recovery

Recover without the original AI chat or remembered commands.

Required result:

`FRESH ENVIRONMENT -> CLOUD CIPHERTEXT -> SEPARATED RECOVERY IDENTITY -> DECRYPT -> VERIFY -> PASS/FAIL/UNKNOWN`

### Gate E — adversarial custody tests

At minimum exercise the hard cases already required by `ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`, including wrong key/epoch, ciphertext mutation, truncation/missing object, stale-valid-object substitution, false upload success, decrypt-success/manifest-fail, secret/plaintext leak prevention, and alternate transport/provider assumptions.

### Gate F — anti-zubora automation

Normal evidence preservation must approach zero manual filing burden.

The final flow should automatically package, hash, encrypt, upload, record custody metadata, verify remote state, retry safely, and surface `PASS / FAIL / UNKNOWN`.

A workflow that depends on remembering many manual commands does not pass.

### Gate G — evidence intelligence and legal/procedure continuity

After custody survives, integrate and test the remaining hard completion requirements:

- automatic evidence triage;
- event evidence coverage / missing-evidence remediation;
- case-pattern warnings before evidence is lost;
- current law / benefit / deadline / official-procedure watching;
- document readiness without unauthorized submission.

### Gate H — final adversarial review / ULTIMATE LOOP

Before promotion:

`DA -> Counter-DA -> issue review -> rotate angle -> repeat until search saturation`

Then run the surviving concrete implementation through the same frozen workloads and known death causes.

Promotion remains fail-closed.

## Top-level verdict at this checkpoint

`THIN_RTS_CANDIDATE_FOR_EXERCISED_WORKLOADS = PASS`

`DEPLOYMENT_IDENTITY_REFERENCE_RUN = PASS_WITH_EXPLICIT_UNKNOWN`

`ENCRYPTED_CLOUD_CUSTODY = IN_PROGRESS`

`REVIVED_RTS_FULL_COMPLETION = NOT_COMPLETE`

`PROMOTION_TO_MAIN = NOT_AUTHORIZED / DRAFT_PR_ONLY`

No cloud object was listed, created, changed, uploaded, downloaded, or deleted by the auth-status observation recorded here.
