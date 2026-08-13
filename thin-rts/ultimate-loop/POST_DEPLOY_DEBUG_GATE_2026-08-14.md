# ULTIMATE LOOP — Post-Deploy Debug / Reality Gate

Date: **2026-08-14**

Status: `CANONICAL / ACTIVE`

Canonical parent: `thin-rts/ULTIMATE_LOOP_METHOD.md`

## Purpose

A published or deployed program has not earned STABLE merely because build/tests passed or deployment completed.

Hard rule:

`DEPLOYED != OBSERVED_CORRECT`

The promoted implementation must be checked against runtime reality on the actual deployed identity and must retain a reproducible failure/retest path.

## Gate

```text
DEPLOY / PUBLISH
-> DEPLOYMENT IDENTITY
-> BOUNDED RUNTIME PROBES
-> EXPECTED vs OBSERVED
-> EVIDENCE BINDING
-> FAILURE CORRELATION
-> ROOT-CAUSE HYPOTHESIS GATE
-> PATCH / CHANGE BY AUTHORIZED EXTERNAL IMPLEMENTER
-> DEPLOYMENT RE-IDENTITY
-> EXACT FAILED-PROBE REPLAY
-> REGRESSION
-> FIX_VALIDATED / RETURN TO ANALYSIS
```

A clean first deployment that satisfies all required runtime probes may enter `DEPLOYMENT_VALIDATED` and become STABLE-eligible without fabricating a repair cycle.

## Hard invariants

- `SELF_DECLARED_IDENTITY != DEPLOYMENT_IDENTITY`;
- `CODE EXISTENCE != RUNTIME EVIDENCE`;
- `RUNTIME-TO-CODE MAPPING != ROOT CAUSE`;
- root-cause promotion requires support, reproduction, falsification and no unresolved counterevidence;
- `PATCH APPLIED != FIX VALIDATED`;
- post-patch Deployment Identity must be re-established;
- every originally failed required probe must be replayed against the new identity;
- probe identity includes the probe-definition fingerprint, not only a label/id;
- regression identity includes the regression-suite fingerprint;
- probe/replay/regression evidence must bind to the verified deployment observation fingerprint, expectation fingerprint and observation session;
- regression PASS requires evidence, not a label only;
- blocked probes remain blocked/unknown and cannot be silently counted as PASS.

## Deployment Identity integration

The generic harness reuses the repository attested Deployment Identity path rather than maintaining a parallel `ESTABLISHED` flag.

Runtime validation requires the existing material proof plus runtime-classification authorization, signed attestation quorum, and independent collector provenance. A self-declared dictionary that merely claims to be established is not accepted.

## Externalization boundary

ULTIMATE LOOP does not need to own browser automation, telemetry, tracing, crash collection, log storage, HTTP clients, profilers or AI patch generation.

Those remain replaceable adapters such as browser test tools, HTTP/CLI probes, logs/traces/metrics systems, error trackers, profilers and human/AI analysis.

The owned responsibility is a thin adapter-neutral evidence contract that binds:

- deployed identity;
- probe identity, definition fingerprint and expected/observed result;
- evidence references;
- root-cause disposition;
- patch identity;
- post-patch re-identity;
- exact failed-probe replay;
- regression-suite identity and evidence;
- final validation state.

## Authority boundary

The debug gate may classify evidence and refuse unsupported closure. It does not create authority to deploy, patch, restart, rollback, publish, access secrets or mutate external systems.

## Relation to STABLE

Workload policy decides which probes are required before STABLE. A purely offline/library artifact may have no live deployment probe, while a web/service/UI workload may require runtime probes after each material deployment.

A material runtime failure reopens BUILD/analysis or the appropriate repair frame. Repeated deployment failure may also trigger METEOR/DARWIN against the current implementation architecture.
