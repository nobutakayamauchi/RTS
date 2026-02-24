# RTS Evidence Pack (Escalation)

## Evidence (Facts Only)
- repo: nobutakayamauchi/RTS
- workflow: RTS Sentinel Analyze
- branch: main
- actor: nobutakayamauchi
- run_id: 22335782661
- run_attempt: 1
- run_url: https://github.com/nobutakayamauchi/RTS/actions/runs/22335782661
- conclusion: success
- created_at: 2026-02-24T03:49:48Z
- updated_at: 2026-02-24T03:49:56Z
- generated_at_utc: 2026-02-24T03:50:08+00:00
- generated_at_jst: 2026-02-24T12:50:08+09:00

## Evidence Level
- evidence_level: L2

## Escalation Rule (Counters)
- window_n: 12
- fail_threshold_last_n: 1
- burst_minutes: 30
- burst_fail_threshold: 2

## Stats (Counters)
- fail_count_last_n: 2
- burst_fail: 0
- last_n_conclusions: ['success', 'success', 'success', 'success', 'success', 'success', 'success', 'success', 'success', 'failure', 'failure', 'success']

## Snapshot Bundle (Frozen)
- bundle_dir: incidents/evidence_snapshots/ESC_20260224_035007_RTS_Sentinel_Analyze_run22335782661_a1/
- manifest: incidents/evidence_snapshots/ESC_20260224_035007_RTS_Sentinel_Analyze_run22335782661_a1/manifest.json
- bundle_hash_sha256: 733c0d7349b362abafad4471c160f4338db2637136d42375ae2de92807de8906

## Inference Separation
- This file contains **evidence only** (facts/counters/snapshots).
- Analysis and conclusion should live in separate files (generated as stubs below).

