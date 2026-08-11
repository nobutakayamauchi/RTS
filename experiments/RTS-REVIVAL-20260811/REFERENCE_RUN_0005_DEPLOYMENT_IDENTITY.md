# Thin RTS Reference Run 0005 — Persistent Service Deployment Identity

Start timestamp: **2026-08-11 19:21 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed at workload start: **32 minutes**

Status: `IN_PROGRESS / RUNTIME_EVIDENCE_REQUIRED`

## Why this workload exists

The initial Thin RTS candidate proved Git-backed reconstructability, destructive recovery, authority-boundary preservation, external evidence discovery, CI runtime evidence, and learning/promotion separation.

A material gap remains in the benchmark: a **long-lived service** where repository/code state must be distinguished from the process that is actually executing.

This workload attacks the historical RTS Deployment Identity responsibility directly.

## Candidate real workload

Candidate service from the current development environment:

`rts-video-flow-web.service`

The name alone is **not evidence** that the service exists, is active, points at the expected working directory, or executes the expected revision.

Until runtime evidence is observed, every runtime claim remains `UNKNOWN`.

## Required chain

Thin RTS must reconstruct and bind, where available:

`expected repository/source`
→ `systemd unit identity`
→ `unit file / WorkingDirectory`
→ `ExecStart / executable or module`
→ `active state + MainPID`
→ `actual process command/material`
→ `repository revision / deployed artifact identity`
→ `active route or externally observable surface`
→ `bounded outcome evidence`

No link may be inferred merely because the code exists in Git.

## First probe

The first probe is intentionally read-only and asks systemd for the service identity and execution configuration/status.

Expected evidence fields:

- `Id`
- `ActiveState`
- `SubState`
- `FragmentPath`
- `WorkingDirectory`
- `ExecStart`
- `MainPID`

## Attack rule

If any expected field is absent, inconsistent, stale, or points outside the expected source/deployment surface, record the mismatch rather than repairing the claim by assumption.

## Current verdict

`UNKNOWN — awaiting first runtime observation`
