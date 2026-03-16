# Organization Log

## Date
2026-03-16

## Task
Batch 1 naming normalization

## Purpose
Normalize the repository naming policy by making `analysis/` the canonical output path while preserving short-term compatibility for `analyze/index.md`.

## Task Type
Organization

## Scope
- `scripts/analyze.py`
- `.github/workflows/incident_close_from_issue.yml`

## Background
The repository had overlapping use of `analysis/` and `analyze/`, creating ambiguity in naming, outputs, workflow staging, and future structure policy.

A prior inventory pass, plan-only pass, and reference-map preparation concluded that:
- `analysis/` should become the canonical directory
- `analyze/` could not be retired immediately
- direct script and workflow consumers still depended on `analyze/index.md`

## What Was Done
- Created a checkpoint commit before edits
- Executed Batch 1 in controlled mode
- Updated `scripts/analyze.py` so canonical output targets `analysis/`
- Preserved short-term compatibility output for `analyze/index.md`
- Updated `.github/workflows/incident_close_from_issue.yml` so staging includes both:
  - `analysis/index.md`
  - `analyze/index.md`

## Files Changed
- `scripts/analyze.py`
- `.github/workflows/incident_close_from_issue.yml`

## Validation Performed
- `python scripts/analyze.py`
- `python -m py_compile scripts/analyze.py`
- repository search for `analysis/` and `analyze/`
- working tree scope check
- recent commit history check

## Result
Success

## Canonical Path Decision
- Canonical path: `analysis/`
- Temporary compatibility alias: `analyze/`

## Compatibility Status
`analyze/index.md` remains transitional and was intentionally retained for short-term compatibility.

Immediate retirement was judged unsafe because active script/workflow consumers still referenced or staged the legacy path.

## Rollback Unit
- Checkpoint commit: `9d5d17e`  
  `chore: checkpoint before batch1 naming normalization`
- Batch 1 implementation commit: `7e71e19`  
  `org: normalize analyze output to analysis with compatibility mirror`

## Safest Rollback Action
- Pre-merge: discard branch or reset to checkpoint
- Post-merge: revert implementation commit while preserving history

## Risks / Remaining Issues
- `analyze/index.md` may still be consumed externally outside the repository
- Full retirement of `analyze/` requires confirmation that all direct repo, workflow, and external consumers have migrated to `analysis/`
- This pass intentionally did not include:
  - root-doc normalization
  - archive/evidence cleanup
  - broader structural reorganization

## Related Documentation Updates
A documentation-only synchronization pass was completed after Batch 1.

Updated files:
- `STRUCTURE_MAP.md`
- `CONTRIBUTING.md`

Documented policy:
- `analysis/` is canonical
- `analyze/` is temporary compatibility only
- no new canonical references should target `analyze/`

## Suggested Next Step
Add a short deprecation criterion note defining when `analyze/` can be formally retired, then proceed to Batch 2 root-doc normalization.
