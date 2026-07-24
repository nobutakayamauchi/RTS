# Feature Build Bundle — Local Candidate Fixture

## Status
Evaluation fixture only. Not approved for promotion or adjacent-repository publication.

## Goal
Deliver a scoped new capability from clarified requirement to handoff-ready output while preserving an immutable local rollback target.

## Included Skills
- requirement-clarifier
- task-decomposer
- scope-locker
- safe-implementer
- verification-runner
- rollback-snapshot-writer
- handoff-writer

## Recommended Execution Order
1. requirement-clarifier (objective, constraints, acceptance criteria)
2. task-decomposer (ordered, scoped task plan)
3. scope-locker (explicit in-scope vs protected areas)
4. safe-implementer (minimal approved changes only)
5. verification-runner (verified/unverified/assumed with evidence)
6. rollback-snapshot-writer (pin the approved baseline and restoration evidence)
7. handoff-writer (continuation-ready summary)

## Expected Outputs
- Clarified requirement contract
- Ordered scoped implementation plan
- Explicit scope boundary statement
- Minimal implementation diff summary
- Evidence-backed verified/unverified/assumed report
- Immutable local rollback snapshot
- Continuation-ready handoff package

## Safety Rules
- Automatic canonical promotion is forbidden.
- Human approval is required before any promotion proposal can advance.
- Adjacent-repository mutation is forbidden by this fixture.
- Runtime and connector implementation remain out of scope.

## When Not to Use
- Tiny one-step changes with no meaningful planning overhead.
- Urgent break/fix incidents where debugging flow is primary.
