# ROLLBACK_RULEBOOK.md

## Purpose
This rulebook defines how rollback safety must be preserved during repository work.

The goal is not only to recover from failure, but to ensure work is done in rollback-safe units from the start.

---

## Core Rules

### Rule 1: No non-trivial direct edits on main
Major tasks should not be performed directly on main.

### Rule 2: One task, one rollback unit
Keep each task scoped so it can be reverted as a single unit.

### Rule 3: Checkpoint before major edits
Before major edits, create a checkpoint commit or equivalent safe rollback point.

### Rule 4: Separate task classes
Do not combine:
- implementation
- organization
- fixes
into one irreversible change set unless explicitly required.

### Rule 5: Prefer discard over expansion
If a change begins to drift or fail validation, prefer rollback over broader speculative editing.

### Rule 6: Preserve history
If changes are already shared, prefer revert-style recovery over destructive history rewriting.

---

## Rollback Levels

### Level 1: Local discard
Use when uncommitted changes are wrong.
Discard only the task-local diff.

### Level 2: Branch discard
Use when an entire task branch should be abandoned.

### Level 3: Revert after merge
Use when merged work must be safely undone while preserving history.

### Level 4: Stable point return
Use a known stable checkpoint or tagged state when broader recovery is required.

---

## Operational Rollback Guidance

Before task execution, define:
- task scope
- rollback unit
- checkpoint moment
- success condition

After task execution, decide:
- accept
- revise
- discard
- revert

---

## Required Output Format
For any risky task, report:

1. rollback unit
2. checkpoint expectation
3. failure indicators
4. safest rollback action
