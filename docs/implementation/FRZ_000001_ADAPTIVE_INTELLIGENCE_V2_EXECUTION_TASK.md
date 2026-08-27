# FRZ-000001 Adaptive Intelligence v2 — Governed Decomposition Execution Task

## Purpose

Convert the already-reviewed Adaptive Intelligence v2 reassessment into canonical FREEZER records without implementing runtime behavior.

This task is limited to:

1. revising parent `RTS-FRZ-000001` to v2 while keeping it `FROZEN / NOT_APPROVED`;
2. creating a fresh Build Assessment from the pinned external/internal evidence;
3. creating a fresh `DECOMPOSE_REQUIRED` Implementation Preflight;
4. creating five new child candidates as `FROZEN / NOT_APPROVED`;
5. rebuilding and verifying indexes/manifests.

This task does **not** authorize selecting, implementing, applying, publishing, scheduling, calling providers, or modifying external repositories.

## Inputs

Use only these committed inputs:

```text
docs/implementation/frz000001_v2_inputs/revise_item_v2.json
docs/implementation/frz000001_v2_inputs/build_assessment_input.json
docs/implementation/frz000001_v2_inputs/preflight_input.json
docs/implementation/frz000001_v2_inputs/child_a_selective_recall_memory_lifecycle.json
docs/implementation/frz000001_v2_inputs/child_b_compact_active_restart_surface.json
docs/implementation/frz000001_v2_inputs/child_c_incremental_resumable_compiler.json
docs/implementation/frz000001_v2_inputs/child_d_reuse_efficiency_knowledge_debt_metrics.json
docs/implementation/frz000001_v2_inputs/child_e_external_transition_pattern_seed_corpus.json
```

## Required sequence

Run from repository root on the PR branch.

```bash
python -m freezer.cli revise RTS-FRZ-000001 \
  --input docs/implementation/frz000001_v2_inputs/revise_item_v2.json

python -m freezer.build_assessment create RTS-FRZ-000001 \
  --input docs/implementation/frz000001_v2_inputs/build_assessment_input.json

python -m freezer.preflight create RTS-FRZ-000001 \
  --input docs/implementation/frz000001_v2_inputs/preflight_input.json

python -m freezer.cli add \
  --input docs/implementation/frz000001_v2_inputs/child_a_selective_recall_memory_lifecycle.json
python -m freezer.cli add \
  --input docs/implementation/frz000001_v2_inputs/child_b_compact_active_restart_surface.json
python -m freezer.cli add \
  --input docs/implementation/frz000001_v2_inputs/child_c_incremental_resumable_compiler.json
python -m freezer.cli add \
  --input docs/implementation/frz000001_v2_inputs/child_d_reuse_efficiency_knowledge_debt_metrics.json
python -m freezer.cli add \
  --input docs/implementation/frz000001_v2_inputs/child_e_external_transition_pattern_seed_corpus.json
```

Do not hard-code child IDs before creation. Let `freezer.cli add` allocate the next contiguous IDs in the committed repository state, and record the resulting mapping in the PR summary.

## Required verification

```bash
python -m freezer.cli verify
python -m freezer.build_assessment verify
python -m freezer.build_assessment gate RTS-FRZ-000001
```

Also run the repository's existing focused FREEZER/unit verification available in the checkout. Do not weaken tests or validation to make this task pass.

## Expected parent state

After canonicalization:

```text
RTS-FRZ-000001
status: FROZEN
build_authority: NOT_APPROVED
current preflight: DECOMPOSE_REQUIRED
selection_ready: false
```

The parent Build Assessment recommendation may be `BUILD_NEXT` rather than `BUILD_NOW`; that is acceptable because the parent is intentionally not an implementation unit. Do not manipulate scores to force `BUILD_NOW`.

## Expected children

Exactly five newly allocated candidates corresponding to:

1. Selective Recall + Memory Lifecycle v1
2. Compact Active + Restart Surface v1
3. Incremental / Resumable Intelligence Compiler v1
4. Reuse Efficiency + Knowledge Debt Metrics v1
5. External Transition Pattern Seed Corpus v1

Every child must remain:

```text
status: FROZEN
build_authority: NOT_APPROVED
```

No child receives an Assessment or PASS Preflight in this task unless a separate explicitly scoped follow-up authorizes it.

## Stop conditions

Stop and report instead of guessing if:

- `RTS-FRZ-000001` is no longer at the expected parent state;
- the next child ID allocation conflicts with newer FREEZER records;
- any input fails schema validation;
- an exact external source/ref or license boundary is contradicted by newer evidence;
- FREEZER verification reports a pre-existing failure unrelated to this task;
- any command would require selecting or starting a child;
- index/manifest rebuild would overwrite unrelated concurrent work.

## Completion line

This task is complete only when the parent v2 revision, current assessment, `DECOMPOSE_REQUIRED` preflight, five frozen child records, derived indexes, and manifest are committed and all required verification passes on the same final head.
