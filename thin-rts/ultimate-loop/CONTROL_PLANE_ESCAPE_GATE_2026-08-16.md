# ULTIMATE LOOP — Control Plane Escape / Recovery Control Surface Gate

Date: **2026-08-16 JST**

Status: `CANDIDATE / PR_PENDING`

## Purpose

When the normal operator surface becomes unusable, degraded, misleading, or unavailable, recovery must not depend on that same failed surface.

The objective is to regain bounded control through an independent surface, preserve available failure evidence, escalate only as far as required, and then prove the recovered runtime through Deployment Identity and the Post-Deploy Reality Gate.

This gate does **not** make CLI, SSH, provider APIs, service managers, reboot mechanisms, or failover engines part of Ultimate Loop. Those remain replaceable external executors.

## Core distinction

A control surface is the mechanism used to observe or actuate a workload, for example:

- web console / GUI;
- CLI;
- provider API / SDK;
- SSH / remote shell;
- service manager such as `systemd`;
- host or provider recovery interface.

The workload is the service or capability being protected.

`CONTROL_SURFACE_FAILURE != WORKLOAD_FAILURE`

A dead GUI may coexist with a healthy workload. A healthy GUI may coexist with a broken workload. They must be evidenced separately.

## State path

```text
PRIMARY CONTROL SURFACE HEALTHY
-> PRIMARY CONTROL SURFACE DEGRADED / FAILED / UNTRUSTWORTHY
-> EVIDENCE CAPTURE ATTEMPT
-> ALTERNATE CONTROL SURFACE ESTABLISHED
-> SERVICE-SCOPE RECOVERY WHEN SUFFICIENT
-> PROCESS-SCOPE RECOVERY WHEN REQUIRED
-> HOST-SCOPE RECOVERY WHEN REQUIRED
-> EXTERNAL RECREATE / FAILOVER WHEN REQUIRED
-> DEPLOYMENT IDENTITY RE-ESTABLISHED
-> POST-DEPLOY REALITY VALIDATION
-> RECOVERED / RETURN TO ANALYSIS
```

Every successful stage stops escalation. A broader destructive action is not justified merely because it is available.

## Hard invariants

- `FAILED CONTROL SURFACE != REQUIRED RECOVERY SURFACE`;
- `NO RECOVERY DEPENDENCY ON THE FAILED CONTROL SURFACE`;
- `CONTROL_SURFACE_FAILURE != WORKLOAD_FAILURE`;
- `GUI FAILURE != PROVIDER FAILURE`;
- `RESTARTED != RECOVERED`;
- `REBOOTED != FIXED`;
- `RECOVERY ACTION != ROOT CAUSE`;
- `RECOVERY ACTION != RECOVERY VALIDATED`;
- destructive escalation requires bounded authority;
- where delay does not materially worsen recovery, capture logs/state before destructive reset;
- skipped pre-reset evidence becomes explicit Recovery Debt rather than silently disappearing;
- after a control-changing recovery action, Deployment Identity must be re-established before runtime claims are accepted;
- Post-Deploy Reality validation must bind to the recovered runtime identity;
- recovery through an alternate surface does not permanently promote that surface or provider.

## Escalation ladder

Use the narrowest available action that can restore verified control:

1. **Escape the failed UI/surface** — switch to an independent CLI, API, SSH path, or another trusted operator surface.
2. **Observe before reset** — acquire logs, health, resource pressure, process/service state, and relevant timestamps when feasible.
3. **Service scope** — restart or reload only the affected service when sufficient.
4. **Process scope** — terminate and recreate the affected process when service-level recovery cannot restore control.
5. **Host scope** — reboot the host only when narrower recovery paths are unavailable or ineffective.
6. **External recovery scope** — recreate, redeploy, or fail over using an independent provider/control path when the host or provider boundary is no longer trustworthy or usable.
7. **Reality validation** — re-establish Deployment Identity and run the required probes before declaring recovery.

The ladder is an escalation order, not a requirement to execute every stage.

## Evidence-before-reset rule

A restart or reboot may erase volatile evidence. Therefore:

```text
IF evidence can be captured without materially worsening the outage
THEN capture it before destructive reset
ELSE restore first and record the missing evidence as Recovery Debt
```

Minimum useful evidence depends on the workload, but may include:

- control-surface failure observation;
- workload health observation independent of that surface;
- logs / journal references;
- memory, disk, CPU, or resource-pressure evidence;
- service/process state;
- action authority;
- executor/action timestamp;
- post-action Deployment Identity and probe evidence.

## Independence rule

An alternate recovery surface must not merely be another view backed by the same failed control path when that shared dependency is the suspected failure domain.

Examples of stronger independence include:

- browser console -> authenticated CLI/API from another host;
- application admin UI -> SSH + service manager;
- failed host-local control -> provider-level recovery plane;
- unusable primary provider control -> pre-authorized external failover path.

Independence is workload- and failure-domain-specific; labels alone do not prove it.

## Relationship to Emergency Recovery

Control Plane Escape is the **control-regain subpath** of bounded recovery.

It may be used before Emergency Failover when the primary workload can still be recovered in place. If the workload remains `FAILED` or `UNSAFE`, or the failure domain cannot be trusted, the existing Emergency Recovery / Failover Gate governs fallback eligibility and temporary recovery semantics.

This gate does not weaken:

- failover authority boundaries;
- fallback identity requirements;
- single-writer fencing requirements;
- recovery validation requirements;
- Recovery Debt;
- prohibition on automatic permanent promotion or failback.

## Externalization boundary

Keep external and replaceable:

- web consoles;
- CLIs and provider SDKs;
- SSH clients and remote shells;
- service managers;
- process supervisors;
- reboot/recreate mechanisms;
- deployment executors;
- provider failover controls.

Ultimate Loop owns only the decision/evidence rule:

> **If the normal control surface fails, do not make recovery depend on it. Escape to an independent control path, use the narrowest sufficient recovery action, and validate the recovered reality before calling it fixed.**
