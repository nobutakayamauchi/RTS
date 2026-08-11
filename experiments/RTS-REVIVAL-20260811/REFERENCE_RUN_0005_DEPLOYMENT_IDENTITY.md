# Thin RTS Reference Run 0005 — Persistent Service Deployment Identity

Start timestamp: **2026-08-11 19:21 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed at workload start: **32 minutes**

Status: `IN_PROGRESS / RUNTIME_WORKTREE_HEAD_OBSERVED`

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

## Observation 0005-B — actual kernel process cwd

Observed timestamp: **2026-08-11 19:23 JST**

Read-only command used:

`readlink -f /proc/86796/cwd`

Observed result:

`/home/ubuntu/rts-video-flow-segment-test`

The actual running kernel process cwd matches the systemd-configured WorkingDirectory exactly.

## Observation 0005-C — client reconnect / PID continuity

Observed timestamp: **2026-08-11 19:28 JST**

Read-only command used:

`systemctl show rts-video-flow-web.service -p MainPID --value`

Observed result:

`86796`

The SSH client reconnect did not coincide with a service PID change. This proves PID continuity across these observations only.

## Observation 0005-D — actual executable behind MainPID

Observed timestamp: **2026-08-11 19:30 JST**

Read-only command used:

`readlink -f /proc/86796/exe`

Observed result:

`/usr/bin/python3.12`

The kernel executable alone does not prove the configured virtual environment is bypassed.

## Observation 0005-E — actual process command line

Observed timestamp: **2026-08-11 19:31 JST**

Read-only command used:

`ps -p 86796 -o args=`

Observed visible result:

`/home/ubuntu/rts-video-flow/venv/bin/python3 -m uvicorn web_console.app_v5:app`

## Observation 0005-F — full null-delimited runtime argv

Observed timestamp: **2026-08-11 19:33 JST**

Read-only command used:

`xargs -0 -a /proc/86796/cmdline`

Observed result:

`/home/ubuntu/rts-video-flow/venv/bin/python3 -m uvicorn web_console.app_v5:app --host 127.0.0.1 --port 8000`

The actual process argv matches the systemd-configured invocation in all material arguments observed.

## Observation 0005-G — current Git HEAD of runtime working directory

Observed timestamp: **2026-08-11 19:34 JST**

Read-only command used:

`git -C /home/ubuntu/rts-video-flow-segment-test rev-parse HEAD`

Observed result:

`216bbc511c306754b5e69f6b58fae021691074fc`

## Material finding after HEAD probe

The directory that is both the configured WorkingDirectory and the runtime-observed cwd is a Git worktree currently pointing at commit:

`216bbc511c306754b5e69f6b58fae021691074fc`

This is a **candidate source revision**, not yet a proven deployed revision for PID `86796`.

Two material uncertainties remain before the source identity can be promoted:

1. the worktree may contain tracked or untracked changes relative to that HEAD;
2. the Python process may have imported source before later filesystem changes, so current worktree state is not automatically equivalent to loaded process state.

Therefore:

`CURRENT_WORKTREE_HEAD_OBSERVED != RUNNING_PROCESS_REVISION_PROVEN`

## Current evidence state

- systemd unit identity: `OBSERVED`
- unit file path: `OBSERVED`
- configured working directory: `OBSERVED`
- actual kernel process cwd: `OBSERVED / MATCHES_CONFIG`
- configured executable/module command: `OBSERVED`
- active/running state: `OBSERVED`
- MainPID: `OBSERVED / SAME BEFORE_AND_AFTER_CLIENT_RECONNECT`
- actual executable behind MainPID: `OBSERVED = /usr/bin/python3.12`
- actual process launcher path: `OBSERVED = /home/ubuntu/rts-video-flow/venv/bin/python3`
- actual application module invocation: `OBSERVED = web_console.app_v5:app`
- full process argv: `OBSERVED / MATCHES_SYSTEMD_CONFIG`
- runtime worktree HEAD: `OBSERVED = 216bbc511c306754b5e69f6b58fae021691074fc`
- runtime worktree cleanliness: `NOT_YET_OBSERVED`
- source/module material loaded by process: `NOT_YET_OBSERVED`
- repository revision bound to running process: `NOT_YET_PROVEN`
- active route/outcome: `NOT_YET_OBSERVED`

## Next probe

Check whether the runtime working tree has tracked or untracked differences from the observed HEAD. A dirty worktree would make `HEAD` alone insufficient even as a candidate source snapshot.

## Current verdict

`PARTIAL PASS — runtime worktree HEAD observed; worktree cleanliness, loaded-source binding, and route/outcome identity remain open`
