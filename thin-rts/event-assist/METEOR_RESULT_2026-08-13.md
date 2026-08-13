# Event Assist — METEOR Gate 2 Result

Timestamp: **2026-08-13 10:02 JST**

Status: `LOCAL_METEOR_SURVIVES / REPOSITORY_CI_REQUIRED`

Candidate: `thin-rts/event-assist/event_state/`

Frozen rule: workload was not weakened after failure.

## Reality comparison

### REALITY_A — external/manual composition only

Composition:

- external AI/search;
- external official sources;
- native reminders;
- existing Git/Custody/Continuity;
- generic `Material Transition Record` only.

Strength: almost zero new code.

Fatal weakness under the frozen workload: the generic record can retain references, but it cannot mechanically guarantee typed evidence-gap state, deadline/source binding, source freshness, watch-health state, document/submission separation, or required-authority state. Those distinctions remain dependent on operator/AI discipline and can silently drift.

Verdict: `FAIL_FOR_ZERO-OMISSION MACHINE-CHECKABLE STATE`.

### REALITY_B — same external composition + bounded binder

Adds only a pure typed validator/report generator. It does not take over any external capability.

Verdict after attacks below: `SURVIVES_UNDER_CURRENT_LOCAL_EVIDENCE`.

## Meteor Round 1 — deaths

Initial unit surface passed 13/13, then the frozen/rotated workload killed five assumptions:

1. `MISSING_RECOVERABLE` could remain visible while aggregate classification still returned `PASS`.
2. a source labeled `CURRENT_OBSERVED` could remain trusted after its declared `stale_after` boundary;
3. a VERIFIED deadline pin could exist without a current official source;
4. a VERIFIED user-specific legal pin could cite an applicability fact that had become `UNKNOWN`;
5. a watch could reference a nonexistent source id.

Autopsy: `VISIBLE_FIELD != ENFORCED_INVARIANT`.

Repairs were limited to fail-closed binding logic. No new service/capability was added.

## Meteor Round 2 / Counter-DA — additional deaths

Rotated attacks found four more material gaps:

6. a `CONFIRMED` applicability fact could lack provenance;
7. an action could require an authority that was `BLOCKED` while the aggregate case still passed;
8. a passed deadline remained only a timestamp and was not surfaced as `OVERDUE`;
9. a mutable official URL could support VERIFIED state without a decision-time observation artifact digest.

All four were repaired without expanding responsibility.

## Repository Meteor Round 3 — publication transport death

The first GitHub Actions execution killed the publication path even though the local candidate had passed. The committed `event_state/` blob had been truncated before `validate_case`, so compilation succeeded but 30 of 31 tests errored with a missing public validator surface.

10. `LOCAL_PASS + GIT_OBJECT_EXISTS` was incorrectly treated as proof that the intended source artifact had arrived intact.

Autopsy: `COMMIT_INTEGRITY != INTENT_ARTIFACT_EQUIVALENCE`.

Repair:

- recompose the same logical binder into a bounded `event_state/` package (`base.py` primitives + `rules.py` cross-binding checks + `runtime.py` report/CLI) and republish the complete artifacts;
- freeze an explicit `SOURCE_MANIFEST.sha256` for the intended Event Assist / PHOENIX publication set;
- require CI to verify the exact manifest line count and every SHA-256 before executing tests;
- retain the failed run as an inherited publication-path death.

No product capability was added by this repair.

## Current test evidence

Local execution after repair:

- base Event Assist tests: **13/13 PASS**;
- frozen + adversarial + Counter-DA Meteor tests: **18/18 PASS**;
- combined Event Assist: **31/31 PASS**;
- creator-absent PHOENIX replacement probe: **6/6 PASS**.

### Frozen Case M — rental move-in

Result: `UNKNOWN_OR_BLOCKED` with `EVIDENCE_GAPS_PRESENT`.

This is a success condition for the tested state: a still-recoverable room-condition evidence class is missing, therefore the case must not claim false completeness. A concrete capture pin remains visible and retains collection-authority state.

### Frozen Case B — childbirth / claim-omission

Result at the frozen evaluation time: `PASS`.

The fixture binds:

- user-confirmed applicability context separately from official-source observations;
- current national/local official-source references;
- decision-time observed source artifacts + SHA-256;
- declared freshness boundaries;
- verified benefit/procedure and deadline pins;
- a news signal that remains only `CANDIDATE` until official confirmation;
- a `DOCUMENT_READY_DRAFT` while submit authority remains blocked;
- external watch health.

The fixture does not hard-code a national legal database into RTS. Current rules remain external observations.

## Real material pilot — PR #319 completion audit

A real public repository event, PR #319's adversarial completion audit, was represented as an EventCase from existing Git/GitHub evidence.

The operator did not manually file an evidence matrix; the external AI/tooling produced the bounded case record from already-held public evidence.

Pilot result at the frozen evaluation time: `PASS` for the EventCase state projection while `promote` authority remains explicitly `BLOCKED`.

Important separation:

`PILOT_STATE_PASS != MERGE_AUTHORITY`

An earlier pilot draft incorrectly made "run CI" itself require promotion authority and therefore blocked the event outcome. Autopsy: verification-gate state and business/event outcome had been mixed. The pilot was recomposed; CI remains a separate promotion gate.

## Operator-burden review

Compared with Reality A, Reality B adds one structured case artifact but removes repeated manual cross-checks for gaps, freshness, watch health, deadline state, and authority. In the real PR #319 pilot, the structured artifact was generated by the external AI from existing evidence; no database, daemon, manual evidence matrix, or new account was required.

Residual burden remains explicit: an external occupant must supply/refresh observations and source artifacts. The binder does not pretend to perform retrieval or reminders itself.

## Search saturation under current evidence

After Round 2 and the decision-time-source attack, rotated tests no longer produced a materially new responsibility. New defects may reopen Meteor.

`LOCAL_SEARCH_SATURATED_UNDER_CURRENT_EVIDENCE`

## Gate 2 verdict

`REALITY_A = KILLED_FOR_MACHINE-CHECKABLE_ZERO-OMISSION_STATE`

`REALITY_B = SURVIVES_LOCALLY`

`REPOSITORY_CI = REQUIRED_BEFORE_ADOPTION`

No claim of perfect security, exhaustive law discovery, legal correctness, or universal Event Assist completion is made by this local result alone.
