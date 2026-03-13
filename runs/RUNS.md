# RTS Runs

This document defines the role of the `runs/` directory in RTS.

The `runs/` directory stores structured execution records.

RTS does not treat runs as temporary notes.
Runs are operational evidence.

---

## Purpose

A run record preserves how a specific execution process unfolded.

Each run may include:

- context
- decision
- constraints
- assumptions
- action
- outcome

This allows later reconstruction of execution history.

---

## Run Types

RTS currently recognizes two practical run categories.

### Example Runs

Example runs are illustrative records.

They exist to demonstrate the RTS format and make the protocol easier to understand.

Examples:

- RUN_EXAMPLE_001.md

### Verified Runs

Verified runs are operational records created from real execution activity.

They serve as evidence-bearing historical artifacts.

Examples:

- RUN_VERIFIED_GOLD_001.md

---

## Naming Convention

Run files should follow a stable naming rule.

Recommended patterns:

RUN_EXAMPLE_001.md
RUN_VERIFIED_GOLD_001.md

Future extensions may introduce:

RUN_YYYY_0001.md

---

## Structural Principle

Runs are append-oriented historical records.

They are not intended to be silently rewritten after the fact.

If interpretation changes, create a new run or an additional record rather than erasing prior structure.

---

## Why Runs Matter

RTS preserves decision reconstructability.

The `runs/` directory is one of the primary places where that reconstructability becomes visible.

Without runs, execution becomes memory loss.
With runs, execution becomes evidence.

---

## Relationship to RTS

RTS defines the protocol.

RTS examples demonstrate usage.

Runs provide operational history.

Together, they form:

Protocol
Examples
Evidence

---

## Status

The `runs/` directory is an active operational layer of RTS.
