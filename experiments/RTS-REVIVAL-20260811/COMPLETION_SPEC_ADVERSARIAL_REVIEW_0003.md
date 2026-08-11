# Thin RTS Completion Spec — Adversarial Review 0003

Timestamp: **2026-08-11 20:05 JST**

Target: revised `thin-rts/COMPLETION_SPEC.md` after Reviews 0001–0002.

Scope: final saturation attack; new classes only.

## Round X — notification channel privacy attack

### DA

The evidence archive can be perfectly encrypted while the warning system leaks the same sensitive fact in plaintext through lock-screen notifications, email subjects, chat previews, calendar titles, or notification logs.

Examples include health events, pregnancy, employment disputes, benefits, legal issues, family events, and evidence gaps. A “helpful” Auto-pin can become a privacy breach.

### Counter-DA

The system can keep the alert channel low-information by default: generic urgency/status externally, details only after opening an authorized protected surface. Users can explicitly opt into richer notification content.

### Issue review

**New material class found: ALERT-CHANNEL CONFIDENTIALITY.**

Required:

- notification content minimization by default;
- no sensitive case/evidence detail in external previews unless explicitly authorized;
- notification channel identity and delivery state recorded where material;
- a secure detail-view path separate from the minimal alert;
- explicit user-controlled disclosure level per channel where supported.

`ENCRYPTED_ARCHIVE != PRIVATE_NOTIFICATION_CHANNEL`.

---

## Round Y — coherent whole-bundle replacement attack

### DA

Per-file hashes can all pass inside a maliciously substituted but internally coherent bundle. If manifest, custody log, and evidence objects are replaced together, internal consistency alone may not identify which sealed bundle state was previously accepted.

Generation/version logic helps, but verification still needs a clear sealed bundle root identity that can be compared across independent copies/attestations.

### Counter-DA

The bundle can expose one canonical root/checkpoint identity derived from the canonical manifest/custody state and referenced evidence digests. That root can be recorded with remote generation/version records and external trust attachments without exposing plaintext evidence.

### Issue review

**New material integrity class found: SEALED BUNDLE ROOT / CHECKPOINT.**

Required:

- canonical manifest representation or otherwise unambiguous root-input definition;
- `BUNDLE_ROOT_DIGEST` or equivalent sealed checkpoint identity;
- root covers or binds evidence object digests, derivative links, custody state, schema/version, and generation identity as defined by the format;
- cloud copy/version records bind the root;
- independent/secondary copy or external attestation can compare against the same root;
- verifier reports the expected vs observed root.

The system need not invent a blockchain, ledger, or WORM engine. Existing external anchoring/versioning is preferred.

---

## Rotation after X/Y

Rechecked:

- secret/key leakage;
- endpoint compromise;
- cloud deletion;
- stale rule/person facts;
- event blind spots;
- alert fatigue;
- alert privacy;
- whole-bundle substitution;
- per-file mutation;
- schema migration;
- decision correction;
- independent verification;
- evidence lifecycle;
- authority transitions;
- external-source mutability;
- provider replacement;
- tool-gap escalation.

No additional materially distinct class emerged beyond the two above and prior reviews.

## Review 0003 verdict

`SURVIVES_WITH_TWO_FINAL_REVISIONS`

After adding alert-channel confidentiality and sealed bundle-root/checkpoint semantics, run one final no-new-class saturation check. If that produces only previously known issues, freeze for implementation.
