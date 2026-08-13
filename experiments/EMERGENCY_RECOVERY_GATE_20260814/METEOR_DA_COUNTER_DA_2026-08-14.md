# Emergency Recovery — METEOR DA / Counter-DA Destructive Workload

Date: **2026-08-14 JST**

Status: `FROZEN_DESTRUCTIVE_WORKLOAD / PRE_MERGE_ONLY`

Contenders:

1. **Existing + MANUAL_BOUNDED composition** — current lifecycle / Continuity / Reality Gate / DARWIN plus a qualified operator and runbook.
2. **Structural extraction** — existing lifecycle remains authority owner; a thin emergency binder adds only missing health/fallback/recovery evidence semantics.
3. **Standalone new build** — independent emergency evaluator used as the strongest new-build counter-prototype.

No contender may weaken the frozen workload after a failure.

## DA: strongest case against the emergency responsibility

- Most failover mechanics already exist externally.
- Many workloads tolerate manual recovery; always-on emergency logic may cost more than downtime.
- Existing lifecycle already models EMERGENCY, RECOVERY, fallback probes, failure-domain independence and failover authority.
- A new engine creates a second policy authority and drift risk.
- An automatic failback or emergency promotion path can make a transient incident permanently alter architecture without METEOR/DARWIN.

## Counter-DA: strongest case for a bounded structural responsibility

A workload with material continuity/RTO requirements still needs a small, explicit contract for evidence and state that external failover products do not provide as Ultimate Loop governance:

- HEALTHY / DEGRADED / FAILED / UNSAFE / UNKNOWN;
- hysteresis for ordinary degradation/failure;
- current health and fallback evidence;
- exact fallback identity;
- failure-domain independence evidence, not labels;
- security/privacy/guardrail compatibility;
- single-writer fencing where applicable;
- failover authority remains external/current lifecycle authority;
- failover execution time/evidence;
- post-change Reality Gate validation bound to the actual fallback;
- temporary recovery is not permanent promotion;
- no automatic failback;
- explicit recovery debt returns to Discovery + root-cause + METEOR/DARWIN.

## Frozen death cases

The three contenders are attacked with the same material cases wherever their architecture permits comparison:

1. flapping degradation must not cause failover;
2. stale/future health evidence must not authorize action;
3. UNKNOWN health must not be guessed into failover;
4. DEGRADED may prepare standby but must not fail over;
5. UNSAFE may take the immediate emergency path without ordinary hysteresis delay;
6. missing fallback identity fails closed;
7. stale/missing fallback probe fails closed;
8. failure-domain labels without evidence fail closed;
9. guardrail compatibility missing/unknown fails closed;
10. single-writer failover without fencing fails closed;
11. technically suitable fallback without failover authority cannot execute;
12. failover remains external — binder does not become actuator;
13. applied failover without Reality Gate validation cannot be called recovered;
14. malformed/future/non-ordered failover timestamps fail closed;
15. Reality validation from the wrong fallback/deployment must not be replayed as recovery evidence;
16. recovery remains temporary and cannot create promotion authority;
17. automatic failback remains blocked pending post-incident judgment;
18. recovery debt cannot be silently dropped;
19. existing provider-degradation + standby precedence behavior remains visible as a known death/ambiguity case;
20. manual composition survives only when a qualified operator, current runbook and workload RTO all permit it;
21. standalone new build must materially outperform structural extraction to justify duplicate policy authority; parity is not enough.

## Promotion rule for this round

`PASSING TESTS != MERGE AUTHORITY`

This round ends at **pre-merge**. A survivor may become `MERGE_READY_CANDIDATE`, but canonicalization and merge require an explicit subsequent instruction.
