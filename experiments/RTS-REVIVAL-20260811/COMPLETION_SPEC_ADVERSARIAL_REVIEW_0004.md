# Thin RTS Completion Spec — Adversarial Review 0004

Timestamp: **2026-08-11 20:07 JST**

Target: compact canonical `thin-rts/COMPLETION_SPEC.md` after Review 0003.

Purpose: final no-new-class check, including regression detection caused by consolidation.

## Regression attack A — privacy/minimization was compressed too far

### DA

The compact spec preserves encryption, notification privacy, and lifecycle, but its canonical text no longer states the broader privacy/minimization invariant strongly enough.

That creates a regression risk: an implementation could legally/technically collect large amounts of third-party or sensitive material, encrypt it perfectly, and still satisfy many structural checks even though collection itself was excessive or unauthorized.

### Counter-DA

The source requirements already contained this boundary; the canonical spec should restore it explicitly rather than relying on lineage documents.

### Review

**Material regression found, not a new conceptual class.**

Restore explicit rules:

- collect only materially justified/authorized content;
- collection, trust, retention, and publication are separate decisions;
- third-party/private material does not become collectible merely because it may be useful;
- redaction creates a derivative and must preserve linkage to the protected original where authorized;
- secrets/private evidence/credentials stay out of public repositories;
- public/presentation copies minimize sensitive content.

---

## Regression attack B — authority separation was narrowed to submission

### DA

The compact spec makes submission authority explicit but can still under-specify earlier powers: observing, collecting, accessing private material, transforming/redacting, changing repository/production state, publishing/disclosing, or approving promotion.

Evidence existence or urgency could therefore drift into authority at an earlier stage.

### Counter-DA

The original evidence gate already separated these authorities. The canonical spec should restore them as first-class state rather than relying on prose such as “authorized collection.”

### Review

**Material regression found, not a new conceptual class.**

Restore separate authority dimensions:

- observe/collect;
- access private material;
- transform/redact;
- publish/disclose;
- change repo/production state;
- submit/sign/spend/represent;
- approve/promote;
- independently attest, only when genuinely independent.

`EVIDENCE_EXISTS != AUTHORITY_EXISTS`.

---

## Further rotation

Rechecked after identifying the two consolidation regressions:

- scope/platform creep;
- evidence integrity vs event truth;
- mutable legal sources;
- stale user facts;
- event blind spots;
- retention/deletion;
- cloud confidentiality/availability;
- key theft/substitution;
- endpoint compromise;
- bundle-root replacement;
- alert fatigue/privacy;
- watch failure;
- case-pattern poisoning;
- decision correction;
- schema migration;
- verifier identity;
- submission authority;
- privacy/third-party capture;
- collection/access authority;
- Deployment Identity boundary.

No materially new class emerged. Only the two canonical-spec regressions above require repair.

## Review 0004 verdict

`NO_NEW_MATERIAL_CLASS / TWO_REGRESSIONS_TO_RESTORE`

After restoring privacy/minimization and full authority separation, perform one final consistency check. If no new class appears, declare:

`SEARCH_SATURATED_UNDER_CURRENT_EVIDENCE`

and freeze the specification for implementation.
