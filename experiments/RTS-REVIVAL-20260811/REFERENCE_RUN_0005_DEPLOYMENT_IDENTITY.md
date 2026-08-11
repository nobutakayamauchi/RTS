# Thin RTS Reference Run 0005 — Persistent Service Deployment Identity

Start timestamp: **2026-08-11 19:21 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed at workload start: **32 minutes**

Status: `IN_PROGRESS / FIRST_RUNTIME_OBSERVATION_CONFIRMED`

## Why this workload exists

The initial Thin RTS candidate proved Git-backed reconstructability, destructive recovery, authority-boundary preservation, external evidence discovery, CI runtime evidence, and learning/promotion separation.

A material gap remains in the benchmark: a **long-lived service** where repository/code state must be distinguished from the process that is actually executing.

This workload attacks the historical RTS Deployment Identity responsibility directly.

## Candidate real workload

Candidate service from the current development environment:

`rts-video-flow-web.service`

The name alone is **not evidence** that the service exists, is active, points at the expected working directory, or executes the expected revision.

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

## Observation 0005-A — systemd identity/status

Observed timestamp: **2026-08-11 19:22 JST**

Read-only command used:

`systemctl show rts-video-flow-web.service -p Id -p ActiveState -p SubState -p FragmentPath -p WorkingDirectory -p ExecStart -p MainPID --no-pager`

Observed fields:

- `Id=rts-video-flow-web.service`
- `ActiveState=active`
- `SubState=running`
- `MainPID=86796`
- `FragmentPath=/etc/systemd/system/rts-video-flow-web.service`
- `WorkingDirectory=/home/ubuntu/rts-video-flow-segment-test`
- `ExecStart` executable path: `/home/ubuntu/rts-video-flow/venv/bin/python3`
- `ExecStart` command: `/home/ubuntu/rts-video-flow/venv/bin/python3 -m uvicorn web_console.app_v5:app --host 127.0.0.1 --port 8000`

## Material finding

The service is not merely present in code or configuration. systemd currently reports it as `active/running` with a concrete `MainPID=86796`.

A potentially material identity split is also visible and must not be normalized away by assumption:

- Python interpreter/venv path is under `/home/ubuntu/rts-video-flow/`
- systemd `WorkingDirectory` is `/home/ubuntu/rts-video-flow-segment-test`

This may be intentional or may represent mixed deployment surfaces. At this stage it is classified only as:

`OBSERVED_PATH_SPLIT / SIGNIFICANCE_UNKNOWN`

It is not yet evidence of a defect.

## Current evidence state

- systemd unit identity: `OBSERVED`
- unit file path: `OBSERVED`
- configured working directory: `OBSERVED`
- configured executable/module command: `OBSERVED`
- active/running state: `OBSERVED`
- MainPID: `OBSERVED`
- actual kernel process cwd: `NOT_YET_OBSERVED`
- actual executable behind MainPID: `NOT_YET_OBSERVED`
- source/module material loaded by process: `NOT_YET_OBSERVED`
- repository revision bound to running process: `NOT_YET_OBSERVED`
- active route/outcome: `NOT_YET_OBSERVED`

## Next probe

Confirm the **actual kernel process working directory** for PID `86796` rather than trusting configuration alone.

## Current verdict

`PARTIAL PASS — real runtime process exists; deployment/source identity not yet closed`
