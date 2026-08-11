# Thin RTS Completion Spec — Adversarial Review 0002

Timestamp: **2026-08-11 20:03 JST**

Target: revised `thin-rts/COMPLETION_SPEC.md` after Review 0001.

Scope: **changed surfaces and remaining blind spots only**.

Method:

`DA → Counter-DA → Issue Review → rotate → saturation`

## Round A — event-detection false confidence

### DA

The revised spec can monitor laws, deadlines, and known events, but it can still create a dangerous illusion: if the system never observed that the event happened, it cannot warn about it.

A user who says “RTS is watching” may incorrectly infer that silence means no action is needed, even when the relevant event source was never connected, authorized, synchronized, or understood.

### Counter-DA

The system can expose its event-intake coverage the same way it exposes watch health. It can distinguish “no event detected within observed sources” from “no event exists.”

### Issue review

**New material class found: EVENT INPUT COVERAGE.**

Required states include:

- authorized event/input sources;
- last successful intake/sync where applicable;
- blind spots / unsupported sources;
- `EVENT_NOT_OBSERVED` distinct from `EVENT_DID_NOT_OCCUR`;
- manual event reporting remains a first-class path.

The system must not imply omniscient life-event detection.

---

## Round B — encrypted but deletable single-copy archive

### DA

Encryption protects confidentiality, not availability. An attacker or accident with cloud credentials may delete the ciphertext. A provider account may be suspended. A sync mistake may propagate deletion. A single encrypted cloud copy can therefore be perfectly confidential and completely useless.

### Counter-DA

The system can remain external-first while requiring recovery from more than one failure domain where feasible: e.g. provider versioning/object-lock capability, a second ciphertext destination, or an offline/independent encrypted copy. It does not need to build a storage engine.

### Issue review

**New material class found: AVAILABILITY / DELETION RESILIENCE.**

Completion must demonstrate that loss/deletion of the primary storage location does not automatically destroy the only recoverable ciphertext copy, or else explicitly fail with `SINGLE_COPY_RISK` and remain incomplete for the durable-evidence gate.

At least one frozen workload should recover after simulated loss of the primary storage location using a separately controlled ciphertext copy or provider-protected historical version.

---

## Round C — recipient-key substitution attack

### DA

Keeping only a public encryption key on the uploader is not sufficient. If an attacker or accidental configuration change replaces that recipient key with a different public key, future bundles can be encrypted successfully and uploaded successfully while becoming unreadable by the intended owner — or readable by an attacker.

The pipeline could report green while silently changing who can decrypt future evidence.

### Counter-DA

Recipient/key-epoch configuration can be integrity-bound and authority-gated. Public keys are not secret, so their fingerprints can be pinned in durable trusted configuration/evidence records. Key changes can require explicit authority and a recovery test.

### Issue review

**New material security class found: RECIPIENT CONFIGURATION INTEGRITY.**

Required:

- expected recipient/key fingerprint(s) bound to key epoch;
- no silent key/recipient replacement;
- recipient change is an authority-recorded security event;
- bundle records the actual recipient/key epoch used;
- new epoch does not become healthy until recovery is demonstrated.

---

## Round D — threat-model overclaim

### DA

“Cloud theft reveals ciphertext only” can be misread as protection against a compromised source device/server. But the source system necessarily sees plaintext before encryption; malware or a live endpoint attacker may exfiltrate it before the archive is encrypted.

### Counter-DA

The product can state its threat boundary precisely. Client-side encryption materially protects stored/transported archives from cloud/object theft; it does not magically secure an already-compromised plaintext endpoint.

### Issue review

**Material boundary clarification required.**

Threat model must distinguish at least:

- `REMOTE_CIPHERTEXT_THEFT`
- `CLOUD_ACCOUNT_READ_ACCESS`
- `CLOUD_DELETE/ROLLBACK`
- `KEY_THEFT`
- `SOURCE_ENDPOINT_COMPROMISE`
- `UPLOADER_CONFIG_COMPROMISE`

Claims and tests must identify which threat is being tested.

---

## Round E — long-term archive format rot

### DA

The product is supposed to be useful months or years later. Recording schema/tool versions is not enough if old bundles become unreadable because the current code no longer supports the schema, a provider-specific API disappears, or a crypto/archive format migrates.

### Counter-DA

The system can prefer open, documented formats and preserve self-describing schema/recovery instructions. Schema migrations can create derived representations without destroying the original bundle/manifests. Provider transport can remain separate from evidence format.

### Issue review

**New material class found: FORMAT / SCHEMA LONGEVITY.**

Required:

- bundle schema version + human-readable specification;
- open/documented archive/encryption formats where practical;
- provider-neutral evidence format;
- old bundle remains verifiable after schema migration;
- migration records parent bundle/digest, transformation tool/version, new digest, and reason;
- original bundle identity is not silently rewritten.

At least one completion test should verify an older-schema fixture or perform a versioned migration without losing verification provenance.

---

## Round F — AI classification correction attack

### DA

Evidence triage, event classification, and applicability classification can be wrong. If a later human correction simply overwrites the classification, the record no longer reconstructs why the original alert or omission occurred.

### Counter-DA

Decision records can be append/version-based: original classification survives, correction/review creates a new decision with actor, reason, time, and supersession reference.

### Issue review

**New material reconstruction class found: CONTESTABLE DECISION HISTORY.**

Material AI/human classifications and corrections must preserve:

`DECISION_ID + INPUT_REFS + RESULT + CONFIDENCE/STATUS + ACTOR/TOOL + TIME + REASON + SUPERSEDES/REVIEW_OF`

Correction must not erase the historical decision that drove prior behavior.

---

## Rotation after Round F

Angles rechecked:

- privacy metadata leakage;
- wrong law source;
- stale eligibility facts;
- deadline notification failure;
- cloud rollback;
- key loss;
- public repo secret leakage;
- evidence deletion;
- provider outage;
- verifier compromise;
- archive migration;
- user correction;
- false-positive event detection;
- false-negative event detection;
- endpoint theft vs cloud theft.

No additional materially distinct class emerged beyond the six above and Review 0001 findings.

## Review 0002 verdict

`SURVIVES_WITH_ADDITIONAL_MATERIAL_REVISIONS`

The revised completion spec survives, but implementation remains blocked until the six new classes are incorporated.

Required additions:

1. event-input coverage / blind-spot semantics;
2. deletion-resilient availability / second failure domain for ciphertext;
3. recipient public-key configuration integrity and change authority;
4. explicit threat-model classification;
5. long-term schema/format migration and backward verification;
6. versioned/contestable decision history.

After incorporation, one final saturation re-attack should seek only genuinely new classes. If none appear, freeze for implementation.
