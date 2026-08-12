# Pre-WITNESS / Pre-Promotion Quarantine v1

Status: `ADOPT / PROMOTION_CANDIDATE`

Purpose: prevent untrusted external material from becoming WITNESS or ULTIMATE LOOP input before its source identity, exact bytes and hygiene verdict are frozen, and apply the same hygiene contract again before generated material is promoted outward.

This is not an antivirus engine and not a GlassWorm-specific subsystem. The surviving RTS responsibility is the boundary contract, evidence binding, regression inheritance and the minimum replaceable glue needed to enforce them.

## Symmetric boundary

`EXTERNAL MATERIAL`
→ `RAW HASH + SOURCE IDENTITY`
→ `PRE-WITNESS QUARANTINE`
→ `CLEAN / BLOCK`
→ only `CLEAN` may enter `WITNESS`
→ WITNESS extracts evidence / invariants
→ `ULTIMATE LOOP ADMISSION`
→ only normalized, evidence-bound learning/regression material may enter the loop
→ candidate output
→ `PRE-PROMOTION EGRESS QUARANTINE`
→ `CLEAN / BLOCK`
→ only `CLEAN` may be promoted to the governed target.

Raw hostile material may be retained as evidence outside the learning path, but it is never promoted merely because it was observed.

## Shared quarantine core

Both directions use `scripts/quarantine_core.py` so intake and egress cannot silently drift into different hygiene policies.

Every boundary record carries:

- boundary phase identity;
- immutable or externally meaningful source/producer/target identity;
- SHA-256 of the exact bytes inspected;
- scanner/core/gate version identity;
- hygiene verdict;
- findings when blocked.

No `CLEAN` verdict means no admission or promotion.

## Pre-WITNESS intake

`python3 scripts/intake_quarantine.py --source-id <identity> <files...>`

The bounded Unicode scanner covers:

- zero-width and selected invisible Unicode controls;
- bidi controls associated with review confusion / Trojan Source style attacks;
- Variation Selectors `U+FE00..U+FE0F` on executable/config surfaces;
- supplementary Variation Selectors `U+E0100..U+E01EF`;
- `.github/workflows/**` and other machine-interpreted text surfaces;
- fail-closed behavior for explicitly submitted unsupported/unscanned file types.

Markdown/text prose is treated differently from executable/config text so ordinary emoji presentation does not automatically fail. Non-emoji basic Variation Selectors and supplementary Variation Selectors remain blocking; unusually dense U+FE0F usage is also blocking.

## Pre-promotion egress

`python3 scripts/egress_quarantine.py --producer-id <identity> --target-id <identity> <files...>`

For repository promotion evidence, `scripts/repository_egress_gate.py` applies the same egress contract to the current guarded repository surface and emits an aggregate manifest SHA-256 over the checked path/hash set.

This means the system does not trust ULTIMATE LOOP, an AI, a generator, or a previous CLEAN result merely because the material originated internally.

`INTERNAL_ORIGIN != TRUSTED_OUTPUT`

## Independent challenger

The current Python Unicode scanner is not allowed to certify itself as the only detector.

A pinned Semgrep challenger is composed in CI with local rules for dynamic execution / shell-execution threat-chain patterns. Before scanning the repository, the challenger must prove that it:

- accepts a clean fixture;
- rejects a Python `eval` fixture;
- rejects a Python shell-execution fixture;
- rejects a JavaScript `eval` fixture.

Only after that self-test may a zero-finding repository scan count as evidence.

The external scanner remains replaceable and does not become sole promotion authority.

## CI hardening

The security workflow currently:

- uses `contents: read` only;
- pins GitHub Actions to full commit SHAs;
- uses `persist-credentials: false` on checkout;
- runs repository-wide Unicode hygiene;
- runs symmetric intake/egress regression tests;
- exercises the repository egress gate and manifest evidence;
- installs a pinned Semgrep version;
- proves the Semgrep challenger against attack fixtures before the clean scan.

## ULTIMATE LOOP integration

### Loop 1 — Raison d'être Destroy

Surviving responsibility:

> Untrusted material must not become trusted WITNESS/learning input, and generated material must not become promoted output, without boundary identity, exact-byte integrity and an explicit hygiene verdict.

Killed responsibilities:

- custom antivirus engine;
- custom malware reputation network;
- custom secret scanner;
- custom GitHub branch-protection implementation;
- custom dependency intelligence platform.

Those remain externalized/composed responsibilities when available.

### Loop 2 — METEOR CRUCIBLE

The concrete scanner/glue must survive inherited threat regressions, false-positive cases, boundary-symmetry attacks and challenger self-tests. Known death causes are retained as regression capsules.

### Loop 3 — DARWIN ARENA

The Python scanner and Semgrep composition have no permanent right to exist. Better external scanners, GitHub-native controls, parsers, policy engines or future platform capabilities may replace them only if they satisfy the same frozen contract and inherited death causes with better evidence, cost or burden.

## Raw evidence vs learning

`RAW THREAT EVIDENCE != LOOP KNOWLEDGE`

Raw suspicious bytes stay quarantined and evidence-bound. WITNESS may derive a normalized threat invariant and regression capsule. ULTIMATE LOOP consumes the normalized, verified result rather than executing or trusting the hostile input itself.

## Unknown-threat rule

No finite scanner proves that future unknown attack classes do not exist.

When a materially new threat class appears:

`NEW THREAT`
→ `FREEZE RAW EVIDENCE`
→ `AUTOPSY / DA`
→ `EXTRACT TRANSFERABLE DEATH CAUSE`
→ `REGRESSION CAPSULE`
→ `ATTACK CURRENT OCCUPANT + CHALLENGERS`
→ `PATCH / RECOMPOSE / REPLACE / KILL`
→ successors inherit the regression.

The protection improvement is therefore not “we imagined every attack.” It is that a newly discovered miss becomes a permanent survival obligation rather than disappearing with the implementation that first missed it.
