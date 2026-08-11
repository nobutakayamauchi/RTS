# Thin RTS Event Assist — Feature Specification

Timestamp: **2026-08-11 20:14 JST**

Status: `SPEC_CUT / INTEGRATION_READY / IMPLEMENTATION_NOT_YET_AUTHORIZED`

This is the integration specification for the successor RTS event-assist capability.
It is a child contract of `thin-rts/COMPLETION_SPEC.md` and does not replace the consolidated completion gate.

## 1. Purpose

Help a non-expert, forgetful operator avoid losing evidence, rights, claims, deadlines, or recoverability after ordinary life/development/dispute events.

The feature must not require the operator to know:

- what evidence is legally or practically important;
- what common mistakes people make after an event;
- what current law/program/procedure may apply;
- what deadline may already be running;
- what form/document may be needed;
- what evidence has already been safely preserved.

## 2. Core flow

`AUTHORIZED EVENT / INPUT`
→ `EVENT CASE`
→ `INPUT-COVERAGE + APPLICABILITY FACTS`
→ `COMMON-FAILURE / CASE-PATTERN CHECK`
→ `EVIDENCE-CANDIDATE TRIAGE`
→ `EVIDENCE HOLDINGS / GAP CHECK`
→ `CURRENT OFFICIAL LAW / PROGRAM / PROCEDURE CHECK WHEN MATERIAL`
→ `ACTION / DEADLINE / EVIDENCE AUTO-PINS`
→ `AUTHORIZED ACQUISITION / EXPORT / CAPTURE`
→ `PRESERVATION JOB`
→ `MANIFEST / HASH / TIME / PROVENANCE / CUSTODY`
→ `CLIENT-SIDE ENCRYPTED STORAGE`
→ `REMOTE GENERATION VERIFY`
→ `DOCUMENT_READY_DRAFT WHEN RELEVANT`
→ `SEPARATE AUTHORITY FOR SUBMISSION / DISCLOSURE`
→ `PASS / FAIL / UNKNOWN`

## 3. Event case contract

Every material event case should expose a stable `event_id` and preserve, where relevant:

- event type / candidate type;
- event/source time and observation time separately;
- event source/provenance;
- user-confirmation state;
- jurisdiction/applicability facts with provenance/staleness;
- evidence candidates;
- evidence actually held;
- still-obtainable / unavailable / blocked / unknown evidence;
- case-pattern warnings and their provenance/type;
- official-source checks and retrieval time;
- deadlines / claim / notice / document states;
- preservation-job references;
- tool gaps;
- user corrections/overrides;
- unresolved UNKNOWN/CONFLICT states.

`EVENT_DETECTED != EVENT_TRUTH_PROVEN`.

## 4. Integration interface

This feature should integrate with Thin RTS through a narrow logical contract rather than owning a new platform.

### Inputs

- `EventObservation`
- `UserConfirmedFact`
- `EvidenceReference`
- `AuthorizedAcquisitionRequest`
- `OfficialSourceObservation`
- `CasePatternCandidate`
- `ToolCapabilityObservation`

### Outputs

- `EventCaseRecord`
- `EvidenceCandidateRecord`
- `EvidenceGapRecord`
- `CasePatternWarning`
- `LegalProgramCheckRecord`
- `ActionPin`
- `DocumentReadyDraft`
- `PreservationJob`
- `ToolGapRecord`
- `DecisionCorrectionRecord`

Existing Thin RTS evidence/custody/encryption/recovery contracts remain authoritative for the preserved payloads.

## 5. Auto-pin classes

Minimum supported logical states:

- `ACTION_REQUIRED`
- `DEADLINE_SOON`
- `POSSIBLY_ELIGIBLE`
- `CLAIM_MAY_BE_MISSING`
- `NOTICE_MAY_BE_REQUIRED`
- `EVIDENCE_GAP`
- `DOCUMENT_GAP`
- `CAPTURE_WINDOW_CLOSING`
- `LAW_OR_PROGRAM_CHANGED`
- `WATCH_DEGRADED`
- `OFFICIAL_CONFIRMATION_REQUIRED`
- `PROFESSIONAL_REVIEW_RECOMMENDED`
- `UNKNOWN`

Every pin must bind its reason, source/provenance, urgency, confidence/status, and next smallest action.

## 6. Case-pattern knowledge

Case-pattern knowledge must remain typed and contestable:

- `COMMON_PRACTICAL_FAILURE`
- `OFFICIAL_RECOMMENDATION`
- `LEGAL_OR_PROCEDURAL_REQUIREMENT`
- `LOCAL_OR_PROVIDER_SPECIFIC`
- `UNVERIFIED_CANDIDATE`

Example: a rental move-in event may trigger a practical warning to preserve room-condition photos and related handover evidence, but the exact legal/procedural statement must come from current authoritative sources when asserted as law.

Past user/system failures may generate pattern candidates. They do not self-promote into legal truth.

## 7. Current-law/program boundary

This feature does not own a national law database, benefits database, case-law database, or news crawler.

It must use external current-source retrieval and preserve:

- declared search scope;
- source class/authority;
- retrieval time;
- effective/version date when material;
- jurisdiction/locality;
- unresolved applicability facts;
- source-as-observed evidence when historical reconstruction matters.

News/social signals may trigger a check but cannot become `VERIFIED` law/program/procedure without authoritative confirmation.

## 8. Evidence preservation boundary

The event-assist feature selects and routes evidence; it does not invent a separate evidence store.

Preservation must flow into the existing Thin RTS legal-evidence/encrypted-custody design:

`ORIGINAL / DERIVATIVE SEPARATION`
→ `HASH + TIME + PROVENANCE + CUSTODY`
→ `SEALED LOGICAL BUNDLE`
→ `COMPRESS`
→ `CLIENT-SIDE ENCRYPT`
→ `UPLOAD`
→ `REMOTE VERSION/GENERATION VERIFY`
→ `FRESH RECOVERY / INDEPENDENT VERIFY`

## 9. User-authority boundary

The feature may recommend, prepare, or preserve under the corresponding authority.

It may not silently:

- sign;
- submit a government/employer/insurer form;
- disclose private evidence;
- contact an external party;
- spend money;
- represent the user legally;
- mutate production/repository state beyond separately authorized scope.

`DOCUMENT_READY_DRAFT != SUBMISSION_AUTHORIZED`.

## 10. External-first build rule

For every responsibility, test in this order:

`EXISTING PRODUCT / OS / SaaS / OFFICIAL PORTAL / API / OSS / CLI / AI TOOL`
→ `COMPOSITION OF EXISTING CAPABILITIES`
→ `BOUNDED MANUAL STEP IF CHEAPER/SAFER`
→ `MINIMAL GLUE`
→ `NEW BUILD ONLY FOR IRREDUCIBLE GAP`

No implementation earns survival merely because it is convenient.

## 11. Frozen prototype workload

Both prototype tracks must receive the same workload.

### Case M — rental move-in

Input: operator reports a recent rental move-in and has not intentionally organized evidence.

Required behavior:

- open an event case;
- surface reviewed/common evidence-preservation risks while capture may still be possible;
- check whether relevant evidence is held;
- distinguish missing-but-obtainable from no-longer-obtainable/unknown;
- preserve authorized captured material through the Thin RTS evidence pipeline;
- avoid presenting practical advice as verified law without authoritative support.

### Case B — childbirth / claim-omission scenario

Input: operator reports a childbirth event but does not know which current benefits/notices/procedures may require action.

Required behavior:

- bind jurisdiction/insurance/employment/household facts only as needed;
- perform bounded current official-source checks;
- identify possible claims/notices/deadlines without fabricating eligibility;
- issue source-bound pins;
- reach `DOCUMENT_READY_DRAFT` where enough facts exist;
- fail closed on missing facts, stale sources, or submission authority.

### Common preservation test

For at least one captured evidence object:

- preserve original/derivative separation;
- hash and custody-bind it;
- encrypt client-side;
- upload to a replaceable selected storage destination;
- verify remote generation identity;
- recover and independently verify from a fresh environment.

## 12. Completion for this feature

The feature is not integrated-complete until:

- the frozen workload passes;
- the same workload survives the Meteor comparison and implementation re-attack;
- no required result depends on hidden chat memory;
- no custom component survives merely because it was already built;
- unresolved gaps remain explicit.

Current verdict:

`FEATURE_SPEC = SURVIVES_AS_REQUIRED_OUTCOME_CONTRACT`

`IMPLEMENTATION = NOT_YET_AUTHORIZED`
