# Ultimate Loop Optional Rework Learning — DA / Counter-DA / METEOR Pilot

Timestamp: 2026-08-21 JST
Status: `PROTOTYPE / OPTIONAL / NO_PROMOTION_AUTHORITY`
Tracking: RTS issue #362

## Frozen subject

Add a bounded optional capability that learns where development work repeatedly backtracks, activates assist only for the current difficult zone, and returns to observation after the zone clears.

This is not a universal core responsibility. It must survive as an optional workload/candidate under the existing Ultimate Loop freeze rule.

## Raison d'etre boundary

The capability may consume existing Git/GitHub/trace/operation evidence. It must not create a new daemon or authoritative database merely to duplicate evidence already held elsewhere.

The smallest surviving responsibility is:

1. normalize bounded rework events;
2. detect current difficult-zone signals without requiring history;
3. optionally use historical clusters as supporting evidence;
4. recommend bounded assist actions;
5. preserve candidate derived knowledge, not copy all raw evidence;
6. clear assist after demonstrated local success.

## DA — kill the proposal

### DA-01: user surveillance disguised as optimization
Kill condition: the mechanism needs broad personal profiling or attributes unrelated to the active task.

Response: task_scope/source/operation and bounded friction markers are sufficient. A difficult zone is a temporary task/environment state, not a human trait.

### DA-02: one failure becomes a permanent weakness
Kill condition: one MULTI_TAB or paste failure creates durable assist or a universal rule.

Response: activation requires a combined signal threshold and current rework evidence. Historical evidence alone cannot force activation.

### DA-03: history dependency makes first use useless
Kill condition: assist cannot fire until a large history exists.

Response: realtime repetition, backtrack, and friction signals can activate without historical evidence.

### DA-04: assist causes more friction than it removes
Kill condition: assist remains globally enabled or follows the user into unrelated work.

Response: assist is scoped to the difficult zone and moves through ASSIST_ACTIVE → CLEARING → OBSERVE.

### DA-05: commit count is misread as incompetence
Kill condition: high commit volume alone is treated as a difficult zone.

Response: commit/trace history is supporting evidence only. Diagnosis must bind repeated responsibility, backtrack, failure recurrence, observation cost, or similar signals.

### DA-06: new storage platform becomes the real product
Kill condition: implementation requires a new database, crawler, service, or daemon before the pilot can operate.

Response: reject. Existing evidence remains authoritative where available; the prototype accepts bounded event/history inputs.

## Counter-DA — kill the defenses

### C-DA-01: requiring many signals misses obvious live failure
A current run may have no history but can still show three consecutive paste/tab/retry failures. Therefore history cannot be mandatory.

### C-DA-02: aggressive thresholds can become paternalistic
A fixed universal threshold is not justified yet. The pilot exposes policy values and freezes only a small default for testing.

### C-DA-03: automatic ENFORCE is premature
The prototype only computes assist state/actions. It grants no shell/UI execution authority and no promotion authority.

### C-DA-04: clearing too early can oscillate
One success is not enough. A bounded success tail is required before CLEARING/OBSERVE.

### C-DA-05: historical evidence can become stale
Old evidence may increase confidence only when scope keys match current work; current successful evidence must prevent old history from forcing assist.

## Prototype contract

Input event fields are bounded to task/operation evidence:

- event_id
- occurred_at
- task_scope
- source
- operation
- outcome
- rework_class
- from_step / to_step
- markers
- evidence_refs

Output includes:

- current/next mode
- difficult_zone
- signal score/components
- bounded assist actions
- derived knowledge candidates
- evidence-use statement

No user identity model is required.

## METEOR attacks frozen before implementation review

The regression workload must include at least:

1. realtime activation with zero history;
2. unrelated historical clusters do not activate assist;
3. ASSIST_ACTIVE enters CLEARING after a success tail;
4. CLEARING returns to OBSERVE when the zone stays clear;
5. massive old negative history cannot override current successful evidence;
6. one isolated multi-tab event does not become a universal rule.

## Pre-merge re-gate

Before promotion, rerun DA and Counter-DA against implementation evidence and CI. Merge is allowed only if:

- the prototype remains optional and scoped;
- no new permanent storage/service responsibility was smuggled in;
- realtime operation does not require history;
- historical evidence cannot force assist against current success;
- assist can clear;
- the frozen METEOR workload passes;
- no merge/deploy authority is inferred from the evaluator.
