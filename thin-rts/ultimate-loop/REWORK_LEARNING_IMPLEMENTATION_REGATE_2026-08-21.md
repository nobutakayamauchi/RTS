# Ultimate Loop Optional Rework Learning — Implementation Re-Gate

Timestamp: 2026-08-21 JST
Status: `SURVIVES CURRENT PROTOTYPE GATE / OPTIONAL ONLY / PROMOTION AUTHORITY SEPARATE`
PR: #363
Issue: #362

## Sequence actually run

`FROZEN SUBJECT → DA → COUNTER-DA → BOUNDED PROTOTYPE → METEOR → IMPLEMENTATION REVIEW → DA/COUNTER-DA REPLAY → MERGE CANDIDATE`

## Prototype finding before final re-gate

The first prototype incorrectly aggregated weak friction signals across every recent scope. Three unrelated one-off signals in three unrelated tasks could therefore combine into one global difficult-zone score and activate assist.

That violated the frozen requirement that assist be limited to the current difficult zone.

The implementation was changed before promotion:

- scoring now occurs per `(task_scope, source, operation)` scope;
- unrelated scopes cannot pool signals;
- `active_scope` is explicit in ASSIST_ACTIVE/CLEARING;
- success-tail clearing is evaluated inside that active scope;
- missing scope identity fails closed;
- historical evidence only contributes to an exactly matching scope.

The exact cross-scope contamination case is now a METEOR regression test.

## DA replay against implementation

### DA-01 surveillance/profile creep

Survives under current evidence. The evaluator accepts task/operation events and evidence refs; it requires no user identity or personal trait model.

### DA-02 one failure becomes permanent weakness

Survives. A single isolated MULTI_TAB event stays OBSERVE in the frozen regression workload.

### DA-03 first-use history dependency

Survives. Realtime friction/repetition/backtrack evidence can activate ASSIST_ACTIVE with empty history.

### DA-04 assist spreads globally

First implementation: `DIED` due to cross-scope signal pooling.

Current implementation: repaired. Signals, assist actions and clearing are bound to `active_scope`; unrelated weak scopes do not combine.

### DA-05 commit count becomes incompetence proxy

Survives the prototype boundary. No commit-count input has automatic authority; history is represented only as explicitly derived matching clusters and raises confidence by bounded policy weight.

### DA-06 storage/platform expansion

Survives. Prototype is a pure evaluator + tests + CI gate; no database, daemon, crawler, or always-on service was added.

## Counter-DA replay

### C-DA-01 too conservative to help on first run

Rejected. The zero-history realtime activation case passes.

### C-DA-02 fixed universal thresholds overfit one operator

Still valid as a limitation. Thresholds remain policy inputs and the current defaults are pilot defaults, not canonical universal constants.

### C-DA-03 evaluator quietly gains execution authority

Rejected under current implementation. Output is recommendation/state only; no shell/UI action executor exists.

### C-DA-04 clearing oscillates after one success

Rejected. The default requires a bounded two-success tail and preserves CLEARING as a separate state.

### C-DA-05 stale history overrides current success

Rejected by regression: even very large matching historical rework cannot force assist when current events are successful and contain no current rework event.

## METEOR workload result

GitHub Actions workflow `Rework Learning Meteor` passed on the repaired implementation head.

Frozen attacks include:

- realtime activation without history;
- unrelated historical scope rejection;
- assisted-scope clearing;
- clearing back to observe;
- stale/large old history cannot override current success;
- one multi-tab event does not create a universal rule;
- unrelated weak scopes cannot pool into a difficult zone;
- missing scope identity fails closed.

## Remaining bounded limitations

- The pilot does not yet ingest Git/GitHub/trace automatically; it evaluates normalized evidence supplied to it.
- Threshold calibration is not yet proven across operators/workloads.
- Historical-cluster freshness/decay is not modeled beyond current-scope matching.
- No claim is made that assist reduces rework until the next material pilot measures before/after outcomes.

These are not hidden. They keep this candidate optional and prevent universal-core promotion.

## Verdict

`OPTIONAL PROTOTYPE SURVIVES CURRENT DA / COUNTER-DA / METEOR GATE`

Merge is acceptable as an optional experimental capability if CI remains green. This verdict does not promote it into the canonical mandatory Ultimate Loop flow and grants no deployment/execution authority.
