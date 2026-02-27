# RTS

## Execution Provenance for AI Systems

AI systems reproduce output.

RTS reproduces decision state — in Git.

If you cannot reconstruct a decision,
you cannot defend it.
If you cannot defend it,
you cannot scale it.

RTS is a minimal, Git-native protocol
for structurally auditable AI execution.

---

## The Claim

RTS makes AI execution reconstructable.
Accountability is impossible without reconstructability.
Not observable.
Reconstructable.

---

## Why Now

AI agents are scaling.
Execution speed increases.
Human oversight shrinks.

When execution scales without structural provenance, fragility becomes systemic.
## Quick Try (60 seconds)

You can verify RTS immediately.

1. Open any `sessions/YYYY-MM/index.md`
2. Pick a run
3. Trace it to its ledger entries
4. Confirm whether an ESC exists

If decision state is structurally reconstructable,
RTS is working.

No setup.
No installation.
Just inspection.
RTS addresses that structural gap.
---

## When You Actually Need RTS

You likely need RTS if at least one of these is true:

- You can reproduce output but cannot explain why it happened.
- Logs show what ran but not which assumptions were active.
- AI workflows branch or mutate mid-session and context gets lost.
- Weeks later you cannot reconstruct the original decision environment.
- Stakeholders require justification, not just results.

If none apply, RTS is unnecessary.
If one applies, you probably already need it.

---

## What RTS Changes

Traditional logging answers:

What happened?

RTS answers:

What state was active when the decision happened?

RTS models execution as structural state transitions.

Each execution captures:

- Context
- Decision
- Assumptions
- Constraints
- Outcome

The unit is the transition.
Not the log line.
---

## ASC2 - Structural Breakpoint Model

RTS does not alert on noise.
It detects structural mutation.

When mutation density crosses a defined boundary:

- Breakpoint is flagged
- Structural state is sealed
- Evidence snapshot (ESC) is generated
- Ledger and metrics become immutable reference

This converts instability into inspectable structure.

Not monitoring.
Structural mutation control.

---

## Real Failure Scenario

An AI system approves an escalation in production.

Two weeks later, a regulator asks:

"Why was this allowed?"

You can reproduce the output.
You cannot reproduce the decision state.

RTS makes that state reconstructable.
---

## What RTS Produces

RTS generates four structural artifacts:

1. Session Ledger (JSONL)
2. Monthly Index
3. Snapshot
4. Evidence Snapshot (ESC)

Git-native.
No SaaS.
No telemetry.
## Architectural Scope

RTS guarantees structural reconstructability of AI execution states.

This guarantee is intentionally narrow.

RTS does not validate ethics, legality, policy correctness, or outcome quality.

RTS ensures that decision state is never structurally lost.

Semantic guarantees require additional layers.
RTS provides the base layer those systems depend on.
---

## Repository Structure

### Sessions

- sessions/YYYY-MM/session_YYYYMMDD.jsonl
- sessions/YYYY-MM/index.json
- sessions/YYYY-MM/index.md
- sessions/YYYY-MM/index_snapshot.json
- sessions/YYYY-MM/index_snapshot.md

### Evidence

- incidents/evidence_snapshots/ESC_*.md

If you inspect only two directories:

- sessions/
- incidents/evidence_snapshots/

You will understand RTS.

---

## ESC (Evidence Snapshot)

Generated only when structural mutation crosses threshold.

Each ESC includes:

- Escalation metrics
- Mutation score
- Transition tail
- Ledger reference

This is permanent structural evidence.
---

## How To Verify RTS

Do not trust claims. Inspect artifacts.

1. Open `sessions/YYYY-MM/index.md`
2. Trace linked ledger entries
3. Confirm ESC exists when breakpoint occurs
4. Diff snapshot states

If it cannot be verified from artifacts, it is not RTS.

---

## How To Adopt RTS

Minimum integration:

1. Append run start / run end events to JSONL
2. Roll up deterministic monthly index
3. Generate ESC only when breakpoint is crossed

No platform dependency required.

---

## Who Needs This

RTS is for systems that must endure.

You likely need it if you:

- Run AI in production
- Require auditability
- Face regulatory exposure
- Need defensible escalation evidence
- Build long-lived AI systems

Not for short-lived demos.

---

## Live Inspection

This repository is public and actively generating structural evidence.

You can:

- Inspect ledgers
- Verify transitions
- Review ESC files
- Clone and replay locally

Transparency over opinion.

For walkthrough requests, open an Issue.

---

## What RTS Is Not

RTS is not:

- An agent framework
- A vector database
- A monitoring tool
- A compliance SaaS

RTS formalizes execution state.

---
## Future Extensions

Because execution state becomes reconstructable and immutable,
higher-order governance systems become technically possible.

Such layers may include:

- Tamper-evident verification
- Policy deviation detection
- Escalation accountability models
- Organizational responsibility flows

RTS does not provide these today.

It provides the structural condition required to build them.

## Future Extensions

Because execution state becomes reconstructable and immutable,
higher-order governance systems become technically possible.

These may include:

- Tamper-evident verification
- Policy deviation detection
- Escalation accountability models
- Organizational responsibility flows

RTS does not provide these today.

It provides the structural condition required to build them.
## Vision

AI execution will scale.  
Trust will not scale automatically.

Governance must become structural.

RTS is a minimal protocol for building that structure.

---

## License

MIT License  
Copyright (c) 2026 Nobutaka Yamauchi
