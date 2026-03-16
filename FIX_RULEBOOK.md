# FIX_RULEBOOK.md

## Purpose
This rulebook defines how breakage and bug fixing must be handled.

The goal is to repair safely, minimize collateral damage, and preserve rollbackability.

---

## Core Rules

### Rule 1: Reproduce first
Before editing, identify:
- what is broken
- where it is broken
- expected behavior
- actual behavior
- how to reproduce the issue

### Rule 2: Prefer the smallest valid fix
Fix the narrowest likely surface first.

### Rule 3: Do not mix fix and cleanup
Do not reorganize or broadly clean up unrelated files during a fix task.

### Rule 4: Check impact surface
Inspect:
- imports
- links
- config references
- scripts
- workflows
- related docs

### Rule 5: Verify after editing
After changes, verify:
- original issue is resolved
- no obvious regression is introduced
- syntax / formatting is still valid
- paths and references still work

### Rule 6: Report uncertainty
If the cause is not clear, stop broad speculation and report likely causes.

### Rule 7: Keep rollback easy
Use reviewable edits and preserve a clean rollback path.

---

## Fix Modes

### Mode A: Hotfix
Use when urgent.
- minimal change only
- restore working state first
- no unrelated cleanup

### Mode B: Normal Fix
Use for standard repairs.
- reproduce
- isolate
- minimally fix
- verify

### Mode C: Structural Fix
Use only when structure itself is the cause.
- identify structural root cause
- separate urgent repair from broader cleanup
- keep the change reviewable

---

## Forbidden During Fix
Unless explicitly requested, do not:
- reorganize directories
- rename files globally
- refactor large sections for style
- redesign architecture
- change public docs broadly

---

## Required Output Format
Each fix task should return:

1. issue summary
2. reproduction path
3. suspected cause
4. files changed
5. exact fix applied
6. verification performed
7. remaining risk / uncertainty
