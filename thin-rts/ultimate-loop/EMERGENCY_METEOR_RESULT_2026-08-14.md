# Ultimate Loop Emergency Recovery — Destructive METEOR Result

Date: **2026-08-14 JST**

Status: `STRUCTURAL_SURVIVOR / MERGE_READY_CANDIDATE / NOT_CANONICAL_UNTIL_MERGED`

Frozen contenders:

1. `EXISTING + MANUAL_BOUNDED`
2. `STRUCTURAL EXTRACTION`
3. `STANDALONE NEW BUILD`

Frozen rule: the workload was not weakened after a failure. Passing a test does not create merge, failover, promotion, or canonicalization authority.

## Result

### Existing + MANUAL_BOUNDED

Verdict: `KEEP_CONDITIONALLY`.

A qualified operator using the existing lifecycle / Continuity / Reality Gate / DARWIN composition remains a valid occupant when the workload RTO permits manual action and the runbook and evidence are current. It loses when the operator is unavailable, the runbook/RTO is insufficient, health state does not justify failover, fallback evidence is stale, or required guardrails are unproven.

Manual composition is therefore not a universal replacement for the structural binder, and the structural binder is not justified merely because automation is possible.

### Structural extraction

Verdict: `METEOR_SURVIVOR / MERGE_READY_CANDIDATE`.

The structural candidate keeps existing `lifecycle.py` as the authority owner and adds only the missing emergency evidence/state bindings. Monitoring, traffic switching, provider APIs, restart, secrets, scheduling and failover actuation remain external.

Surviving responsibilities include:

- normalized `HEALTHY / DEGRADED / FAILED / UNSAFE / UNKNOWN` semantics;
- ordinary degradation/failure hysteresis;
- current fallback identity/probe/freshness evidence;
- failure-domain independence and guardrail evidence;
- single-writer fencing requirement;
- `DEGRADED -> STANDBY_PREPARED`, not failover;
- `FAILED / UNSAFE -> FAILOVER_ELIGIBLE` only through existing failover authority;
- external failover actuation only;
- persisted trigger snapshot after failover;
- post-failover Reality validation bound to the selected fallback and validation time;
- temporary recovery without permanent promotion;
- automatic failback prohibition;
- explicit Recovery Debt returning to Discovery, root-cause review and METEOR/DARWIN.

### Standalone new build

Verdict: `REJECT`.

The standalone candidate can reach functional parity on the bounded workload, but parity does not justify duplicating lifecycle authority, evidence rules and emergency transition policy. No material architecture-superiority evidence was observed that compensates for the additional policy-drift and maintenance surface.

`PARITY != ARCHITECTURE SUPERIORITY`.

## Deaths discovered and retained

The destructive rounds exposed material holes before the survivor state:

1. recovery validation could be accepted for the wrong fallback identity;
2. recovery validation time could precede the actual failover;
3. an applied recovery was incorrectly compared with the newest primary-health sample instead of its persisted triggering observation;
4. a later `HEALTHY` primary sample could erase the active temporary fallback state, debt and failback prohibition;
5. standalone operation-mode typos could bypass single-writer fencing;
6. the manual contender could map non-failure health states to `PRIMARY_UNAVAILABLE`;
7. the manual contender could accept an expired fallback probe;
8. the existing lifecycle still exposes the known provider-degradation precedence ambiguity where `watch_action=METEOR` can later be represented as `next_state=STANDBY` when a high-resilience standby is present.

The first seven are repaired in the candidate workload and preserved as regression memory. The eighth remains visible as an inherited lifecycle ambiguity; the structural emergency path avoids depending on that ambiguous representation by making degradation preparation explicit.

## Final regression evidence

On the tested candidate head before this result-only record:

- existing lifecycle baseline: `PASS`;
- inherited lifecycle destructive METEOR: `PASS`;
- emergency prototype regression: `PASS`;
- emergency destructive METEOR: `PASS`;
- review-found death regressions: `PASS`;
- combined focused test count: **84 / 84 PASS**;
- final review findings for the manual contender were repaired and their threads resolved.

## Architecture boundary

The survivor does **not** authorize or implement:

- a monitoring platform;
- health-check acquisition infrastructure;
- a traffic switch or load balancer;
- DNS/service-mesh control;
- provider SDK ownership;
- secret storage;
- an always-on daemon/scheduler;
- autonomous failover;
- automatic failback;
- emergency-to-permanent promotion.

External mechanisms remain replaceable occupants. The owned responsibility is only the bounded governance/evidence contract.

## Pre-merge verdict

`MANUAL_BOUNDED = KEEP WHEN RTO ALLOWS`

`STRUCTURAL EXTRACTION = METEOR WINNER`

`STANDALONE NEW ENGINE = REJECT`

`GENERAL FAILOVER PLATFORM = KEEP KILLED`

`CANONICALIZATION = PENDING EXPLICIT MERGE DECISION`

This result stops immediately before merge. Any material code change after the tested head reopens regression before merge authority can be exercised.
