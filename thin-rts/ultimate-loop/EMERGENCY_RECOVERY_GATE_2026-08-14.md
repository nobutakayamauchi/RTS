# ULTIMATE LOOP — Emergency Recovery / Failover Gate

Date: **2026-08-14 JST**

Status: `CANONICAL / ACTIVE / MERGED_PR_331`

## Purpose

When a workload declares continuity material and a critical external dependency becomes degraded, unavailable or unsafe, preserve the human-important capability with the smallest verified recovery action without converting emergency use into permanent promotion authority.

The gate is workload-conditional. If the workload RTO permits bounded manual recovery, `MANUAL_BOUNDED` remains a valid occupant.

## State path

```text
HEALTHY
-> DEGRADED
-> STANDBY_PREPARED
-> FAILED / UNSAFE
-> FAILOVER_ELIGIBLE
-> EXTERNAL_FAILOVER
-> RECOVERY_VALIDATION_REQUIRED
-> TEMPORARY_RECOVERY_VALIDATED
-> RECOVERY_DEBT_OPEN
-> DISCOVERY / ROOT-CAUSE / METEOR-DARWIN
-> RETURN / PARTIAL REPLACE / FULL REPLACE / STANDBY
```

`UNKNOWN` health fails closed to review rather than guessing a failover.

## Hard invariants

- `EMERGENCY_USE != PROMOTION`;
- `SERVICE_AVAILABLE != SERVICE_HEALTHY`;
- `DEGRADED != FAILED`;
- ordinary degradation/failure requires hysteresis before failover eligibility;
- `FAILOVER_ELIGIBLE != FAILOVER_EXECUTED`;
- failover actuation remains external and separately authorized;
- fallback identity must be explicit;
- fallback recovery-probe evidence must be current;
- material failure-domain independence requires evidence, not a label;
- security/privacy/guardrail compatibility is not waived by emergency;
- single-writer failover requires fencing evidence;
- `FAILOVER_EXECUTED != RECOVERY_VALIDATED`;
- applied recovery preserves its triggering-observation snapshot; later primary health does not rewrite the history of the failover;
- Reality validation must bind to the selected fallback identity and occur after failover application;
- `TEMPORARY_RECOVERY_VALIDATED != PERMANENT_REPLACEMENT`;
- automatic failback is prohibited;
- a recovered primary does not erase the active temporary occupant or Recovery Debt;
- post-incident Discovery, root-cause review and METEOR/DARWIN remain debt before permanent occupant judgment.

## Authority boundary

This gate does not own or authorize monitoring, DNS/load-balancer changes, service-mesh control, provider SDK actions, restart, secret access, traffic switching, deployment, rollback, promotion or failback.

Existing `lifecycle.py` remains the lifecycle/failover authority owner. The gate may classify evidence and declare an external failover eligible; an authorized external operator/tool performs the action.

## Recovery binding

After failover is applied, the recovery record preserves at least:

- fallback candidate identity;
- triggering health state/source/time;
- failover authority evidence reference;
- executor evidence reference;
- application time;
- explicit failback request state.

The Post-Deploy Reality Gate then validates the actual temporary occupant. A validation for a different fallback or a validation timestamp before the failover cannot close recovery.

## Recovery Debt

A temporary recovery carries:

- `DISCOVERY_REFRESH`;
- `ROOT_CAUSE_REVIEW`;
- `METEOR_DARWIN`;
- `PERMANENT_OCCUPANT_DECISION`.

Emergency restoration may shorten the normal comparison path; it may not silently erase the skipped judgment.

## Externalization boundary

Keep external and replaceable:

- health acquisition/monitoring;
- circuit breakers/retries;
- DNS/load balancers/service meshes;
- traffic switching;
- provider APIs;
- secret stores;
- schedulers;
- deployment/failover executors.

`EMERGENCY GATE != FAILOVER PLATFORM`.

## METEOR disposition

- Existing + `MANUAL_BOUNDED`: `KEEP_CONDITIONALLY` when operator/runbook/RTO satisfy the workload.
- Structural extraction: `PROMOTED / CANONICAL ACTIVE` after destructive METEOR and PR #331 merge.
- Standalone new engine: `REJECT` because parity does not justify duplicated lifecycle authority and policy drift.

See `EMERGENCY_METEOR_RESULT_2026-08-14.md` for destructive evidence and retained death causes.
