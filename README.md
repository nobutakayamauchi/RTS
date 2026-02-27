# RTS

## Execution Provenance for AI Systems

AI systems reproduce output.  
RTS reproduces decision state.

RTS is a minimal Git-native protocol for making AI-assisted execution structurally auditable.

---

## The One Sentence

RTS makes AI execution structurally reconstructable.

Not observable.  
Reconstructable.

---

## The Problem

AI scales execution.  
It does not scale trust.

Traditional logs show:
- What ran
- What output was generated

They do not show:
- Which assumptions were active
- What state transitions occurred
- Why escalation logic triggered
- How structural mutation accumulated

When something breaks weeks later, output may be reproducible.

Intent is not.

---

## What RTS Changes

RTS converts execution into structured provenance blocks.

Each execution records:
- Context
- Decision
- Constraint
- Assumption
- Action
- Outcome

Execution becomes state-aware.

The unit is not the log entry.  
It is the state transition.

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

If you are building short-lived demos, RTS is unnecessary.

---

## Architecture (Minimal View)

RTS operates using four structural layers:

1. Append-only session ledger (JSONL)
2. Deterministic monthly index
3. Immutable snapshot sealing
4. Breakpoint-triggered evidence snapshots

Execution is modeled as a sequence of state transitions.

No SaaS.  
No telemetry.  
Git-native.

---

## Ledger + Index + Snapshot

### Session Ledger

Path:
sessions/YYYY-MM/session_YYYYMMDD.jsonl

Properties:
- Append-only
- One event per line
- Deterministic structure
- Git-tracked

---

### Monthly Index

Paths:
sessions/YYYY-MM/index.json
sessions/YYYY-MM/index.md

Aggregates:
- Run transitions
- Dangling runs
- Mutation indicators
- Evidence linkage

---

### Snapshot

Path:
sessions/YYYY-MM/index_snapshot.*

Purpose:
- Seal structural state at a point in time
- Enable diff and replay

---

### Evidence Snapshot (ESC)

Path:
incidents/evidence_snapshots/ESC_<date>_<rule>.md

Generated when structural mutation crosses a defined threshold.

Captures:
- Escalation metrics
- Mutation score
- Transition tail
- Ledger reference

---

## Escalation and Mutation Logic

RTS detects structural mutation.

When mutation crosses a defined boundary:
- Breakpoint is flagged
- Evidence snapshot is generated
- Structural state is sealed

This enables post-hoc reconstruction without ambiguity.

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
No external service required.

---

## Live Inspection

This repository is public.

You can:
- Inspect session ledgers
- Verify state transitions
- Review evidence snapshots
- Audit escalation logic
- Clone and replay locally

Transparency over opinion.

For walkthrough requests, open an issue.

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

Governance is not a feature.  
It is a structural property.

RTS is a minimal protocol for building that property.

---

## License

MIT License  
Copyright (c) 2026 Nobutaka Yamauchi
