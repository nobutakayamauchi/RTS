# OLT v0.3 timeline — source diff review

Status: `INGESTED / EVIDENCE-BOUNDED / NOT PROMOTED`

Source workbook: `Operator_Load_Timeline_v0_3_timeline.xlsx`.

## Accepted v0.3 additions

The repository representation now preserves these v0.3 timeline layers:

- monthly four-repository authored-PR focus as a `WEAK` portfolio proxy;
- short-window RTS PR density as a `WEAK` output-burst proxy;
- selected source-bound decision/rework ledger;
- timeline invariants and anti-overclaim rules;
- the v0.2 actual-load windows and load-shape diagnostics remain separate from the weak timeline proxies.

The selected decision ledger recomputes to:

- `J_selected = 21`;
- `R_selected = 7`;
- `D3_selected = 3`.

The tracked portfolio proxy shows a broad surface migration of RTS -> RTS-AGE -> RTS-minicompany/RTS -> RTS across the currently tracked repositories. This is development-surface evidence only. It is not converted to human workload share.

The maximum selected RTS PR-density proxy is `104 / 7 = 14.8571 PR/day` for 2026-03-01..07. The sharp decline after that remains an output-surface observation only; fatigue or cognitive decline is not inferred from it.

## Material discrepancy found during ingestion

`Timeline_Dashboard_v0_3` displays judgment pressure `0` for the rts-video-flow 2026-08-03..06 window while the corresponding `Actual_Calc_v0_2` row has only `O=3` observed and leaves `J` and `R` unobserved.

Under the active invariant `Unknown != zero`, the expression `(J+R)/O` is therefore **UNOBSERVED**, not zero.

Repository canonicalization:

- source/dashboard value: `0`;
- canonical evidence-bounded value: `null / UNOBSERVED`;
- no correction is inferred for the missing J or R axes.

This discrepancy is retained in `olt_timeline_v0_3.json` and regression-tested. The source workbook is not mutated by this branch.

## What v0.3 still does not prove

- January 20 to present is not yet a complete event-level OLT corpus.
- Authored PR share is not human workload share.
- PR density is not fatigue evidence.
- Zero PRs do not establish zero design/chat work.
- The selected decision ledger is a lower-bound subset, not a complete decision count.
- ChatGPT conversation timestamps have not yet been fully bound into project-switch `X` and semantic decision `J` at event level.

Next material evidence is the conversation/event join required to fill missing `J` and `X` without promoting weak GitHub proxies into semantic human load.
