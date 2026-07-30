# RTS Repository Inventory Baseline v1

> Measurement only. This report authorizes no deletion, movement, consolidation, or runtime change.

- Baseline commit: `f141276ab6b88b5e4ea98efeb53cf2ff9c7f27b9`
- Files: **1,033**
- Repository bytes measured: **10,550,670**
- Recognized UTF-8 text files: **926**
- Recognized UTF-8 text lines: **83,365**
- Top-level entries: **60**
- File-extension groups: **15**

The categories below overlap intentionally. They describe repository shape and do not decide canonical ownership or removal eligibility.

## Descriptive category totals

| Name | Files | Lines | Bytes |
|---|---:|---:|---:|
| `ci_workflows` | 29 | 2,407 | 106,695 |
| `documentation` | 312 | 24,627 | 723,883 |
| `governed_records_and_history` | 379 | 22,471 | 7,766,706 |
| `pointer_index_manifest_candidates` | 161 | 7,720 | 339,803 |
| `runtime_source` | 223 | 36,667 | 1,587,824 |
| `schemas_and_contracts` | 25 | 2,228 | 74,273 |
| `structured_data` | 393 | 20,980 | 1,280,298 |
| `tests` | 52 | 7,353 | 325,040 |

## Largest top-level areas by text lines

| Name | Files | Lines | Bytes |
|---|---:|---:|---:|
| `proof_engine_pilot` | 193 | 16,860 | 1,111,764 |
| `freezer` | 115 | 9,023 | 383,638 |
| `docs` | 94 | 8,696 | 247,660 |
| `tests` | 52 | 7,353 | 325,040 |
| `incidents` | 146 | 5,230 | 6,906,011 |
| `scripts` | 24 | 5,204 | 155,834 |
| `logs` | 18 | 4,539 | 109,409 |
| `.github` | 35 | 2,553 | 111,914 |
| `execution_controller` | 18 | 2,133 | 74,889 |
| `sessions` | 88 | 2,040 | 307,482 |
| `governed_loop` | 9 | 1,960 | 71,332 |
| `human_review_ledger` | 16 | 1,451 | 58,262 |
| `evolution` | 11 | 1,243 | 21,081 |
| `rts_kernel` | 11 | 1,230 | 36,517 |
| `skill_regression` | 17 | 1,198 | 50,004 |
| `pilot_runs` | 48 | 995 | 72,830 |
| `outcome_evidence` | 12 | 954 | 37,619 |
| `pilot_run_contract` | 14 | 935 | 45,857 |
| `learning_proposals` | 11 | 891 | 49,311 |
| `loop_core` | 7 | 824 | 29,200 |
| `promotion_application_preview` | 9 | 761 | 33,361 |
| `adaptive_governance` | 8 | 722 | 26,830 |
| `asset_manifest` | 13 | 640 | 95,421 |
| `runs` | 5 | 446 | 6,955 |
| `memory` | 4 | 402 | 23,009 |
| `vibecode` | 3 | 399 | 7,948 |
| `radar` | 5 | 359 | 34,278 |
| `legal` | 4 | 334 | 9,559 |
| `services` | 1 | 320 | 12,884 |
| `IMP_2026-03-16_rts_ai_live_logging_completion_summary.md` | 1 | 275 | 7,348 |

## Largest extension groups by text lines

| Name | Files | Lines | Bytes |
|---|---:|---:|---:|
| `.py` | 223 | 36,667 | 1,587,824 |
| `.md` | 298 | 24,306 | 696,652 |
| `.json` | 353 | 18,317 | 1,166,202 |
| `.yml` | 31 | 2,433 | 107,185 |
| `.html` | 10 | 1,362 | 39,208 |
| `.yaml` | 9 | 230 | 6,911 |
| `.txt` | 2 | 50 | 1,315 |
| `.zip` | 51 | 0 | 161,972 |
| `.bin` | 31 | 0 | 6,642,031 |
| `.sha256` | 8 | 0 | 22,619 |
| `.jsonl` | 6 | 0 | 64,423 |
| `[no extension]` | 5 | 0 | 1,603 |
| `.patch` | 3 | 0 | 32,226 |
| `.b64` | 2 | 0 | 18,546 |
| `.log` | 1 | 0 | 1,953 |

## Interpretation boundary

This baseline answers how large the repository is and where material is concentrated. It does not yet answer which files are authoritative, generated, historical, duplicated, or safely removable. Those decisions belong to the next shape-up stage after explicit classification and reference analysis.

## Measurement note

The current v1 line counter recognizes the declared text suffix set. Files such as `.jsonl`, `.patch`, `.sha256`, and `.log` are included in file and byte totals but not in the v1 text-line total. This limitation is explicit and does not affect the main concentration findings.

## Declared exclusions

The following probe files were excluded so this baseline represents the pre-shape-up `main` tree:

- `.github/workflows/rts-shapeup-inventory-probe.yml`
- `scripts/maintenance/measure_repository.py`
