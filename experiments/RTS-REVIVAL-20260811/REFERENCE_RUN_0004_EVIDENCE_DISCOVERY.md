# Thin RTS Reference Run 0004 — Evidence Discovery Without RTS Index Builder

Timestamp: **2026-08-11 19:03 JST**

## Legacy responsibility under test

Legacy implementation: `scripts/evidence_index_build.py`.

The script scans RTS-local evidence snapshot files and generates month-scoped JSON/Markdown indexes, including a computed `latest` item.

The responsibility is split into two separate questions:

1. **Can an operator find/reconstruct the relevant evidence?**
2. **Is a persistent RTS-owned generated monthly index itself required?**

## External replacement exercised

GitHub repository search was exercised directly against `nobutakayamauchi/RTS` for `ESC_` evidence.

The external search returned, among other results:

- `sessions/2026-02/evidence_index.md`
- `sessions/2026-02/evidence_index.json`
- `incidents/evidence_snapshots/ESC_20260224_034927_RTS_Sentinel_Analyze_run22335769087_a1/evidence.md`
- `incidents/evidence_snapshots/ESC_20260224_034805_RTS_Sentinel_Analyze_run22335738840_a1/evidence.md`
- `incidents/evidence_snapshots/ESC_20260224_035007_RTS_Sentinel_Analyze_run22335782661_a1/evidence.md`
- related session/index/analysis/incident artifacts.

This was performed without executing `scripts/evidence_index_build.py` or creating a new RTS-owned index runtime.

## Result

For the current reconstructability workload, **evidence discovery is externally reproducible** through GitHub repository search/history plus ordinary inspection.

Verdict: `PASS` for discovery/reconstruction.

## Important boundary

This experiment does **not** claim that GitHub search is a deterministic substitute for every possible historical `latest-by-custom-filename-sort` output produced by the legacy script.

That deterministic generated index is only rebuilt if a real workload demonstrates that:

- GitHub/native search/listing is insufficient;
- the exact generated ordering is materially required;
- the gap cannot be satisfied by an external query/tool;
- the benefit exceeds maintenance/state cost.

Until such a failure exists:

- evidence search/listing: `EXTERNALIZE`
- generated RTS-local monthly index: `DROP / ARCHIVE`
- legacy `evidence_index_build.py`: `ARCHIVE`
- new custom indexer: `NOT_AUTHORIZED`

This preserves the information-retrieval outcome without reviving generated state merely because the old implementation had it.
