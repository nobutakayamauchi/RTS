# Thin RTS — Case Pattern Evidence Warning Requirement

Timestamp: **2026-08-11 19:54 JST**

Status: `HARD_COMPLETION_REQUIREMENT / NOT_YET_PASSED`

This requirement extends the event-evidence coverage and automatic evidence triage requirements.

## Purpose

Many users do not know in advance which facts or records may later become important evidence. Thin RTS must therefore learn from recurring real-world failure patterns and surface simple, timely preservation warnings when a relevant event is detected or explicitly reported.

The system is not a legal-advice oracle. Its job is to reduce preventable evidence loss by asking the right preservation question early enough that the evidence may still be obtainable.

## Case-pattern library

Thin RTS must maintain or consume a replaceable, reviewable library of recurring event/failure patterns.

Each pattern should contain at minimum:

- `pattern_id`
- event / situation label
- trigger phrases or structured event conditions
- common evidence-loss mistake(s)
- recommended evidence candidate(s)
- recommended capture timing
- original/metadata requirements when material
- privacy/authority constraints
- source/provenance of the pattern
- jurisdiction/context tag when material
- confidence / review status
- last review/update time
- known limitations / UNKNOWN elements

Patterns may be learned from prior user failures, public official guidance, case summaries, practitioner-provided checklists, and other authorized sources, but no single source is treated as exhaustive truth.

## Just-in-time warning behavior

When the user reports or the authorized system observes an event matching a known pattern, Thin RTS should immediately perform an evidence-gap check.

Example:

User: `引っ越しをした`

Potential warning:

> 退去・入居時の室内状態が後で争点になることがあります。部屋全体と傷・汚れ・設備状態を、日付が分かる形で撮影・保存できていますか？

The system should then classify the relevant evidence candidates as:

- `PRESENT_VERIFIED`
- `PRESENT_UNVERIFIED`
- `MISSING_STILL_OBTAINABLE`
- `MISSING_TIME_SENSITIVE`
- `MISSING_NO_LONGER_OBTAINABLE`
- `BLOCKED_BY_AUTHORITY_OR_PRIVACY`
- `UNKNOWN`

If evidence is missing but still obtainable, the system should surface a concrete next preservation action rather than merely saying `missing`.

## Warning priority

Warnings should be prioritized by expected loss if delayed, not by how many patterns can be displayed.

High-priority warning candidates include evidence that is:

- likely to disappear or change quickly;
- controlled by another party;
- difficult to reconstruct later;
- dependent on device/account/provider access that may soon be lost;
- materially useful for identifying time, source, sequence, condition, authority, or outcome;
- commonly lost through a known user mistake.

The system should avoid flooding the user with low-value warnings. Repeated or duplicate warnings should be compressed.

## Learn from failure

When a later dispute or reconstruction reveals that useful evidence was missing, Thin RTS should create a candidate learning record:

`EVENT`
→ `MISSING / WEAK EVIDENCE`
→ `WHY IT WAS LOST`
→ `WHEN IT COULD HAVE BEEN CAPTURED`
→ `NEW OR UPDATED CASE PATTERN`
→ `DA / REVIEW`
→ `PROMOTION OR REJECTION`

A past mistake should become a future warning mechanism when the pattern survives review.

No individual mistake may be generalized into a universal rule without review.

## Event examples

Examples are illustrative, not exhaustive:

- move-in / move-out → room condition photos/video, meter readings, keys, handover records, damage/repair communications;
- workplace meeting / disciplinary discussion → notice, attendees, written conditions, follow-up email, contemporaneous notes, permitted recordings where lawful/authorized;
- accident / property damage → scene condition, time/location, involved parties, contemporaneous photos/video, repair/estimate records;
- online transaction / marketplace dispute → listing state, seller/buyer identity, order/payment records, messages, delivery/receipt state;
- account suspension / service dispute → displayed notice, timestamps, account identifiers, correspondence, relevant terms/version references;
- software incident → runtime/deployment identity, logs, request/session ids, screenshots, config/revision identity, observed outcome.

## Tool-gap behavior

If the evidence pattern calls for a capture method the current environment cannot perform, Thin RTS must not immediately build a custom subsystem.

Flow:

`NEEDED EVIDENCE`
→ `CHECK EXISTING DEVICE/OS/APP EXPORT`
→ `CHECK EXISTING OSS/CLI/API/PROVIDER TOOL`
→ `CHECK BOUNDED MANUAL CAPTURE`
→ `CHECK AUTHORITY/PRIVACY`
→ `TOOL_GAP`
→ `WITNESS DESTROY LOOP / METEOR GATE`
→ `ADD ONLY SURVIVING GLUE OR IRREDUCIBLE BUILD`

## Privacy / authority boundary

A warning that evidence may be useful does not authorize unlawful or unauthorized collection.

The system must distinguish:

- `SHOULD_PRESERVE_IF_AUTHORIZED`
- `AUTHORIZED_TO_COLLECT`
- `NOT_AUTHORIZED`
- `LEGAL_OR_POLICY_UNCERTAIN`

When authority is unclear, the system should preserve the question and warn the user rather than silently collecting restricted material.

## Completion test

This requirement passes only if Thin RTS can demonstrate on a frozen test set that:

1. a user-reported event activates the correct case pattern;
2. the system asks about the highest-value time-sensitive evidence;
3. existing evidence is recognized and not redundantly requested;
4. missing evidence is classified correctly;
5. an obtainable missing item produces a concrete capture action;
6. a common user mistake produces an appropriate warning;
7. an unavailable capability becomes a `TOOL_GAP` rather than automatic custom build;
8. a prior simulated failure can update a candidate pattern and later improve the warning behavior;
9. a pattern with weak/conflicting support remains bounded by confidence/UNKNOWN rather than being presented as legal certainty;
10. privacy/authority constraints can suppress or block collection while still preserving the warning.

## Current verdict

`NOT_COMPLETE`

The requirement is now defined, but no frozen case-pattern corpus, event matcher, evidence-gap checker, or demonstrated warning loop has yet passed the completion test.