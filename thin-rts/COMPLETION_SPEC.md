# Thin RTS — Consolidated Completion Specification

Initial consolidation: **2026-08-11 20:00 JST**

Adversarial revisions:

- Review 0001 — broad DA / Counter-DA
- Review 0002 — targeted re-attack
- Review 0003 — saturation attack
- Review 0004 — consolidation-regression check

Status: `FINAL_CONSISTENCY_CHECK / NOT_COMPLETE`

This is the canonical integrated completion contract for the successor RTS candidate.
Detailed requirement documents and adversarial reviews remain evidence for how this contract was derived, but new implementation work should target this consolidated surface rather than re-expanding overlapping architecture prose.

## 1. Founding invariant

`COMPLETION_SPEC != IMPLEMENTATION_AUTHORIZATION`

This specification defines **outcomes, evidence obligations, state boundaries, and frozen workloads**.
It does not authorize a monolithic platform or any particular custom component.

Every proposed custom responsibility must independently survive:

`DROP / EXTERNALIZE / GLUE / IRREDUCIBLE_BUILD`

A mandatory outcome may be implemented entirely with external tools.

## 2. Product outcome

The successor RTS is complete only when it reproduces the practical development responsibilities of old RTS **and** closes the old evidence/legal-reconstruction hole with a low-burden workflow suitable for an operator who may be poor at filing, forget deadlines, and lack legal/procedural knowledge.

Integrated outcome:

`AUTHORIZED INPUT / EVENT`
→ `EVENT CLASSIFICATION + INPUT-COVERAGE STATE`
→ `BOUND APPLICABILITY FACTS / JURISDICTION`
→ `BOUNDED CURRENT LAW / PROGRAM / PROCEDURE CHECK WHEN RELEVANT`
→ `CASE-PATTERN / COMMON-MISTAKE WARNING`
→ `EVIDENCE TRIAGE + COVERAGE CHECK`
→ `MISSING-EVIDENCE / TOOL-GAP DETECTION`
→ `AUTHORIZED COLLECTION / EXPORT / CAPTURE`
→ `ORIGINAL / DERIVATIVE SEPARATION`
→ `HASH / TIME / PROVENANCE / CUSTODY / LIFECYCLE`
→ `HISTORICAL SOURCE-AS-OBSERVED BINDING WHEN MATERIAL`
→ `SEALED LOGICAL REPRODUCTION BUNDLE`
→ `COMPRESS + CLIENT-SIDE ENCRYPT TO PINNED RECIPIENT / KEY EPOCH`
→ `UPLOAD + GENERATION / VERSION / ROOT VERIFICATION`
→ `DELETION-RESILIENT SECOND FAILURE DOMAIN`
→ `PRIORITIZED PRIVACY-SAFE AUTO-PINS`
→ `DOCUMENT_READY_DRAFT`
→ `SEPARATE AUTHORITY FOR SUBMISSION / DISCLOSURE / PROMOTION`
→ `FRESH-ENVIRONMENT RESTORE`
→ `INDEPENDENT VERIFY`
→ `PASS / FAIL / UNKNOWN`

No stage may silently manufacture legal certainty, authority, completeness, runtime identity, event truth, independent custody, monitoring coverage, or recoverability.

## 3. User model

Assume the operator may:

- forget filing/backups;
- not know which evidence matters;
- not know which deadline, benefit, claim, notice, or procedure exists;
- lose a phone/server/device;
- make mistakes under stress;
- need to explain the record months or years later.

A design that is safe only when the operator remembers a long checklist FAILS.

Normal evidence preservation should approach zero manual filing steps while still failing visibly when automation cannot complete.

## 4. Evidence claim separation

Never collapse these into one “verified” state:

- `CONTENT_INTEGRITY` — preserved bytes match recorded identity;
- `CAPTURE_PROVENANCE` — acquisition path/actor/tool/source;
- `TIME_ATTESTATION` — timestamp evidence and independence/trust level;
- `SOURCE_AUTHENTICITY` — evidence for claimed source/creator/system;
- `EVENT_TRUTH` — whether the underlying real-world event occurred as alleged.

`CONTENT_INTEGRITY_PASS != EVENT_TRUTH_PROVEN`

When all timing/custody systems remain under one ultimate administrator, preserve `INDEPENDENCE_NOT_PROVEN`.

At least one frozen workload should attach an external timestamp/transparency/signature/notarial/equivalent attestation to a covered root digest when feasible, without overstating what that attestation proves.

## 5. Historical source vs current source

Legal/procedure/program decisions must distinguish:

- `SOURCE_AS_OBSERVED_AT_DECISION_TIME`
- `SOURCE_CURRENTLY_REVALIDATED`

When material and authorized, preserve a bounded decision-time source artifact/snapshot/version/extract plus digest, source reference, and retrieval time.

A mutable live URL alone is not sufficient historical reconstruction.
Later revalidation must not overwrite the original observed basis.

## 6. Applicability facts and bounded legal discovery

Material facts used for jurisdiction, eligibility, deadlines, forms, or procedures should bind:

`VALUE + PROVENANCE + OBSERVED/CONFIRMED_TIME + STATUS + STALENESS/EXPIRY + USER_CONFIRMATION_WHEN_REQUIRED`

Device location or conversational inference must not silently substitute for residence, insurer, employer, household status, event date, or other material facts.

Legal/program discovery is explicitly bounded:

`DECLARED SEARCH SCOPE + AUTHORITATIVE SOURCE CLASSES CHECKED + RETRIEVAL TIMES + CONTEXT + UNRESOLVED GAPS`

Never claim `ALL_RELEVANT_LAW_FOUND` merely because search returned no more results.
Use `UNKNOWN`, `CONFLICT`, or `PROFESSIONAL_REVIEW_RECOMMENDED` when appropriate.

News/social/public chatter is discovery signal only until current authoritative sources support promotion.

## 7. Event-input coverage

`EVENT_NOT_OBSERVED != EVENT_DID_NOT_OCCUR`

Expose, where applicable:

- authorized event/input sources;
- last successful intake/sync;
- unsupported/disconnected sources;
- known blind spots;
- manual reporting path;
- event-classification confidence/status.

The system must not imply omniscient life-event detection.

## 8. Privacy / minimization

Legal or evidentiary usefulness does not authorize indiscriminate collection.

`COLLECT != TRUST != RETAIN != PUBLISH`

Rules:

- collect only materially justified and authorized content;
- third-party/private material does not become collectible merely because it may be useful;
- raw sensitive material is retained only when materially justified;
- secrets, provider credentials, private keys, and private evidence payloads stay out of public repositories;
- public/presentation copies minimize sensitive content;
- redaction creates a derivative and must preserve protected-original linkage where authorized;
- collection, transformation, retention, disclosure, and deletion remain distinct decisions.

Encryption reduces disclosure risk but does not cure overcollection.

## 9. Authority separation

`EVIDENCE_EXISTS != AUTHORITY_EXISTS`

Keep separate, where material:

- authority to observe/collect;
- authority to access private material;
- authority to transform/redact;
- authority to publish/disclose;
- authority to change repository/production state;
- authority to submit/sign/spend/represent;
- authority to approve/promote;
- authority to independently attest, only when genuinely independent.

Urgency, eligibility, evidence value, or AI confidence cannot manufacture authority.

## 10. Evidence lifecycle

Encryption does not justify indefinite retention.

Supported lifecycle states include:

- `ACTIVE_PRESERVE`
- `PRESERVATION_HOLD`
- `RETENTION_REVIEW`
- `DELETE_AUTHORIZED`
- `DELETED_WITH_RECORD`
- `UNKNOWN_DO_NOT_DESTROY`

Deletion is a custody event with authority, reason, time, target identity, and verification where material.
Convenience/index/derivative copies may expire earlier than canonical protected evidence.
No automated cleanup may destroy material evidence under an active hold or unresolved preserve state.

## 11. External-first implementation boundary

Prefer existing tools/services for archive/compression, cryptography, cloud/object transport/versioning, scheduling/notifications, official-source retrieval, document/PDF/form handling, Git/GitHub history/review, CI/regression, external trust/timestamps, and OS/provider runtime evidence.

Candidate custom surface is limited to the smallest surviving glue for:

- event/evidence schemas;
- manifest/custody/root binding;
- adapter/orchestration contracts;
- state/deadline/Auto-pin records;
- case-pattern review/promotion;
- document-ready metadata;
- PASS/FAIL/UNKNOWN verification reports.

No custom cipher, KDF, secret-sharing cryptography, cloud engine, national law database, news crawler, autonomous legal-decision engine, custom runtime kernel, or custom WORM store is authorized merely for completeness.

## 12. Threat model

Security PASS must name the threat class tested. At minimum distinguish:

- `REMOTE_CIPHERTEXT_THEFT`
- `CLOUD_ACCOUNT_READ_ACCESS`
- `CLOUD_DELETE_OR_ROLLBACK`
- `KEY_THEFT`
- `SOURCE_ENDPOINT_COMPROMISE`
- `UPLOADER_CONFIG_COMPROMISE`

Client-side archive encryption protects against some storage/transport threats; it does **not** make plaintext safe on an already-compromised endpoint.

`SECURITY_EXISTS != SECURITY_WORKS`

## 13. Key lifecycle and recipient integrity

Every encrypted generation binds a `KEY_EPOCH` or equivalent recipient-generation identity.

A healthy key epoch requires:

- intended recipient/key fingerprint(s);
- separately protected recovery path;
- recovery-copy verification date;
- rotation procedure;
- compromise-response procedure;
- successful fresh-environment recovery drill for the frozen workload.

No silent recipient replacement.
Recipient/key change requires authority, old/new identity, reason, time, and recovery proof.
A bundle encrypted successfully to an unintended/unauthorized recipient is FAIL.

## 14. Sealed bundle root and cloud generation identity

Each sealed logical bundle requires an unambiguous checkpoint such as `BUNDLE_ROOT_DIGEST` derived from a defined canonical root input that binds, according to the schema:

- evidence object digests;
- original/derivative links;
- custody state;
- lifecycle state where material;
- schema/version;
- bundle/generation identity;
- other integrity-critical manifest fields.

Verification reports expected vs observed root.

Remote custody binds, where available:

`BUNDLE_ID + GENERATION + BUNDLE_ROOT_DIGEST + PLAINTEXT_DIGEST/IDENTITY + CIPHERTEXT_DIGEST + PROVIDER_OBJECT_ID/VERSION + PRIOR_GENERATION_REF + OBSERVED_TIME`

`REMOTE_OBJECT_EXISTS != CURRENT_CUSTODY_PROVEN`

Detect or explicitly mark UNKNOWN for rollback, stale-valid substitution, truncation, wrong object/version, or generation ambiguity.
A mutable `latest.*` pointer must not be the sole current truth.

## 15. Availability / deletion resilience

Confidential ciphertext in one deletable failure domain is not durable evidence preservation.

The frozen workload must demonstrate recovery after simulated loss of the primary storage location using one externally implemented path such as:

- separately controlled second ciphertext copy;
- provider-protected historical/versioned copy outside the primary object-deletion failure;
- independently retrievable encrypted copy in another failure domain.

If only one deletable recoverable ciphertext copy exists, surface `SINGLE_COPY_RISK` and do not pass the durable-evidence gate.

RTS does not need to build its own redundant storage engine.

## 16. Auto-pin attention and notification privacy

Material Auto-pins should bind:

- severity/consequence;
- deadline/urgency;
- confidence/source quality;
- recoverability window;
- next smallest action;
- deduplication/grouping;
- acknowledgement/snooze/expiry where appropriate;
- escalation as a deadline/recoverability window closes.

`ALERT_EXISTS != USER_WAS_EFFECTIVELY_WARNED`

Notification channels are a separate confidentiality boundary:

`ENCRYPTED_ARCHIVE != PRIVATE_NOTIFICATION_CHANNEL`

Default external previews should minimize sensitive case/evidence details.
Where supported, preserve channel identity, delivery state, and user-selected disclosure level; sensitive details belong behind an authorized protected view unless explicitly allowed.

## 17. Watch health

Every recurring legal/program/deadline/news/source watch should expose, where available:

`LAST_SUCCESSFUL_CHECK + NEXT_EXPECTED_CHECK + SOURCE_SET + FAILURE_STATE + STALENESS_THRESHOLD + NOTIFICATION_DELIVERY_STATE`

A stale/broken watch surfaces `WATCH_DEGRADED` or `UNKNOWN`; it must not silently continue presenting old results as current coverage.

## 18. Case-pattern typing and contestable decisions

Case-pattern knowledge distinguishes at least:

- `COMMON_PRACTICAL_FAILURE`
- `OFFICIAL_RECOMMENDATION`
- `LEGAL_OR_PROCEDURAL_REQUIREMENT`
- `LOCAL_OR_PROVIDER_SPECIFIC`
- `UNVERIFIED_CANDIDATE`

Pattern repetition does not promote anecdote into law.

Material classifications/corrections are versioned rather than overwritten:

`DECISION_ID + INPUT_REFS + RESULT + CONFIDENCE/STATUS + ACTOR/TOOL + TIME + REASON + REVIEW_OF/SUPERSEDES`

A later correction may replace operational effect but must not erase the historical decision that drove prior behavior.

No archive/audit reconstruction may depend on hidden model chain-of-thought; preserve explicit result, material basis/source references, uncertainty, and tool/model identity needed for audit.

## 19. Document/submission authority state machine

Procedure assistance uses explicit states such as:

`IDENTIFIED`
→ `ELIGIBILITY_UNCONFIRMED / ELIGIBILITY_CONFIRMED`
→ `DOCUMENT_READY_DRAFT`
→ `USER_REVIEW_REQUIRED`
→ `SUBMISSION_AUTHORIZED`
→ `SUBMITTED`
→ `RECEIPT / OUTCOME_OBSERVED`

Eligibility, urgency, or document readiness cannot manufacture submission authority.

## 20. Logical reproducibility and long-term format survival

Require deterministic **logical identity and verification**, not necessarily byte-identical compressed/encrypted archives across platforms/tool versions.

Record:

- bundle schema/version;
- human-readable schema/recovery specification;
- logical path/object identity;
- evidence/object/root digests;
- archive tool/version/parameters;
- encryption tool/version/format/key epoch;
- verification procedure/invariants.

Prefer open/documented archive/encryption formats and provider-neutral bundle identity.

Schema/format migration is a derivative/custody transformation:

`PARENT_BUNDLE/ROOT + TOOL/VERSION + TIME + REASON + NEW_BUNDLE/ROOT`

Do not silently rewrite original bundle identity.
At least one completion test must verify an older-schema fixture or perform a versioned migration while preserving provenance.

## 21. Verifier identity

A verification report binds:

- verifier implementation/version/digest or external tool identity;
- schema version;
- commands/procedure;
- inputs covered;
- expected invariants/root;
- PASS / FAIL / UNKNOWN;
- discrepancies.

At least one frozen completion path must not require trusting RTS-owned verifier code; ordinary/off-the-shelf tooling must independently verify material integrity invariants.

## 22. Legal / epistemic boundary

Thin RTS provides evidence workflow/integrity engineering plus issue spotting for deadlines, benefits, procedures, and evidence gaps.

It does **not** guarantee legal admissibility/acceptance, exhaustive legal discovery, currentness of cached rules, event truth from hashes, authority from evidence existence, event nonexistence from silence, durable preservation from one cloud object, or endpoint security from archive encryption.

Mandatory states include, where appropriate:

`UNKNOWN / CONFLICT / EVIDENCE_INSUFFICIENT / WATCH_DEGRADED / INDEPENDENCE_NOT_PROVEN / SINGLE_COPY_RISK / PROFESSIONAL_REVIEW_RECOMMENDED`

## 23. Frozen integrated completion workload

The final workload must demonstrate the whole chain, including at minimum:

1. real event via declared authorized input;
2. visible event-input coverage/blind spots;
3. time/provenance/staleness-bound applicability facts;
4. early common-mistake/evidence-gap warning;
5. reasoned evidence triage;
6. correction of one material classification without erasing prior decision history;
7. privacy/minimization decision for at least one sensitive/third-party candidate;
8. explicit authority separation for collection/access/transform/disclosure/submission;
9. authorized capture of still-obtainable evidence where possible;
10. bounded current authoritative legal/program/procedure search;
11. historical source-as-observed preserved separately from later revalidation;
12. prioritized Auto-pin with privacy-safe external notification behavior;
13. current `DOCUMENT_READY_DRAFT` without unauthorized submission;
14. original/derivative separation;
15. byte-level evidence hashes + time + description + custody + lifecycle;
16. integrity/provenance/time/authenticity/event-truth states remain separate;
17. sealed `BUNDLE_ROOT_DIGEST` or equivalent checkpoint;
18. compression + client-side encryption to verified intended recipient/key epoch;
19. upload with generation/version/root identity;
20. remote identity/current-generation verification;
21. stale/rollback/substitution test;
22. simulated primary storage loss with successful recovery from second failure domain;
23. fresh-environment recovery with separated recovery identity;
24. independent verification of evidence/custody/derivative/root invariants;
25. recorded verifier identity/procedure;
26. deliberate mutation, missing file, stale object, wrong parent, wrong execution, and rollback detection;
27. unauthorized recipient/key change fails closed;
28. wrong/missing collection/disclosure/submission authority fails closed;
29. stale/news-only legal source is not promoted to verified current law;
30. broken/stale watch surfaces `WATCH_DEGRADED/UNKNOWN`;
31. explicit retention/preservation/deletion-review behavior;
32. at least one external root-digest trust/timestamp/transparency attachment when feasible;
33. older-schema verification or provenance-preserving migration;
34. explicit threat-class test with no broader security promotion;
35. final PASS/FAIL/UNKNOWN report reconstructable without original AI conversation.

The workload may not be weakened after failure.

## 24. Completion verdict

`NEW_RTS_STATUS = COMPLETE` is prohibited until all are true:

- old RTS responsibility reproduction: `PASS_FOR_FROZEN_REFERENCE_WORKLOAD`
- persistent-service Deployment Identity: `PASS`
- engineering evidence gate: `PASS_FOR_ENGINEERING_EVIDENCE_GATE`
- encrypted cloud custody + fresh recovery: `PASS`
- deletion-resilient ciphertext availability: `PASS`
- event evidence coverage + case-pattern warning: `PASS`
- automatic evidence triage: `PASS`
- privacy/minimization + authority boundaries: `PASS`
- bounded current law/program/deadline watch + document readiness: `PASS`
- alert/watch/event-input coverage: `PASS`
- lifecycle/rollback/key-epoch/recipient-integrity: `PASS`
- sealed bundle root + independent verification: `PASS`
- schema longevity/migration: `PASS`
- integrated adversarial workload: `PASS`

Case-specific legal acceptability always remains outside automatic promotion.

Until then:

`NEW_RTS_STATUS = NOT_COMPLETE`

## 25. Implementation sequencing after final saturation

`finish Deployment Identity workload`
→ `Destroy/Meteor each proposed custom responsibility`
→ `build only surviving minimal manifest/custody/root/reproduction glue`
→ `bind existing compression/encryption/cloud/redundancy tools`
→ `add only surviving event/case-pattern/triage state`
→ `bind current official-source legal/program/deadline checks externally where possible`
→ `add minimal Auto-pin / DOCUMENT_READY behavior that survives attack`
→ `run frozen integrated destructive/reference workload`
→ `repair only observed gaps`
→ `fresh recovery + provider/deletion failure drill`
→ `final verdict`

The implementation gets attacked again.
A surviving specification grants no survival right to its code.

## 26. Source lineage

Material source documents:

- `experiments/RTS-REVIVAL-20260811/LEGAL_EVIDENCE_COMPLETION_GATE.md`
- `experiments/RTS-REVIVAL-20260811/ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`
- `experiments/RTS-REVIVAL-20260811/AUTO_EVIDENCE_TRIAGE_REQUIREMENT.md`
- `experiments/RTS-REVIVAL-20260811/EVENT_EVIDENCE_COVERAGE_REQUIREMENT.md`
- `experiments/RTS-REVIVAL-20260811/CASE_PATTERN_WARNING_REQUIREMENT.md`
- `experiments/RTS-REVIVAL-20260811/LEGAL_RULES_AND_BENEFITS_WATCH_REQUIREMENT.md`
- `experiments/RTS-REVIVAL-20260811/COMPLETION_SPEC_ADVERSARIAL_REVIEW_0001.md`
- `experiments/RTS-REVIVAL-20260811/COMPLETION_SPEC_ADVERSARIAL_REVIEW_0002.md`
- `experiments/RTS-REVIVAL-20260811/COMPLETION_SPEC_ADVERSARIAL_REVIEW_0003.md`
- `experiments/RTS-REVIVAL-20260811/COMPLETION_SPEC_ADVERSARIAL_REVIEW_0004.md`
