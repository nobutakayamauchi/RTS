# Thin RTS Reference Run 0005 — Persistent Service Deployment Identity

Start timestamp: **2026-08-11 19:21 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed at workload start: **32 minutes**

Status: `IN_PROGRESS / FULL_RUNTIME_ARGV_CONFIRMED`

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

## Observation 0005-B — actual kernel process cwd

Observed timestamp: **2026-08-11 19:23 JST**

Read-only command used:

`readlink -f /proc/86796/cwd`

Observed result:

`/home/ubuntu/rts-video-flow-segment-test`

## Material finding after cwd probe

The actual running kernel process cwd matches the systemd-configured WorkingDirectory exactly.

Therefore:

- configured WorkingDirectory: `CONFIRMED_BY_RUNTIME`
- actual process cwd: `OBSERVED`
- the earlier path split remains real, because the interpreter/venv path is still under `/home/ubuntu/rts-video-flow/` while the running process cwd is under `/home/ubuntu/rts-video-flow-segment-test`
- the split is still `SIGNIFICANCE_UNKNOWN`; no defect claim is authorized yet

## Observation 0005-C — client reconnect / PID continuity

Observed timestamp: **2026-08-11 19:28 JST**

The mobile SSH client disconnected/restarted. After reconnect, the service PID was re-queried instead of assuming continuity.

Read-only command used:

`systemctl show rts-video-flow-web.service -p MainPID --value`

Observed result:

`86796`

## Material finding after reconnect

The SSH client failure did not coincide with a service PID change. The same `MainPID=86796` was observed again after reconnect.

This proves only PID continuity across these observations. It does not prove that executable/module/source/revision identity has remained unchanged; those remain separate claims.

## Observation 0005-D — actual executable behind MainPID

Observed timestamp: **2026-08-11 19:30 JST**

Read-only command used:

`readlink -f /proc/86796/exe`

Observed result:

`/usr/bin/python3.12`

## Material finding after executable probe

The kernel reports the process executable as the system Python binary `/usr/bin/python3.12`.

This does **not** by itself prove that the configured virtual environment is bypassed. A virtual-environment Python entry commonly resolves to the underlying interpreter binary, while environment-specific import paths and package state remain separate runtime facts.

## Observation 0005-E — actual process command line

Observed timestamp: **2026-08-11 19:31 JST**

Read-only command used:

`ps -p 86796 -o args=`

Observed visible result:

`/home/ubuntu/rts-video-flow/venv/bin/python3 -m uvicorn web_console.app_v5:app`

## Material finding after command-line probe

The running process command line confirms that PID `86796` was launched through the configured virtual-environment Python path and is invoking:

`-m uvicorn web_console.app_v5:app`

The visible `ps` output may be terminal-width truncated, so absence of the configured host/port suffix in that view was not treated as a mismatch.

## Observation 0005-F — full null-delimited runtime argv

Observed timestamp: **2026-08-11 19:33 JST**

Read-only command used:

`xargs -0 -a /proc/86796/cmdline`

Observed result:

`/home/ubuntu/rts-video-flow/venv/bin/python3 -m uvicorn web_console.app_v5:app --host 127.0.0.1 --port 8000`

## Material finding after full argv probe

The actual process argv now matches the systemd-configured invocation in all material arguments observed:

- launcher: `/home/ubuntu/rts-video-flow/venv/bin/python3`
- module runner: `-m uvicorn`
- application import target: `web_console.app_v5:app`
- bind host: `127.0.0.1`
- port: `8000`

This closes the earlier terminal-width ambiguity. The configured execution command and the actual process argv are consistent.

The remaining material gap is no longer the command itself. It is the identity of the source tree/revision from which `web_console.app_v5` is being resolved and whether the running process can be bounded to that repository state rather than merely to a directory name.

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
- source tree repository identity: `NOT_YET_OBSERVED`
- repository revision bound to running process: `NOT_YET_OBSERVED`
- active route/outcome: `NOT_YET_OBSERVED`

## Next probe

Identify the Git revision currently checked out in the runtime working directory. This is only a **candidate deployed revision** until later evidence binds it to the already-running process.

## Current verdict

`PARTIAL PASS — unit, PID, cwd, executable, launcher, module and full argv are runtime-confirmed; source/revision/route identity not yet closed`
