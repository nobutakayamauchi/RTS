# Thin RTS Reference Run 0005 — Persistent Service Deployment Identity

Start timestamp: **2026-08-11 19:21 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed at workload start: **32 minutes**

Status: `IN_PROGRESS / ENTRY_MODULE_INDEX_BLOB_OBSERVED`

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

`100644 8d6e1b60f2dd530b801f40842526919d3e677f8 0 web_console/app_v5.py`

## Material finding after entry-module probe

The runtime argv names `web_console.app_v5:app`, and the corresponding source path `web_console/app_v5.py` is a tracked Git file with index blob identity:

`8d6e1b60f2dd530b801f40842526919d3e677f8`

This is useful but still **not sufficient** to claim that PID `86796` loaded exactly those bytes:

- `ls-files -s` identifies the index entry, not the already-loaded Python module in memory;
- the overall worktree is dirty;
- a file could theoretically change after process start even if later restored;
- Python import/load-time identity has not yet been captured by the application itself.

Therefore the correct state is:

`ENTRY_MODULE_INDEX_BLOB_OBSERVED != LOADED_PROCESS_SOURCE_PROVEN`

The next narrow check is to hash the current worktree bytes for `web_console/app_v5.py` and compare them with the Git index blob. If they match, current file bytes are bound to the index blob, while the separate load-time question remains explicit.

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
- entry-module index blob: `OBSERVED = 8d6e1b60f2dd530b801f40842526919d3e677f8`
- current entry-module worktree bytes: `NOT_YET_HASHED`
- source/module material loaded by process: `NOT_YET_PROVEN`
- repository revision bound to running process: `NOT_PROVEN`
- active route/outcome: `NOT_YET_OBSERVED`

## Next probe

Hash the current worktree bytes of `web_console/app_v5.py` with Git's object hashing and compare them with the observed index blob.

## Current verdict

`PARTIAL PASS — the tracked entry module has an observed Git index identity, but current bytes/load-time identity/route outcome remain open`
