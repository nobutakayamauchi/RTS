# Thin RTS — Legal Rules, Benefits & Deadline Watch Requirement

Timestamp: **2026-08-11 19:56 JST**

Status: `HARD_COMPLETION_REQUIREMENT / NOT_YET_PASSED`

This requirement extends:

- `LEGAL_EVIDENCE_COMPLETION_GATE.md`
- `AUTO_EVIDENCE_TRIAGE_REQUIREMENT.md`
- `EVENT_EVIDENCE_COVERAGE_REQUIREMENT.md`
- `CASE_PATTERN_WARNING_REQUIREMENT.md`

A future Thin RTS completion verdict is invalid unless the system can detect not only evidence gaps, but also **applicable legal rules, currently usable public programs/procedures, deadlines, and likely application/claim omissions** from ordinary life events.

## User model

The system MUST assume the operator:

- does not know which laws/regulations apply;
- does not know which benefits, allowances, reimbursements, notifications, claims, or public procedures exist;
- may not know that an event starts a deadline;
- may forget to claim money or submit a required notice;
- may hear about a new risk/change only through ordinary news;
- wants the system to surface the next action quickly, not require a legal research workflow.

The response is automated current-source checking, event-triggered reminders, document readiness, and explicit uncertainty — not pretending the user is a lawyer.

## Event → legal/procedure watch

When an authorized event is detected or reported, Thin RTS should create a bounded event case and check, where relevant:

`EVENT`
→ `JURISDICTION / RESIDENCE / INSURANCE / EMPLOYMENT / HOUSEHOLD CONTEXT`
→ `APPLICABLE LAW / REGULATION / OFFICIAL GUIDANCE`
→ `AVAILABLE BENEFIT / CLAIM / NOTICE / PROCEDURE`
→ `ELIGIBILITY QUESTIONS`
→ `DEADLINE / EFFECTIVE DATE`
→ `REQUIRED DOCUMENTS / EVIDENCE`
→ `CURRENT HOLDINGS / GAPS`
→ `ALERT / AUTO-PIN`
→ `DOCUMENT-READY STATE`
→ `USER-AUTHORIZED SUBMISSION OR MANUAL NEXT ACTION`

Examples of trigger classes include birth, pregnancy, marriage/divorce, moving, job start/loss, illness/injury, disability, caregiving, death, accident, disaster, housing trouble, contract termination, benefits interruption, and material employment changes.

## Source hierarchy — current law and procedure

High-consequence legal/procedure conclusions MUST be grounded in current authoritative sources.

Preferred sources, depending on the question:

1. current laws/regulations and official legal databases;
2. competent ministry/agency official guidance, notices, forms, FAQs, and implementation documents;
3. relevant local-government official pages/forms for locality-specific procedures;
4. official public-procedure portals such as MyNaPortal where available;
5. official government policy/update feeds and promulgation/implementation notices;
6. court or other competent official material where procedural/evidentiary relevance is material.

Secondary reporting/news may be used as a **discovery signal only**. A news article or social post alone may not promote a legal rule, entitlement, deadline, or required action to `VERIFIED`.

## Time / jurisdiction identity

Every legal/procedure finding must preserve, where material:

- source authority;
- source reference;
- retrieval/observation time;
- effective date / start date / end date;
- jurisdiction/locality;
- administering organization;
- insurer/employer/household conditions where relevant;
- deadline and deadline basis;
- version/form identity;
- known transition or amendment status;
- unresolved applicability questions.

`OLD_RULE_EXISTS != CURRENT_RULE_APPLIES`.

A cached finding must be revalidated when its age, an approaching deadline, a known amendment, a change in user circumstances, or another material trigger makes staleness plausible.

## Auto-pin statuses

The system should surface compact event-linked pins such as:

- `ACTION_REQUIRED`
- `DEADLINE_SOON`
- `POSSIBLY_ELIGIBLE`
- `CLAIM_MAY_BE_MISSING`
- `NOTICE_MAY_BE_REQUIRED`
- `DOCUMENT_GAP`
- `EVIDENCE_GAP`
- `LAW_OR_PROGRAM_CHANGED`
- `CHANGE_PENDING / WATCH`
- `OFFICIAL_CONFIRMATION_REQUIRED`
- `NOT_APPLICABLE`
- `UNKNOWN`

A pin must explain **why it exists**, what current official source supports it, what is still unknown, and the next smallest action.

## Claim-omission prevention

The system must actively look for common omission patterns where a person may lose money, rights, or procedural position by doing nothing.

For each event it should ask:

- is there a benefit/allowance/reimbursement/insurance payment that may require action?
- is there a notice/registration/application that is not fully automatic?
- is there a deadline or retroactivity limit?
- does the municipality/insurer/employer administer the actual filing?
- what documents are normally needed?
- does the user already possess those documents/evidence?
- if not, can they still be obtained now?

The system must not assume that a benefit is automatically paid merely because the user appears eligible.

## Example pattern — childbirth

A reported childbirth should trigger current-source checks rather than a fixed hard-coded checklist.

The system should at least test for potentially relevant items such as:

- health-insurance childbirth-related benefits;
- child allowance / child-related municipal procedures;
- birth registration and related local procedures;
- employer/insurance notifications where applicable;
- required documents and deadlines;
- whether the procedure is automatic, direct-paid, user-applied, insurer-specific, employer-specific, or municipality-specific.

Amounts, eligibility conditions, forms, and deadlines must be read from current authoritative sources at the time of the event rather than frozen into the RTS codebase.

## Document-ready state

When a relevant procedure is identified, Thin RTS should prepare a `DOCUMENT_READY` packet without silently filing it.

The packet may contain or reference:

- official form/source;
- form/version/effective date;
- required attachments;
- known user/event fields;
- fields still requiring confirmation;
- submission destination;
- deadline;
- online / mail / counter / employer / insurer submission method;
- authority required for actual submission;
- evidence proving what was ultimately submitted and when.

Safe prefill or checklist generation is allowed. External submission, signature, disclosure of sensitive information, or legal representation requires explicit authority appropriate to that action.

## Emerging-news / rapid-response watch

The system may observe authorized public information streams for emerging patterns that suggest a new risk, fraud pattern, administrative change, benefits change, or commonly missed procedure.

Flow:

`NEWS / PUBLIC SIGNAL`
→ `UNVERIFIED_SIGNAL`
→ `SEARCH OFFICIAL PRIMARY SOURCES`
→ `CONFIRM CHANGE / NO CONFIRMATION / CONFLICT`
→ `MAP TO AFFECTED EVENT/USER CONDITIONS`
→ `AUTO-PIN IF MATERIAL`
→ `RECHECK AT EFFECTIVE DATE OR DEADLINE`

News volume, repetition, or virality does not itself establish legal truth.

Official government update feeds and rulemaking/public-comment sources may be watched directly when they materially improve early detection of pending changes.

## No silent legal certainty

The system provides evidence-backed legal/procedure **issue spotting and workflow assistance**, not an unconditional promise of legal correctness.

It must preserve:

- `UNKNOWN` when facts are missing;
- `CONFLICT` when authoritative sources or interpretations materially conflict;
- `PROFESSIONAL_REVIEW_RECOMMENDED` when case-specific interpretation or high consequences justify escalation;
- the exact sources and dates used for the alert.

A low-confidence model inference may trigger a check, but may not be presented as a verified legal obligation or entitlement.

## Privacy / profile minimization

Eligibility checking may require sensitive context, but the system must request and retain only what is materially needed.

Residence, household, insurance, employment, health/disability, pregnancy/birth, income, and similar attributes must not be broadly published or copied into public repositories.

The legal/program watch must integrate with encrypted custody and explicit authority boundaries.

## External-first implementation

The preferred composition is:

- existing official public sources and procedure portals for current rules/forms;
- existing search/retrieval capability for source discovery;
- existing schedulers/notification mechanisms for deadline/watch alerts;
- existing document/PDF/form tooling where available;
- Thin RTS glue only for event binding, source provenance, applicability questions, deadline state, document readiness, audit trail, and PASS/FAIL/UNKNOWN classification.

No custom national law database, benefits database, news crawler, legal model, or submission platform is authorized merely for architectural completeness.

A custom component may be considered only when a repeated real workload demonstrates an irreducible gap after external alternatives are tested.

## Adversarial / completion tests

Before this requirement passes, the frozen workload must demonstrate at least:

1. a life event that activates a national benefit/procedure check;
2. a procedure whose details vary by municipality/insurer/employer and therefore cannot be answered from a national rule alone;
3. a claim/notification that is not safely assumed to be automatic;
4. a deadline approaching and an auto-pin produced with source/date/basis;
5. an outdated cached rule rejected or revalidated against a newer official source;
6. a pending or newly changed rule detected from an official update/rulemaking source;
7. a news-only signal that remains `UNVERIFIED_SIGNAL` until official confirmation;
8. a generated `DOCUMENT_READY` packet whose form/version/source are current;
9. a case where insufficient user facts produce `UNKNOWN` rather than fabricated eligibility;
10. a case where the system recommends professional review rather than overclaiming;
11. actual submission remaining blocked until appropriate user authority is present;
12. an audit record that reconstructs why the alert existed, what source supported it, what action was taken, and whether the procedure was completed.

## Completion verdict

`NOT_COMPLETE`

Architecture text alone is insufficient. Passing requires current-source retrieval, event-triggered applicability checking, deadline alerting, document readiness, and adversarial stale/conflict/authority tests on real workloads.
