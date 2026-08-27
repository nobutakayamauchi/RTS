# FRZ-000011 — Selective Recall + Memory Lifecycle v1 — METEOR Result

Date: **2026-08-27**

Status: `REPOSITORY_METEOR_SURVIVOR / LOCAL_VERIFICATION_BOUNDARY`

## Frozen responsibility

Reuse RTS historical memory without rereading the whole corpus while preventing stale, superseded, quarantined, raw, or irrelevant memory from silently becoming current execution authority.

This child owns only a deterministic, repository-local, non-authorizing selective-recall/lifecycle layer over the existing RTS memory/index assets. It does not own a new database, provider runtime, crawler, deployment engine, autonomous promotion engine, or external action surface.

## Baseline candidate and retained death

Initial candidate destructive run:

- commit: `e632e4e20d27e6bf12fb3177494f084a1a4c2c33`
- GitHub Actions run: `33047223630`
- result: **FAILED** on the frozen DA workload.

Retained death classes:

1. irrelevant event/scope records could incur source-body freshness hashing before cheap metadata rejection;
2. excluded memory identities were emitted as an unbounded list, allowing diagnostics to grow with corpus size;
3. stale irrelevant memory had to remain metadata-ineligible without paying freshness I/O.

`SELECTIVE RECALL != HASH EVERYTHING THEN FILTER`

`BOUNDED RETRIEVAL != UNBOUNDED EXCLUSION DUMP`

## Minimal repair

Repair commit: `dfd463cc7a39d069816512d7d45c795d52d18b85`

The repair only moves lifecycle/supersession/event/scope rejection before source freshness hashing, hashes only metadata-eligible candidates, and replaces per-memory exclusion identity output with `excluded_count` plus bounded `exclusion_counts` aggregates. It adds no authority, external I/O, autonomous lifecycle mutation, or second memory store.

## Counter-DA survivor

Independent repaired-head validation:

- head: `8071b31e6d00480383230e57f52061c503216ddc`
- GitHub Actions run: `33047645367`
- Selective Recall baseline: **19/19 PASS**
- DA + Counter-DA: **5/5 PASS**
- existing FREEZER regression: **41/41 PASS**
- FREEZER verification: **PASS**
- Build Assessment verification: **PASS**
- registry freshness: **2/2 CURRENT**
- recall execution authority: `NONE`
- recall promotion authority: `NONE`
- smallest-anchor CLI probe: **PASS**
- direct `RAW -> CANONICAL`: **REJECTED** as required.

Counter-DA proves both sides: irrelevant/scope-mismatched strata remain cold, while a relevant stale candidate still pays the freshness check and is rejected as `STALE`.

## METEOR verdict

`INITIAL CANDIDATE = DIES`

`MINIMAL REPAIR = SURVIVES SAME DEATH WORKLOAD`

`REPAIRED SELECTIVE-RECALL LAYER = PROMOTED SURVIVOR UNDER CURRENT REPOSITORY EVIDENCE`

This is composition, not replacement, of the existing RTS memory index.

## Deployment / Reality applicability

This occupant is repository-local and read-only. It has no live service, publish target, payment surface, provider execution, or production runtime route. Fabricating Deployment Identity would therefore be invalid.

Equivalent verification boundary:

`COMMITTED SOURCE + DETERMINISTIC CLI + FROZEN DESTRUCTIVE TESTS + CURRENT SOURCE HASHES + FREEZER GOVERNANCE VERIFICATION`

No claim of external-user success, population-scale performance, universal semantic retrieval quality, or autonomous safe promotion is made.

## Permanent regression memory

The DA death tests remain committed in `tests/test_selective_recall_da.py`. Future changes must preserve the cold-irrelevant-strata boundary, relevant-stale rejection, bounded diagnostics, and non-authorizing output.
