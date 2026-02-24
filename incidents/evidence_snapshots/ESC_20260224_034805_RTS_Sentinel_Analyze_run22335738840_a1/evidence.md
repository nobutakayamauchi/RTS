# RTS Evidence Pack (Escalation)

## Evidence (Facts Only)
- repo: nobutakayamauchi/RTS
- workflow: RTS Sentinel Analyze
- branch: main
- actor: nobutakayamauchi
- run_id: 22335738840
- run_attempt: 1
- run_url: https://github.com/nobutakayamauchi/RTS/actions/runs/22335738840
- conclusion: success
- created_at: 2026-02-24T03:47:47Z
- updated_at: 2026-02-24T03:47:57Z
- generated_at_utc: 2026-02-24T03:48:06+00:00
- generated_at_jst: 2026-02-24T12:48:06+09:00

## Evidence Level
- evidence_level: L2

## Escalation Rule (Counters)
- window_n: 12
- fail_threshold_last_n: 1
- burst_minutes: 30
- burst_fail_threshold: 2

## Stats (Counters)
- fail_count_last_n: 3
- burst_fail: 0
- last_n_conclusions: ['success', 'success', 'success', 'success', 'success', 'success', 'success', 'failure', 'failure', 'success', 'failure', 'success']

## Snapshot Bundle (Frozen)
- bundle_dir: incidents/evidence_snapshots/ESC_20260224_034805_RTS_Sentinel_Analyze_run22335738840_a1/
- manifest: incidents/evidence_snapshots/ESC_20260224_034805_RTS_Sentinel_Analyze_run22335738840_a1/manifest.json
- bundle_hash_sha256: 2c3395fb8acf749b82b96d2a8302cb4fb7624f6780d53c69d9ab99c7f8d1570b

## Inference Separation
- This file contains **evidence only** (facts/counters/snapshots).
- Analysis and conclusion should live in separate files (generated as stubs below).

