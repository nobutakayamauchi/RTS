# Thin RTS Reference Run 0005 — Persistent Service Deployment Identity

Start timestamp: **2026-08-11 19:21 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed at workload start: **32 minutes**

Status: `IN_PROGRESS / SOURCE_MTIME_AND_SERVER_TIMEZONE_OBSERVED`

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

## Observation 0005-H — runtime worktree status

Observed timestamp: **2026-08-11 19:36 JST**

Read-only command used:

`git -C /home/ubuntu/rts-video-flow-segment-test status --short`

Observed result: **DIRTY WORKTREE**.

Tracked changes observed:

- `D output/.gitkeep`
- `D projects/vlog-template/README.md`
- `M web_console/static/new-vlog.html`
- `M web_console/static/timed-narration.html`

Untracked material observed includes:

- `docs/debug-safety/`
- `output`
- `output.before-service-20260804T040957Z/`
- `projects`
- `projects.before-service-20260804T040957Z/`
- `state/`
- `venv`
- several `web_console/app_v5.py.before-*` backups
- several `web_console/static/*.bak` files

This means HEAD alone cannot identify the complete current filesystem state.

## Observation 0005-I — tracked entry-module index identity

Observed timestamp: **2026-08-11 19:38 JST**

Read-only command used:

`git -C /home/ubuntu/rts-video-flow-segment-test ls-files -s web_console/app_v5.py`

Observed result:

`100644 b86de1b60f2dd530b801f40842526919d3e677f8 0 web_console/app_v5.py`

### Record correction

An earlier written reconstruction of Observation 0005-I transcribed the blob as beginning `8d6e...`. The screen-observed command output is `b86de1b60f2dd530b801f40842526919d3e677f8`; this document now preserves the observed value and records the correction instead of silently retaining the transcription error.

## Observation 0005-J — current worktree entry-module bytes

Observed timestamp: **2026-08-11 20:45 JST**

Read-only command used:

`git -C /home/ubuntu/rts-video-flow-segment-test hash-object web_console/app_v5.py`

Observed result:

`b86de1b60f2dd530b801f40842526919d3e677f8`

The current bytes of `web_console/app_v5.py` hash to the exact same Git object identity observed for the tracked index entry in Observation 0005-I.

Therefore, at the 20:45 JST observation point:

`WORKTREE_ENTRY_MODULE_BYTES_MATCH_INDEX = PROVEN_FOR_OBSERVED_FILE`

This does **not** prove that PID `86796` loaded those exact bytes when the process started. A long-lived Python process may have imported the module before later filesystem changes or restoration. The loaded-source/time binding therefore remains a separate unresolved question.

## Observation 0005-K — process start time

Observed timestamp: **2026-08-11 20:46 JST**

Read-only command used:

`ps -p 86796 -o lstart=`

Observed raw result:

`Thu Aug  6 13:04:20 2026`

The command output did not include an explicit timezone. The raw value is therefore preserved without silently assigning a zone.

This establishes a process-start clock reading for PID `86796` that can be compared with filesystem modification-time evidence, but it does not by itself prove which source bytes were imported at startup.

## Observation 0005-L — current entry-module filesystem modification time

Observed timestamp: **2026-08-11 20:48 JST**

Read-only command used:

`stat -c '%y %n' /home/ubuntu/rts-video-flow-segment-test/web_console/app_v5.py`

Observed result:

`2026-08-06 13:04:19.163352128 +0000 /home/ubuntu/rts-video-flow-segment-test/web_console/app_v5.py`

The filesystem mtime is explicitly UTC and precedes the raw `ps lstart` clock reading by approximately 0.84 seconds **if** that `ps` reading is interpreted in the server's local timezone.

This is temporal support only. File mtime can be changed independently and does not attest which source bytes Python imported.

## Observation 0005-M — server local timezone

Observed timestamp: **2026-08-11 20:50 JST**

Read-only command used:

`date '+%Z %z'`

Observed result:

`UTC +0000`

The server's current local timezone is UTC. This supports interpreting local-time-rendered process timestamps from ordinary system tools as UTC on this host, but the prior `ps lstart` output itself did not carry a zone token. A direct systemd start timestamp with an explicit zone is preferable before treating the 0.84-second ordering as final evidence.

## Material finding after source/time probes

The runtime argv names `web_console.app_v5:app`, and the corresponding source path `web_console/app_v5.py` is a tracked Git file whose current worktree bytes match the observed index blob identity:

`b86de1b60f2dd530b801f40842526919d3e677f8`

Observed timing evidence now includes:

- source-file mtime: `2026-08-06 13:04:19.163352128 +0000`;
- process `lstart` raw clock: `Thu Aug 6 13:04:20 2026`;
- server local timezone: `UTC +0000`.

This is consistent with the current entry-module file having been present before the process started. It materially strengthens the source-side Deployment Identity chain, but it still does **not** prove load-time bytes:

- mtime is mutable metadata rather than a cryptographic load-time measurement;
- the file could theoretically have changed and later been restored while retaining/manipulating timestamps;
- the overall worktree is dirty;
- modified static files may contribute runtime behavior independently of the Python entry module;
- Python import/load-time identity has not been captured by the application itself.

Therefore the correct state is:

`CURRENT_BYTES_MATCH_INDEX + SOURCE_MTIME_PRECEDES_PROCESS_START_SUPPORTED != LOADED_PROCESS_SOURCE_PROVEN`

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
- runtime worktree cleanliness: `DIRTY / OBSERVED`
- entry-module index blob: `OBSERVED = b86de1b60f2dd530b801f40842526919d3e677f8`
- current entry-module worktree bytes: `OBSERVED / MATCH_INDEX = b86de1b60f2dd530b801f40842526919d3e677f8`
- process start clock reading: `OBSERVED = Thu Aug 6 13:04:20 2026`
- current entry-module filesystem mtime: `OBSERVED = 2026-08-06 13:04:19.163352128 +0000`
- server local timezone: `OBSERVED = UTC +0000`
- temporal ordering: `SUPPORTED / DIRECT_EXPLICIT_ZONE_FOR_PROCESS_START_NOT_YET_OBSERVED`
- source/module material loaded by process: `NOT_YET_PROVEN`
- repository revision bound to running process: `NOT_PROVEN`
- active route/outcome: `NOT_YET_OBSERVED`

## Next probe

Observe the systemd-recorded main-process start timestamp with explicit timezone if available.

## Current verdict

`PARTIAL PASS — current tracked entry-module bytes match the observed Git index blob and source mtime is consistent with predating process start; exact load-time identity and route/outcome remain open`
