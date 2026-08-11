# Thin RTS Completion Spec — Adversarial Review 0001

Timestamp: **2026-08-11 20:01 JST**

Target: `thin-rts/COMPLETION_SPEC.md`

Method:

`DA → Counter-DA → Issue Review → rotate angle → repeat → saturation check`

This review attacks the **reason, boundary, safety, operability, and completion claims** of the consolidated successor-RTS specification before implementation.

The target is allowed to die. Historical investment and conversational momentum grant no survival right.

## Round 1 — Raison d'être / scope attack

### DA

The completion specification may have recreated the exact failure mode Thin RTS was meant to avoid: a small evidence/reconstruction protocol has expanded into a life-event detector, legal/procedure watcher, benefits checker, evidence collector, cloud custody system, key recovery system, notification engine, form-preparation workflow, and learning system.

A specification this broad can become a new platform by requirements alone even if every paragraph says “external-first.”

If the same outcome can be achieved by composing existing AI/search, official sources, calendar/reminder systems, encryption tools, cloud tools, Git/GitHub, and ordinary document tools, then a large RTS-owned implementation is unjustified.

### Counter-DA

The specification does not require RTS to own those implementations. Its surviving candidate responsibility is cross-boundary binding:

- which event triggered which check;
- which current source supported which alert;
- which evidence object supports which fact;
- which evidence is missing or still obtainable;
- which authority permitted collection/submission/disclosure;
- which ciphertext corresponds to which protected evidence bundle;
- whether restore/verification actually succeeded;
- which unresolved claims remain UNKNOWN.

Those bindings do not automatically exist merely because the external tools exist.

### Issue review

**Survives, but only if the specification is treated as an outcome/test contract rather than build authorization.**

Required revision:

`COMPLETION_SPEC != IMPLEMENTATION_AUTHORIZATION`

Every custom component still requires its own Destroy Loop / Meteor decision. The integrated spec may authorize a workload, never a platform by implication.

---

## Round 2 — “legal-grade” authenticity attack

### DA

Hashes, Git history, cloud storage, and custody logs prove internal consistency better than they prove the historical truth of an event. A user can hash a fabricated file. A self-controlled server can create a backdated narrative. A screenshot can be edited before capture. A Git commit timestamp is not automatically an independent timestamp.

Therefore “legal-grade evidence” is an overclaim if the system confuses **integrity after capture** with **authenticity of the underlying event**.

### Counter-DA

The specification already refuses guaranteed legal acceptance and allows external trust attachments. It can make a narrower defensible claim: preserve bytes, provenance, acquisition method, transformations, time sources, uncertainty, and third-party attestations where available, without claiming that those facts independently prove the real-world event.

### Issue review

**Material gap found.**

Required distinctions:

- `CONTENT_INTEGRITY`
- `CAPTURE_PROVENANCE`
- `TIME_ATTESTATION`
- `SOURCE_AUTHENTICITY`
- `EVENT_TRUTH`

They must not collapse into one “verified” flag.

At least one completion workload should attach an external/independent time or transparency attestation to a covered digest when feasible, while preserving `INDEPENDENCE_NOT_PROVEN` when all systems remain under one administrator.

---

## Round 3 — source reconstruction attack

### DA

The legal/program watch can cite a current official webpage, but months later that page may have changed or disappeared. A URL and retrieval timestamp alone do not reconstruct what the system actually relied on when it raised an alert.

This would undermine the very dispute-reconstruction property the product claims to provide.

### Counter-DA

The system can preserve a bounded source snapshot or source artifact when authorized and practical, plus digest, retrieval time, source URL/reference, and a current revalidation result. When copying the full source is inappropriate, it can preserve an official downloadable artifact, version identifier, structured excerpt/metadata, or a hash/reference sufficient to explain what was relied upon.

### Issue review

**Material gap found.**

A legal/procedure decision record must distinguish:

- `SOURCE_AS_OBSERVED_AT_DECISION_TIME`
- `SOURCE_CURRENTLY_REVALIDATED`

Current truth and historical decision provenance are separate responsibilities.

---

## Round 4 — personal-context poisoning / stale-fact attack

### DA

Benefits, deadlines, procedures, and jurisdiction often depend on user facts such as residence, insurer, employment status, household composition, dates, and eligibility facts. If those are silently inferred, stale, or copied from old conversation state, a perfectly current official rule can still generate a wrong alert.

### Counter-DA

The system can bind every material applicability fact to provenance, observation/confirmation time, confidence/status, and expiry/reconfirmation rules. Missing facts produce questions or UNKNOWN rather than silent assumptions.

### Issue review

**Material gap found.**

Required state for material applicability facts:

`VALUE + SOURCE/PROVENANCE + OBSERVED/CONFIRMED_TIME + STATUS + STALENESS/EXPIRY + USER_CONFIRMATION_WHEN_REQUIRED`

Device location must not silently substitute for legal residence, jurisdiction, insurer, employer, or household status.

---

## Round 5 — evidence overcollection / lifetime attack

### DA

“Preserve uncertain evidence” plus automatic collection can create a privacy warehouse. Storage can grow without bound, retain third-party sensitive data, increase breach damage, and make deletion legally/operationally dangerous. Encryption reduces disclosure risk but does not solve over-retention.

### Counter-DA

The product already separates collection, trust, retention, and publication. It can add lifecycle state and require preservation holds only where justified, with review/deletion authority explicitly recorded.

### Issue review

**Material gap found.**

Evidence lifecycle must become explicit, for example:

- `ACTIVE_PRESERVE`
- `PRESERVATION_HOLD`
- `RETENTION_REVIEW`
- `DELETE_AUTHORIZED`
- `DELETED_WITH_RECORD`
- `UNKNOWN_DO_NOT_DESTROY`

Deletion must itself be a custody event. A convenience copy may expire without destroying the canonical protected object when preservation still applies.

---

## Round 6 — encryption/key-recovery attack

### DA

Key separation can fail in both directions:

- one key copy → permanent loss risk;
- many convenient key copies → theft compromise risk;
- cloud + recovery key under the same account → fake separation;
- long-lived key without rotation → growing blast radius;
- backup key never tested → theoretical recovery only.

### Counter-DA

The requirement already demands separated recovery and fresh-environment drills. This can be strengthened without inventing cryptography by using external-tool-supported multiple recipients/identities, key epochs, separately protected recovery copies, and explicit rotation/compromise procedures.

### Issue review

**Survives with revision.**

Add mandatory:

- key epoch identity;
- rotation path;
- compromise response;
- recovery-copy verification date;
- successful restore drill per materially new key epoch before the epoch is considered operationally safe.

Do not implement custom key-splitting cryptography merely to satisfy architecture aesthetics.

---

## Round 7 — cloud “success” / rollback attack

### DA

Remote existence checking can still accept a stale but valid encrypted archive. A provider can overwrite objects, versioning can be disabled, a sync tool can delete remote history, or an attacker with account access can replace the latest pointer with an older valid object.

### Counter-DA

The existing adversarial set already calls for stale substitution detection. This can be made structural by using unique/content-bound object identity, recording provider version/object identifiers where available, and maintaining a monotonic bundle generation/custody chain rather than relying on “latest filename.”

### Issue review

**Material gap found.**

Remote custody must not define truth as “object exists.” It must bind:

`BUNDLE_ID + GENERATION + PLAINTEXT_DIGEST + CIPHERTEXT_DIGEST + PROVIDER_OBJECT_ID/VERSION + PRIOR_GENERATION_REF + OBSERVED_TIME`

Rollback/stale substitution must fail or remain UNKNOWN.

---

## Round 8 — alert fatigue / zubora paradox attack

### DA

A system designed for an operator who forgets things can defeat itself by producing too many warnings. If every possible benefit, evidence gap, news signal, and common mistake becomes an Auto-pin, the user learns to ignore the system. “More warnings” can reduce practical safety.

### Counter-DA

The product can treat attention as a scarce resource and rank alerts by consequence, deadline, recoverability, confidence, and actionability. Low-value duplicates can be suppressed without suppressing the underlying record.

### Issue review

**Material gap found.**

Auto-pin requires lifecycle and prioritization:

- severity/consequence;
- deadline/urgency;
- confidence/source quality;
- recoverability window;
- next smallest action;
- deduplication/grouping;
- acknowledgement/snooze/expiry;
- escalation when a deadline materially approaches.

`ALERT_EXISTS != USER_WAS_EFFECTIVELY_WARNED`.

---

## Round 9 — automation submission / authority confusion attack

### DA

`DOCUMENT_READY` may gradually drift into “the system basically filed it.” Prefilling sensitive forms, sending attachments, electronic signatures, or employer/insurer/municipal submissions can cross authority and disclosure boundaries. Convenience pressure will push toward silent execution.

### Counter-DA

The existing authority boundary already blocks silent submission. The remaining issue is making the transition mechanically explicit rather than relying on prose.

### Issue review

**Survives with revision.**

Separate states:

`IDENTIFIED → ELIGIBILITY_UNCONFIRMED/CONFIRMED → DOCUMENT_READY_DRAFT → USER_REVIEW_REQUIRED → SUBMISSION_AUTHORIZED → SUBMITTED → RECEIPT/OUTCOME_OBSERVED`

No transition to `SUBMISSION_AUTHORIZED` may be manufactured by the system from eligibility or urgency alone.

---

## Round 10 — case-pattern learning poisoning attack

### DA

Learning from “what people often forget” can encode anecdotes, misinformation, demographic bias, outdated practice, or malicious input. A repeated bad pattern can become a repeated bad warning.

### Counter-DA

The current design already distinguishes anecdote from legal truth and includes reviewed promotion. It can further separate empirical “common failure” guidance from normative legal requirements.

### Issue review

**Survives with revision.**

Pattern entries need type and provenance, e.g.:

- `COMMON_PRACTICAL_FAILURE`
- `OFFICIAL_RECOMMENDATION`
- `LEGAL/PROCEDURAL_REQUIREMENT`
- `LOCAL/PROVIDER_SPECIFIC`
- `UNVERIFIED_CANDIDATE`

Promotion requires evidence appropriate to the type. Pattern popularity must never upgrade a practical hint into law.

---

## Round 11 — deterministic bundle attack

### DA

Requiring a deterministic reproduction bundle can be misread as requiring byte-for-byte deterministic archive output across compressor versions/platforms. That creates avoidable implementation burden and can fail despite perfectly preserved evidence.

### Counter-DA

What matters is deterministic **logical identity and verification**, not necessarily identical ZIP/tar ciphertext bytes across different tool versions.

### Issue review

**Requirement needs narrowing.**

Require deterministic manifest/schema/path identity and reproducible verification results. Record archive/encryption tool/version/parameters. Do not require identical compressed/encrypted bytes unless a workload specifically needs that property.

---

## Round 12 — verifier trust attack

### DA

An independent verifier that is itself silently modified can certify a bad bundle. A PASS report without verifier identity is weak evidence.

### Counter-DA

The completion gate already requires ordinary/off-the-shelf verification paths. The verifier itself can be identified and its result cross-checked with standard hashes/signature/encryption tools.

### Issue review

**Material gap found.**

Verification report must bind:

- verifier implementation/version/digest or external tool identity;
- schema version;
- commands/procedure used;
- inputs covered;
- expected invariants;
- PASS/FAIL/UNKNOWN result;
- discrepancies.

At least one path must not require trusting RTS-owned verifier code.

---

## Round 13 — monitoring dependency / offline failure attack

### DA

Deadline/news/benefit monitoring assumes network access, source availability, scheduler health, credentials, and notification delivery. A silent monitor failure is worse than no monitor if the operator believes the system is watching.

### Counter-DA

A watch can expose health and freshness rather than silently promising coverage.

### Issue review

**Material gap found.**

Every active watch needs observable state such as:

`LAST_SUCCESSFUL_CHECK + NEXT_EXPECTED_CHECK + SOURCE_SET + FAILURE_STATE + STALENESS_THRESHOLD + NOTIFICATION_DELIVERY_STATE`

A stale/broken watch must surface `WATCH_DEGRADED/UNKNOWN`, not continue presenting old advice as current.

---

## Round 14 — testability / impossible “all law” attack

### DA

The phrase “check applicable law/programs” is unbounded. No finite system can prove it found every relevant law, benefit, local program, form, exception, or case. A completion gate requiring exhaustive legal discovery is impossible to pass honestly.

### Counter-DA

The product does not need omniscience. It needs a bounded search protocol, source hierarchy, explicit coverage scope, uncertainty, and escalation when material gaps remain.

### Issue review

**Material wording correction required.**

Completion means:

`BOUNDED_CURRENT_SOURCE_SEARCH_PER_DECLARED_SCOPE + TRACEABLE_RESULTS + UNKNOWN/CONFLICT/ESCALATION`

It must never claim `ALL_RELEVANT_LAW_FOUND` unless a competent authority or specifically bounded dataset justifies that claim.

---

## Saturation rotation

Additional angles checked after the material issues above:

- multi-device recovery;
- provider replacement;
- public-repository secret leakage;
- wrong execution/outcome binding;
- stale source substitution;
- lost convenience indexes;
- user stress/error;
- historical-vs-current truth;
- scope creep into custom crypto/cloud/legal DB;
- independent authority claims;
- evidence mutation/deletion;
- form/version staleness;
- private third-party material;
- alert delivery;
- key loss/theft tradeoff.

These produced combinations or refinements of the already identified issues rather than materially new classes.

## Adversarial saturation verdict

`SEARCH_SATURATED_UNDER_CURRENT_EVIDENCE`

This is **not proof of completeness**. New workloads or failures reopen the review.

## Final DA verdict

`COMPLETION_SPEC: SURVIVES_WITH_MATERIAL_REVISIONS`

The specification was **not killed outright** because a surviving irreducible responsibility remains: bind external tools, current sources, evidence objects, authority, custody, alerts, recovery, and verification into a reconstructable state machine with explicit uncertainty.

What **was killed**:

- any implication that the completion spec authorizes a monolithic platform;
- any implication that hash integrity proves event truth;
- any implication that a live URL reconstructs historical source state;
- any implication that stale personal context may drive eligibility silently;
- any implication that encryption alone solves evidence lifecycle/privacy;
- any implication that “remote object exists” proves current custody state;
- any implication that more warnings always improve safety;
- any implication that deterministic logical verification requires identical archive bytes;
- any implication that the system can exhaustively discover all applicable law/programs.

## Required revisions before implementation

1. Add explicit `SPEC != BUILD AUTHORIZATION` invariant.
2. Separate integrity/provenance/time/source-authenticity/event-truth states.
3. Preserve historical source-as-observed alongside current revalidation.
4. Bind material user applicability facts to provenance/time/staleness/confirmation.
5. Add evidence retention/preservation/deletion lifecycle.
6. Add key epoch/rotation/compromise/recovery-drill state.
7. Add monotonic cloud bundle generation/version identity and rollback detection.
8. Add attention-budget/alert lifecycle semantics.
9. Make submission state transitions explicit and authority-gated.
10. Type and provenance case-pattern learning.
11. Narrow deterministic requirement to logical bundle/verification identity.
12. Bind verifier identity and require one non-RTS verification path.
13. Add monitor/watch health and degraded-state semantics.
14. Bound legal/program discovery scope; never claim exhaustive legal discovery.

## Re-attack rule

After these revisions are incorporated:

1. run one shorter DA / Counter-DA review only for the changed surfaces;
2. if no materially new class appears, freeze for implementation;
3. implement the smallest surviving glue only;
4. hit the implementation with the frozen integrated reference/adversarial workload;
5. repair observed gaps, not hypothetical architecture;
6. re-run the same workload after every material repair.

The next implementation may die even though this specification survived.
