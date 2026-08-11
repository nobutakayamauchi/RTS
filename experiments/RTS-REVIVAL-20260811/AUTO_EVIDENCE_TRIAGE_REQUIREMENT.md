# Thin RTS — Automatic Evidence Triage & Preservation Requirement

Timestamp: **2026-08-11 19:49 JST**

Status: `HARD_COMPLETION_REQUIREMENT / NOT_YET_PASSED`

This requirement extends both:

- `LEGAL_EVIDENCE_COMPLETION_GATE.md`
- `ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`

A future Thin RTS completion verdict is invalid unless this requirement also passes.

## User model

Assume the primary operator:

- does not know what may later become legally or factually important;
- has limited legal knowledge;
- is poor at manual evidence organization;
- may not recognize evidence value at the moment it appears;
- may remember relevance only after the source has disappeared;
- should not need to manually classify every item.

The system therefore needs an automated **potential-evidence triage layer**, not merely a secure archive.

## Core outcome

Within an explicitly authorized collection scope, Thin RTS should be able to observe candidate material, estimate whether it may be relevant to an active or foreseeable dispute/claim, and automatically route material into encrypted evidence preservation when the cost of losing it is materially higher than the cost/risk of retaining it.

The system must NOT claim that its classification is legal advice or that an item is legally admissible merely because it was preserved.

## Source-of-truth hierarchy for triage

Triage rules should be grounded in, in descending order where applicable:

1. the operator's explicitly stated dispute/claim/issues and material facts;
2. current official court filing/evidence guidance and official forms;
3. current statutes/regulations/official administrative guidance relevant to the dispute type;
4. official published case-law patterns where available;
5. lawyer/professional instructions supplied by the operator;
6. project-specific prior accepted evidence categories and observed failure history;
7. model inference only as a bounded fallback.

Case-law search is evidence for patterns, not a complete universe of all judgments. Absence from a published database must not be treated as proof that a category is irrelevant.

## Evidence feature extraction

For each candidate item, the triage layer should extract or infer, where available:

- source/origin;
- event/creation/capture time;
- sender/creator/actor;
- subject/person/system involved;
- medium/type (message, email, contract, recording, photo, video, log, receipt, medical document, attendance record, order, notice, screenshot, etc.);
- whether the item records a request, instruction, agreement, refusal, change, payment, attendance, health state, access, publication, deletion, threat, warning, approval, denial, or outcome;
- which known issue/claim/fact it may support or contradict;
- whether it has an original/attachment/metadata chain that could be lost by later copying;
- volatility/disappearance risk;
- privacy/sensitivity level;
- whether retention appears authorized and within purpose.

## Triage verdicts

Every candidate receives one of:

- `PRESERVE_HIGH` — strong potential material relevance; preserve automatically.
- `PRESERVE_REVIEW` — plausible relevance or high loss-risk; preserve to encrypted review quarantine.
- `IGNORE_LOW` — low expected relevance and low loss-risk; do not preserve by default.
- `BLOCKED` — collection/retention is not authorized or would cross a prohibited boundary.
- `UNKNOWN` — system cannot responsibly classify; do not silently convert UNKNOWN into LOW.

The triage layer must record the reason/features/source references that produced the verdict.

## Asymmetric-loss rule

Evidence triage is not ordinary spam filtering.

A false negative may permanently destroy later proof, while a false positive usually creates storage/privacy/review cost.

Therefore, **within authorized scope**, the classifier may bias toward encrypted preservation when:

- the material is highly volatile;
- the source may disappear or be edited;
- the item is uniquely tied to a material event;
- the relevance is uncertain but potentially high;
- an official form/guidance/case-law pattern makes the category plausibly material.

However, this bias does not override privacy, secrecy, access-control, interception/recording law, contractual restrictions, or purpose limitation.

## Official-form / filing-shape awareness

The system should be able to map preserved material into the kinds of descriptive fields commonly required for evidence explanation and later filing preparation, including where applicable:

- evidence number/id;
- original/copy/derivative status;
- title/subject;
- creation/event date;
- creator/source;
- acquisition method;
- fact/issue the evidence may support;
- notes/limitations;
- confidentiality/redaction status.

This mapping is preparatory metadata only; it does not itself file evidence or decide litigation strategy.

## Case-law / guidance update model

The system may periodically refresh externally maintained legal/evidence reference material, but must preserve:

- source identity;
- retrieval timestamp;
- jurisdiction/scope;
- version/date where available;
- whether the source is official;
- transformation/summarization history;
- uncertainty and known incompleteness.

A newer source may change triage rules prospectively. Previously preserved originals are not deleted merely because a classifier changed.

## Automatic preservation path

For `PRESERVE_HIGH` and authorized `PRESERVE_REVIEW` items:

`CANDIDATE SOURCE`
→ `CAPTURE ORIGINAL / ORIGINAL REFERENCE`
→ `CONTENT DIGEST + METADATA`
→ `TRIAGE VERDICT + REASON`
→ `EVIDENCE MANIFEST / CUSTODY EVENT`
→ `BUNDLE OR QUARANTINE`
→ `CLIENT-SIDE ENCRYPTION`
→ `SELECTED CLOUD STORAGE`
→ `REMOTE VERIFY`
→ `PASS / FAIL / UNKNOWN`

Manual filing by the operator should not be required for routine preservation.

## Review quarantine

Uncertain material should not be treated as proven evidence merely because it is retained.

`PRESERVE_REVIEW` items should remain clearly separated from confirmed/material evidence sets until reviewed or promoted by an authorized person/process.

Retention, legal relevance, admissibility, and publication are separate decisions.

## Anti-surveillance / authority boundary

Automatic evidence triage MUST NOT become an excuse for indiscriminate monitoring.

Before collection/preservation, the system must be able to determine or record:

- what source/surface it is authorized to inspect;
- whose data may be involved;
- what purpose justifies collection;
- whether capture itself requires additional permission/consent;
- whether plaintext may leave the local trust boundary;
- what retention period/hold applies where known.

If authority is unclear, classification is `BLOCKED` or `UNKNOWN`, not automatic capture by convenience.

## Human override

The operator or authorized professional may:

- force-preserve an item;
- mark an item as non-material;
- place/remove a legal hold;
- change dispute/issue definitions;
- provide a lawyer-defined evidence checklist;
- correct a misclassification.

Overrides themselves become auditable custody/decision records and do not silently rewrite the original classifier output.

## Explainability requirement

For every automatic preserve decision, the system must be able to answer in simple language:

- **Why was this saved?**
- **What issue might it relate to?**
- **What source/rule/pattern triggered it?**
- **What is still UNKNOWN?**
- **Where is the encrypted copy?**
- **What would be lost if the original disappeared?**

The operator should not need legal vocabulary to understand the answer.

## Adversarial test set

Before completion, this layer must survive at least:

1. obviously material evidence is recognized and preserved automatically;
2. ambiguous but high-loss-risk material goes to `PRESERVE_REVIEW`, not silent discard;
3. irrelevant bulk/noise does not flood the evidence store uncontrollably;
4. an item matching a historical pattern but outside authorized scope is blocked;
5. official guidance changes and the rule version/source can be reconstructed;
6. a case-law source is incomplete and the system does not interpret absence as irrelevance;
7. classifier confidence is high but the supporting source is stale/low-authority — no promotion to certain legal relevance;
8. operator override preserves the original classification history;
9. preserved original is later redacted/summarized without overwriting the original linkage;
10. encrypted cloud preservation completes even when the operator performs no manual filing action;
11. false-positive review item can be isolated/expired where lawful without corrupting other evidence/custody history;
12. false-negative discovery during later review causes a rule-learning proposal without retroactively fabricating prior certainty.

The workload must not be weakened after failure.

## Current external-first design hypothesis

Still subject to WITNESS/Meteor testing:

- legal reference retrieval: official court/statutory/case-law sources via external search/retrieval;
- classification/feature extraction: existing AI/model capability;
- source capture/export: existing platform/provider APIs or local OS tools where authorized;
- encryption/cloud preservation: external off-the-shelf tools from `ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`;
- Thin RTS custom surface: normalized issue model, triage contract, source/rule provenance, custody binding, preservation trigger, explanation, and fail-closed state.

No custom legal expert system, court-admissibility oracle, case-law database, crawler platform, storage engine, or cryptographic implementation is authorized unless a tested irreducible gap survives.

## Completion verdict

`NOT_COMPLETE`

Completion requires a real reference workload in which potential evidence is detected without manual filing, correctly triaged, automatically encrypted/preserved to the selected cloud, later reconstructed with the triggering rule/source and custody history, and adversarial false-positive/false-negative/authority cases are exercised.
