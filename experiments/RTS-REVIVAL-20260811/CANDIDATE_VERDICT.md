# RTS Revival Time Attack — Candidate Verdict

Timestamp: **2026-08-11 19:04 JST**

Benchmark origin: **2026-08-11 18:49 JST**

Elapsed to candidate verdict: **15 minutes**.

## Candidate result

- `THIN_RTS_CANDIDATE`: `PASS_FOR_CURRENT_REFERENCE_WORKLOAD`
- `ADDITIONAL_SOFTWARE_SERVICE_COST`: `JPY_0_TARGET_MET`
- `CUSTOM_RTS_RUNTIME_REQUIRED`: `NOT_PROVEN`
- `CUSTOM_RTS_CONTROLLER_REQUIRED`: `NOT_PROVEN`
- `CUSTOM_RTS_GOVERNANCE_KERNEL_REQUIRED`: `NOT_PROVEN`
- `FULL_HISTORICAL_EQUIVALENCE`: `EVIDENCE_INSUFFICIENT`
- `PROMOTION_TO_MAIN`: `NOT_AUTHORIZED / DRAFT_PR_ONLY`

## What was actually rebuilt

Thin RTS v0 consists of a very small RTS-owned responsibility surface:

1. a material-transition record contract;
2. a reconstruction/fail-closed rule binding external evidence, authority, runtime/outcome references, learning/review, promotion boundaries, and unknowns.

The implementation-heavy responsibilities remain outside Thin RTS.

## Externalized responsibilities actually exercised

### Durable evidence / recovery

Git/GitHub history preserved pre-attack content, destructive corruption, and exact recovery.

`thin-rts/README.md` was deliberately corrupted and then restored from preserved Git evidence. The restored blob exactly matched the original blob.

Result: `PASS`.

### Decision authority boundary

Legacy `scripts/decision_boundary_append.py` responsibility was reproduced through a committed authority-boundary record plus Git history.

The record was deliberately mutated to a synthetic invalid broader scope, the original was independently recovered from the prior commit, and the current file was restored exactly.

Result: `PASS`.

### Evidence discovery

Legacy generated evidence-index discovery was challenged with external GitHub repository search/history. Relevant ESC/index/session artifacts were discoverable without executing `scripts/evidence_index_build.py`.

Result: `PASS_FOR_DISCOVERY`; exact custom legacy latest-sort behavior remains unproven as necessary and therefore is not rebuilt.

### Runtime / execution evidence

A real external GitHub Actions execution was observed for tested head commit `0dc5cf91746b876c7c59a5df50d3a647d31d07f2`:

- workflow: `Unicode Guard`
- run id: `31480351896`
- job id: `93743627933`
- job conclusion: `success`
- invisible-unicode guard step: `success`

This is runtime evidence for that CI workload. It is not inferred from code existence.

### Outcome / learning / promotion separation

- CI success exists as external execution/outcome evidence.
- `LEARNING_PROPOSAL_0001.md` exists as a proposal only.
- PR #313 is open as a **draft** external review surface.
- successful construction/CI did not silently authorize merge/promotion.

Result: `PASS` for separation of execution outcome, learning, review, and promotion authority.

### Legal/privacy boundary

The new records retain normalized intent/structural references rather than copying unnecessary raw private conversation payloads into the public repository.

The historical lesson that auditability does not justify unnecessary raw wording retention was preserved.

Result: `PASS` for the current workload.

## Surviving Thin RTS minimum

`external systems + minimal reconstructive binding contract + explicit authority boundaries`

No dedicated daemon, service, scheduler, queue, database, vector store, custom WORM store, custom replay DB, custom CI engine, custom promotion controller, or RTS-owned agent runtime became necessary in the exercised workloads.

## Old implementation responsibilities currently killed or externalized

- `scripts/decision_boundary_append.py` → historical implementation `ARCHIVE`; responsibility externalized to Git/GitHub + thin record.
- `scripts/evidence_index_build.py` → generated local index not justified for the current retrieval workload; search/retrieval `EXTERNALIZE`.
- custom recovery engine → not required for tested Git-backed corruption/recovery.
- custom regression engine → not required for tested GitHub CI workload.
- custom promotion controller → not required; authority remains external/human and fail-closed.
- custom RTS Runtime/Controller/Governance Kernel → no current evidence of necessity.

## What is not proven yet

1. **Full equivalence across every historical RTS scenario.** The current test covers multiple material responsibility classes but not every historical script/provider/environment.
2. **Administratively Independent Authority.** Still not demonstrable under a single ultimate administrator and must not be simulated in code.
3. **A persistent production-service Deployment Identity scenario.** The current real runtime proof is a GitHub Actions job, not a long-lived service deployment.
4. **The remembered `5400x` acceleration figure.** No surviving evidence establishes it, and this 15-minute candidate build is not scope-equivalent to the historical 44-minute reproduction package or the full historical RTS development period.

## Speed conclusion

The time attack has demonstrated that a tested external-first Thin RTS candidate can be composed, exercised, destructively attacked, recovered, externally CI-checked, and authority-separated in **15 minutes** from the reset benchmark origin.

That is a measured result.

It does **not** by itself prove a `5400x` multiplier.

## Next gate

Do not add features merely to chase completeness.

Continue only with a materially new reference workload or failure mode. If a workload demonstrates an irreducible gap, send only that gap through WITNESS Destroy Loop / Meteor Gate before authorizing new glue.
