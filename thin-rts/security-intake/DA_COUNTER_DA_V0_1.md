# Pre-WITNESS / Pre-Promotion Quarantine — DA / Counter-DA v0.2

Status: `SURVIVED / READY_FOR_ADOPTION`

## Candidate under attack

> Put an evidence-bound quarantine immediately before WITNESS ingestion, preserve raw evidence separately, turn discovered threat conditions into METEOR regressions, admit only verified normalized learning into ULTIMATE LOOP, and enforce the same hygiene contract again before generated output is promoted.

## DA Round 1 — kill the proposal

### DA-01 — GlassWorm-specific subsystem is unjustified

Attack: a bespoke GlassWorm engine would fossilize one incident and violate Thin RTS externalization.

Verdict: `FAIL`.

Repair: kill the incident-specific subsystem. Preserve only the generic quarantine contract. GlassWorm becomes one inherited regression capsule.

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

Verdict: `FAIL` for explicit governed intake/egress.

Repair: explicit intake and egress fail closed for unsupported/unscanned file types.

## Counter-DA Round 2 — attack the repairs

### CDA-01 — test corpus itself can contaminate the repository

Attack: embedding actual invisible/Variation Selector characters in Python regression source makes the guard fail on its own fixtures and leaves hostile bytes in normal source history.

Verdict: `FAIL`.

Repair: regression fixtures synthesize dangerous codepoints at runtime with `chr(...)`; malicious bytes are not committed as literal source text.

### CDA-02 — attacker splits a payload across prose to evade a simple line threshold

Attack: line-local density alone is weak.

Verdict: `FAIL` for line-only heuristics.

Repair: prose blocks all non-U+FE0F basic selectors and all supplementary selectors regardless of density, with a file-level U+FE0F density backstop.

### CDA-03 — scanner compromise / lower-substrate compromise

Attack: a compromised interpreter, runner, repository credential or scanner source can lie about CLEAN.

Verdict: `SURVIVES_AS_SCOPE_LIMIT`, not solved by adding a larger custom RTS security engine.

Repair/containment: evidence records retain scanner/core/gate identity and exact hashes; GitHub workflow is read-only; checkout credentials are not persisted; Actions are full-SHA pinned; an independent scanner is composed. No claim of physical truth is made from one scanner alone.

### CDA-04 — Unicode-only defense misses token theft, dependencies and visible malicious code

Attack: GlassWorm is not reducible to invisible Unicode.

Verdict: `SURVIVES_AS_SCOPE_LIMIT`.

Disposition: GitHub account/credential security, branch/ruleset controls, dependency intelligence, secret scanning and other platform controls remain separate external responsibilities. The quarantine contract composes them rather than pretending to replace them.

### CDA-05 — egress remains asymmetric

Attack: pre-ingest hygiene does not stop ULTIMATE LOOP or an AI from later generating dangerous output.

Verdict: `FAIL`.

Repair: factor shared `quarantine_core.py`; add `egress_quarantine.py`; exercise `repository_egress_gate.py` in actual PR CI; bind producer/target identities and exact output hashes; emit aggregate manifest SHA-256.

GitHub evidence on run #1077: repository egress checked 1015 files, 1015 CLEAN, 0 BLOCK, with a concrete manifest digest.

### CDA-06 — the evaluation rubric itself was wrong

Attack: the previous score was presented as `94/100`, but the category maxima summed to 110. A security gate whose own score arithmetic is inconsistent is not promotion-grade evidence.

Verdict: `FAIL`.

Repair: discard the old score rather than renormalizing it after the fact. Freeze a new acceptance rubric whose maxima sum exactly to 100 and require direct evidence for every row.

This is retained as a meta-regression: the evaluator is inside the attack surface.

### CDA-07 — egress CLI + unit tests do not prove promotion enforcement

Attack: an adapter that merely exists can be bypassed operationally.

Verdict: `FAIL`.

Repair: CI now executes the repository-wide promotion egress gate on the actual PR merge surface. The result includes producer identity, target identity, checked-file count and manifest hash.

### CDA-08 — independent scanner with zero findings may simply be broken

Attack: `0 findings` is meaningless if the external scanner/rules cannot detect the intended attack class.

Verdict: `FAIL`.

Repair: before scanning the repository, the Semgrep challenger must accept a clean fixture and reject three generated attack fixtures: Python `eval`, Python shell execution and JavaScript `eval`.

GitHub run #1077: challenger self-test succeeded, then the repository scan completed with 0 blocking findings.

### CDA-09 — adding a security scanner can create a new supply-chain or credential path

Attack: the defense itself downloads code and runs in CI; an unbounded scanner integration could increase the blast radius.

Verdict: `FAIL` for the first loose composition.

Repair/containment:

- Semgrep engine version pinned to `1.172.0`;
- GitHub Actions pinned to full commit SHAs;
- workflow permission remains `contents: read`;
- checkout uses `persist-credentials: false`;
- no repository secret is required for the challenger;
- challenger is independent evidence, not sole promotion authority.

## Historical design-gap autopsy

The original Unicode Guard was created before systematic DA/Counter-DA became a normal design step for this surface. It defended the threat classes that were explicitly considered at the time, but Variation Selector encoding and the `.github` exclusion were not adversarially generated as counterexamples.

Classification: `DESIGN_COVERAGE_DEBT / PROCESS_GAP`, not evidence that the earlier guard did nothing.

The process correction is more important than the one patch:

`NEW MATERIAL THREAT CLASS`
→ freeze raw evidence
→ DA/autopsy the miss
→ extract transferable death cause
→ create regression capsule
→ attack current occupant and challengers
→ successors inherit the death cause.

This does not make future imagination complete. It makes discovered misses durable and forces later implementations to survive them.

## Raison d'être verdict

`SURVIVES`

The surviving responsibility is:

> No untrusted object may become WITNESS/learning input, and no generated object may become promoted output, without boundary identity, exact-byte integrity and an explicit hygiene verdict.

## METEOR verdict

`EXTERNAL_CONTROLS + THIN_GLUE_SURVIVES_CURRENT_EVIDENCE`

The Python scanner and Semgrep composition remain replaceable occupants. The contract, evidence boundary and inherited death causes are the protected objects.

## Promotion verdict

`SURVIVED / READY_FOR_ADOPTION`

Evidence satisfied before final promotion:

- actual GitHub CI is green;
- 14 symmetric quarantine regressions are green;
- repository-wide egress is exercised on the PR surface;
- the independent scanner proves it can reject attack fixtures before its clean scan;
- CI credentials and Action references are hardened;
- the score rubric has been corrected and frozen at exactly 100 maximum points.

Unknown future threat classes remain possible and reopen METEOR/DARWIN when observed; that uncertainty is not hidden by the adoption verdict.
