# Thin RTS — MOVABLE FRAME / DARWIN ARENA

Timestamp: **2026-08-11 20:23 JST**

Status: `POST_IMPLEMENTATION_LIFECYCLE_SPEC / FROZEN_FOR_USE`

Formal name: **DARWIN ARENA — Continuous Replacement Survival Loop**

This specification defines what happens **after** a responsibility has survived necessity destruction, concrete implementation destruction, and formal promotion.

It extends the successor RTS lifecycle beyond first implementation.

## 1. Founding rule

`IMPLEMENTED != PERMANENT`

`PROMOTED != IMMUNE`

`WORKED_ONCE != BEST_AVAILABLE_NOW`

A promoted implementation earns a place in the system, not a permanent right to keep that place.

Every replaceable responsibility should live inside a **Movable Frame**: a stable logical slot whose occupant can be replaced without rewriting the whole system when a materially better survivor appears.

## 2. Full three-stage survival lifecycle

The successor RTS development lifecycle is:

### Gate 1 — Necessity Survival

`RAISON D'ÊTRE DESTROY LOOP`

Question:

> Should this responsibility exist at all?

Kill unnecessary outcomes, externalize what already exists, and preserve only the irreducible responsibility.

### Gate 2 — Concrete Reality Survival

`METEOR CRUCIBLE — Reality Survival Loop`

Question:

> Can this exact concrete implementation survive reality better than its alternatives?

Materialize the strongest external/composed candidate and the smallest justified custom/glue candidate, then attack them with the same frozen workload.

Only surviving concrete responsibilities may be formally promoted.

### Gate 3 — Post-Implementation Evolution

`DARWIN ARENA — Continuous Replacement Survival Loop`

Question:

> Does the current occupant still deserve this slot now that a credible challenger exists?

The incumbent may survive, be recomposed, be partially replaced, or die.

## 3. Movable Frame model

A Movable Frame is a stable responsibility contract, not a permanent implementation.

Each frame should identify:

- `FRAME_ID`;
- required outcome / responsibility;
- accepted inputs and outputs;
- evidence and verification contract;
- authority boundary;
- state ownership boundary;
- privacy/security boundary;
- migration/export/import contract where state exists;
- current occupant identity/version;
- current baseline workload and known limitations;
- rollback/recovery path;
- lineage / predecessor reference.

The frame should be as implementation-neutral as practical.

Examples of possible occupants include:

- an external SaaS/API;
- an OS/native capability;
- an OSS/CLI tool;
- an AI/tool composition;
- a Thin RTS glue component;
- a hybrid composition.

## 4. Challenger triggers

DARWIN ARENA does not run continuously for novelty.
A challenger enters only when a material trigger exists, such as:

- a new external product/tool/API/OSS capability becomes available;
- an existing dependency gains a materially useful capability;
- a provider changes price, terms, API, reliability, or security posture;
- the incumbent fails a real workload;
- repeated operator friction appears;
- a security/privacy weakness is discovered;
- maintenance burden becomes material;
- a new composition removes custom code;
- a new custom minimum demonstrably closes a surviving external gap;
- schema/platform/runtime evolution makes the incumbent stale;
- a real-world event produces a materially new failure class.

`NEW EXISTS != CHALLENGE REQUIRED`.

A challenger must have a plausible material advantage before consuming comparison work.

## 5. Arena entry

The challenger is first assembled into a materially exercisable candidate.

Then compare:

- `INCUMBENT` — current promoted occupant;
- `CHALLENGER` — new external/composed/custom/hybrid candidate.

Both receive:

1. the same frozen regression workload that originally justified the frame;
2. all known adversarial cases accumulated since promotion;
3. any new real workload that triggered the challenge;
4. the same evidence requirements and authority constraints.

The incumbent does not win merely because migration is inconvenient.
The challenger does not win merely because it is newer.

## 6. Arena scoring

Compare whole-life fitness, not one benchmark number.

Material axes include:

- outcome correctness;
- failure visibility;
- security/privacy;
- recoverability;
- evidence/reconstructability;
- operator burden;
- maintenance burden;
- integration complexity;
- provider dependence / lock-in;
- migration risk;
- runtime/resource cost;
- monetary cost;
- performance where material;
- legal/procedural compatibility where material;
- long-term format/schema survivability.

A challenger should replace the incumbent only when the **total system outcome** is materially better or when the incumbent has a material uncontained defect.

## 7. Arena loop

For every material challenge:

`TRIGGER`
→ `ASSEMBLE CHALLENGER`
→ `IDENTITY / BASELINE BOTH CANDIDATES`
→ `RUN SAME WORKLOAD`
→ `ATTACK BOTH`
→ `AUTOPSY FAILURES`
→ `COUNTER-DA`
→ `PATCH / RECOMPOSE / CONTAIN IF JUSTIFIED`
→ `RETEST SAME WORKLOAD`
→ `COMPARE WHOLE-LIFE FITNESS`
→ `SURVIVAL VERDICT`

Continue rotated attacks while materially new failure classes appear.

Stop at:

`SEARCH_SATURATED_UNDER_CURRENT_EVIDENCE`

## 8. Survival verdicts

Per frame:

- `INCUMBENT_SURVIVES`
- `CHALLENGER_REPLACES_INCUMBENT`
- `HYBRID_RECOMPOSITION_SURVIVES`
- `PARTIAL_REPLACEMENT`
- `BOTH_DIE_REOPEN_NECESSITY`
- `EVIDENCE_INSUFFICIENT`

A replacement verdict must identify the exact responsibility rows that move.

## 9. Replacement / death procedure

If the incumbent loses:

1. preserve its final identity, version and deployed/runtime evidence;
2. preserve the reason it lost;
3. preserve material failure/autopsy evidence;
4. preserve migration/compatibility assumptions;
5. export state through the frame contract where state exists;
6. install the winner under explicit authority;
7. re-establish Deployment Identity;
8. replay the frozen workload against the promoted replacement;
9. verify rollback/recovery where material;
10. mark the predecessor `RETIRED`, `ARCHIVED`, or `DEAD` with lineage linkage.

No silent replacement.

`REPLACEMENT_DECISION != DEPLOYMENT_AUTHORITY`.

## 10. Safe state migration

A movable frame must not pretend every component is stateless.

Where state exists, replacement requires explicit treatment of:

- canonical vs derived state;
- export format;
- import/reconstruction path;
- schema/version compatibility;
- secrets/credentials;
- evidence/custody preservation;
- incomplete migration;
- rollback boundary;
- dual-write or shadow period only when justified.

If state cannot be safely migrated or reconstructed, the challenger may lose despite otherwise better functionality.

## 11. Shadow / duel mode

Where practical and authorized, a challenger may run in shadow mode before replacement:

`SAME INPUT`
→ `INCUMBENT RESULT`
→ `CHALLENGER RESULT`
→ `COMPARE WITHOUT GRANTING CHALLENGER AUTHORITY`

Shadow execution must not duplicate external side effects, submissions, spending, disclosure, production mutation, or other irreversible action merely for comparison.

For side-effecting responsibilities, use simulation, replay, read-only observation, bounded canary, or another safe equivalent where possible.

## 12. No sunk-cost protection

Historical investment grants no survival right.

`WE BUILT IT != WE KEEP IT`

If an external/composed replacement now performs the responsibility better at lower whole-life burden, the custom implementation may be retired.

Likewise:

`EXTERNAL FIRST != EXTERNAL FOREVER`.

If an external dependency becomes materially worse and a smaller custom/hybrid replacement now wins the same workload, externalization may lose its slot.

## 13. Frame inheritance

When a new occupant survives, it inherits:

- the frame's frozen regression workload;
- known failure classes;
- unresolved limitations;
- required authority boundaries;
- evidence/recovery obligations;
- predecessor autopsy lessons.

The winner does not reset history.

`NEW OCCUPANT != NEW MEMORY`.

## 14. Real-world reopening

After promotion, normal use remains part of the evolutionary process.

A real failure may trigger:

`OBSERVED FAILURE`
→ `AUTOPSY`
→ `PATCH / CONTAIN / RECOMPOSE / CHALLENGER`
→ `DARWIN ARENA`

If the failure challenges the need itself rather than only the occupant, reopen Gate 1.

If the need survives but the occupant fails, reopen Gate 2 or Gate 3 as appropriate.

## 15. Relationship to successor RTS

The successor RTS is therefore not a static stack.

It is a set of **replaceable responsibility frames** whose occupants have different survival histories.

Architecture goal:

`STABLE OUTCOME CONTRACTS + REPLACEABLE IMPLEMENTATIONS + PRESERVED LINEAGE`

not:

`PERMANENT COMPONENT TREE`.

## 16. Lifecycle summary

`IDEA / WISH`
→ `PROTOTYPE SWARM`
→ `GATE 1: RAISON D'ÊTRE DESTROY LOOP`
→ `SURVIVING RESPONSIBILITY`
→ `REALITY A / REALITY B / JUSTIFIED HYBRID`
→ `GATE 2: METEOR CRUCIBLE`
→ `PROMOTED SURVIVOR`
→ `MOVABLE FRAME OCCUPANT`
→ `REAL USE`
→ `MATERIAL CHALLENGER OR FAILURE`
→ `GATE 3: DARWIN ARENA`
→ `SURVIVE / RECOMPOSE / REPLACE / DIE`
→ `NEW BASELINE + INHERITED HISTORY`
→ repeat.

## 17. Final invariant

**Nothing is immortal. The responsibility may survive while its implementation dies.**

The system evolves by preserving outcomes and lessons, not by preserving code for its own sake.
