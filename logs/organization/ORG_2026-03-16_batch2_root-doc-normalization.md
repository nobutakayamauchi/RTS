# Organization Log

## Date
2026-03-16

## Task
Batch 2 root-doc normalization

## Purpose
Execute a small, safe root-level documentation normalization pass by moving clearly explanatory/spec/rulebook documents from the repository root into appropriate `docs/` subtrees, while preserving the root as the public and operational entry shell.

## Task Type
Organization

## Scope
Move only a very small set of clearly non-entry explanatory documents from root into existing `docs/` subtrees.

## Background
The repository organization plan defined Batch 2 as a root-doc normalization pass.

The root layer should remain focused on:
- public entrypoints
- operational shell files
- rulebooks required for immediate operator use
- static site/public interface files

Non-entry explanatory documents were identified as move candidates to reduce root-level discoverability noise.

## What Was Done
- Created a checkpoint commit before edits
- Executed a single small reorganization commit
- Moved the following files:
  - `RTS_SPEC.md` → `docs/spec/RTS_SPEC.md`
  - `genesis_smartphone.md` → `docs/genesis/genesis_smartphone.md`
  - `operator_rulebook_jp_v1_0.md` → `docs/rulebook/operator_rulebook_jp_v1_0.md`

## Why These Files Were Chosen
These files were selected as the first safe move-candidate set because:
- they are clearly explanatory/spec/rulebook documents
- they are not runtime, code, workflow, or operational shell files
- they match the structure policy that explanatory/expansion materials should live under `docs/`
- they fit within the "small pass" constraint for Batch 2

## Files Moved
- `RTS_SPEC.md` → `docs/spec/RTS_SPEC.md`
- `genesis_smartphone.md` → `docs/genesis/genesis_smartphone.md`
- `operator_rulebook_jp_v1_0.md` → `docs/rulebook/operator_rulebook_jp_v1_0.md`

## References Updated
None required in this pass.

No direct in-repository references to the old root paths were detected for these three files during this move set.

## Files Intentionally Kept at Root
The following classes of files were intentionally preserved at root:
- public/operational entry files such as `README.md`
- security / charter / structure control files such as:
  - `SECURITY.md`
  - `SENTINEL_CHARTER.md`
  - `STRUCTURE_MAP.md`
- static entry files such as:
  - `index.md`
  - `index.html`
  - `search.html`
  - `search_index.json`
- rulebooks and operator-control documents such as:
  - `AGENTS.md`
  - `ORGANIZE_RULEBOOK.md`
  - `FIX_RULEBOOK.md`
  - `ROLLBACK_RULEBOOK.md`

## Validation Performed
- checkpoint commit created before the pass
- `git mv` used for each moved file
- repository search for direct references to old root paths
- staged name-status diff reviewed
- root-level inventory checked after move
- working tree status checked
- recent commit history checked

## Result
Success

## Rollback Unit
- Checkpoint commit: `a7897d0`  
  `chore: checkpoint before batch2 small root-doc normalization`
- Batch 2 implementation commit: `b310a95`

## Safest Rollback Action
- Pre-merge: discard branch or reset to checkpoint
- Post-merge: revert `b310a95` while preserving history

## Risks / Remaining Issues
- External consumers outside the repository may still reference the old root paths
- Local repository search did not detect in-repo references, but external links cannot be fully proven absent from local search alone
- This pass intentionally did not include:
  - code logic changes
  - workflow redesign
  - archive/evidence cleanup
  - broader root cleanup beyond the first 3-file move set

## Related Notes
The diff view in Codex may show additional files when comparing across the full branch range. The actual Batch 2 move set is limited to the three moved files above; broader branch diffs may include prior Batch 1 and docs-sync changes.

## Suggested Next Step
Proceed to Batch 3: define and execute a controlled archive/evidence boundary cleanup for:
- `sessions/`
- `incidents/evidence_snapshots/`

This should begin with a policy-confirmation / prep pass before any move execution.
