# RTS Revival Time Attack — Candidate Verdict Addendum

Timestamp: **2026-08-11 21:05 JST**

This addendum does **not** rewrite the measured 19:04 candidate verdict or its **15-minute** elapsed result. It records materially new evidence obtained after that checkpoint.

## Reference Run 0005 — persistent service Deployment Identity

Result:

`REFERENCE_RUN_0005_DEPLOYMENT_IDENTITY = PASS_FOR_BOUNDED_RUNTIME_RECONSTRUCTION_WITH_EXPLICIT_UNKNOWN`

The previously open persistent-service Deployment Identity workload was exercised against the live `rts-video-flow-web.service` without restart, cleanup, source mutation, or destructive application calls.

The observed chain reached:

`systemd unit`
→ configured and actual working directory
→ configured and actual uvicorn argv
→ stable MainPID `86796`
→ current Git HEAD plus explicit dirty-worktree state
→ tracked entry-module blob
→ current entry-module bytes matching that blob
→ source mtime preceding explicit UTC service start
→ PID `86796` owning `127.0.0.1:8000`
→ root HTTP `200`
→ live OpenAPI `200`
→ application identity `RTS Vlog Composition Console v3`, version `0.1.0`, 33 paths
→ project-specific `GET /api/health` returning `{"status":"ok"}`
→ same MainPID `86796` at closure.

This closes the original candidate-verdict item stating that a persistent production-service Deployment Identity scenario had not yet been exercised.

## Important surviving UNKNOWN

The run intentionally does **not** claim exact load-time source attestation.

`LOADED_SOURCE_REVISION = NOT_PROVEN`

The running Python process did not emit a load-time digest. Current file bytes, Git identity, filesystem mtime, and service start ordering materially support the reconstruction chain but cannot cryptographically prove which exact source bytes were imported by the already-running process.

Therefore:

`CODE_EXISTS != RUNTIME`

`CURRENT_HEAD != COMPLETE_RUNTIME_REALITY`

remain preserved invariants rather than being papered over by a false PASS.

## Updated candidate interpretation

The external-first Thin RTS candidate has now survived a materially broader real workload than at the 19:04 checkpoint:

- Git-backed destructive recovery;
- authority-boundary corruption and restoration;
- external evidence discovery;
- external CI runtime evidence;
- learning/review/promotion separation;
- privacy-minimized public evidence records;
- persistent live-service Deployment Identity through a bounded project-specific runtime outcome.

No custom RTS Runtime, Controller, Governance Kernel, daemon, queue, database, scheduler, vector store, custom CI engine, or promotion engine became necessary for these exercised responsibilities.

`ADDITIONAL_SOFTWARE_SERVICE_COST = JPY_0_TARGET_STILL_MET_FOR_EXERCISED_WORKLOADS`

## New hard completion gates remain open

The broader revived RTS is **not complete** merely because Run 0005 passed.

The later completion requirements remain separate hard gates, including:

- dispute-ready legal evidence engineering and independent verification;
- encrypted provider-neutral cloud custody and fresh-environment recovery;
- automatic evidence triage;
- event evidence coverage and missing-evidence remediation;
- case-pattern warning before evidence is lost;
- current law / benefit / deadline / official-procedure watching and document readiness.

Current top-level state:

`THIN_RTS_CANDIDATE_FOR_EXERCISED_REFERENCE_WORKLOADS = PASS`

`REVIVED_RTS_FULL_COMPLETION = NOT_COMPLETE`

`PROMOTION_TO_MAIN = NOT_AUTHORIZED / DRAFT_PR_ONLY`

## Speed statement remains unchanged

The measured first candidate checkpoint remains **15 minutes from the 18:49 JST reset origin**.

Later evidence and new completion requirements extend the experiment but do not retroactively alter that measurement.

The remembered `5400x` figure remains **UNPROVEN** because no scope-equivalent surviving evidence establishes such a multiplier.
