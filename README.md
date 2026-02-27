RTS

Execution Provenance for AI Systems

AI systems reproduce output.
RTS reproduces decision state — in Git.

RTS is a minimal, Git-native protocol for structurally auditable AI execution.

⸻

The Claim

RTS makes AI execution reconstructable.

Not observable.
Reconstructable.

⸻

Why Now

AI agents are scaling.
Execution speed increases.
Human oversight shrinks.

When execution scales without structural provenance, fragility becomes systemic.

RTS addresses that structural gap.

⸻

When You Actually Need RTS

You likely need RTS if at least one of these is true:
	•	You can reproduce output, but cannot explain why it happened.
	•	Logs show what ran, but not which assumptions were active.
	•	AI workflows branch or mutate mid-session and context gets lost.
	•	Weeks later, you cannot reconstruct the original decision environment.
	•	Stakeholders require justification, not just results.

If none apply, RTS is unnecessary.
If one applies, you probably already need it.

⸻

What RTS Changes

Traditional logging answers:

What happened?

RTS answers:

What state was active when the decision happened?

RTS models execution as state transitions.

Each execution captures:
	•	Context
	•	Decision
	•	Assumptions
	•	Constraints
	•	Outcome

The unit is the transition.
Not the log line.

⸻

ASC2 — Structural Breakpoint Model

RTS does not alert on noise.
It detects structural mutation.

When mutation density crosses a defined boundary:
	1.	Breakpoint is flagged
	2.	Structural state is sealed
	3.	Evidence snapshot (ESC) is generated
	4.	Ledger + metrics become immutable reference

This converts instability into inspectable structure.

Not monitoring.
Structural mutation control.

⸻

Real Failure Scenario

Imagine:

An AI system approves an escalation in production.

Two weeks later, a regulator asks:

“Why was this allowed?”

You can reproduce the output.
You cannot reproduce the decision state.

RTS makes that state reconstructable.

⸻

What RTS Produces

RTS generates four structural artifacts:
	1.	Session Ledger (JSONL) — append-only execution events
	2.	Monthly Index — deterministic aggregation
	3.	Snapshot — sealed structural state
	4.	Evidence Snapshot (ESC) — breakpoint proof

Git-native.
No SaaS.
No telemetry.

⸻

Repository Structure

Sessions
	•	sessions/YYYY-MM/session_YYYYMMDD.jsonl
	•	sessions/YYYY-MM/index.json
	•	sessions/YYYY-MM/index.md
	•	sessions/YYYY-MM/index_snapshot.*

Evidence
	•	incidents/evidence_snapshots/ESC_*.md

If you inspect only two places:
	1.	sessions/
	2.	incidents/evidence_snapshots/

You will understand RTS.

⸻

ESC (Evidence Snapshot)

Generated only when structural mutation crosses threshold.

Each ESC contains:
	•	Escalation metrics
	•	Mutation score
	•	Transition tail
	•	Ledger reference

This is permanent structural evidence.

⸻

How to Verify RTS

Do not trust claims. Inspect artifacts.
	1.	Open sessions/YYYY-MM/index.md
	2.	Trace linked ledger entries
	3.	Confirm ESC exists when breakpoint occurs
	4.	Diff snapshot states

If it cannot be verified from artifacts, it is not RTS.

⸻

How to Adopt RTS

Minimum integration:
	1.	Append run start / run end events to JSONL
	2.	Roll up deterministic monthly index
	3.	Generate ESC only when breakpoint is crossed

No platform dependency required.

⸻

Who Needs This

RTS is for systems that must endure.

You likely need it if you:
	•	Run AI in production
	•	Require auditability
	•	Face regulatory exposure
	•	Need defensible escalation evidence
	•	Build long-lived AI systems

Not for short-lived demos.

⸻

Live Inspection

This repository is public and actively generating structural evidence.

You can:
	•	Inspect ledgers
	•	Verify transitions
	•	Review ESC files
	•	Clone and replay locally

Transparency over opinion.

For walkthrough requests, open an Issue.

⸻

What RTS Is Not

RTS is not:
	•	An agent framework
	•	A vector database
	•	A monitoring tool
	•	A compliance SaaS

RTS formalizes execution state.

⸻

Vision

AI execution will scale.
Trust will not scale automatically.

Governance must become structural.

RTS is a minimal protocol for building that structure.

⸻

License

MIT License
Copyright (c) 2026 Nobutaka Yamauchi
