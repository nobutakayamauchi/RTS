# Operator Load Timeline v0.2 — evidence-bounded actual calculation

Status: `OBSERVED LOWER-BOUND DATA / NOT PROMOTED`

Source model: `Operator_Load_Timeline_v0_2_actual.xlsx` supplied by the operator and cross-checked against the recovered v0.1 contract.

## Delta from v0.1

v0.1 established the auditable model and a small number of anchor windows. v0.2 adds three important rules and a wider observed corpus:

1. **Blank axis means UNOBSERVED, not zero.** Missing E/J/O/R/X values contribute zero only to the displayed lower-bound arithmetic. They remain `null` in machine-readable evidence.
2. **Axis coverage travels with every lower-bound score.** `coverage = observed_axes / 5`. A 52-point result at 60% coverage is not directly equivalent to a 52-point fully observed vector.
3. **Orchestration uses only known, non-double-counted gate time.** `O = governed_stages + known_bounded_gate_minutes / 15`; a missing gate duration never deletes the governed stage itself.

The scalar remains secondary. `(E,J,O,R,X)` plus evidence coverage is the truth-bearing record.

## Current observed lower bounds

| project/window | E | J | O | R | X | coverage | OLT lower bound | commits/stage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RTS Pre-Kernel 2/16 + 2/18 | 22.25 | — | — | — | — | 20% | 20.1 | — |
| RTS Post-Kernel 2/26–27 sample | 3.72 | — | — | — | — | 20% | 5.1 | — |
| RTS PR #283–286 | — | 3 | 7.75 | 4 | — | 60% | 27.2 | 16.5 |
| RTS 7/27 #276–291 | — | 10 | 26.50 | 10 | — | 60% | 52.2 | 14.1 |
| RTS 8/9 #302–308 | — | 2 | 9.69 | 11 | — | 60% | 29.0 | 7.9 |
| RTS 8/9 #309–312 | — | 5 | 4.00 | — | — | 40% | 22.9 | 11.8 |
| RTS 8/11 #313–315 | — | 4 | 3.48 | 4 | — | 60% | 25.2 | 35.7 |
| RTS-minicompany 7/15–16 | — | 11 | 15.43 | 7 | — | 60% | 49.4 | 11.6 |
| RTS-minicompany #91 | — | 3 | 1.00 | — | — | 40% | 12.8 | 361.0 |
| RTS-AGE #76→#77 | — | 2 | 2.00 | 2 | — | 60% | 14.7 | 20.0 |
| rts-video-flow 8/3–6 | — | — | 3.00 | — | — | 20% | 5.2 | 61.7 |

The largest current RTS lower bound is the 2026-07-27 governed sequence: `OLT >= 52.2` with only J/O/R observed. E and X remain unknown.

## Amplification ratio

Machine-visible output can be tracked separately from human load:

`Gamma = machine_visible_output / governed_human_stages`

For the current corpus, commit count is used only as a machine-visible output proxy. Gamma is **not an OLT load axis** and must never be read as human effort.

Examples:

- RTS #283–286: 16.5 commits/stage
- RTS 7/27: 14.1
- RTS 8/9 Deployment Identity: 7.9
- RTS 8/11: 35.7
- RTS-minicompany 7/15–16: 11.6
- RTS-minicompany #91: 361.0
- RTS-AGE #76→#77: 20.0
- rts-video-flow 8/3–6: 61.7

The extreme #91 case is direct evidence for the invariant `361 commits != 361 human actions`.

## Judgment Pressure Ratio

For windows where J, R and O are all observed, the descriptive shape ratio is:

`JPR = (J + R) / O`

Examples from current bounded observations:

- RTS 7/27: about 0.75 — orchestration-heavy governed throughput.
- RTS 8/9 Deployment Identity: about 1.34 — comparatively high adversarial/rework pressure.

JPR is not a fatigue score and is **not guaranteed to be a lower bound** when J/R/O themselves are partial lower-bound observations. It is a workload-shape diagnostic only and must travel with coverage/evidence notes.

## Pre/Post-Kernel anchor

The recovered intervention dataset remains the strict anchor:

- Pre-Kernel: 17 confirmed HUMAN events + 78.7 eligible active minutes -> `E = 22.2467`.
- Post-Kernel materialized sample: HUMAN=3, AUTO=7, UNKNOWN=5 -> `Q=66.7%`, `A=70.0%`, `E=3.7167`.
- The separate spreadsheet Summary still says 3/8/8. This conflict remains explicit.

This is empirical evidence that raw GitHub activity stopped being a defensible proxy for human effort once automation became material.

## Human Return ETA consequence

The ETA layer should now treat historical observations as:

`(duration, E?, J?, O?, R?, X?, coverage, task_class, evidence_strength)`

rather than forcing every historical window into a complete vector.

The next model-comparison round must test whether partial-vector neighbors improve held-out return-time prediction without inventing missing axes. Until then, complete-vector OLT similarity remains an optional prior and v0.2 lower-bound rows are preserved as calibration/evidence data rather than silently imputed.
