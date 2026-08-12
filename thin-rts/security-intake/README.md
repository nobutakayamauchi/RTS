# Pre-WITNESS Intake Quarantine v0

Status: `SHADOW_CANDIDATE / NOT_PROMOTION_AUTHORITY`

Purpose: prevent untrusted external material from becoming WITNESS or ULTIMATE LOOP input before its source identity, bytes and hygiene verdict are frozen.

This is not an antivirus engine and not a GlassWorm-specific subsystem. The surviving RTS responsibility is only the intake contract and the minimum glue needed to enforce it.

## Boundary

`EXTERNAL MATERIAL`
→ `RAW HASH + SOURCE IDENTITY`
→ `INTAKE QUARANTINE`
→ `CLEAN / BLOCK`
→ only `CLEAN` may enter `WITNESS`
→ WITNESS extracts evidence / invariants
→ `ULTIMATE LOOP ADMISSION`
→ only normalized, evidence-bound learning/regression material may enter the loop.

Raw hostile material may be retained as evidence outside the learning path, but it is never promoted merely because it was observed.

## Required intake record

Every admitted object must carry at least:

- immutable or externally meaningful `source_id`;
- SHA-256 of the exact bytes inspected;
- scanner/gate version identity;
- hygiene verdict;
- findings when blocked.

No `CLEAN` verdict means no WITNESS ingestion.

## Current minimum scanner

`python3 scripts/intake_quarantine.py --source-id <identity> <files...>`

The current bounded scanner covers:

- zero-width and selected invisible Unicode controls;
- bidi controls associated with review confusion / Trojan Source style attacks;
- Variation Selectors `U+FE00..U+FE0F` on executable/config surfaces;
- supplementary Variation Selectors `U+E0100..U+E01EF`;
- `.github/workflows/**` and other machine-interpreted text surfaces;
- fail-closed behavior for explicitly submitted unsupported/unscanned file types.

Markdown/text prose is treated differently from executable/config text so ordinary emoji presentation does not automatically fail. Non-emoji basic Variation Selectors and supplementary Variation Selectors remain blocking; unusually dense U+FE0F usage is also blocking.

## ULTIMATE LOOP integration

The gate participates in the method, not as a permanent implementation slot.

### Loop 1 — Raison d'être Destroy

Surviving responsibility:

> Untrusted material must not become trusted WITNESS/learning input without immutable identity and a hygiene verdict.

Killed responsibilities:

- custom antivirus engine;
- custom malware reputation network;
- custom secret scanner;
- custom GitHub branch-protection implementation;
- custom dependency intelligence platform.

Those should be externalized or composed from existing tools when available.

### Loop 2 — METEOR CRUCIBLE

The concrete scanner/glue must survive inherited threat regressions and false-positive cases. Known death causes are retained as regression capsules.

### Loop 3 — DARWIN ARENA

The current Python scanner has no permanent right to exist. A better external scanner, GitHub-native control, parser, policy engine or future platform capability may replace it if it satisfies the same frozen intake contract with better evidence, cost or burden.

## Raw evidence vs learning

`RAW THREAT EVIDENCE != LOOP KNOWLEDGE`

Raw suspicious bytes stay quarantined and evidence-bound. WITNESS may derive a normalized threat invariant and regression capsule. ULTIMATE LOOP consumes the normalized, verified result rather than executing or trusting the hostile input itself.

## Symmetry rule

The same hygiene contract should be applied again before loop-generated code/config/workflow output is promoted to GitHub or a live environment.

This v0 implements the pre-WITNESS gate and CI regression surface. Full egress enforcement remains a promotion requirement, not a claim of completion.
