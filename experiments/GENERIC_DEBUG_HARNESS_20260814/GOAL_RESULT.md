# /goal — Generic Debug Harness v0

Date: **2026-08-14**

Status: `MONOLITHIC_DEBUG_PLATFORM_KILLED / THIN_EVIDENCE_HARNESS_SURVIVES`

## Verdict

Do **not** build a browser-testing, telemetry, error-monitoring, profiling, AI-patching or self-healing platform inside RTS. Those execution/collection responsibilities remain external and replaceable.

A thin adapter-neutral evidence harness survives because ULTIMATE LOOP still needs one shared fail-closed contract after deployment:

`DEPLOYMENT IDENTITY -> PROBES -> FAILURE EVIDENCE -> EXTERNAL ANALYSIS/PATCH -> RE-IDENTITY -> FAILED-PROBE REPLAY -> REGRESSION -> FIX_VALIDATED`

The existing Deployment Identity boundary is reused. Old PR #299 is not revived wholesale; only its surviving invariants are inherited.

Hard rules:

- `CODE EXISTENCE != RUNTIME EVIDENCE`
- `RUNTIME-TO-CODE MAPPING != ROOT CAUSE`
- `PATCH APPLIED != FIX VALIDATED`
- blocked/missing runtime evidence fails closed;
- a patch must establish post-patch deployment identity;
- every previously failed required probe must replay PASS with evidence;
- regression must PASS with evidence.

The first occupant is `debug_harness.py`: a small pure evaluator with no network, process execution, browser, telemetry store, database, credentials, patching, deployment or promotion authority.

`BUILD THIN EVIDENCE HARNESS / KILL GENERIC DEBUG PLATFORM`.
