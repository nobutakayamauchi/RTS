# RTS

## Execution Provenance for AI Systems

AI systems reproduce output.

RTS reproduces decision state — in Git.

RTS is a minimal, Git-native protocol for structurally auditable AI execution.

---

## The Claim

RTS makes AI execution reconstructable.

Not observable.  
Reconstructable.

---

## Why Now

AI agents are scaling.

Execution speed increases.  
Human oversight shrinks.

When execution scales without structural provenance, fragility becomes systemic.

RTS addresses that structural gap.

---

## What RTS Changes

Traditional logging answers:

What happened?

RTS answers:

What state was active when the decision happened?

RTS models execution as state transitions.

Each execution captures:

- Context
- Decision
- Assumptions
- Constraints
- Outcome

The unit is the transition.  
Not the log line.

---

## Who Needs This

RTS is for systems that must endure.

You may need RTS if you:

- Run AI in production
- Require auditability
- Face regulatory exposure
- Need defensible escalation evidence
- Build long-lived AI systems

Not for short-lived demos.

---

## Architecture (High Level)

RTS consists of four structural layers:

1. Append-only session ledger (JSONL)
2. Deterministic monthly index
3. Immutable snapshot sealing
4. Breakpoint-triggered evidence snapshots

Git-native.

No SaaS.  
No telemetry.

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

Example event structure:

ts → ISO8601 timestamp  
kind → sentinel.run.start / sentinel.run.end  
workflow → workflow name  
run_id → numeric identifier  
status → success / failure / cancelled  
commit → commit SHA  

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
- Structural state is sealed

This enables unambiguous reconstruction.

---

## Live Inspection

This repository is public and actively generating structural evidence.

You can:

- Inspect session ledgers
- Verify transitions
- Review evidence snapshots
- Clone and replay locally

Transparency over opinion.

If you want a live walkthrough, open an Issue.

---

## What RTS Is Not

RTS is not:

- An agent framework
- A vector database
- A monitoring tool
- A compliance SaaS

RTS formalizes execution state.

---

## Vision

AI execution will scale.

Trust must become structural.

RTS is a minimal protocol for building that structure.

---

## License

MIT License  
Copyright (c) 2026 Nobutaka Yamauchi
