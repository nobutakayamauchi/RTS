# Reference Run 0005 — Live Route Inventory

Observed timestamp: **2026-08-11 21:02 JST**

Parent evidence:

- `REFERENCE_RUN_0005_DEPLOYMENT_IDENTITY.md`
- `REFERENCE_RUN_0005_HTTP_SURFACE_PROGRESS_2056.md`

Read-only command used:

`python3 -c "import json,urllib.request as u; d=json.load(u.urlopen('http://127.0.0.1:8000/openapi.json')); [print(','.join(sorted(v.keys())).upper(),k) for k,v in d['paths'].items()]"`

Observed live route inventory:

- `GET /`
- `GET /api/source/{project_name}/{item_id}`
- `GET /api/output/{project_name}`
- `POST /api/output/render`
- `POST /api/compile`
- `GET /api/output-file/{project_name}/{filename}`
- `DELETE /api/output/cut`
- `DELETE /api/output/all`
- `GET /api/trash/{project_name}`
- `POST /api/trash/restore`
- `POST /api/trash/restore-all`
- `DELETE /api/trash/purge`
- `DELETE /api/trash/purge-all`
- `DELETE,POST /api/material`
- `DELETE,POST /api/narration-segment`
- `GET /api/media-info/{project_name}/{item_id}`
- `POST /api/script-suggestion`
- `POST /api/post-narration`
- `GET /api/health`
- `GET /api/project/{project_name}`
- `POST /api/narration`
- `POST /api/audio-mode`
- `POST /api/reorder`
- `GET /api/download/{project_name}`
- `POST /api/project`
- `GET /api/timed-narration/{project_name}/{item_id}`
- `GET /api/timed-narration-file/{project_name}/{item_id}`
- `POST /api/timed-narration`
- `POST /api/cloud-render/prepare`
- `POST /api/cloud-render/prepare-project`
- `POST /api/cloud-render/approve`
- `POST /api/cloud-render/dispatch`
- `GET /api/cloud-render/status/{request_id}`

This independently confirms the previously reported `PATHS=33` count and provides method-level route shape from the live OpenAPI surface.

## Safety classification for next bounded probe

The inventory includes materially destructive or state-changing methods (`POST`, `DELETE`). They are **not** selected for the next runtime check without explicit necessity and authority.

`GET /api/health` is the narrowest project-specific read-only candidate visible in the live route graph because it has no path parameters and is conventionally intended to report service health.

Selection rule:

`READ_ONLY / NO_PATH_ARGUMENT / PROJECT_SPECIFIC → /api/health`

## Observation 0005-T — project-specific health outcome

Observed timestamp: **2026-08-11 21:03 JST**

Read-only command:

`curl -sS http://127.0.0.1:8000/api/health`

Observed result:

`{"status":"ok"}`

This proves that the live project-specific `/api/health` route executed and returned an application-level health payload at the observation point.

Therefore:

`PROJECT_SPECIFIC_READ_ONLY_ROUTE = OBSERVED`

`HEALTH_ROUTE_RESPONSE = {"status":"ok"}`

This is a bounded functional outcome. It does not prove semantic correctness of the full application, exact loaded-source revision, or equivalence of the dirty worktree to Git HEAD.

## Current progress state

`OPENAPI_ROUTE_GRAPH = OBSERVED / 33 PATHS`

`METHOD_SHAPE = OBSERVED`

`DESTRUCTIVE_ROUTES = IDENTIFIED / NOT_INVOKED`

`PROJECT_SPECIFIC_HEALTH_ROUTE = OBSERVED / {"status":"ok"}`

`BOUND_FUNCTIONAL_OUTCOME = OBSERVED`

The remaining material identity limitation remains:

`LOADED_SOURCE_REVISION = NOT_PROVEN`

A useful final continuity check is to confirm that the service MainPID is still `86796` after the HTTP/OpenAPI/health observations, so the beginning and end of the run remain bound to the same process identity.

No service restart, worktree mutation, project mutation, render, delete, purge, restore, cloud dispatch, or other state-changing endpoint was invoked while creating this inventory or health observation.
