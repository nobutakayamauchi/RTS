# GitHub portfolio timing backfill pilot

Timestamp: **2026-08-11 23:22 JST**

Status: `DISCOVERED / OPTIONAL WEAK CALIBRATION / NOT PROMOTED`

The connected GitHub surface exposed **22 owned repositories** at discovery time: **18 public and 4 private**. Repository names for private repositories are intentionally not copied into this public RTS branch.

This is enough historical surface to justify testing portfolio-wide calibration, but not enough to justify trusting raw commit gaps as work duration.

## Role in Human Return ETA

Portfolio backfill is a **missing-data prior**, not the primary clock.

Priority remains:

1. semantically bound run start -> first human hinge (`STRONG`);
2. materially credible but incomplete timing (`MEDIUM`);
3. GitHub portfolio commit-session approximation (`WEAK`);
4. chunk/load prior;
5. cold-start fallback.

The purpose of the portfolio corpus is to improve low-sample and cold-start behavior. If holdout tests show no material ETA improvement, the portfolio backfill should be dropped.

## Privacy boundary

The prototype backfill:

- reads repository/commit metadata from GitHub through the existing provider API;
- emits only a deterministic repository hash key, bounded SHA prefixes, and timestamps;
- does **not** emit repository names or commit messages into the generated history;
- treats every inferred commit session as `WEAK` evidence;
- does not fabricate a duration from a single commit;
- splits sessions across configurable idle gaps.

Private runtime history must not be committed to this public repository.

## Promotion test

Portfolio history survives only if it improves return-time prediction on held-out real runs without materially increasing false precision or operator burden.

Required comparison:

`TIMESTAMP_ONLY` vs `CHUNK_ONLY` vs `PORTFOLIO_PRIOR` vs `HYBRID`

Measure at minimum:

- absolute return-time error;
- early-return waste (human came back too soon);
- late-return waste (machine needed the human earlier);
- false-confidence rate;
- behavior on new task classes;
- behavior when Git history contains long idle gaps or unrelated commits.

`MORE HISTORY != BETTER EVIDENCE.`

The backfill exists only to reduce uncertainty where stronger evidence is missing.
