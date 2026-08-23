# AGENTS.md

## Purpose
This repository is operated with ChatGPT and Codex as development collaborators.

ChatGPT is used for:
- requirement clarification
- specification drafting
- organization policy drafting
- fix policy drafting
- review support
- logging support

Codex is used for:
- implementation
- file organization
- local fixes
- path/reference updates
- test execution
- reviewable changes

This repository must remain reviewable, structured, and rollback-safe.

---

## Core Operating Principles

1. Do not edit blindly.
2. Read repository rules before acting.
3. Keep tasks small and reviewable.
4. Separate implementation tasks from organization tasks.
5. Prefer minimal valid changes.
6. Preserve rollbackability.
7. Report uncertainty instead of guessing aggressively.

---

## Task Types

### Implementation Task
Used when adding or changing behavior.

Rules:
- do not reorganize unrelated files
- do not perform broad cleanup unless explicitly requested
- follow the provided spec
- keep changes scoped to the task
- verify the implemented behavior

### Organization Task
Used when cleaning file structure, naming, placement, or archive boundaries.

Rules:
- do not change logic unless explicitly required
- focus on structure only
- identify clutter, overlap, and ambiguity
- prefer reviewable file moves
- preserve references and links

### Fix Task
Used when something is broken.

Rules:
- reproduce first
- identify the smallest likely fix surface
- do not mix repair with unrelated cleanup
- verify that the original issue is resolved
- report cause, changed files, and remaining uncertainty

---

## File Handling Rules

- Do not rename, move, merge, or split files unless the task explicitly allows it.
- Do not modify unrelated directories during a local task.
- Preserve public-facing documentation unless directly relevant.
- Do not rewrite large sections for style alone.
- Prefer incremental, reviewable changes over sweeping rewrites.

---

## Repository Safety Rules

- Never make non-trivial edits directly on main.
- Use one branch per task when possible.
- Create a checkpoint before major edits.
- Keep implementation and organization tasks separate.
- If validation fails, prefer rollback over speculative expansion.
- If uncertainty increases, stop and report.

---

## Expected Output Format

For any non-trivial task, return:

1. Task summary
2. Files inspected
3. Files changed
4. What was done
5. What was verified
6. Risks or uncertainty
7. Suggested next step

---

## Priority Order

When rules conflict, prioritize in this order:

1. repository safety
2. rollbackability
3. task scope discipline
4. correctness
5. cleanliness

---

## Default Behavior

If the task is ambiguous:
- inspect first
- summarize current structure
- identify likely safe next actions
- avoid large speculative edits

If the task is organizational:
- produce an inventory first unless explicitly told to reorganize immediately

If the task is a fix:
- reproduce and isolate before editing

If the task is implementation:
- follow spec and acceptance criteria

---

## Ultimate Loop shared runtime adapter

This repository may use the host-installed shared Ultimate Loop Codex runtime, but the shared runtime does not reopen RTS development.

When the user writes `/goal` or explicitly asks to run Ultimate Loop:

1. read `docs/CANONICAL_INDEX.md` first;
2. read `docs/audit/RTS_DEVELOPMENT_FREEZE_2026-08-09.md` and `docs/audit/RTS_FINAL_ABOLITION_GATE_2026-08.md` before proposing implementation;
3. treat the repository's current state as `FROZEN / ENDED` unless an explicit human decision authorizes a bounded reopening;
4. use the shared `ultimate-loop` skill and explicit custom roles only as an analysis/verification mechanism within that boundary;
5. do not vendor or duplicate the shared Ultimate Loop skill/custom-role files into RTS merely to enable `/goal`.

Hard rules:

- `/goal` != automatic development restart;
- historical capability != current authority to modify;
- a new idea, external capability, or benchmark result is a WATCH/DARWIN trigger candidate, not automatic permission to resume implementation;
- if the correct bounded result is KEEP/FROZEN/NO-CHANGE, stop there instead of inventing work;
- any material reopening must identify the exact frozen invariant being reconsidered, the new evidence that changes the prior decision, the permitted change surface, and the fresh Reality Gate;
- `REPOSITORY_IMPLEMENTED != CODEX_RUNTIME_VALIDATED`;
- `PROMPT NON-MUTATION != TECHNICAL READ-ONLY`.

Repository-local freeze and canonical records override generic global runtime guidance.
