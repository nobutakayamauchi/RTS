# RTS Ecosystem Project Registry

This registry records the current rescue classification of repositories around RTS.

It is a working registry, not a protocol change.

The purpose is to prevent frozen, half-built, inactive, or adjacent repositories from becoming ambiguous debt.

## Classification Labels

- ACTIVE: continue using or maintaining now
- CANON: canonical reference point
- REFERENCE: minimal reference implementation or proof
- RESCUE: valuable but needs boundary stabilization
- MONEY-LINE: closest to revenue-producing workflow
- SALES-LP: external sales surface
- PRODUCT: independent product candidate
- PROFILE: public identity and ecosystem entry point
- PARTS: reusable component shelf
- FREEZE: keep but do not actively develop now
- REVIEW BEFORE USE: do not resume without a concrete review task
- DO NOT ACTIVATE: preserve only as research or history unless explicitly re-scoped
- INACTIVE: keep minimal unless a future purpose is defined

## Active / Canonical

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| RTS | ACTIVE / CANON | Canonical protocol and structural ledger | Keep core stable; maintain ecosystem map |
| RTS-Minimal-Runtime | ACTIVE / REFERENCE | Minimal reconstructable runtime proof | Keep small; avoid feature expansion |
| RTS-AGE | RESCUE / GATEWAY | Agentic gateway and execution lab | Stabilize gateway/provider boundary |
| RTS-minicompany | ACTIVE / MONEY-LINE | Solo business operation MVP | Validate local CLI and human approval workflow |
| rts01-offer | ACTIVE / SALES-LP | Static offer landing page | Keep offer aligned with delivery workflow |
| seminar-compass | ACTIVE / PRODUCT | Learning reconstruction product candidate | Validate local test/app path and output contract |
| nobutakayamauchi | ACTIVE / PROFILE | Public profile and RTS positioning surface | Keep aligned with current RTS ecosystem position |

## Parts / Extension Shelves

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| RTS-Skills- | PARTS / SKILLS | Reusable operational skills | Later skill inventory pass |
| RTS-MCP-Packs | PARTS / CONNECTOR-PACKS | Connector pack definitions | Later pack inventory pass |
| RTS-Hermes-Drive | PARTS / ORCHESTRATION | Orchestration bridge | Later relationship review with Skills/Packs |
| RTS-Design-Research | PARTS / DESIGN-LAYER | Design research extension | Later design decision workflow review |
| rts-dev-protocol | PARTS / DOCTRINE | Structure-first development notes | Extract useful doctrine into stable docs if needed |

## Frozen / Review-Only Shelves

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| RTS-Talent-Registry | FREEZE / GOVERNANCE-REGISTRY / REVIEW BEFORE USE | Governance registry concept | Leave frozen unless a governance review task exists |
| RTS-Signal-Feeds | FREEZE / SIGNAL-SKELETON / REVIEW BEFORE USE | Non-executable signal skeleton | Leave frozen unless a signal review task exists |
| rts-video-flow | FREEZE / VIDEO-WORKFLOW / REVIEW BEFORE USE | Local video workflow prototype | Leave frozen unless a video workflow review task exists |
| AIX | FREEZE / TRADING-LAB / DO NOT ACTIVATE | Private research scaffold | Keep separate from RTS business/product line |

## Inactive / Minimal Repositories

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| codex-connector-test | ARCHIVE / TEST-FIXTURE / REVIEW ONLY | Connector test sandbox | Keep only if future connector checks need it |
| ryoushuushotesutoyou | PRIVATE TEST / REVIEW ONLY | One-off receipt/output test | Treat as outside the active RTS ecosystem |
| rts-lite | INACTIVE / EMPTY PLACEHOLDER / REVIEW ONLY | Empty lightweight placeholder | Use RTS-Minimal-Runtime instead for minimal RTS reference work |

## Promotion Rule

A repository may move from PARTS, FREEZE, or INACTIVE to ACTIVE only after:

1. Its role is documented.
2. Its relation to RTS core is clear.
3. It has a status document.
4. It has a next safe task.
5. It does not require changing RTS core to become useful.
6. It has a concrete current reason to be active.

## Removal Rule

A repository should not be removed only because it is inactive.

Removal or archival review is appropriate when:

1. The repository is a pure test artifact.
2. It has no reusable code, documentation, or decision history.
3. It is superseded by a clearer repository.
4. The operator confirms it has no remaining practical value.

## Current Rescue State

Completed in this rescue pass:

1. RTS-AGE rescue boundary
2. RTS-minicompany money-line boundary
3. seminar-compass product boundary
4. rts01-offer sales surface boundary
5. RTS-Minimal-Runtime reference lock
6. component shelf inventory locks
7. frozen/review-only shelf locks
8. inactive/minimal repository labels
9. profile ecosystem summary refresh

Recommended next:

1. Keep daily focus on `RTS-minicompany` and `rts01-offer`.
2. Use `RTS-AGE` only for concrete implementation assistance.
3. Keep component shelves inactive unless pulled into a specific task.
4. Leave frozen and inactive repositories alone unless a review task exists.
