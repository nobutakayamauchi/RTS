# Ultimate Loop Emergency Recovery — Necessity Review / DA / Counter-DA

Date: **2026-08-14 JST**

Status: `STRUCTURAL_EXTRACTION_SURVIVES / STANDALONE_ENGINE_NOT_JUSTIFIED / PROTOTYPE_METEOR_AUTHORIZED`

Frozen order:

`DROP -> EXTERNALIZE -> COMPOSE -> MANUAL_BOUNDED -> STRUCTURAL_EXTRACT -> NEW BUILD ONLY IF IRREDUCIBLE`

## Frozen responsibility

When a material external dependency becomes degraded, unavailable, unsafe or operationally unusable, preserve the human-important capability with the smallest verified recovery action, without converting emergency use into permanent promotion authority.

This is workload-conditional. If continuity is not material, normal failure or bounded manual recovery remains valid.

## Existing and external holders

External systems already own most mechanics: health checking, endpoint removal, retry/circuit breaking, DNS/load-balancer failover, service-mesh failover, monitoring and traffic switching. ULTIMATE LOOP should not recreate those mechanisms.

Existing RTS already owns most governance:

- `thin-rts/ultimate-loop/lifecycle.py` models `EMERGENCY`, `RECOVERY`, emergency triggers, fallback probes, failure-domain independence and failover authority;
- Continuity / Recovery owns provider-neutral reconstruction and warns that logical labels do not prove real independence;
- Post-Deploy Debug / Reality Gate owns verified Deployment Identity and post-change validation;
- METEOR / DARWIN own permanent replacement judgment;
- PHOENIX owns lineage/regeneration.

## Current structural gaps

The current lifecycle binder does not yet express all of the desired emergency semantics:

- material `PROVIDER_DEGRADATION` is classified as `METEOR` at the trigger layer, but an already-present high-resilience fallback can later produce `STANDBY` and override the final `next_state`; there is no explicit `DEGRADED -> PREPARE_STANDBY` emergency-preparation state or precedence contract;
- emergency recovery-probe freshness/provenance is not bound;
- failure-domain `VERIFIED` is not itself tied to an evidence reference;
- guardrail compatibility is not hard in the emergency path;
- single-writer failover has no fencing requirement;
- validated temporary recovery is not distinct from permanent promotion;
- recovery debt and manual post-incident judgment are not explicit;
- automatic failback is not explicitly forbidden.

The provider-degradation precedence behavior was observed directly in the prototype comparison and is retained as a future METEOR death case rather than hidden by changing the workload.

## Manual bounded alternative

A runbook plus a human operator can compose external failover tooling with Continuity, Deployment Identity, Reality Gate and DARWIN. This is the preferred occupant when a qualified operator can meet the workload RTO. No executable evaluator is justified merely for completeness.

## Structural prototype

`experiments/EMERGENCY_RECOVERY_GATE_20260814/structural_prototype.py`

It reuses the existing lifecycle evaluator for trigger, candidate and authority semantics and adds only missing bindings:

- normalized `HEALTHY / DEGRADED / FAILED / UNSAFE / UNKNOWN`;
- current health-observation identity/time plus hysteresis evidence before ordinary degradation/failure transition;
- explicit fallback candidate identity;
- current fallback probe reference and freshness;
- failure-domain independence evidence reference;
- guardrail compatibility evidence;
- optional single-writer fencing requirement;
- DEGRADED prepares standby without failover;
- FAILED/UNSAFE uses existing lifecycle emergency eligibility and external failover only;
- failover execution evidence and temporal ordering;
- post-failover Reality Gate requirement;
- temporary recovery rather than permanent promotion;
- automatic failback blocked;
- explicit recovery debt: Discovery Refresh, root-cause review, METEOR/DARWIN and permanent-occupant decision.

It owns no monitoring or actuator.

## Standalone new-build counter-prototype

`experiments/EMERGENCY_RECOVERY_GATE_20260814/standalone_prototype.py`

The independent evaluator can reproduce the same bounded outputs, so a standalone engine is technically feasible. But it duplicates authority, candidate disposition, evidence freshness and emergency transition logic already owned by the lifecycle binder. That creates policy drift risk.

Verdict under current evidence: `STANDALONE NEW ENGINE NOT JUSTIFIED UNLESS STRUCTURAL PROTOTYPE FAILS METEOR`.

## Prototype attack repairs

The first prototype pass exposed and repaired evidence holes before this gate closed:

- fallback eligibility previously permitted a missing `candidate_id`; the structural and standalone candidates now fail closed on missing fallback identity;
- applied recovery evidence previously accepted any nonblank `applied_at`; both candidates now require timezone-aware ISO-8601 and enforce `HEALTH_OBSERVED < FAILOVER_APPLIED <= EVALUATION_TIME`;
- test coverage preserves malformed/future recovery timestamps as permanent death cases.

These repairs do not authorize canonicalization. They only make the candidates eligible for the next destructive comparison.

## Next attack set

The next gate must cover at least: flapping degradation, stale standby evidence, false failure-domain independence, missing guardrail compatibility, single-writer failover without fencing, missing failover authority, no verified fallback, UNKNOWN health, failover without Reality validation, accidental permanent promotion, automatic failback, dropped recovery debt, degradation/standby precedence, and architecture growth into monitoring/traffic-switch/provider/secret/scheduler infrastructure.

## Gate verdict

`EMERGENCY RESPONSIBILITY = CONDITIONALLY NECESSARY`

`GENERAL MONITORING / FAILOVER PLATFORM = NOT JUSTIFIED`

`EXTERNAL FAILOVER MECHANICS = KEEP / COMPOSE`

`MANUAL_BOUNDED = VALID WHEN WORKLOAD RTO ALLOWS IT`

`CURRENT RTS LIFECYCLE + CONTINUITY + REALITY GATE + DARWIN = REUSE`

`STRUCTURAL EMERGENCY BINDING = SURVIVES AS PROTOTYPE`

`STANDALONE NEW ENGINE = NOT JUSTIFIED UNDER CURRENT ARCHITECTURE`

`CANONICALIZATION = NOT YET AUTHORIZED`

Next gate: destructive METEOR against the structural prototype, with the existing/manual composition and standalone new-build candidate retained as challengers.
