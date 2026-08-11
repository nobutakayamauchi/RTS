# Event Assist Meteor Duel — Frozen Comparison Gate

Timestamp: **2026-08-11 20:14 JST**

Status: `READY_FOR_PROTOTYPE_EXECUTION / NOT_YET_RUN`

Targets:

- Prototype A: `EVENT_ASSIST_PROTOTYPE_A_EXTERNAL.md`
- Prototype B: `EVENT_ASSIST_PROTOTYPE_B_MINIMAL_BUILD.md`
- Outcome contract: `thin-rts/event-assist/FEATURE_SPEC.md`

## Rule

The two prototype tracks must be attacked with the **same frozen workload, evidence requirements, and scoring axes**.

Do not weaken the workload after one track fails.
Do not reward custom code merely for existing.
Do not reward external composition merely for being external.

`EXTERNAL FIRST != EXTERNAL FOREVER`.

## Phase 0 — Destroy the desired implementation

Before executing either prototype, attack each required responsibility:

1. can the outcome be eliminated/simplified?
2. can an existing product/OS/SaaS/official portal/API/OSS/CLI/model do it?
3. can existing capabilities be composed safely?
4. can a bounded manual step beat automation?
5. what integration/maintenance/security/provider burden does composition introduce?
6. what exact remainder is irreducible?

Verdict per responsibility:

- `DROP`
- `EXTERNALIZE`
- `GLUE`
- `IRREDUCIBLE_BUILD`
- `EVIDENCE_INSUFFICIENT`

## Frozen workload

Run the cases defined in `FEATURE_SPEC.md` without changing their success criteria:

- Case M — rental move-in / evidence omission prevention;
- Case B — childbirth / claim-procedure omission prevention;
- Common preservation — hash/custody/encrypt/upload/remote verify/fresh restore/independent verify.

## Scoring axes

### Outcome fitness

- catches material evidence gaps early enough to act;
- preserves UNKNOWN instead of fabricating certainty;
- checks current authoritative sources when legal/procedural claims matter;
- produces usable prioritized next actions;
- reaches document-ready draft state without unauthorized submission;
- completes verifiable preservation/recovery.

### Evidence / epistemic fitness

- source/provenance binding;
- event truth vs content integrity separation;
- source-as-observed preservation;
- stale/conflict detection;
- reconstructability without chat memory.

### Security / privacy

- least privilege;
- plaintext exposure;
- key separation/recovery;
- third-party privacy/minimization;
- notification leakage;
- provider/config compromise blast radius.

### Reliability / recovery

- failure visibility;
- retry/idempotency behavior;
- watch health;
- cloud rollback/stale-object resistance;
- fresh-environment recovery;
- tool/schema/provider rot handling.

### Operator burden

- routine manual filing steps;
- number of places user must remember state;
- warning fatigue;
- recovery complexity;
- ability to function under stress.

### Whole-life cost

- new software/service cost;
- implementation size;
- maintenance burden;
- integration complexity;
- provider lock-in;
- operational failure modes.

## Required adversarial attacks

Both tracks must face at least:

- missing event facts;
- wrong event classification;
- missing evidence while capture window closes;
- stale legal/program source;
- news-only false signal;
- case-pattern poisoning;
- duplicate/contradictory alerts;
- notification privacy leak attempt;
- unauthorized collection or submission;
- one-byte evidence mutation;
- missing evidence object;
- wrong derivative parent;
- stale but valid cloud generation substitution;
- wrong key epoch / recipient substitution;
- provider upload success claim with missing/wrong remote object;
- scheduler/watch failure;
- original device/server loss;
- verifier operating without original AI conversation.

## Comparison rule

No single global winner is required.
Compare by **responsibility row**.

Example final map:

| Responsibility | A result | B result | Meteor verdict |
|---|---|---|---|
| current official-source retrieval | PASS | custom unnecessary | EXTERNALIZE |
| archive/encryption | PASS | custom prohibited | EXTERNALIZE |
| event state binding | brittle/manual | PASS | GLUE |
| alert delivery | PASS | custom unnecessary | EXTERNALIZE |

Only rows with demonstrated irreducible remainder may authorize new code.

## Stop rule

Continue DA / Counter-DA / rotated attack while materially new failure classes appear.
Stop when rotated attacks produce only already-known classes:

`SEARCH_SATURATED_UNDER_CURRENT_EVIDENCE`

New real evidence reopens the gate.

## Final possible verdicts

- `A_SURVIVES / B_KILLED`
- `A_SURVIVES_WITH_B_GLUE`
- `A_FAILS / B_SURVIVES_FOR_LISTED_GAPS_ONLY`
- `BOTH_FAIL / REQUIREMENT_OR_ASSUMPTION_REOPENED`
- `EVIDENCE_INSUFFICIENT`

Current state:

`METEOR_DUEL = READY_NOT_RUN`
