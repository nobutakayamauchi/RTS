# Thin RTS — Event-Driven Evidence Coverage & Remediation Requirement

Timestamp: **2026-08-11 19:51 JST**

Status: `HARD_COMPLETION_REQUIREMENT / NOT_YET_PASSED`

This requirement extends:

- `LEGAL_EVIDENCE_COMPLETION_GATE.md`
- `ENCRYPTED_CLOUD_CUSTODY_REQUIREMENT.md`
- `AUTO_EVIDENCE_TRIAGE_REQUIREMENT.md`

Thin RTS is not complete unless it can move from **"an event happened"** to **"what should have been preserved, what was actually preserved, what is missing, and how to remediate the gap"** without requiring the operator to already understand evidence law or evidence-management practice.

## User outcome

When a material event is detected or declared, Thin RTS should automatically create an `EVENT_EVIDENCE_CASE` and answer four separate questions:

1. **What happened?**
2. **What evidence classes are normally useful for proving or disputing material facts about this kind of event?**
3. **Which of those evidence classes have actually been preserved and verified?**
4. **For each missing class, can the gap still be remediated safely and lawfully, and if so with what existing external tool or minimum new glue?**

The operator should not need to know in advance what an evidence checklist ought to contain.

## Event record

Each material event receives a stable event id and records at minimum:

- `event_id`
- `event_type_or_description`
- `event_time_or_range`
- `detection_or_report_time`
- `people/systems/locations involved` where authorized and material
- `candidate facts in dispute`
- `source of the event signal`
- `authority/privacy boundary`
- `known unknowns`
- `evidence coverage status`
- `remediation status`

An event description is not itself treated as a proven fact.

## Event → evidence plan

The system generates a **candidate evidence plan**, not a legal conclusion.

For each event it should derive, where relevant, candidate evidence classes such as:

- original documents / notices / contracts / forms;
- messages / email / chat / delivery metadata;
- audio / video / photographs;
- system/application logs;
- file/version/repository history;
- runtime/deployment identity;
- timestamps and location/context metadata;
- receipts / transaction/payment records;
- access/permission/authority records;
- medical/technical/professional records when lawfully available;
- witness/contact references;
- subsequent correction/retraction/response records;
- evidence showing absence, non-response, failure, or inconsistency where that absence itself is material.

The plan must preserve the reason each class was suggested and the source/basis for the suggestion.

## Common-mistake check

For each event, Thin RTS must run a **common evidence-handling mistake check**.

Examples include:

- only preserving screenshots while losing the original message/file/metadata;
- editing, cropping, converting, renaming, or re-saving the only original copy;
- failing to preserve the full conversation/thread/context;
- losing timestamps, sender/recipient/account identifiers, headers, version IDs, or route/source references;
- preserving a current state but not the state that existed at the time of the event;
- assuming a Git commit or file existence proves deployed runtime behavior;
- failing to record who acquired/copied/transformed evidence and when;
- mixing protected originals with presentation/redacted derivatives;
- relying on one device or one cloud account only;
- keeping ciphertext and its only decryption secret in the same trust boundary;
- preserving a summary while losing the source;
- failing to capture a disappearing/ephemeral source while it is still available;
- collecting data without clear authority or beyond necessary scope;
- deleting material because the operator believed it was "probably irrelevant" before triage.

The mistake model is advisory and must remain updateable as new real failures are observed.

## Coverage matrix

For every candidate evidence class, produce an explicit status:

- `PRESERVED_VERIFIED` — captured, integrity/provenance checks passed;
- `PRESERVED_UNVERIFIED` — object exists but verification is incomplete;
- `PARTIAL` — some material components/metadata/context are missing;
- `MISSING_RECOVERABLE` — absent now, but a lawful/authorized acquisition path remains;
- `MISSING_IRRECOVERABLE` — evidence is known or strongly evidenced to be no longer obtainable;
- `BLOCKED_AUTHORITY` — acquisition would exceed current authority/scope;
- `BLOCKED_TECHNICAL` — current tools cannot acquire/preserve it safely;
- `NOT_APPLICABLE` — reason recorded;
- `UNKNOWN` — insufficient evidence to classify.

No event receives an overall `PASS` while a material class remains silently unclassified.

## Missing-evidence remediation

When a material class is absent, Thin RTS must not jump directly to custom development.

Remediation order:

`CHECK EXISTING SOURCE`
→ `CHECK EXISTING EXPORT/DOWNLOAD FEATURE`
→ `CHECK EXISTING OSS / CLI / API / PROVIDER TOOL`
→ `CHECK MANUAL ONE-TIME ACQUISITION`
→ `CHECK EXTERNAL SPECIALIST / AUTHORIZED PROCESS`
→ `BOUNDED GLUE`
→ `IRREDUCIBLE BUILD ONLY IF STILL PROVEN`

Any proposed new tool must return through the WITNESS Destroy Loop / Meteor Gate before build authorization.

## Tool-gap record

If a material evidence class cannot be preserved with current capabilities, create a `TOOL_GAP` record containing:

- missing evidence class;
- event(s) affected;
- why the evidence matters;
- why current tools are insufficient;
- deadline/volatility if the source may disappear;
- legal/authority constraints;
- strongest available external alternatives tested;
- minimum capability still missing;
- whether temporary manual preservation is possible;
- `DROP / EXTERNALIZE / GLUE / IRREDUCIBLE_BUILD` verdict.

A tool is not authorized merely because it would be convenient.

## Volatility / urgency

Some event evidence is perishable.

The system should assign a preservation urgency based on factors such as:

- source can be edited/deleted/expired;
- logs have known retention windows;
- cloud/provider export may later become unavailable;
- device may be lost/replaced;
- account access may be revoked;
- physical condition may change;
- third-party records may require a timely request.

Urgency affects **preservation priority**, not authority. A volatile source does not grant permission to collect unlawfully.

## Event completion state

An event may close only with an explicit coverage report containing:

- facts/issues the evidence package is intended to support or challenge;
- evidence classes requested by the plan;
- objects actually preserved;
- integrity/provenance verification results;
- remaining gaps;
- remediation attempts;
- unresolved UNKNOWN/BLOCKED items;
- encrypted-cloud custody status where applicable;
- reproduction/verification status;
- any expert/legal-review recommendation.

Suggested bounded event verdicts:

- `EVENT_EVIDENCE_COMPLETE_FOR_CURRENT_PLAN`
- `EVENT_EVIDENCE_PARTIAL`
- `EVENT_EVIDENCE_BLOCKED`
- `EVENT_EVIDENCE_UNKNOWN`

`COMPLETE_FOR_CURRENT_PLAN` never means universally legally sufficient; new facts, claims, or professional advice may reopen the event plan.

## Automation / anti-zubora behavior

The normal operator experience should be closer to:

> "Something happened" → system creates the event case → proposes what to preserve → captures what it lawfully can → verifies and encrypts it → tells the operator only what remains missing or blocked.

The operator should not be expected to manually maintain an evidence matrix.

When a new event resembles a previous event with a demonstrated missing-evidence failure, the prior failure should automatically influence the new event plan so that the same preventable evidence-loss pattern is not repeated unchanged.

## Adversarial completion tests

Before Thin RTS completion, this layer must demonstrate at least:

1. a declared event with several expected evidence classes;
2. one class already preserved correctly;
3. one class preserved incorrectly (for example screenshot-only without original/context) and detected as `PARTIAL`;
4. one missing but recoverable class and a successful remediation;
5. one missing class blocked by authority and correctly left blocked;
6. one technical tool gap evaluated through external-first replacement before any build;
7. one volatile evidence source that receives higher preservation priority;
8. a common handling mistake caught before original evidence is destroyed;
9. encrypted cloud preservation of the resulting event bundle;
10. fresh-environment verification/reproduction of the event evidence report without the original chat/session.

The workload must not be weakened after failure.

## Completion verdict

`NOT_COMPLETE`

Architecture text is insufficient. Passing requires a real event workload whose evidence coverage, missing-item remediation, mistake detection, encrypted custody, and independent reconstruction are all demonstrated.