# OLT v0.4 Diff Review — ChatGPT timestamp fusion

Status: `EVIDENCE INGESTED / DRAFT PR / NOT PROMOTED`

Source workbook: `Operator_Load_Timeline_v0_4_chat_fused.xlsx`.

## Material differences from v0.3

v0.3 established portfolio focus, PR burst proxies, a selected decision ledger, evidence hierarchy and evidence-bounded spot OLT windows.

v0.4 adds a normalized event ledger and daily fusion layer:

- exact confirmed HUMAN Git/Chat timestamps can contribute Execution E;
- Pre-Kernel 17 HUMAN events are split onto their real JST dates instead of one combined window;
- Post-Kernel HUMAN/AUTO/UNKNOWN rows remain actor-separated;
- date-only or formal semantic records may contribute J/R/O where supported but never fabricate E;
- semantic duplicates are retained as corroboration but excluded from rollup;
- unresolved project attribution remains unresolved instead of being guessed;
- Jan 20 through Aug 12 is represented as a daily range where missing days are `UNOBSERVED`, not zero.

## Recovered exact-human anchor

The workbook reports 36 exact confirmed HUMAN events and 167.06666666666672 minutes of eligible adjacent activity (<30 minutes).

The repository canonical copy recomputes these values from ten observed project/day anchors. Per day:

`E = exact_human_events + active_minutes / 15`.

This includes the original Pre-Kernel anchor split into:

- 2026-02-16: 8 events, 31.4333 min, E=10.0956;
- 2026-02-18: 9 events, 47.2667 min, E=12.1511.

## 2026-07-27 fusion

Five exact ChatGPT HUMAN events provide 36.6667 minutes of eligible active time:

`E = 5 + 36.6667/15 = 7.4444`.

The existing governed GitHub row remains J=10, O=26.5, R=10. ChatGPT decision evidence totaling J=5 is treated as a corroborating subset and is not added again.

Canonical fused partial vector:

`(E=7.4444, J=10, O=26.5, R=10, X=UNOBSERVED)`

Axis coverage rises from 60% to 80%; the evidence-bounded display lower bound rises from v0.3 `52.205955` to v0.4 `61.529923`.

This is a stronger lower bound, not a claim that the true day is exactly 61.53.

## 2026-07-23 unresolved reversal

The exact 14:45–14:46 ChatGPT reversal sequence is retained as `UNRESOLVED_PROJECT` with E=2.0578 and R=3. A later MiniCompany `PUBLIC_SALE_APPROVED` formal record contributes J=3 to MiniCompany.

No evidence currently proves that the reversal concerned the public-sale decision, so the two project identities are not joined. They may be fused only at the overall-day level as separate known contributions.

## Source representation note: unobserved axis cells

Some v0.4 workbook daily tables render numeric `0` in cells whose corresponding observation flags mark the axis unobserved. This is acceptable as a spreadsheet display convention only if the flags are always consulted, but it is unsafe as a machine-readable representation.

Repository canonical rule:

- observed zero contribution -> `0`;
- unobserved axis -> `null`;
- unobserved day -> no synthetic zero-load vector.

This preserves the active invariant `Unknown != zero` and prevents later ETA/OLT fusion from treating missing evidence as measured absence.

## New bounded glue

`olt.fuse_partial_vectors()` sums observed project contributions axis-by-axis while preserving an axis as `None` when no input has evidence for it. It is explicitly a lower-bound fusion operation.

`olt_daily_v0_4.json` is the machine-readable evidence-bounded daily anchor corpus. `test_olt_daily_v04.py` recomputes:

- exact-human totals;
- daily E from exact event count and active minutes;
- every stored project-day coverage and OLT lower bound;
- Jul 27 v0.3 -> v0.4 increase;
- Jul 23 unresolved/project-level separation plus overall-day fusion;
- null preservation for unobserved axes;
- no fatigue inference and no zero-work inference for missing days.

## Still not proven

- Complete ChatGPT event-level history from 2026-01-20 to present;
- complete X/context-switch history;
- complete E on semantic-only high-load days such as Aug 9 and Aug 11;
- safe imputation of missing axes;
- fatigue/cognitive decline from output gaps or OLT alone;
- Human Return ETA accuracy improvement from partial daily OLT before held-out validation.

The next material evidence is more exact HUMAN timestamps, especially the March RTS construction burst, May–June AGE/MiniCompany transition, and Aug 6–11 Deployment Identity/WITNESS period.
