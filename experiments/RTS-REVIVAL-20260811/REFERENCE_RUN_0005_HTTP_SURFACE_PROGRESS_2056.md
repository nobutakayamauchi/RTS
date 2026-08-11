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

## Observation 0005-R — OpenAPI application surface

Observed timestamp: **2026-08-11 20:58 JST**

Read-only command:

`curl -sS -o /dev/null -w 'CODE=%{http_code} TYPE=%{content_type} SIZE=%{size_download}\n' http://127.0.0.1:8000/openapi.json`

Observed result:

`CODE=200 TYPE=application/json SIZE=31608`

This materially strengthens the runtime-outcome observation because the process is not only returning a root HTML document; the application also exposes a live OpenAPI document from the same bound runtime surface.

Therefore:

`OPENAPI_ROUTE_REACHABLE = OBSERVED`

`OPENAPI_HTTP_STATUS = 200`

`OPENAPI_MEDIA_TYPE = application/json`

`OPENAPI_RESPONSE_SIZE = 31608 bytes`

This supports that an application route graph is live behind the observed uvicorn process.

It still does not prove the exact source blob loaded at process startup, nor does it establish semantic correctness of each documented route.

## Progress verdict

The evidence chain has now reached both a human-facing root response and a framework/application metadata surface:

`SYSTEMD UNIT`
→ `MAINPID 86796`
→ `ACTUAL UVICORN ARGV`
→ `web_console.app_v5:app`
→ `127.0.0.1:8000 LISTENER OWNED BY PID 86796`
→ `HTTP / = 200`
→ `text/html; charset=utf-8`
→ `15381-byte root response`
→ `HTTP /openapi.json = 200`
→ `application/json`
→ `31608-byte OpenAPI response`

Current classification:

`DEPLOYMENT_IDENTITY_RUNTIME_CHAIN = STRONGLY_OBSERVED_THROUGH_APPLICATION_SURFACE`

Remaining material limitation:

`LOADED_SOURCE_REVISION = NOT_PROVEN`

No service restart, source mutation, worktree cleanup, or production change was performed by these observations.
