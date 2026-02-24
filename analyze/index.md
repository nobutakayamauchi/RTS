# RTS Sentinel Analyze

Generated: 2026-02-24 01:53 UTC

## Inputs

- memory/index.md (priority): [memory/index.md](memory/index.md)
- incidents/*.md: [incidents](incidents)
- logs/*.md: [logs](logs)

## Incident Trend

- Incidents observed (raw): 12
- Incidents observed (deduplicated): 2
- Duplicate pairs detected: 10
- Latest incident mtime: 2026-02-24 01:53 UTC

## Latest Incidents (deduplicated)

- RTS Incident Report — Execution Audit Template v3.1 ([incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md)) (mtime: 2026-02-24 01:53 UTC, sha:af1bf626)
- RTS INCIDENT REPORT ([incidents/INC_20260222_1545_Cursor_ContextLoss.md](incidents/INC_20260222_1545_Cursor_ContextLoss.md)) (mtime: 2026-02-24 01:53 UTC, sha:9f2a9e4b)

## Execution Stability

- Logs observed: 6
- Latest log mtime: 2026-02-24 01:53 UTC

## Latest Logs

- RTS Operational Workflow Log --- Smartphone Operator Method ([logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md)) (mtime: 2026-02-24 01:53 UTC, sha:1c613dac)
- RTS AI RADAR LOG ([logs/RADAR_LOG.md](logs/RADAR_LOG.md)) (mtime: 2026-02-24 01:53 UTC, sha:f71ef752)
- BLOCK_00000015 — RTS PUBLIC RELEASE & MONETIZATION ACTIVATION ([logs/BLOCK_00000015_RTS_PUBLIC_RELEASE.md](logs/BLOCK_00000015_RTS_PUBLIC_RELEASE.md)) (mtime: 2026-02-24 01:53 UTC, sha:8fb84074)
- BLOCK_00000016 — RTS Tester Recruitment Phase Initiated ([logs/BLOCK_00000016_RTS_TESTER_RECRUITMENT.md](logs/BLOCK_00000016_RTS_TESTER_RECRUITMENT.md)) (mtime: 2026-02-24 01:53 UTC, sha:8010baaf)
- BLOCK_00000017 ([logs/BLOCK_00000017_GENESIS_AUTONOMOUS.md](logs/BLOCK_00000017_GENESIS_AUTONOMOUS.md)) (mtime: 2026-02-24 01:53 UTC, sha:1ddad98d)
- BLOCK_00000018 ([logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md](logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md)) (mtime: 2026-02-24 01:53 UTC, sha:c7ce9cb2)

## Observed Risk Patterns

Evidence-first keyword scan across incidents + logs. No inference beyond evidence hits.

### Risk Topic Ranking

- error: 8
- failure: 8
- server error: 5
- session reset: 4
- github mobile: 3
- auth: 1
- context loss: 1
- timeout: 1
- workflow interruption: 1
- deleted workflow: 0
- token: 0

### Evidence Hits (top per topic)

#### auth
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)

#### context loss
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

#### deleted workflow
- none

#### error
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)
- [logs/RADAR_LOG.md](logs/RADAR_LOG.md) (logs/RADAR_LOG.md#sha:f71ef752)

#### failure
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)
- [logs/RADAR_LOG.md](logs/RADAR_LOG.md) (logs/RADAR_LOG.md#sha:f71ef752)
- [logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md](logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md) (logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md#sha:c7ce9cb2)
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

#### github mobile
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)

#### server error
- [logs/RADAR_LOG.md](logs/RADAR_LOG.md) (logs/RADAR_LOG.md#sha:f71ef752)

#### session reset
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)
- [logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md](logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md) (logs/BLOCK_00000018_AUTORESET_ENGINE_ONLINE.md#sha:c7ce9cb2)
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

#### timeout
- [logs/RADAR_LOG.md](logs/RADAR_LOG.md) (logs/RADAR_LOG.md#sha:f71ef752)

#### token
- none

#### workflow interruption
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

---

## Sentinel Phase-3

### Failure Cascade Detection

Co-occurrence-based detection (same doc contains multiple risk topics). Evidence-only.

#### Recent Cascade Hits (last 7 days)

##### cascade: error + workflow interruption
- none

##### cascade: server error + error
- [logs/RADAR_LOG.md](logs/RADAR_LOG.md) (logs/RADAR_LOG.md#sha:f71ef752)

##### cascade: session reset + context loss
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

##### cascade: error + session reset
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)

##### cascade: workflow interruption + session reset
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

#### Cascade Hits (all time, top)

##### cascade: error + workflow interruption
- none

##### cascade: server error + error
- [logs/RADAR_LOG.md](logs/RADAR_LOG.md) (logs/RADAR_LOG.md#sha:f71ef752)

##### cascade: session reset + context loss
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

##### cascade: error + session reset
- [logs/EXECUTION_LOG.md](logs/EXECUTION_LOG.md) (logs/EXECUTION_LOG.md#sha:1c613dac)

##### cascade: workflow interruption + session reset
- [incidents/INCIDENT_RULES.md](incidents/INCIDENT_RULES.md) (incidents/INCIDENT_RULES.md#sha:af1bf626)

### Drift Detection

- baseline: not found (previous analyze/index.md missing or unparsable)

- delta: unavailable

### Self Awareness Ledger

- This section records measurable generation conditions (no inference).

- generated_utc: 2026-02-24T01:53:10.888854+00:00
- inputs: incidents_raw=12, incidents_dedup=2, logs=6
- dedup: duplicate_pairs=10
- drift_baseline_available: false

---

## Provenance

- This report is generated by `scripts/analyze.py`.
- Sources are not modified. Only parsed.
- Evidence links point to repository paths.
