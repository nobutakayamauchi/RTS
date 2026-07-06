# RTS Ecosystem Project Registry

This registry records the current rescue classification of repositories around RTS.

It is a working registry, not a protocol change.

The purpose is to prevent frozen, half-built, or adjacent repositories from becoming ambiguous debt.

## Classification Labels

- ACTIVE: continue using or maintaining now
- CANON: canonical reference point
- REFERENCE: minimal reference implementation or proof
- RESCUE: valuable but needs boundary stabilization
- MONEY-LINE: closest to revenue-producing workflow
- SALES-LP: external sales surface
- PRODUCT: independent product candidate
- PARTS: reusable component shelf
- FREEZE: keep but do not actively develop now
- ARCHIVE CANDIDATE: likely keep only for history/testing
- DELETE CANDIDATE: safe to delete after final operator confirmation

## Active / Canonical

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| RTS | ACTIVE / CANON | Canonical protocol and structural ledger | Keep core stable; maintain ecosystem map |
| RTS-Minimal-Runtime | ACTIVE / REFERENCE | Minimal reconstructable runtime proof | Keep small; avoid feature expansion |
| RTS-AGE | RESCUE / GATEWAY | Agentic gateway and execution lab | Stabilize gateway/provider boundary |
| RTS-minicompany | ACTIVE / MONEY-LINE | Solo business operation MVP | Validate local CLI and human approval workflow |
| rts01-offer | ACTIVE / SALES-LP | Static offer landing page | Document delivery workflow relation |
| seminar-compass | ACTIVE / PRODUCT | Learning reconstruction product candidate | Validate local test/app path and output contract |
| nobutakayamauchi | ACTIVE / PROFILE | Public profile and RTS positioning surface | Keep aligned with current RTS ecosystem position |

## Parts / Extension Shelves

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| RTS-Skills | PARTS / SKILLS | Reusable operational skills | Later skill inventory pass |
| RTS-MCP-Packs | PARTS / CONNECTOR-PACKS | Connector pack definitions | Later pack inventory pass |
| RTS-Hermes-Drive | PARTS / ORCHESTRATION | Orchestration bridge | Later relationship review with Skills/Packs |
| RTS-Design-Research | PARTS / DESIGN-LAYER | Design research extension | Later design decision workflow review |
| rts-dev-protocol | PARTS / DOCTRINE | Structure-first development notes | Extract useful doctrine into stable docs if needed |

## Frozen / Later Review

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| RTS-Talent-Registry | FREEZE / GOVERNANCE-PARTS | AI talent governance registry | Keep for later ecosystem governance review |
| RTS-Signal-Feeds | FREEZE / SIGNAL-PARTS | Signal intelligence layer | Keep for later signal workflow review |
| rts-video-flow | FREEZE / MEDIA-PARTS | Video workflow scaffold | Keep for later media workflow review |
| AIX | FREEZE / RESEARCH | Execution-aware arbitrage research scaffold | Keep separate from RTS business/product line |

## Archive / Delete Candidates

| Repository | Status | Role | Next Safe Action |
|---|---|---|---|
| codex-connector-test | ARCHIVE CANDIDATE | Connector test repository | Archive after confirming no active dependency |
| ryoushuushotesutoyou | DELETE CANDIDATE | Receipt image/output test | Delete or archive after final operator confirmation |
| rts-lite | ARCHIVE / DELETE CANDIDATE | Empty or obsolete lightweight placeholder | Delete or archive after confirming no active dependency |

## Promotion Rule

A repository may move from PARTS or FREEZE to ACTIVE only after:

1. Its role is documented.
2. Its relation to RTS core is clear.
3. It has a Minimum Alive status document.
4. It has a next safe task.
5. It does not require changing RTS core to become useful.

## Deletion Rule

A repository should not be deleted only because it is inactive.

Deletion is appropriate when:

1. The repository is a pure test artifact.
2. It has no reusable code, documentation, or decision history.
3. It is superseded by a clearer repository.
4. The operator confirms it has no remaining practical value.

## Current Rescue Order

Completed or in progress:

1. RTS-AGE
2. RTS-minicompany
3. seminar-compass
4. rts01-offer
5. RTS ecosystem map / registry

Recommended next:

1. RTS-Minimal-Runtime status lock
2. RTS-Skills inventory pass
3. RTS-Design-Research inventory pass
4. Archive/delete candidate confirmation
