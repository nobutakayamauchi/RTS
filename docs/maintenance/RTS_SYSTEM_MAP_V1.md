# RTS System Map v1

> Descriptive map only. This document does not authorize deletion, movement, consolidation, repository splitting, or authority changes.

## Baseline

This map is bound to `main` commit:

```text
f141276ab6b88b5e4ea98efeb53cf2ff9c7f27b9
```

Measured repository shape:

| Measure | Result |
|---|---:|
| Files | 1,033 |
| Repository bytes | 10,550,670 |
| Recognized UTF-8 text files | 926 |
| Recognized UTF-8 text lines | 83,365 |
| Top-level entries | 60 |
| Python files | 223 |
| Markdown files | 298 |
| JSON files | 353 |
| CI workflow files | 29 |
| Test files | 52 |

The machine-readable baseline is `RTS_REPOSITORY_INVENTORY_V1.json`. The human-readable measurement table is `RTS_REPOSITORY_INVENTORY_V1.md`.

## Current structural map

```text
RTS repository
├─ Protocol and reconstruction core
│  ├─ rts_core
│  ├─ rts_kernel
│  ├─ schemas
│  ├─ root protocol and rulebook documents
│  └─ docs/overview and reconstruction documentation
│
├─ Governance and controlled change
│  ├─ freezer
│  ├─ adaptive_governance
│  ├─ asset_manifest
│  ├─ human_review_ledger
│  └─ promotion_application_preview
│
├─ Bounded execution and continuation
│  ├─ loop_core
│  ├─ execution_controller
│  ├─ governed_loop
│  ├─ pilot_run_contract
│  └─ pilot_runs
│
├─ Evidence, regression, and learning proposals
│  ├─ outcome_evidence
│  ├─ skill_regression
│  └─ learning_proposals
│
├─ Product and validation layer
│  ├─ proof_engine_pilot
│  ├─ product and pilot documentation under docs
│  └─ reader, privacy, generalization, and customer-pilot records
│
├─ Operational and historical surfaces
│  ├─ incidents
│  ├─ logs
│  ├─ sessions
│  ├─ runs
│  ├─ memory
│  ├─ evolution
│  └─ artifacts
│
└─ Support and public surfaces
   ├─ scripts
   ├─ .github/workflows
   ├─ security
   ├─ radar
   ├─ legal
   ├─ templates
   ├─ services
   └─ root HTML, search, and operator documents
```

This grouping is architectural description, not a canonical ownership decision. Some files may serve more than one group.

## Where the size actually is

### 1. Product-validation code is the largest text area

`proof_engine_pilot` contains:

```text
193 files
16,860 recognized text lines
1,111,764 bytes
```

That is about 20.2% of the measured text lines. It is the first place to examine for product-specific concentration, internal submodule boundaries, repeated builders, repeated validators, and records that may belong outside the permanent core.

This is not a finding that the directory is defective or removable.

### 2. Governance is substantial but expected

`freezer` contains:

```text
115 files
9,023 recognized text lines
383,638 bytes
```

This is about 10.8% of the measured text lines. Because FREEZER carries immutable lifecycle records, indexes, assessments, preflights, and verification logic, high file count alone does not indicate waste.

The next stage must distinguish:

- canonical rules and validators;
- immutable history;
- current pointers;
- reproducible indexes and manifests;
- fixtures and tests.

### 3. Documentation and tests are major, not incidental

```text
docs    94 files / 8,696 lines
tests   52 files / 7,353 lines
```

Together they represent about 19.3% of measured text lines. The shape-up must reduce navigation and duplication without weakening reconstruction, test coverage, or human readability.

### 4. Physical storage is dominated by incident evidence, not code

`incidents` contains 6,906,011 bytes, about 65.5% of the measured repository bytes. The `.bin` group alone contains 6,642,031 bytes, about 63.0% of the repository bytes.

Therefore:

- repository byte size is not a reliable measure of source-code obesity;
- incident evidence storage must be assessed separately from code cleanup;
- binary snapshots must not be deleted merely to improve headline repository size;
- any later storage change requires evidence-retention, integrity, reference, and reconstruction review.

### 5. The main cognitive-load signal is top-level fragmentation

The repository has 60 top-level entries. This is the strongest immediate navigation problem.

A new operator or AI session currently has to decide among many root modules, root documents, historical areas, product areas, and support areas before it can locate the authoritative entry point.

The first safe improvement should therefore be an explicit entry map and classification—not a mass directory move.

### 6. Three formats hold nearly all measured text

```text
Python     36,667 lines
Markdown   24,306 lines
JSON       18,317 lines
```

Together they account for about 95.1% of measured text lines.

This means the practical shape-up targets are:

- Python validator and builder duplication;
- Markdown entry-point and explanation duplication;
- JSON history, pointer, index, manifest, fixture, and output classification.

### 7. Pointer, index, manifest, and checkpoint names form a review hotspot

A filename-based heuristic found:

```text
161 files
7,720 recognized text lines
```

These are only candidates. The heuristic does not establish that they are generated or redundant.

The next stage must label each relevant path as one of:

```text
CANONICAL_SOURCE
IMMUTABLE_HISTORY
CURRENT_POINTER
REGENERABLE_INDEX_OR_MANIFEST
TEST_FIXTURE
STATUS_OR_RESUME_VIEW
PRODUCT_OUTPUT
UNKNOWN_REQUIRES_REVIEW
```

### 8. CI needs later consolidation review, not immediate deletion

The repository contains 29 workflow files and approximately 2,407 workflow lines.

That is enough surface area to justify a later matrix covering:

- trigger paths;
- duplicated setup;
- repeated full-suite execution;
- dedicated governed checks;
- artifact generation;
- temporary candidate workflows;
- Unicode and integrity checks.

No workflow consolidation is part of this stage.

## First shape-up conclusions

The repository is not simply a large application. It combines:

1. permanent protocol and reconstruction rules;
2. runtime and validation code;
3. immutable governed records;
4. generated or pointer-like views;
5. product-specific pilot machinery;
6. documentation and tests;
7. incident and operational evidence.

The shape-up must not optimize all seven categories with the same method.

## Recommended order after this measurement stage

```text
Stage 1  Measure and map                         CURRENT
Stage 2  Classify canonical / generated / history / fixture
Stage 3  Unify operator and AI entry points
Stage 4  Identify duplicate Python primitives and validators
Stage 5  Review CI trigger and execution duplication
Stage 6  Review documentation duplication
Stage 7  Re-measure and compare
Stage 8  Decide whether Core and product layer need physical separation
```

## Next bounded stage

The next PR should perform classification and reference analysis only.

Expected output:

- one path-classification contract;
- one inventory of current pointers, indexes, manifests, histories, fixtures, status views, and product outputs;
- reference checks identifying which candidates are consumed by code, tests, CI, or documentation;
- explicit `KEEP`, `REGENERABLE`, `RELOCATE_LATER`, and `UNKNOWN` recommendations;
- no deletion or movement.

## Stop conditions

Stop and require review if classification would:

- rewrite or invalidate signed history;
- change a fingerprint or chain;
- make reconstruction dependent on an uncommitted artifact;
- confuse current state with historical evidence;
- treat a naming heuristic as proof;
- change runtime behavior or authority;
- move files before references are fully mapped.

## Stage-1 decision

```text
REPOSITORY_SHAPE_MEASURED
SYSTEM_MAP_RECORDED
NO_CLEANUP_ACTION_AUTHORIZED
NEXT_STAGE_CLASSIFICATION_AND_REFERENCE_ANALYSIS_ONLY
```
