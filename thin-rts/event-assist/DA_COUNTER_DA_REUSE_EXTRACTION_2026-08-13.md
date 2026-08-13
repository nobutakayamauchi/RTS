# Event Assist — DA / Counter-DA Reuse, Extraction, New-Build Gate

Timestamp: **2026-08-13 10:02 JST**

Status: `GATE_1_REOPENED / REUSE_FIRST / MINIMAL_BINDER_SURVIVES`

Purpose: rerun necessity analysis after the adversarial completion gate killed the full-successor completion claim.

Order was deliberately frozen as:

`KEEP EXISTING -> EXTRACT FROM EXISTING STRUCTURE -> NEW BUILD ONLY IF IRREDUCIBLE`

A desired feature was not allowed to authorize its own implementation.

## 1. Existing responsibilities that already survive

| Needed outcome | Existing holder | Result |
|---|---|---|
| generic material transition envelope, authority, outcome, UNKNOWN | `thin-rts/RECORD_TEMPLATE.md` | `KEEP` |
| hostile-input / promotion-output hygiene | `thin-rts/security-intake/` | `KEEP` |
| evidence packaging, digest binding, encryption/custody receipt semantics | `thin-rts/cloud-custody/` | `KEEP` |
| provider-neutral Tier-0 capture, fresh reconstruction, alternate recovery path | `thin-rts/continuity/` | `KEEP` |
| Git history / immutable review evidence | Git + GitHub | `EXTERNAL / KEEP` |
| current official-source retrieval | external search/browser/official portals | `EXTERNALIZE` |
| scheduling / notifications | external/native scheduler | `EXTERNALIZE` |
| document/PDF/form rendering | external document tooling | `EXTERNALIZE` |
| AI interpretation / candidate classification | external AI/model occupant | `EXTERNALIZE` |
| submission, signature, disclosure, spending | authorized human/external action surface | `EXTERNALIZE / AUTHORITY_REQUIRED` |

No new storage, crypto, cloud, crawler, legal database, scheduler, daemon, submission platform, or general agent runtime survives.

## 2. What can be structurally extracted

`Material Transition Record` already contains the generic reconstruction skeleton:

- stable record identity;
- intent;
- source reference;
- assumptions/constraints;
- authority holder/scope;
- action reference;
- outcome reference;
- PASS/FAIL/BLOCKED/UNKNOWN classification;
- review/promotion separation;
- next state;
- explicit unknowns.

That means Event Assist does **not** need a second general event database or workflow engine.

The event layer can be modeled as a typed projection over the same durable ideas.

## 3. What does not survive as free-form reuse

DA attacked the proposal: "put the rest in generic text/reference fields."

Verdict: `FAIL`.

Free-form fields cannot reliably prove or machine-check:

- evidence coverage status such as `MISSING_RECOVERABLE` versus `BLOCKED_AUTHORITY`;
- whether a material gap is still present while an aggregate case says PASS;
- deadline identity and the source that created the deadline;
- whether a VERIFIED legal/procedure pin still has a current official basis;
- whether an official mutable URL has a decision-time observed artifact + digest;
- whether applicability facts are confirmed or UNKNOWN;
- whether an external watch is stale, failed, or references a nonexistent source;
- whether a document is only `DOCUMENT_READY_DRAFT` or actually submission-authorized;
- whether an action needs authority that is currently BLOCKED;
- whether a deadline is now overdue;
- correction/supersession lineage without overwriting prior decisions.

The missing capability is therefore **typed binding and mechanical fail-closed validation**, not another service.

## 4. Surviving new-build responsibility

`IRREDUCIBLE_NEW_BUILD = ONE PURE STATE BINDER / VALIDATOR`

Candidate occupant:

`thin-rts/event-assist/event_state/`

Hard containment:

- no network access;
- no background process;
- no database;
- no provider credentials;
- no source retrieval;
- no scheduler;
- no evidence payload storage;
- no cryptography;
- no cloud transport;
- no autonomous submission;
- no promotion authority;
- input/output are UTF-8 JSON plus explicit references to external/retained evidence.

Its job is only:

`EXTERNAL OBSERVATIONS + EXISTING EVIDENCE/CUSTODY REFS`
-> `TYPED CASE BINDING`
-> `MECHANICAL GAP / DEADLINE / WATCH / AUTHORITY REPORT`
-> `PASS / UNKNOWN_OR_BLOCKED`

## 5. Counter-DA: "the binder is just old RTS growing back"

Attack: one bounded state-binding package can still become a seed for a new monolith.

Containment:

- every external capability remains an explicit reference, not imported into the module;
- no plugin framework or provider abstraction is introduced here;
- no persistent service lifetime exists;
- no action executor exists;
- schemas fail closed instead of adding generic dynamic behavior;
- DARWIN may replace the Python occupant if a simpler external validator later preserves the same deaths and workload.

`BINDER_EXISTS != PLATFORM_AUTHORIZED`.

## 6. Counter-DA: current-source evidence can mutate

A live official URL alone does not preserve what was observed at decision time.

Repair:

For a `VERIFIED` legal/deadline pin or ready-state document, the current official source must also bind:

- a decision-time observed artifact reference;
- a lowercase SHA-256 digest of that artifact;
- a declared freshness boundary when the workload needs one.

Storage remains Git/Custody/Continuity responsibility. The binder stores only the binding.

## 7. Gate verdict

`MONOLITHIC_EVENT_ASSIST = DEAD`

`EXISTING_CUSTODY_RECOVERY_SECURITY = REUSED`

`GENERIC_EVENT_ENVELOPE = EXTRACTED_FROM_EXISTING_RECORD_MODEL`

`TYPED_STATE_BINDER = SURVIVES AS MINIMAL NEW BUILD`

`GATE_2_METEOR = AUTHORIZED FOR THIS BOUNDED OCCUPANT ONLY`
