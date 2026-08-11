# Reference Run 0005 — HTTP Surface Progress

Observed continuation timestamp: **2026-08-11 20:56 JST**

Parent run:

`REFERENCE_RUN_0005_DEPLOYMENT_IDENTITY.md`

This file records the next read-only runtime observations without rewriting the earlier evidence chain.

## Observation 0005-O — active listener identity

Observed timestamp: **2026-08-11 20:53 JST**

Read-only command:

`ss -ltnp 'sport = :8000'`

Observed result materially showed:

- state: `LISTEN`
- local address: `127.0.0.1:8000`
- process: `python3`
- PID: `86796`
- file descriptor: `6`

This binds the already-observed service MainPID `86796` to the configured loopback HTTP listener on port 8000.

Therefore:

`ACTIVE_NETWORK_SURFACE = OBSERVED`

`SYSTEMD_MAINPID_86796 = LISTENER_PID_86796`

## Observation 0005-P — bounded root-route response

Observed timestamp: **2026-08-11 20:54 JST**

Read-only command:

`curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/`

Observed result:

`200`

This proves that the bound listener accepted an HTTP request to `/` and returned HTTP status 200 at the observation point.

It does not prove semantic correctness of the returned page or exact loaded-source identity.

Therefore:

`ROOT_ROUTE_REACHABLE = OBSERVED`

`BOUNDED_HTTP_STATUS = 200`

## Observation 0005-Q — response media type and size

Observed timestamp: **2026-08-11 20:56 JST**

Read-only command:

`curl -sS -o /dev/null -w 'CODE=%{http_code} TYPE=%{content_type} SIZE=%{size_download}\n' http://127.0.0.1:8000/`

Observed result:

`CODE=200 TYPE=text/html; charset=utf-8 SIZE=15381`

This adds a bounded response-shape observation:

- HTTP status: `200`
- media type: `text/html; charset=utf-8`
- downloaded response size: `15381` bytes

The result supports that the runtime surface is serving an HTML root page, not merely accepting a TCP connection.

It still does not establish:

- exact semantic correctness of the HTML;
- exact source blob loaded at process startup;
- equivalence of the entire dirty worktree to Git HEAD;
- correctness of modified static assets not yet independently bound.

## Progress verdict

The evidence chain has now reached a real bounded runtime outcome:

`SYSTEMD UNIT`
→ `MAINPID 86796`
→ `ACTUAL UVICORN ARGV`
→ `web_console.app_v5:app`
→ `127.0.0.1:8000 LISTENER OWNED BY PID 86796`
→ `HTTP / = 200`
→ `text/html; charset=utf-8`
→ `15381-byte response`

Current classification:

`DEPLOYMENT_IDENTITY_RUNTIME_CHAIN = STRONGLY_OBSERVED_THROUGH_HTTP_SURFACE`

Remaining material limitation:

`LOADED_SOURCE_REVISION = NOT_PROVEN`

No service restart, source mutation, worktree cleanup, or production change was performed by these observations.
