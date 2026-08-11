# Thin RTS — Consolidated Completion Specification

Timestamp: **2026-08-11 20:00 JST**

Adversarial revisions:

- **2026-08-11 20:01 JST — DA / Counter-DA Review 0001**
- **2026-08-11 20:03 JST — targeted re-attack Review 0002**

Status: `FROZEN_PENDING_FINAL_SATURATION_REATTACK / NOT_COMPLETE`

This file is the integration point for the hard completion requirements accumulated during the RTS revival time attack.

The individual requirement documents remain detailed source material. This file defines how they combine into one product boundary and one completion verdict.

## Founding invariant — specification is not build authorization

`COMPLETION_SPEC != IMPLEMENTATION_AUTHORIZATION`

This specification defines outcomes, evidence obligations, state boundaries, and workloads.
It does **not** authorize a monolithic RTS platform or any particular custom component.

Every proposed custom implementation remains subject to the WITNESS-style Destroy Loop / Meteor decision:

`DROP / EXTERNALIZE / GLUE / IRREDUCIBLE_BUILD`

A capability may be mandatory as an outcome while its implementation is entirely externalized.

## Product boundary

Thin RTS is complete only when it can reproduce the practical development responsibilities of old RTS **and** close the old evidence/legal-reconstruction hole with a low-burden, external-first evidence protection workflow suitable for an operator who may be poor at filing, forget deadlines, and lack legal/procedural knowledge.

Completion therefore requires one integrated loop:

`AUTHORIZED EVENT / DEVELOPMENT / DISPUTE-RELEVANT INPUT`
→ `EVENT CLASSIFICATION + EVENT-INPUT COVERAGE STATE`
→ `BOUND APPLICABILITY FACTS / JURISDICTION`
→ `BOUNDED CURRENT LAW / PROGRAM / PROCEDURE CHECK WHEN RELEVANT`
→ `CASE-PATTERN / COMMON-MISTAKE WARNING`
→ `EVIDENCE CANDIDATE TRIAGE`
→ `EVIDENCE COVERAGE CHECK`
→ `MISSING-EVIDENCE / TOOL-GAP DETECTION`
→ `COLLECT / EXPORT / CAPTURE THROUGH AUTHORIZED EXTERNAL TOOLS`
→ `ORIGINAL / DERIVATIVE SEPARATION`
→ `HASH / TIME / PROVENANCE / CUSTODY RECORD`
→ `SOURCE-AS-OBSERVED SNAPSHOT/REFERENCE WHEN MATERIAL`
→ `LOGICAL REPRODUCTION BUNDLE`
→ `COMPRESS`
→ `CLIENT-SIDE ENCRYPT WITH PINNED RECIPIENT / KEY EPOCH`
→ `UPLOAD TO USER-SELECTED CLOUD / STORAGE`
→ `REMOTE OBJECT / GENERATION / VERSION VERIFICATION`
→ `DELETION-RESILIENT SECOND FAILURE DOMAIN OR EXPLICIT INCOMPLETE STATE`
→ `AUTO-PIN DEADLINES / CLAIMS / MISSING ITEMS`
→ `DOCUMENT_READY_DRAFT WHEN A PROCEDURE IS IDENTIFIED`
→ `SEPARATE USER AUTHORITY FOR SUBMISSION / DISCLOSURE / PROMOTION`
→ `FRESH-ENVIRONMENT RESTORE`
→ `INDEPENDENT VERIFY`
→ `PASS / FAIL / UNKNOWN`

No stage may silently manufacture legal certainty, authority, evidence completeness, runtime identity, historical authenticity, event truth, independent custody, monitoring coverage, or recoverability.

## Hard completion sources

The following documents are mandatory parts of this specification:

1. `experiments/RTS-REVIVAL-20260811/LEGAL_EVIDENCE_COMPLETION_GATE.md`
2. `experiments/RTS-REVIVAL-20260811/ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`
3. `experiments/RTS-REVIVAL-20260811/AUTO_EVIDENCE_TRIAGE_REQUIREMENT.md`
4. `experiments/RTS-REVIVAL-20260811/EVENT_EVIDENCE_COVERAGE_REQUIREMENT.md`
5. `experiments/RTS-REVIVAL-20260811/CASE_PATTERN_WARNING_REQUIREMENT.md`
6. `experiments/RTS-REVIVAL-20260811/LEGAL_RULES_AND_BENEFITS_WATCH_REQUIREMENT.md`
7. `experiments/RTS-REVIVAL-20260811/COMPLETION_SPEC_ADVERSARIAL_REVIEW_0001.md`
8. `experiments/RTS-REVIVAL-20260811/COMPLETION_SPEC_ADVERSARIAL_REVIEW_0002.md`

The adversarial reviews are normative only for the material revisions explicitly incorporated here; they do not become an endlessly expanding architecture source.

## User model — mandatory design constraint

The normal workflow MUST NOT require the operator to be good at evidence management or law.

Assume the operator may:

- forget to file or back up evidence;
- not know which evidence matters;
- not know which legal/procedural deadline has started;
- not know which benefit/claim exists;
- lose a phone/server/device;
- make mistakes under stress;
- need to explain the record months or years later.

A design that works only when the operator remembers a long checklist is a failure.

## Epistemic separation — integrity is not event truth

The system MUST keep these claims separate:

- `CONTENT_INTEGRITY`
- `CAPTURE_PROVENANCE`
- `TIME_ATTESTATION`
- `SOURCE_AUTHENTICITY`
- `EVENT_TRUTH`

A PASS for content integrity MUST NOT silently promote source authenticity or event truth.

When all timing/custody systems remain under one administrator, preserve `INDEPENDENCE_NOT_PROVEN` rather than simulate independence.

Where feasible in the frozen workload, at least one covered digest should receive an external/independent timestamp, transparency, signature, notarization, or equivalent attestation through an external provider/tool.

## Historical source observation vs current truth

A legal/procedure/program alert must preserve two distinct concepts:

- `SOURCE_AS_OBSERVED_AT_DECISION_TIME`
- `SOURCE_CURRENTLY_REVALIDATED`

When material and authorized, the decision-time record should preserve a bounded source snapshot/artifact, official downloadable document, version identifier, structured source extract, or other reproducible representation plus digest and retrieval time.

A live URL alone is not sufficient historical reconstruction when the source is mutable.

A later revalidation must not overwrite what the system originally observed.

## Applicability-fact binding

Material facts used to determine jurisdiction, eligibility, deadlines, forms, or procedure must carry, where relevant:

`VALUE + SOURCE/PROVENANCE + OBSERVED_OR_CONFIRMED_TIME + STATUS + STALENESS/EXPIRY + USER_CONFIRMATION_WHEN_REQUIRED`

Device location or conversational inference must not silently substitute for legal residence, insurer, employer, household status, or other material applicability facts.

Missing or stale material facts produce a question, `UNKNOWN`, or professional escalation rather than a fabricated answer.

## Bounded legal/program discovery

The system cannot honestly prove that it found every relevant law, case, program, form, exception, or local procedure.

Completion therefore means:

`BOUNDED_CURRENT_SOURCE_SEARCH_PER_DECLARED_SCOPE + TRACEABLE_RESULTS + UNKNOWN/CONFLICT/ESCALATION`

Preserve:

- declared search scope;
- source classes actually checked;
- retrieval times;
- jurisdiction/context assumptions;
- unresolved coverage gaps.

Do not emit `ALL_RELEVANT_LAW_FOUND` or equivalent universal certainty without a separately justified bounded authority/dataset.

## Evidence lifecycle / retention

Encryption does not justify indefinite retention.

Each material evidence object or bundle must support explicit lifecycle state such as:

- `ACTIVE_PRESERVE`
- `PRESERVATION_HOLD`
- `RETENTION_REVIEW`
- `DELETE_AUTHORIZED`
- `DELETED_WITH_RECORD`
- `UNKNOWN_DO_NOT_DESTROY`

Deletion is itself a custody event and must preserve authority, reason, time, target identity, and verification of what was deleted when material.

Convenience/index/derivative copies may have shorter retention than canonical protected evidence.

No automated cleanup may destroy material evidence merely because a storage period elapsed while a preservation hold or unresolved dispute state applies.

## External-first implementation rule

Thin RTS is glue, not a new platform unless evidence forces otherwise.

Prefer existing capabilities for archive/compression, cryptography, cloud/object transport, scheduling/notifications, official-source retrieval/search, document/PDF/form handling, Git/GitHub history/review, CI/regression, external signatures/timestamps/notarization/transparency, and OS/provider runtime identity.

Custom code is limited to the smallest surviving responsibilities such as:

- event/evidence record schema;
- evidence manifest and custody binding;
- provider/tool adapter contract;
- orchestration glue;
- state / deadline / Auto-pin records;
- logical reproduction/verification contract;
- deterministic PASS / FAIL / UNKNOWN verification report;
- case-pattern registry and reviewed promotion path;
- document-ready metadata binding.

No custom cipher, KDF, key-sharing cryptography, cloud engine, national law database, news crawler, autonomous legal-decision engine, custom runtime kernel, or custom WORM store is authorized merely for completeness.

## Security boundary

- plaintext evidence must not be uploaded to cloud merely because transport is convenient;
- cloud ciphertext and long-term decryption secret must not live in the same trust boundary by default;
- server-side unattended automation should preferably need encryption capability only;
- private recovery identity must have a separately recoverable path;
- public repositories must contain no private keys, provider credentials, secrets, or private evidence payloads;
- filename/path metadata should be minimized when practical without making recovery fragile;
- security-sensitive changes receive adversarial review;
- `SECURITY EXISTS != SECURITY WORKS`.

## Explicit threat model

Security claims must name the threat being tested. At minimum distinguish:

- `REMOTE_CIPHERTEXT_THEFT`
- `CLOUD_ACCOUNT_READ_ACCESS`
- `CLOUD_DELETE_OR_ROLLBACK`
- `KEY_THEFT`
- `SOURCE_ENDPOINT_COMPROMISE`
- `UPLOADER_CONFIG_COMPROMISE`

Client-side encryption can materially protect stored/transmitted archives from ciphertext/cloud theft; it does **not** make plaintext safe on an already-compromised source endpoint.

No security PASS may silently expand from one threat class to another.

## Key lifecycle / recovery boundary

Encrypted custody must bind a `KEY_EPOCH` or equivalent recipient-generation identity.

A production-capable key epoch requires:

- identified encryption recipient/material;
- expected recipient/key fingerprint(s);
- separately protected recovery path;
- recovery-copy verification date;
- rotation procedure;
- compromise-response procedure;
- at least one successful fresh-environment restore drill before the epoch is considered operationally safe for the frozen completion workload.

Recipient/key changes are security/authority events. They must not occur silently.

Each bundle must record the actual recipient/key epoch used.

The design must not invent custom cryptography or custom secret-sharing merely to satisfy redundancy aesthetics.

## Recipient configuration integrity

A public encryption key is not secret, but its identity is security-critical.

The uploader must verify the intended recipient/key fingerprint or equivalent pinned identity before treating an encrypted bundle as healthy.

A changed recipient configuration requires:

- explicit authority;
- recorded old/new key epoch identity;
- reason;
- transition time;
- recovery proof for the new epoch.

A pipeline that encrypts successfully to an unauthorized or unintended recipient is a FAIL.

## Cloud object / rollback identity

`REMOTE_OBJECT_EXISTS != CURRENT_CUSTODY_PROVEN`

A remote preservation record should bind, where available:

`BUNDLE_ID + GENERATION + PLAINTEXT_DIGEST + CIPHERTEXT_DIGEST + PROVIDER_OBJECT_ID_OR_VERSION + PRIOR_GENERATION_REF + OBSERVED_TIME`

Detect or explicitly mark UNKNOWN for stale valid-object substitution, rollback, truncation, wrong object identity, or provider-version ambiguity.

A single mutable `latest.zip`-style object name must not be the sole current-generation truth.

## Availability / deletion resilience

Confidential ciphertext that exists in only one deletable failure domain is not durable evidence preservation.

The completion workload must demonstrate one of the following externally implemented outcomes:

- a separately controlled second ciphertext copy;
- provider-protected historical/versioned copy that survives simulated primary-object loss;
- another independently retrievable encrypted copy outside the primary deletion failure domain.

If only one deletable recoverable ciphertext copy exists, surface `SINGLE_COPY_RISK` and do not pass the durable-evidence completion gate.

The system need not build its own redundant storage engine.

## Alert / attention budget

Each material Auto-pin should support:

- severity/consequence;
- deadline/urgency;
- confidence/source quality;
- recoverability window;
- next smallest action;
- deduplication/grouping;
- acknowledgement/snooze/expiry where appropriate;
- escalation when a recoverability or deadline window materially closes.

`ALERT_EXISTS != USER_WAS_EFFECTIVELY_WARNED`

The underlying record may remain even when duplicate notifications are suppressed.

## Watch health / degraded monitoring

Every active recurring law/program/deadline/news/source watch must expose observable health, including where available:

`LAST_SUCCESSFUL_CHECK + NEXT_EXPECTED_CHECK + SOURCE_SET + FAILURE_STATE + STALENESS_THRESHOLD + NOTIFICATION_DELIVERY_STATE`

A broken or stale watch must surface `WATCH_DEGRADED` or `UNKNOWN` rather than continue presenting old results as current coverage.

## Event-input coverage / blind spots

`EVENT_NOT_OBSERVED != EVENT_DID_NOT_OCCUR`

The system must expose what event/input sources are actually authorized and observed.

Where applicable preserve:

- authorized event/input sources;
- last successful intake/sync;
- unsupported or disconnected sources;
- known blind spots;
- manual event-reporting path;
- event-classification confidence/status.

Silence from the system must not imply that no relevant life event occurred when the event was outside observed/authorized inputs.

## Case-pattern knowledge typing

Pattern types may include:

- `COMMON_PRACTICAL_FAILURE`
- `OFFICIAL_RECOMMENDATION`
- `LEGAL_OR_PROCEDURAL_REQUIREMENT`
- `LOCAL_OR_PROVIDER_SPECIFIC`
- `UNVERIFIED_CANDIDATE`

Each pattern requires provenance appropriate to its type.

Popularity or repetition of an anecdote must never upgrade a practical hint into law.

## Contestable decision history

Material event classifications, evidence triage decisions, eligibility/applicability decisions, case-pattern promotions, and human corrections must be versioned rather than silently overwritten.

A material decision record should preserve:

`DECISION_ID + INPUT_REFS + RESULT + CONFIDENCE_OR_STATUS + ACTOR_OR_TOOL + TIME + REASON + REVIEW_OF_OR_SUPERSEDES`

A later correction may supersede an earlier decision operationally, but must not erase the historical decision that drove prior alerts/actions.

## Document/submission authority state machine

Procedure assistance must use explicit state transitions such as:

`IDENTIFIED`
→ `ELIGIBILITY_UNCONFIRMED / ELIGIBILITY_CONFIRMED`
→ `DOCUMENT_READY_DRAFT`
→ `USER_REVIEW_REQUIRED`
→ `SUBMISSION_AUTHORIZED`
→ `SUBMITTED`
→ `RECEIPT / OUTCOME_OBSERVED`

Eligibility, urgency, or document readiness alone cannot manufacture `SUBMISSION_AUTHORIZED`.

External submission, signature, disclosure of sensitive material, spending, representation, or production-state change requires the authority appropriate to that action.

## Logical reproducibility, not archive-byte superstition

The system requires deterministic **logical identity and verification**, not necessarily byte-identical compressed/encrypted archives across different operating systems or tool versions.

The bundle must record:

- schema/version;
- logical path/object identity;
- evidence/object digests;
- archive/compression tool + version + parameters;
- encryption tool + version/format/recipient epoch;
- verification procedure and expected invariants.

Byte-identical archive/ciphertext output is required only if a specific workload independently demonstrates that need.

## Format / schema longevity

The evidence format must remain reconstructable independently of any one cloud provider or current RTS code version.

Require:

- explicit bundle schema version;
- human-readable schema/recovery specification;
- open/documented archive and encryption formats where practical;
- provider-neutral evidence/bundle identity;
- backward verification of older bundles or a recorded migration path;
- migration as a derivative/custody transformation with parent digest, tool/version, time, reason, and new digest;
- preservation of original bundle identity rather than silent rewriting.

At least one frozen completion test must verify an older-schema fixture or perform a versioned migration while preserving provenance.

## Verifier identity

A verification report must bind:

- verifier implementation/version/digest or external tool identity;
- schema version;
- commands/procedure used;
- inputs covered;
- expected invariants;
- PASS / FAIL / UNKNOWN result;
- discrepancies.

At least one frozen completion verification path must not require trusting RTS-owned verifier code; ordinary/off-the-shelf tools must independently check material integrity invariants.

## Legal / epistemic boundary

Thin RTS provides issue spotting, evidence workflow assistance, deadline/benefit/procedure checking, and evidence-integrity engineering.

It does NOT guarantee that:

- a court/regulator/counterparty will accept a record;
- an AI classification is a legal conclusion;
- a news report proves a legal change;
- a cached rule is still current;
- missing search results mean no relevant law/case/program exists;
- evidence existence creates authority to disclose or submit it;
- content integrity proves source authenticity or event truth;
- an unobserved event did not occur;
- ciphertext is durable merely because one cloud object exists;
- client-side archive encryption protects an already-compromised plaintext endpoint.

Mandatory states include `UNKNOWN`, `CONFLICT`, `EVIDENCE_INSUFFICIENT`, `WATCH_DEGRADED`, `INDEPENDENCE_NOT_PROVEN`, `SINGLE_COPY_RISK`, and `PROFESSIONAL_REVIEW_RECOMMENDED` where appropriate.

## Integrated completion test

A final frozen Reference Workload must exercise the whole chain, not separate demos only.

At minimum it must demonstrate:

1. a real event is identified through a declared authorized input path;
2. event-input coverage and blind spots are visible;
3. material applicability facts are bound with provenance/time/staleness and confirmed where necessary;
4. event-specific common evidence omissions are surfaced early;
5. candidate evidence is triaged with reasons and provenance;
6. at least one material classification is later reviewed/corrected without erasing prior decision history;
7. missing evidence is classified and still-obtainable material is captured through authorized existing tools where possible;
8. applicable current official legal/procedure/program information is checked within a declared bounded scope;
9. the historical source-as-observed basis is preserved separately from later current revalidation where material;
10. at least one deadline/claim/notice/document gap produces a prioritized Auto-pin;
11. a current `DOCUMENT_READY_DRAFT` packet is prepared without unauthorized submission;
12. originals and derivatives are separated and linked;
13. evidence objects receive byte-level hashes, timestamps, descriptions, custody records, and lifecycle state;
14. integrity/provenance/time/source-authenticity/event-truth claims remain separately classified;
15. the evidence/reproduction bundle is logically identified, compressed and client-side encrypted;
16. intended recipient/key fingerprint is verified and the actual key epoch is recorded;
17. ciphertext is uploaded to a selected external storage destination with generation/version identity;
18. remote object identity/presence/current-generation state is verified rather than trusting upload success;
19. simulated primary remote-object/location loss still leaves one separately recoverable ciphertext copy/version outside that primary deletion failure domain;
20. stale/rollback/substituted remote state is detected or explicitly UNKNOWN;
21. the active key epoch has a separated recovery path and demonstrated restore drill;
22. the original machine/server is treated as lost;
23. a fresh environment retrieves ciphertext and separated recovery material;
24. decryption and extraction succeed;
25. independent verification recomputes hashes and verifies custody/derivative links using at least one non-RTS verification path;
26. verifier identity and procedure are recorded;
27. a deliberate mutation/missing/stale/wrong-parent/wrong-execution/rollback test is detected;
28. an unauthorized recipient/key change fails closed;
29. a wrong/missing submission/disclosure authority state fails closed;
30. a legal/procedure source that is stale or only news-derived is not promoted to verified current law;
31. a stale or failed watch surfaces `WATCH_DEGRADED/UNKNOWN`;
32. one evidence item or bundle demonstrates explicit preservation/retention/deletion-review lifecycle behavior;
33. at least one external trust/timestamp/transparency attachment is demonstrated when feasible, without overstating independence;
34. one older-schema fixture or migration path remains independently verifiable;
35. at least one threat-model test states exactly which threat was tested and refuses broader security promotion;
36. the final report states PASS / FAIL / UNKNOWN and all unresolved gaps without needing the original AI conversation.

## Completion verdict

The successor RTS is not complete until all of the following are true:

- old RTS practical responsibility reproduction: `PASS_FOR_FROZEN_REFERENCE_WORKLOAD`
- persistent-service Deployment Identity: `PASS`
- engineering evidence preservation/reproduction gate: `PASS_FOR_ENGINEERING_EVIDENCE_GATE`
- encrypted cloud custody + fresh recovery: `PASS`
- deletion-resilient ciphertext availability: `PASS`
- event evidence coverage + case-pattern warnings: `PASS`
- automatic evidence triage: `PASS`
- bounded current legal/program/deadline watch + document readiness: `PASS`
- alert/watch/event-input coverage behavior: `PASS`
- lifecycle/rollback/key-epoch/recipient-integrity behavior: `PASS`
- schema longevity + independent verifier behavior: `PASS`
- integrated adversarial workload: `PASS`
- unresolved material legal acceptability: always remains case-specific and is never auto-promoted.

Until then:

`NEW_RTS_STATUS = NOT_COMPLETE`

## Implementation sequencing

The requirements are frozen as one batch pending one final saturation re-attack.

Further additions should be integrated only when materially new; do not create overlapping architecture layers for wording variants.

After saturation:

`finish Deployment Identity workload`
→ `run Destroy/Meteor on each proposed custom responsibility`
→ `build only surviving minimal evidence manifest/custody/reproduction glue`
→ `bind existing compression/encryption/cloud/redundancy tooling`
→ `add only surviving event/case-pattern/triage records`
→ `bind current-source legal/program/deadline checks externally where possible`
→ `add minimal Auto-pin / DOCUMENT_READY state that survives attack`
→ `run one integrated destructive/reference workload`
→ `repair only observed gaps`
→ `fresh recovery + provider/deletion failure drill`
→ `final verdict`

The implementation itself must be attacked again. A surviving specification does not grant survival rights to its code.
