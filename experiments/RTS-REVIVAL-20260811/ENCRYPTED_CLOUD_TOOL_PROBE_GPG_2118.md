# Encrypted Cloud Custody — Existing Tool Probe: GnuPG

Observed timestamp: **2026-08-11 21:18 JST**

Parent requirement:

`ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`

## Probe result

Read-only command:

`gpg --version`

Observed result materially includes:

- `gpg (GnuPG) 2.4.4`
- `libgcrypt 1.10.3`
- Home: `/home/ubuntu/.gnupg`
- supported public-key families: `RSA, ELG, DSA, ECDH, ECDSA, EDDSA`
- supported ciphers include `AES, AES192, AES256` among others
- supported hashes include `SHA256, SHA384, SHA512` among others

## Current classification

`GPG_EXECUTABLE = PRESENT / /usr/bin/gpg`

`PUBLIC_KEY_CAPABILITY = PRESENT_AT_TOOL_LEVEL`

`MODERN_HASH_AND_CIPHER_SUPPORT = PRESENT_AT_TOOL_LEVEL`

This proves only that a mature off-the-shelf cryptographic tool is already available on the server and advertises primitives relevant to public-key encryption and integrity-oriented workflows.

It does **not** yet prove suitability for the encrypted cloud custody requirement. In particular, the following remain to be exercised rather than assumed:

- producer can encrypt without holding the long-term decryption secret;
- multiple recovery recipients or equivalent recovery separation can be achieved without collapsing trust boundaries;
- a fresh environment can decrypt and verify a preserved bundle;
- wrong key / stale object / mutation / truncation fail closed;
- private keys are not copied into the server or cloud trust boundary for convenience;
- provider-neutral upload/restore tooling exists or is justified separately;
- normal operation can approach zero manual filing burden.

## Destroy-Loop interpretation

The absence of `age` from the current PATH does **not** authorize installing or building anything yet.

Because GnuPG is already present, the next question is whether existing cryptographic tooling plus an existing transport can satisfy the requirement before any new dependency or custom implementation survives.

`EXISTS != SUITABLE`

`NOT_INSTALLED != BUILD_REQUIRED`

No key generation, encryption, decryption, secret inspection, package installation, or cloud mutation was performed in this probe.
