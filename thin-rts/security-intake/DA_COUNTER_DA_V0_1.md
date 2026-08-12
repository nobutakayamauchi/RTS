# Pre-WITNESS Intake Quarantine — DA / Counter-DA v0.1

Status: `COMPLETED_FOR_CURRENT_EVIDENCE / SHADOW_ONLY`

## Candidate under attack

Original candidate:

> Put a security check immediately before WITNESS ingestion, preserve raw evidence separately, turn discovered threat conditions into METEOR regressions, admit only verified normalized learning into ULTIMATE LOOP, and re-check output before promotion.

## DA Round 1 — kill the proposal

### DA-01 — GlassWorm-specific subsystem is unjustified

Attack: a bespoke GlassWorm engine would fossilize one incident and violate Thin RTS externalization.

Verdict: `FAIL`.

Repair: kill the incident-specific subsystem. Preserve only the generic `Pre-WITNESS Intake Quarantine` contract. GlassWorm becomes one inherited regression capsule.

### DA-02 — blanket `U+FE00..U+FE0F` ban breaks legitimate prose

Attack: U+FE0F is ordinary emoji presentation syntax. A global ban creates unnecessary false positives.

Verdict: `FAIL`.

Repair: context-sensitive policy. Executable/config surfaces block Variation Selectors. Prose permits ordinary U+FE0F at low density while blocking other basic selectors, supplementary selectors and suspicious density.

### DA-03 — existing Unicode Guard does not protect workflows

Attack: `.github` was excluded, so workflow YAML could carry dangerous invisible content while the guard reported green.

Verdict: `FAIL`.

Repair: remove `.github` from excluded directories. Workflow YAML is now scanned.

### DA-04 — scanning after WITNESS is too late

Attack: if WITNESS or a downstream AI interprets hostile material first, a later scanner cannot prove that ingestion was safe.

Verdict: `FAIL`.

Repair: freeze source identity and exact-byte hash first, then hygiene scan, then allow only CLEAN material into WITNESS.

### DA-05 — raw hostile evidence can poison the learning loop

Attack: preserving the malicious sample and feeding it directly into ULTIMATE LOOP confuses evidence custody with learning admission.

Verdict: `FAIL`.

Repair: preserve raw evidence outside the learning path. WITNESS extracts a normalized invariant/regression capsule. The loop consumes the normalized result, not the hostile bytes.

### DA-06 — unsupported file types silently escape the gate

Attack: a scanner that skips unknown extensions can produce false confidence.

Verdict: `FAIL` for explicit WITNESS intake.

Repair: `scripts/intake_quarantine.py` fails closed for explicitly submitted unsupported/unscanned file types.

## Counter-DA Round 2 — attack the repairs

### CDA-01 — test corpus itself can contaminate the repository

Attack: embedding actual invisible/Variation Selector characters in Python regression source makes the guard fail on its own fixtures and leaves hostile bytes in normal source history.

Verdict: `FAIL`.

Repair: regression fixtures synthesize codepoints at runtime with `chr(...)`; malicious bytes are not committed as literal source text.

### CDA-02 — attacker splits a payload across prose to evade a simple line threshold

Attack: line-local density alone is weak.

Verdict: `FAIL` for line-only heuristics.

Repair: current prose policy blocks all non-U+FE0F basic selectors and all supplementary selectors regardless of density, with a file-level U+FE0F density backstop. Known GlassWorm-style Variation Selector encoding therefore has to survive multiple independent conditions.

### CDA-03 — scanner compromise / lower-substrate compromise

Attack: a compromised Python interpreter, runner, repository credential or scanner source can lie about CLEAN.

Verdict: `SURVIVES_AS_SCOPE_LIMIT`, not solved by more Thin RTS code.

Disposition: retain scanner/gate version and content hash in the evidence record; use GitHub/platform controls and independent external scanners where available. Do not claim physical truth from this gate alone.

### CDA-04 — Unicode-only defense misses token theft, dependency compromise and malicious visible code

Attack: GlassWorm is not reducible to invisible Unicode.

Verdict: `SURVIVES_AS_SCOPE_LIMIT`.

Disposition: the gate is a composable contract, not a complete malware detector. GitHub credential hardening, branch/ruleset controls, action/dependency pinning and external security scanners remain external responsibilities/challengers.

### CDA-05 — egress remains asymmetric

Attack: pre-ingest hygiene does not stop ULTIMATE LOOP or an AI from later generating dangerous output.

Verdict: `OPEN_PROMOTION_GAP`.

Disposition: require the same hygiene contract at promotion/egress before this candidate can be considered complete. CI currently re-scans repository output, but a general live-environment egress adapter is not yet implemented.

## Raison d'être verdict

`SURVIVES`

The responsibility is not “detect GlassWorm.”

The surviving responsibility is:

> No untrusted object may become WITNESS/learning input without immutable source identity, exact-byte integrity and an explicit hygiene verdict.

## METEOR verdict

Current minimal candidate:

`EXTERNAL_CONTROLS + THIN_GLUE_SURVIVES_SHADOW`

The Python scanner is replaceable. The contract is the protected object.

## Promotion verdict

`NOT_YET_PROMOTED`

Blocking reasons:

- GitHub CI must run on the candidate branch/PR and remain green;
- egress symmetry is specified but not fully implemented as a generic adapter;
- independent/external scanner composition is not yet demonstrated live.

No material failure discovered in DA/Counter-DA justifies killing the intake responsibility itself.
