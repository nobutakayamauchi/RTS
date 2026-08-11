# Event Assist Prototype B — Minimal New Build Boundary

Timestamp: **2026-08-11 20:14 JST**

Status: `PAPER_PROTOTYPE / HELD_BEHIND_METEOR / NOT_YET_AUTHORIZED`

## Thesis

Define the smallest plausible custom component that could replace only the irreducible gaps left by Prototype A.

This document is **not authorization to build it yet**.
It exists so the Meteor comparison has a concrete custom alternative rather than comparing an external composition against a vague imagined platform.

## Proposed custom surface

A small event-assist orchestrator/library, not a platform.

It would own only:

1. normalized event-case state;
2. applicability-fact state with provenance/staleness;
3. typed case-pattern matching;
4. evidence-candidate / evidence-gap state;
5. Auto-pin state and dedup/escalation semantics;
6. source-observation references;
7. preservation-job requests into existing Thin RTS evidence custody;
8. document-ready draft metadata;
9. provider/tool adapter calls;
10. deterministic PASS / FAIL / UNKNOWN reports.

It would **not** own:

- web search engine;
- law/case-law/benefits database;
- news crawler;
- AI model runtime;
- cryptography;
- cloud storage implementation;
- notification delivery platform;
- PDF engine;
- electronic-signature/notary/timestamp service;
- final legal judgment;
- autonomous external submission;
- RTS controller/kernel/daemon unless separately proven irreducible.

## Candidate internal state machine

`OBSERVED`
→ `NEEDS_CONFIRMATION / CONFIRMED / UNKNOWN`
→ `COVERAGE_CHECKED`
→ `ACTION_PINNED / NO_ACTION / UNKNOWN`
→ `PRESERVATION_REQUESTED`
→ `PRESERVATION_VERIFIED / FAILED / UNKNOWN`
→ `DOCUMENT_READY_DRAFT` when applicable
→ `USER_REVIEW_REQUIRED`
→ external authority boundary

Every state transition must keep evidence/provenance references.

## Adapter boundary

Candidate narrow adapter interfaces:

- `source.search_or_fetch()`
- `evidence.acquire_or_reference()`
- `evidence.preserve()`
- `storage.put/get/stat/version()`
- `alert.deliver_status()`
- `document.render_or_prefill()`
- `verify.run()`

The adapter layer must not convert a provider/tool response into a stronger claim than the provider/tool actually supports.

## Why this alternative might survive

Potential reasons Prototype A could become worse than a small custom orchestrator:

- too many loosely coupled manual state transitions;
- inability to reconstruct why a pin existed across external tools;
- inconsistent UNKNOWN/CONFLICT/authority semantics;
- repeated loss of event→evidence→deadline→preservation linkage;
- brittle provider-specific glue repeated in many places;
- alert dedup/escalation state not expressible safely with ordinary artifacts;
- operator burden remains high despite nominal automation.

These are hypotheses only. They require observed Prototype A failures.

## Kill criteria

Prototype B dies if existing composition plus smaller glue can satisfy the frozen workload with materially lower or equal:

- security risk;
- maintenance cost;
- operational burden;
- recovery complexity;
- vendor dependency;
- correctness risk;
- implementation size.

Prototype B also dies if its custom state/orchestrator merely recreates capabilities already available in an external tool without a demonstrated integration failure.

## If Prototype B survives

Build only the responsibility rows that survive Meteor as `GLUE` or `IRREDUCIBLE_BUILD`.

No all-or-nothing winner is required. The final architecture may be:

`Prototype A composition + one or more tiny surviving B responsibilities`.

Current verdict:

`BUILD_AUTHORIZATION = NOT_AUTHORIZED`

`METEOR_VERDICT = NOT_RUN`
