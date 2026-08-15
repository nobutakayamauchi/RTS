# Development Portfolio — 2026-08-15

Status: `ACTIVE PRIORITY MAP`

This file separates immediate revenue work, recurring-revenue candidates, high-ticket B2B, large ventures, and internal development infrastructure.

## Priority map

| Priority | Product / system | Role | Current decision |
|---|---|---|---|
| S0 | BridgePatch / AI業務レスキュー | Immediate revenue | `BLOCKER_REVIEW_NOW` |
| S0 | RTS AXIS | Immediate revenue | `BLOCKER_REVIEW_NOW` |
| S1 | Post Adapter v0 | Sales/content infrastructure | `BUILD_NEXT` |
| S1 | X pain-point radar | Lead discovery infrastructure | `KEEP / CONNECT_AFTER_V0` |
| A | RTS Flight Recorder | High-ticket B2B foundation | `PRESERVE / BUILD_AFTER_REVENUE_PATH` |
| A | Debug Engine | High-ticket B2B foundation | `PRESERVE / BUILD_AFTER_REVENUE_PATH` |
| A | Repair Forge / Patch Proposal path | High-ticket B2B foundation | `PRESERVE / HUMAN_GATE_REQUIRED` |
| B | Self-hosted newsletter / AI distribution base | Recurring revenue candidate | `DEFER` |
| B | 限界開発 Vlog / video automation | Product + public development proof | `PRESERVE` |
| B1 | Real World Roguelike | Large venture | `FROZEN / NOT_SELECTED / LARGE_VENTURE_PRIORITY_1` |
| C | High Friends | Large social product | `DEFER` |
| INTERNAL | Ultimate Loop / RTS Evolution | Development factory | `USE, DO NOT EXPAND FOR ITS OWN SAKE` |
| INTERNAL | Obsidian / FREEZER / Figma bridges | External source-of-truth infrastructure | `BUILD ONLY WHEN ACTIVE WORK REQUIRES IT` |

## Revenue ladder

```text
Pain discovery / public proof
        ↓
BridgePatch fit check
        ↓
JPY 10,000 portable implementation spec
        ↓
JPY 50,000 simple-tool work
        ↓
RTS AXIS JPY 49,500 decision/priority engagement
        ↓
complex AI/system work
        ↓
Flight Recorder -> Debug Engine -> Repair/patch proposal
        ↓
higher-ticket B2B
```

The ladder is not a forced customer journey. It is the internal product map showing how existing assets can support progressively higher-value work.

## Active-cycle rule

For the current cycle, new development is allowed only when at least one is true:

1. It directly removes a BridgePatch or RTS AXIS sales blocker.
2. It is Post Adapter v0 after blocker review is complete.
3. It is required to validate or safely deliver a paid engagement already obtained.
4. It fixes an active production defect that prevents current work.

Everything else returns to the portfolio/FREEZER path instead of interrupting work in progress.

## Real World Roguelike — preserved large venture

Canonical portfolio decision:

```text
NAME: Real World Roguelike
CLASS: LARGE_VENTURE
LARGE_VENTURE_PRIORITY: 1
STATE: FROZEN
SELECTION: NOT_SELECTED
BUILD_AUTHORITY: NOT_GRANTED
CURRENT_CYCLE_IMPLEMENTATION: FORBIDDEN
```

Preserved concept boundary:

```text
real-world exploration
-> safe on-site confirmation
-> location/state evidence update
-> XP / achievement / reward
-> shared world-data improvement
-> new missions
```

Preserved monetization/design directions include sponsored/event missions, fitness missions, local business opportunities, rescue missions, field bounties, IP collaboration, and data/API value. These remain candidate directions, not promises or current build scope.

The central strategic hypothesis worth preserving is:

> Useful real-world actions can simultaneously be gameplay and evidence that improves the shared world state.

### Wake rule

Do not wake this project merely because it is exciting. Reconsider selection after the immediate revenue path has evidence and a bounded MVP can be proposed without displacing the active revenue cycle.

## Ultimate Loop / RTS rule

Ultimate Loop / RTS is treated as the factory, not the product that must become perfect before anything can be sold.

Allowed internal improvement:

> An active product reveals a missing capability that materially blocks delivery, safety, evidence, or iteration speed.

Rejected internal improvement:

> A new subsystem is interesting but does not move the active revenue or delivery path.

That rejected work belongs in FREEZER/portfolio review.
