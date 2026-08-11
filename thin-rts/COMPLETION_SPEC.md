# Thin RTS — Consolidated Completion Specification

Timestamp: **2026-08-11 20:00 JST**

Status: `FROZEN_FOR_IMPLEMENTATION / NOT_COMPLETE`

This file is the integration point for the hard completion requirements accumulated during the RTS revival time attack.

The individual requirement documents remain the detailed source of truth. This file defines how they combine into one product boundary and one completion verdict.

## Product boundary

Thin RTS is complete only when it can reproduce the practical development responsibilities of old RTS **and** close the old evidence/legal-reconstruction hole with a low-burden, external-first evidence protection workflow suitable for an operator who may be poor at filing, forget deadlines, and lack legal/procedural knowledge.

Completion therefore requires one integrated loop:

`EVENT / DEVELOPMENT / DISPUTE-RELEVANT INPUT`
→ `EVENT CLASSIFICATION`
→ `CURRENT LAW / PROGRAM / PROCEDURE CHECK WHEN RELEVANT`
→ `CASE-PATTERN / COMMON-MISTAKE WARNING`
→ `EVIDENCE CANDIDATE TRIAGE`
→ `EVIDENCE COVERAGE CHECK`
→ `MISSING-EVIDENCE / TOOL-GAP DETECTION`
→ `COLLECT / EXPORT / CAPTURE THROUGH AUTHORIZED EXTERNAL TOOLS`
→ `ORIGINAL / DERIVATIVE SEPARATION`
→ `HASH / TIME / PROVENANCE / CUSTODY RECORD`
→ `DETERMINISTIC REPRODUCTION BUNDLE`
→ `COMPRESS`
→ `CLIENT-SIDE ENCRYPT`
→ `UPLOAD TO USER-SELECTED CLOUD / STORAGE`
→ `REMOTE OBJECT VERIFICATION`
→ `AUTO-PIN DEADLINES / CLAIMS / MISSING ITEMS`
→ `DOCUMENT_READY WHEN A PROCEDURE IS IDENTIFIED`
→ `SEPARATE USER AUTHORITY FOR SUBMISSION / DISCLOSURE / PROMOTION`
→ `FRESH-ENVIRONMENT RESTORE`
→ `INDEPENDENT VERIFY`
→ `PASS / FAIL / UNKNOWN`

No stage may silently manufacture legal certainty, authority, evidence completeness, runtime identity, or independent custody.

## Hard completion sources

The following documents are mandatory parts of this specification:

1. `experiments/RTS-REVIVAL-20260811/LEGAL_EVIDENCE_COMPLETION_GATE.md`
   - original/derivative separation
   - cryptographic content identity
   - time identity
   - provenance / chain of custody
   - dispute-use evidence descriptions
   - runtime/deployment binding
   - authority separation
   - reproduction package
   - independent verification
   - external-trust attachment model
   - privacy/minimization
   - adversarial evidence tests

2. `experiments/RTS-REVIVAL-20260811/ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`
   - compression + client-side encryption before cloud storage
   - encryption/decryption key separation
   - recoverable key strategy rather than one irreplaceable key
   - replaceable provider adapter
   - automated preservation for a forgetful operator
   - remote existence verification
   - fresh-environment decrypt/restore/verify drill

3. `experiments/RTS-REVIVAL-20260811/AUTO_EVIDENCE_TRIAGE_REQUIREMENT.md`
   - automatically classify possible evidence
   - preserve uncertainty rather than discard uncertain material prematurely
   - use authoritative/current sources where legal relevance is asserted
   - record why an item was preserved or ignored
   - no unauthorized surveillance or collection

4. `experiments/RTS-REVIVAL-20260811/EVENT_EVIDENCE_COVERAGE_REQUIREMENT.md`
   - create an event case when something material happens
   - ask what evidence should normally exist
   - check what is actually held
   - detect common preservation mistakes
   - distinguish still-obtainable / no-longer-obtainable / blocked / unknown evidence
   - route true capture/tool gaps through WITNESS before custom implementation

5. `experiments/RTS-REVIVAL-20260811/CASE_PATTERN_WARNING_REQUIREMENT.md`
   - maintain reviewed common-failure patterns
   - when an event such as moving is reported, immediately surface likely evidence omissions
   - learn from repeated missing-evidence failures without treating one anecdote as legal truth
   - warn early enough that evidence can still be captured

6. `experiments/RTS-REVIVAL-20260811/LEGAL_RULES_AND_BENEFITS_WATCH_REQUIREMENT.md`
   - check current applicable law/regulation/official guidance when relevant
   - check currently usable benefits, allowances, reimbursements, notices, and procedures
   - preserve jurisdiction, effective date, source, form/version and deadline identity
   - use news/public chatter only as an unverified discovery signal until official confirmation
   - generate Auto-pins such as `ACTION_REQUIRED`, `DEADLINE_SOON`, `CLAIM_MAY_BE_MISSING`, `DOCUMENT_GAP`, `UNKNOWN`
   - prepare `DOCUMENT_READY` material without silently filing/signing/disclosing

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

## External-first implementation rule

Thin RTS is glue, not a new platform unless evidence forces otherwise.

Prefer existing capabilities for:

- archive/compression;
- cryptography;
- cloud/object transport;
- scheduling/notifications;
- current official-source retrieval/search;
- document/PDF/form handling;
- Git/GitHub history and review;
- CI/regression;
- signatures/timestamps/notarization/transparency services;
- OS/provider runtime identity.

Custom code is limited to the smallest surviving responsibilities such as:

- event/evidence record schema;
- evidence manifest and custody binding;
- provider/tool adapter contract;
- orchestration glue;
- state / deadline / Auto-pin records;
- deterministic PASS / FAIL / UNKNOWN verification report;
- case-pattern registry and reviewed promotion path;
- document-ready metadata binding.

No custom cipher, KDF, cloud engine, national law database, news crawler, autonomous legal-decision engine, custom runtime kernel, or custom WORM store is authorized merely for completeness.

## Security boundary

- plaintext evidence must not be uploaded to cloud merely because transport is convenient;
- cloud ciphertext and long-term decryption secret must not live in the same trust boundary by default;
- server-side unattended automation should preferably need encryption capability only;
- private recovery identity must have a separately recoverable path;
- public repositories must contain no private keys, provider credentials, secrets, or private evidence payloads;
- filename/path metadata should be minimized when practical without making recovery fragile;
- security-sensitive changes receive adversarial review;
- `SECURITY EXISTS != SECURITY WORKS`.

## Legal / epistemic boundary

Thin RTS provides issue spotting, evidence workflow assistance, deadline/benefit/procedure checking, and evidence-integrity engineering.

It does NOT guarantee that:

- a court/regulator/counterparty will accept a record;
- an AI classification is a legal conclusion;
- a news report proves a legal change;
- a cached rule is still current;
- missing search results mean no relevant law/case/program exists;
- evidence existence creates authority to disclose or submit it.

Mandatory states include `UNKNOWN`, `CONFLICT`, `EVIDENCE_INSUFFICIENT`, and `PROFESSIONAL_REVIEW_RECOMMENDED` where appropriate.

## Integrated completion test

A final frozen Reference Workload must exercise the whole chain, not separate demos only.

At minimum it must demonstrate:

1. a real event is identified;
2. event-specific common evidence omissions are surfaced early;
3. candidate evidence is triaged with reasons and provenance;
4. missing evidence is classified and still-obtainable material is captured through authorized existing tools where possible;
5. applicable current official legal/procedure/program information is checked when relevant;
6. at least one deadline/claim/notice/document gap produces an Auto-pin;
7. a current `DOCUMENT_READY` packet is prepared without unauthorized submission;
8. originals and derivatives are separated and linked;
9. evidence objects receive byte-level hashes, timestamps, descriptions, and custody records;
10. the evidence/reproduction bundle is compressed and client-side encrypted;
11. ciphertext is uploaded to a selected external storage destination;
12. remote object identity/presence is verified rather than trusting upload success;
13. the original machine/server is treated as lost;
14. a fresh environment retrieves ciphertext and separated recovery material;
15. decryption and extraction succeed;
16. independent verification recomputes hashes and verifies custody/derivative links;
17. a deliberate mutation/missing/stale/wrong-parent/wrong-execution test is detected;
18. a wrong/missing authority state fails closed;
19. a legal/procedure source that is stale or only news-derived is not promoted to verified current law;
20. the final report states PASS / FAIL / UNKNOWN and all unresolved gaps without needing the original AI conversation.

## Completion verdict

The successor RTS is not complete until all of the following are true:

- old RTS practical responsibility reproduction: `PASS_FOR_FROZEN_REFERENCE_WORKLOAD`
- persistent-service Deployment Identity: `PASS`
- engineering evidence preservation/reproduction gate: `PASS_FOR_ENGINEERING_EVIDENCE_GATE`
- encrypted cloud custody + fresh recovery: `PASS`
- event evidence coverage + case-pattern warnings: `PASS`
- automatic evidence triage: `PASS`
- current legal/program/deadline watch + document readiness: `PASS`
- integrated adversarial workload: `PASS`
- unresolved material legal acceptability: always remains case-specific and is never auto-promoted.

Until then:

`NEW_RTS_STATUS = NOT_COMPLETE`

## Implementation sequencing

The requirements are now frozen as one batch for implementation. Further conversational additions should be appended to this integrated specification only when they are materially new; do not keep creating overlapping architecture layers for wording variants.

Implementation order:

`finish Deployment Identity workload`
→ `build minimal evidence manifest/custody/reproduction glue`
→ `bind existing compression/encryption/cloud tooling`
→ `add event/case-pattern/triage records`
→ `bind current-source legal/program/deadline checks`
→ `add Auto-pin / DOCUMENT_READY state`
→ `run one integrated destructive/reference workload`
→ `repair only observed gaps`
→ `fresh recovery`
→ `final verdict`
