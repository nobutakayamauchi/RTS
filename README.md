# RTS

## Execution Provenance for AI Systems

AI systems reproduce output.  

RTS reproduces decision state.

RTS is a minimal Git-native protocol for structurally auditable AI execution.

---

## The One Sentence

RTS makes AI execution reconstructable.

Not observable.  
Reconstructable.

---

## The Problem

AI scales execution.

It does not scale trust.

Logs show:

- What ran
- What output was generated

Logs do not show:

- Active assumptions
- State transitions
- Escalation triggers
- Structural mutation

Weeks later, output may be reproducible.

Intent is not.

---

## What RTS Changes

RTS records execution as state transitions.

Each execution captures:

- Context
- Decision
- Constraint
- Assumption
- Action
- Outcome

The unit is not the log entry.

It is the transition.

---

## Who This Is For

RTS is for systems that must endure.

You may need RTS if you:

- Run AI in production
- Build autonomous AI workflows
- Require auditability
- Face regulatory exposure
- Conduct reproducible AI research
- Need defensible escalation evidence

If you build short-lived demos, RTS is unnecessary.

---

## Architecture

RTS consists of four structural layers:

1. Append-only session ledger (JSONL)
2. Deterministic monthly index
3. Immutable snapshot sealing
4. Breakpoint-triggered evidence snapshots

No SaaS.

No telemetry.

Git-native.

---

## Ledger Structure

### Session Ledger

Path:

sessions/YYYY-MM/session_YYYYMMDD.jsonl

Properties:

- Append-only
- One event per line
- Deterministic
- Git-tracked

---

### Monthly Index

sessions/YYYY-MM/index.json  
sessions/YYYY-MM/index.md

Aggregates:

- Run transitions
- Dangling runs
- Mutation indicators
- Evidence linkage

---

### Snapshot

sessions/YYYY-MM/index_snapshot.*

Seals structural state at a point in time.

Enables diff and replay.

---

### Evidence Snapshot (ESC)

incidents/evidence_snapshots/ESC_<date>_<rule>.md

Generated when mutation crosses a defined threshold.

Captures:

- Escalation metrics
- Mutation score
- Transition tail
- Ledger reference

---

## Escalation Logic

RTS detects structural mutation.

When mutation crosses a boundary:

- Breakpoint is flagged
- Evidence snapshot is generated
- State is sealed

This enables unambiguous reconstruction.

---

## Structural Principles

- Append-only integrity
- Git-native provenance
- Local-first execution
- Deterministic rollup
- No external telemetry
- Transparent inspection

Provenance belongs to the repository.

---

## Practical Impact

Without structural provenance:

- Decisions cannot be defended
- Failures cannot be reconstructed
- Escalation becomes guesswork

RTS restores structural continuity.

---

## Try It

cd starter/python  
python START_HERE.py

Execution provenance begins immediately.

No configuration required.

---

## Live Inspection

This repository is public.

You can:

- Inspect session ledgers
- Verify transitions
- Review evidence snapshots
- Audit escalation logic
- Clone and replay locally

Transparency over opinion.

---

## What RTS Is Not

RTS is not:

- An agent framework
- A vector database
- A monitoring dashboard
- A compliance SaaS
- A memory embedding system

It formalizes execution state.

---

## Vision

AI execution will scale.

Trust will not scale automatically.

Governance must become structural.

RTS is a minimal protocol for building that property.

---

## License

MIT License  
Copyright (c) 2026 Nobutaka Yamauchi
