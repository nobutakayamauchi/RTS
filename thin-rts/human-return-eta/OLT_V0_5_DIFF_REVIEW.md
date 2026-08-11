# OLT v0.5 Diff Review — deeper history recovery

Status: evidence-bounded ingestion review for `Operator_Load_Timeline_v0_5_deeper_history.xlsx`.

This file records what materially changed from the repository's v0.4 corpus. It does **not** declare the historical timeline complete.

## Recovery delta

v0.4 -> v0.5:

- exact HUMAN events: `36 -> 57` (`+21`)
- exact ChatGPT USER events: `16 -> 37` (`+21`)
- eligible exact-HUMAN active minutes: `167.0667 -> 225.9000` (`+58.8333 min`)
- observed calendar days with evidence: `19 -> 26` (`+7`)
- observed daily peak remains `2026-07-27`, OLT lower bound `61.5299`

The breadth changed much more than the peak.

## Newly material March human decision line

March was previously dominated by a WEAK GitHub output fact: `104 PR / 7 days` during 2026-03-01..07. v0.5 adds exact human ChatGPT evidence:

- 2026-03-03: `E=6.7722`, `J=2`, OLT LB `16.3592`
- 2026-03-06: `E=2.13`, `J=3`, OLT LB `13.9756`
- 2026-03-13: `E=1`, `J=2`, OLT LB `9.2051`
- 2026-03-16: `E=1`, `J=2`, OLT LB `9.2051`

March recovered totals are therefore `10 exact Chat USER events` and `J>=9` from directly scored decisions.

The semantic sequence is evidence for architecture/governance work beneath the output burst: README scope choices, Boundary Discipline before implementation, human-decision vs AI-work-log separation, and boundary meaning/direction semantics.

It is **not** proof that every March PR was caused by those four decision clusters. Stage-to-chat binding remains open.

## Other new anchors

- 2026-04-20: four exact HUMAN architecture-exploration messages around Hermes / RTS Skills / MCP / repository separation; `E=4.7444` only. Questions are not silently promoted to decisions.
- 2026-05-07: the portfolio inventory chain expands to four exact HUMAN messages; `E=6.21` with no fabricated J.
- 2026-06-29: MiniCompany spec-first -> Codex delegation -> Reference Intake sequence; `E=3.0656`, `J=4`, OLT LB `18.0347`.
- 2026-08-04: exact Vlog deployment command; `E=1` only.

## Monthly fused lower-bound shape

The v0.5 monthly vectors are **observed evidence mass**, not average daily load and not estimates for missing days.

| Month | E | J | O | R | Coverage | OLT mass |
|---|---:|---:|---:|---:|---:|---:|
| 2026-02 | 25.9633 | 2 | ? | 2 | 60% | 32.8478 |
| 2026-03 | 10.9022 | 9 | ? | ? | 40% | 36.2438 |
| 2026-04 | 10.1322 | 2 | ? | 1 | 60% | 21.4786 |
| 2026-05 | 9.4944 | 3 | ? | ? | 40% | 22.2831 |
| 2026-06 | 4.0656 | 6 | ? | ? | 40% | 23.9856 |
| 2026-07 | 9.5022 | 19 | 26.5 | 15 | 80% | 71.1791 |
| 2026-08 (1-12) | 2 | 17 | 18.17 | 17 | 80% | 60.0907 |

`X` remains unobserved at monthly level in this corpus.

## Interpretation boundary

Current working hypothesis:

`Implementation -> Architecture -> Orchestration -> Adversarial Judgment`

The recovered vectors are consistent with that role transition, especially the rising observed J/O/R share in July-August. This remains a **partial-evidence hypothesis**, not a causal or clinical conclusion.

Do not infer:

- fatigue from PR drops, gaps, or low observed OLT;
- human effort from raw PR/commit counts;
- zero workload on unobserved days;
- a decision from an architecture question unless an explicit choice is present;
- complete context-switch X until cross-project exact HUMAN sequences are materially recovered.

## Next material evidence test

The highest-value next step is March stage binding:

`recovered exact human decision hinge -> PR/governed stage sequence -> next human hinge`

Target: RTS PR `#1..#130`, with special attention to the 2026-03-01..07 104-PR burst.

This can expose a time-varying human amplification measure such as machine-visible stages/commits between human decision hinges without pretending raw output equals human work.

Candidate quantities must remain descriptive until held-out validation:

- governed stages per human hinge;
- machine-visible output per human hinge;
- gate minutes per human hinge;
- time from human decision to next human intervention;
- semantic class of the human hinge (D1/D2/D3).

## Survival status

`v0.5 = INGESTED / PARTIAL / NOT PROMOTION EVIDENCE`

The model still lacks full 2026-01-20->present ChatGPT event materialization and complete X. The historical gaps remain visible rather than synthetically filled.
