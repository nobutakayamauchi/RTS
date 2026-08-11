# Thin RTS Completion Gate — Legal-Grade Evidence Preservation & Reproduction

Timestamp: **2026-08-11 19:40 JST**

Status: `HARD_COMPLETION_GATE / NOT_YET_PASSED`

## Completion rule

Thin RTS is **not complete** merely because it can reconstruct development state, survive destructive tests, or reproduce the practical responsibilities of the old RTS.

Completion additionally requires a demonstrated evidence-preservation and reproduction capability designed to withstand material dispute.

This gate exists because evidence preservation / legal-grade reconstruction was a material hole in the old RTS.

This is an engineering evidence-integrity target, **not a promise that any particular court, regulator, counterparty, or lawyer must accept a record as legally sufficient in every case**.

## Required evidence properties

A completed Thin RTS must demonstrate all of the following on a real reference workload.

### 1. Original / derivative separation

- Original captured evidence is never silently overwritten by a normalized, redacted, converted, summarized, or reformatted derivative.
- Every derivative records its parent evidence identifier(s), transformation, actor/tool, timestamp, and resulting digest.
- Public/presentation copies may minimize private content, but the system must preserve a bounded way to prove which protected original they derive from.

### 2. Content identity

For each material evidence object:

- record a stable evidence identifier;
- record byte-level cryptographic digest(s), with SHA-256 or stronger preferred for the evidence manifest even when Git object identities are also available;
- record size and media/type metadata when material;
- verify the digest again during export/reconstruction.

Git commit/blob identities remain useful provenance references, but Git identity alone is not treated as the sole legal-evidence integrity mechanism.

### 3. Time identity

Record separately where available:

- event/source time;
- capture time;
- repository/commit time;
- external-system observation time;
- time zone / offset;
- clock source or uncertainty when material.

A later timestamp must not be silently substituted for the time of the underlying event.

### 4. Provenance / chain of custody

Every material custody transition records:

- evidence id;
- prior location/reference;
- new location/reference;
- actor or tool;
- authority/scope;
- action performed;
- reason;
- timestamp;
- pre/post digest when bytes may have changed;
- whether the operation was copy, move, transform, redact, export, destroy, or verify.

No record may claim independent custody when the same ultimate administrator controls all participating systems.

### 5. Evidence description for dispute use

Each evidence item must be exportable with a human-readable description that can identify, where applicable:

- evidence number/id;
- original vs copy/derivative;
- title/subject;
- creation/event date;
- creator/source;
- acquisition method;
- what fact the evidence is intended to support;
- relevant notes/limitations;
- confidentiality/redaction status.

### 6. Runtime / deployment binding

When the evidence concerns software behavior, the package must distinguish and bind, where material:

- source/repository identity;
- clean/dirty worktree state;
- specific tracked file/blob identity;
- deployment/service identity;
- WorkingDirectory/cwd;
- executable/launcher;
- argv/module;
- PID/process lifetime;
- deployed artifact or load-time identity if available;
- active route/surface;
- execution/session/request identity;
- observed outcome.

`CODE_EXISTS != RUNTIME_REALITY` remains mandatory.

### 7. Authority separation

Evidence existence does not manufacture authority.

The record must distinguish:

- authority to observe/collect;
- authority to access private material;
- authority to transform/redact;
- authority to publish/disclose;
- authority to change repository/production state;
- authority to approve/promote;
- administratively independent authority, when genuinely present.

### 8. Reproduction package

A completed evidence bundle must be reconstructable by a third party from an export containing at minimum:

- evidence manifest;
- digest list;
- provenance/custody log;
- evidence descriptions;
- relevant originals or protected references;
- derivative linkage;
- environment/deployment identity where material;
- commands/procedure required for verification/reproduction;
- expected results;
- UNKNOWN / missing / disputed elements;
- version/schema identity for the bundle itself.

A verifier must be able to detect at least one deliberately modified evidence object.

### 9. Independent verification

The bundle must support verification without requiring the original AI conversation or trusting a narrative summary.

At least one independent verification path must use ordinary/off-the-shelf tooling and must:

- recompute hashes;
- detect a changed/missing file;
- check parent/derivative linkage;
- follow referenced repository/runtime evidence;
- produce a bounded PASS/FAIL/UNKNOWN result.

### 10. External trust attachment

Thin RTS must be able to attach, without owning the trust provider, external proof references such as:

- electronic signature/certificate evidence;
- trusted timestamp/date-information evidence;
- notarization/public-notary evidence;
- independent archive/transparency-log evidence;
- other external attestations.

The zero-additional-cost core does not require purchasing any such service for every record. However the evidence model must preserve the attachment, verification status, provider identity, time, and covered digest when external proof is used.

### 11. Privacy / minimization

Legal/evidentiary value does not authorize indiscriminate retention or publication.

- raw sensitive material is retained only when materially justified and authorized;
- public repositories must not receive secrets/private payloads merely for audit convenience;
- redaction creates a derivative and must not destroy the protected original linkage;
- collection, trust, retention, and publication remain separate decisions.

### 12. Destructive / adversarial test set

Before completion, the evidence layer must survive at least:

1. one-byte evidence mutation;
2. deleted evidence object;
3. substituted stale object with a valid historical hash/reference;
4. wrong execution → outcome binding;
5. timestamp inconsistency;
6. derivative whose claimed parent is wrong;
7. missing custody event;
8. missing promotion/disclosure authority;
9. public-copy redaction while protected original remains verifiable;
10. partial loss of a convenience/index copy while canonical evidence survives;
11. verifier operating without the original chat/session;
12. export → independent verify → reproduction on a fresh location/environment where feasible.

The workload must not be weakened after a failure.

## Completion verdicts

- `NOT_COMPLETE` — any mandatory property is unimplemented or untested.
- `EVIDENCE_INSUFFICIENT` — evidence exists but does not justify a pass.
- `PASS_FOR_ENGINEERING_EVIDENCE_GATE` — all mandatory properties demonstrated on the frozen workload.
- `LEGAL_ACCEPTABILITY_NOT_GUARANTEED` — always remains true; case-specific legal sufficiency belongs to the relevant legal process/professional authority.

## Current state

`NOT_COMPLETE`

The existing Thin RTS experiments already demonstrate useful pieces: Git-backed history/recovery, explicit authority boundaries, external CI evidence, privacy-minimized public records, and Deployment Identity observation.

They do **not yet** demonstrate the complete evidence bundle, cryptographic evidence manifest, custody log, independent verifier, tamper test, derivative linkage, export/reproduction package, or optional external-trust attachment model required by this gate.

Therefore the earlier Thin RTS candidate remains a candidate only. This gate supersedes any interpretation that the new RTS is complete today.
