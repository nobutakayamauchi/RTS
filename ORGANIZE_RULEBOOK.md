# ORGANIZE_RULEBOOK.md

## Purpose
This rulebook defines how repository organization must be handled.

The goal is to reduce clutter without introducing functional breakage.

---

## Core Rules

### Rule 1: Structure work is separate from implementation work
Do not mix file organization with feature implementation unless explicitly instructed.

### Rule 2: Inventory before reorganization
Before moving files, identify:
- current top-level directories
- their apparent roles
- overlap between directories
- clutter hotspots
- files with unclear placement

### Rule 3: Preserve behavior
Organization work should not change repository behavior unless structural repair is explicitly required.

### Rule 4: Prefer minimal structural moves
Do not perform broad reorganization without a clear policy.
Move only what is justified by the approved organization plan.

### Rule 5: Preserve references
Before finalizing any move or rename, inspect:
- internal links
- relative paths
- imports
- script references
- README references
- workflow references

### Rule 6: Separate active, archived, and uncertain materials
If needed, classify files into:
- active
- pending review
- archived
- unclear / needs owner decision

### Rule 7: Report ambiguity
If file ownership or role is unclear, report it instead of forcing a guess.

---

## Organization Modes

### Mode A: Inventory Only
Use when first examining a cluttered repository.
Allowed:
- read files
- summarize roles
- identify overlap
- propose next actions

Not allowed:
- file moves
- renames
- structural edits

### Mode B: Controlled Reorganization
Use after organization policy has been approved.
Allowed:
- move files according to approved policy
- update references
- repair broken links caused by approved moves

Not allowed:
- unrelated cleanup
- logic changes
- speculative restructuring

### Mode C: Archive Pass
Use when separating inactive materials.
Allowed:
- move clearly inactive items into archive locations
- preserve traceability
- update references if needed

Not allowed:
- delete historical material unless explicitly requested

---

## Recommended Classification Pass

For each major file or folder, classify as:

- active
- support
- draft
- archive
- duplicate candidate
- unclear

---

## Forbidden During Organization
Unless explicitly requested, do not:
- rewrite logic
- redesign architecture
- rewrite docs broadly
- merge unrelated content
- delete historical records
- change naming conventions globally in the same pass

---

## Required Output Format
Each organization task should return:

1. current structure summary
2. overlap / ambiguity list
3. clutter hotspots
4. proposed classification
5. proposed moves
6. references that may break
7. safest next organization step
