# Event Assist Prototype A — External Composition

Timestamp: **2026-08-11 20:14 JST**

Status: `PAPER_PROTOTYPE / EXTERNAL_FIRST / NOT_YET_SCORED`

## Thesis

Attempt to satisfy `thin-rts/event-assist/FEATURE_SPEC.md` almost entirely with existing capabilities and the smallest possible Thin RTS binding glue.

This is the preferred track. It receives first right of refusal.

## Candidate composition

### Event interpretation / triage

Use an existing AI/tooling layer to:

- classify an authorized reported event;
- identify missing applicability facts;
- generate evidence candidates;
- compare against reviewed case patterns;
- produce structured candidate pins.

The model is not the authority for law or evidence truth. Its output remains source-bound and contestable.

### Current legal / program / procedure retrieval

Use existing web/search/browser/API capability against authoritative current sources and official portals.

Do not build a law database or news crawler.

### Case-pattern registry

Use ordinary versioned data/documents in Git/GitHub with provenance/type/review state.

Do not build a separate knowledge database unless real retrieval/scale failures require one.

### Evidence integrity

Use standard/off-the-shelf hashing and archive tooling plus Thin RTS manifest/custody records.

Candidate tools/classes:

- standard SHA-256 tooling;
- standard archive/compression tooling;
- Git/GitHub for public-safe structural history;
- external trusted timestamp/signature/transparency attachment where useful.

### Encryption / recovery

Use an existing well-reviewed file-encryption tool; favor public-key recipient encryption so the unattended producer need not retain the long-term decryption secret.

No custom cipher/KDF/key-sharing protocol.

### Cloud transport

Use an existing provider-neutral transfer/CLI/API adapter where possible.

Thin RTS records only the logical provider/object/version/generation evidence needed for custody and recovery.

### Scheduling / alerts

Use existing OS/platform scheduler and existing notification surfaces where available.

Thin RTS owns alert state/health semantics, not a new scheduler or messaging platform.

### Forms / document readiness

Use current official forms plus existing document/PDF/form tooling.

Thin RTS binds form/version/source, known values, unknown fields, required attachments, deadline, destination, and authority state.

### Independent verification

Use ordinary external tools to recompute hashes, decrypt/extract when authorized, and verify logical bundle invariants without trusting the AI conversation.

## Minimal Thin RTS glue allowed in Prototype A

Only responsibilities that cannot be expressed safely through ordinary existing artifacts may survive, such as:

- small event-case schema;
- case-pattern typed record;
- evidence manifest/custody binding;
- Auto-pin state record;
- tool/provider adapter interface;
- verification report contract;
- orchestration glue connecting external tools.

## What Prototype A is trying to kill

Prototype A explicitly tries to kill the need for:

- custom event-processing service;
- custom law/benefit database;
- custom evidence database;
- custom encryption system;
- custom cloud client;
- custom notification engine;
- custom form-submission engine;
- custom long-running RTS controller/kernel.

## Failure conditions

Prototype A fails a responsibility only when the frozen workload demonstrates a material gap such as:

- cannot preserve required state or provenance;
- external-tool composition creates materially worse security/recovery burden;
- repeated manual action defeats the forgetful-operator requirement;
- no stable adapter can represent provider/version identity;
- source/currentness/authority cannot be bounded safely;
- reliability/maintenance/integration complexity exceeds a smaller custom implementation;
- the same gap recurs after reasonable external alternatives are tried.

Aesthetic dislike or extra commands do not prove failure.

## Deliverable shape

If this prototype survives, the successor RTS implementation should be mostly:

`EXTERNAL TOOLS + VERSIONED RECORD CONTRACTS + THIN ORCHESTRATION GLUE`

Current verdict:

`METEOR_VERDICT = NOT_RUN`
