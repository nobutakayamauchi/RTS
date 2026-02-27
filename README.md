# RTS

## Execution Provenance for AI Systems

AI systems can reproduce output.  
Can you reproduce the decision state?

RTS is a minimal Git-native protocol for making AI-assisted execution structurally auditable.

---

## How to Read This Document

RTS is layered. You do not need to read everything.

### If you are an AI engineer

Read:
- Why Logging Was Not Enough  
- State Transition Model  
- Ledger + Index + Snapshot Architecture  

### If you are a startup founder or product owner

Read:
- What Problem RTS Solves  
- Practical Impact  
- Live Inspection  

### If you are a researcher or governance-focused

Read:
- Structural Principles  
- Escalation and Evidence Model  

### If you are implementation-focused

Jump directly to:
- Ledger + Index + Snapshot Architecture  

### Minimal Reading Path

If you read only three sections, read:

1. Why Logging Was Not Enough  
2. State Transition Model  
3. Evidence Snapshot Logic  

That is the core of RTS.

---

## Why RTS Exists

As AI-assisted execution scales, decision context disappears.

Logs show:

- What ran  
- What output was generated  

They do not show:

- Which assumptions were active  
- What state transitions occurred  
- Why escalation logic triggered  
- How structural mutation accumulated  

When something breaks weeks later, output may be reproducible.

Intent is not.

RTS preserves structural continuity.

---

## Why Logging Was Not Enough

Traditional logging answers:

What happened?

RTS attempts to answer:

What state was active when the decision happened?

This distinction becomes critical when:

- AI agents branch execution paths  
- Assumptions mutate mid-session  
- Escalation depends on prior state  
- Behavioral drift accumulates silently  

Structured logs capture events.

RTS models state transitions.

The unit is not the log entry.  
It is the transition.

---

## What Problem RTS Solves

When AI replaces manual execution, human responsibility does not disappear.

You still must:

- Defend decisions  
- Explain failures  
- Audit escalation  
- Answer stakeholders  

Without structural provenance, this becomes guesswork.

RTS converts execution into a reconstructable ledger.

---

## State Transition Model

RTS treats execution as:

- Append-only session ledger in JSONL format  
- Deterministic monthly aggregation  
- Immutable snapshot sealing  
- Breakpoint-based mutation detection  
- Evidence snapshot extraction  

Execution is modeled as a sequence of state transitions.

Not monitoring.  
Not orchestration.  
Not observability.

Execution provenance.

---

## Ledger + Index + Snapshot Architecture

### Session Ledger

Path:

sessions/YYYY-MM/session_YYYYMMDD.jsonl

Characteristics:

- Append-only  
- Git-tracked  
- One event per line  
- Deterministic structure  

### Monthly Index

Paths:

sessions/YYYY-MM/index.json  
sessions/YYYY-MM/index.md  

Aggregates:

- Run transitions  
- Dangling runs  
- State mutation indicators  
- Evidence linkage  

### Snapshot

Path:

sessions/YYYY-MM/index_snapshot.*

Purpose:

- Seals point-in-time structural state  
- Enables diff and replay  

### Evidence Snapshot (ESC)

Path:

incidents/evidence_snapshots/ESC_<date>_<rule>.md  

Generated when a structural breakpoint is detected.

Captures:

- Escalation metrics  
- Mutation score  
- Transition tail  
- Ledger reference  

---

## Escalation and Mutation Logic

RTS detects structural mutation thresholds.

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

RTS may be relevant if you:

- Build autonomous AI workflows  
- Run AI in production systems  
- Require auditability  
- Face regulatory uncertainty  
- Conduct reproducible AI research  
- Need defensible escalation evidence  

If you are building short-lived demos, RTS is unnecessary.

RTS is for systems that must endure.

---

## Try It

cd starter/python  
python START_HERE.py  

Execution provenance begins immediately.

No external service required.

---

## Live Inspection

This repository is public.

You may:

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
