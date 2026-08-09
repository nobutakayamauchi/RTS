# FREEZER Post-2026-07-26 Intake Task

Status: STAGED_FOR_FREEZER_CAPTURE
Date: 2026-08-09
Scope: Recover adopted or implementation-waiting RTS / 限界開発 assets discussed after the last committed FREEZER index generation (2026-07-26) and preserve them without interrupting current WIP.

## Why this task exists

The committed FREEZER index currently contains RTS-FRZ-000001 through RTS-FRZ-000010 and was generated on 2026-07-26. Important design decisions made after that date are not represented in the committed FREEZER queue. This task preserves those decisions before any build work is started.

FREEZER rule remains unchanged: capture first, assess later, one WIP item at a time, and never auto-start implementation.

## Candidate intake set

### Candidate A — RTS Flight Recorder

Proposed next ID: `RTS-FRZ-000011`
Type: `architecture`
Initial state: `FROZEN`
Build authority: `NOT_APPROVED`

Purpose: observe real runtime/user operations, preserve execution evidence, and feed actual outcomes back into RTS debugging and learning flows.

Preserved requirements:
- record runtime actions and outcomes rather than infer them from code existence;
- preserve timestamps, execution context, evidence, and failure boundaries;
- support replay/reconstruction where safe;
- keep observation separate from automatic repair authority;
- provide explicit shutdown/kill behavior when instrumentation becomes unsafe or destabilizing.

Reason frozen: valuable and already adopted conceptually, but must not interrupt the current active build and requires a bounded preflight before implementation.

### Candidate B — Repair Patch Generation Mechanism

Proposed next ID: `RTS-FRZ-000012`
Type: `architecture`
Initial state: `FROZEN`
Build authority: `NOT_APPROVED`

Purpose: consume verified Flight Recorder/debug evidence and produce governed repair-patch proposals.

Preserved requirements:
- patch generation is proposal-first, not unrestricted autonomous mutation;
- evidence must identify the observed failure and deployment identity;
- generated patches require validation, rollback boundaries, and human/governed approval according to risk;
- repair authority must remain separate from observation authority;
- unsafe or low-confidence repair paths are quarantined rather than applied.

Dependencies: Flight Recorder / observation evidence and Deployment Identity.

### Candidate C — Deployment Identity Layer

Proposed next ID: `RTS-FRZ-000013`
Type: `architecture`
Initial state: `FROZEN`
Build authority: `NOT_APPROVED`

Purpose: establish what is actually deployed before runtime implementation classification or debugging conclusions are made.

Required invariant:

> Deployment Identity MUST be established before runtime implementation classification.

Identity examples:
- service/unit;
- working directory;
- executable/module;
- active route surface;
- deployed commit/revision where available.

Preserved rule:

> Code existence != runtime evidence.

Reason frozen: discovered through dogfood of the debug system; it is a structural requirement, but should be integrated only after preflight identifies the correct boundary and affected components.

### Candidate D — Governed Web Intake / Acquisition Layer

Proposed next ID: `RTS-FRZ-000014`
Type: `architecture`
Initial state: `FROZEN`
Build authority: `NOT_APPROVED`

Purpose: provide a shared, auditable intake layer for public Web pages, documents, and browser-mediated acquisition without reimplementing mature OSS crawlers.

Preserved architecture:
- common acquisition core;
- replaceable adapters such as Crawl4AI/Crawlee/Scrapy/browser-use/MarkItDown where appropriate;
- Policy Gate before acquisition;
- Acquisition Identity and Evidence records;
- source URL, time, acquisition method, auth state where applicable, status/result, and source hash;
- capability separation between Owner and Public profiles.

Public profile constraints:
- default to bounded/public acquisition;
- no silent use of authenticated sessions;
- no automatic CAPTCHA or access-control bypass;
- no fingerprint-evasion or restriction-bypass capability exposed by default;
- rate limiting and explicit policy checks;
- unsafe capability must be unavailable rather than merely hidden in UI.

Owner profile:
- may expose broader experimental capability for dogfood;
- still retains audit logs, emergency stop, rollback/recovery boundaries, and explicit policy evidence.

Reason frozen: value hypothesis is positive, but product value, OSS reuse/licensing, legal/ToS boundary, maintenance load, and smartphone-first usability require FC/build-value assessment before construction.

### Candidate E — Limit Over / Quarantine / Safe Release Policy

Proposed next ID: `RTS-FRZ-000015`
Type: `process`
Initial state: `FROZEN`
Build authority: `NOT_APPROVED`

Purpose: make release safety a standard rule for all publicly distributed 限界開発 outputs, not only Web Intake.

Canonical promotion path:

`LIMIT OVER -> Dogfood / Observation -> Hazard Found -> QUARANTINE / EMERGENCY FREEZE -> Safety Requirement -> Devil's Advocate / Validation -> SAFE RELEASE or OWNER ONLY`

Normative rules:
- LIMIT OVER does not mean safety-off;
- audit logging, emergency stop, rollback/recovery, and permission boundaries remain active in Owner mode;
- Owner mode removes selected preventive capability limits so the developer can encounter unknown risk before users do;
- any hazardous capability discovered in dogfood is stopped and quarantined immediately;
- a quarantined capability cannot be promoted to Public until a safety requirement is implemented and validated;
- if risk cannot be bounded adequately, capability remains OWNER ONLY or is rejected;
- Public builds are safety-promoted builds, not simple copies of the Owner build.

Reason frozen: adopted as a general release principle; implementation into the release/governance machinery should be done as a bounded process change rather than ad-hoc edits.

## Items intentionally NOT captured separately in this intake

### Debug system itself

The debug system is already active/dogfooded rather than merely deferred. This intake captures the newly discovered missing structural layer (Deployment Identity) and the deferred observation/repair mechanisms instead of duplicating the whole debug system as a fresh candidate.

### Vlog product feature backlog

Product-specific Vlog features belong to the Vlog project's own implementation backlog unless they become reusable RTS infrastructure. They should not be mixed into the RTS FREEZER merely because RTS is used during development.

## Required formalization work

Before merging these as real FREEZER items:

1. Create immutable `v001.json` plus `current.json` for each accepted candidate.
2. Preserve raw priority dimensions rather than inventing only a final score.
3. Rebuild `freezer/index/items.json`, `freezer/index/priority.json`, and `freezer/index/build_priority.json` with the existing deterministic code.
4. Rebuild `freezer/manifests/manifest.sha256`.
5. Run `python -m freezer.cli verify` and `python -m freezer.build_assessment verify`.
6. Do not create build assessments or preflights merely to make the records look ready; missing assessment/preflight is valid for newly captured work.
7. Do not select or start any candidate during this intake.

## Suggested initial dependency graph

```text
RTS-FRZ-000013 Deployment Identity
        |\
        | \
        v  v
RTS-FRZ-000011 Flight Recorder
        |
        v
RTS-FRZ-000012 Repair Patch Generation

RTS-FRZ-000015 Limit Over / Quarantine / Safe Release
        |
        v
RTS-FRZ-000014 Governed Web Intake / Acquisition
```

The release-safety policy is cross-cutting and may later become a dependency of other public-distribution candidates as they are recalled.

## Human decision recorded

The operator approved recovering the post-2026-07-26 implementation-waiting assets into the FREEZER workflow. This document stages that recovery while preserving the existing FREEZER invariant that derived indexes/manifests must be rebuilt and verified before the formal candidate records are merged.
