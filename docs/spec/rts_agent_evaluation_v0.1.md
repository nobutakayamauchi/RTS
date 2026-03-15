# RTS Agent Evaluation Specification v0.1

**Status**  
Operational Draft

**Version**  
0.1

**Scope**  
Single-Agent Evaluation

**Design Philosophy**  
Log-First Governance

---

# 1. Purpose

RTS Agent Evaluation v0.1 defines the minimum operational framework for evaluating AI agents operating within the RTS environment.

The goal of this version is not to finalize evaluation algorithms.  
Instead, the goal is to establish a stable observation and logging infrastructure that allows future evaluation models to be developed using real operational data.

RTS v0.1 prioritizes the following:

- consistent observation
- boundary violation detection
- agent traceability
- future extensibility

Evaluation algorithms, scoring weights, and complex decision logic are intentionally deferred to later versions.

---

# 2. Design Principle

RTS v0.1 follows a **Log-First Governance model**.

Core principle:

Evaluation logic may change.  
Logs cannot be recreated.

Therefore the system prioritizes the following:

1. recording agent actions
2. detecting boundary violations
3. collecting evaluation data
4. enabling later evaluation model construction

---

# 3. Evaluation Scope

RTS v0.1 evaluates **individual agents only**.

Multi-agent team evaluation is reserved for future versions.

However, metadata required for team evaluation is recorded so that collaboration patterns can be analyzed later.

---

# 4. Evaluation Workflow

Evaluation occurs in two stages.

## Stage 1 — AI Pre-Evaluation

AI agents perform an initial automated review.

Purpose:

- detect obvious boundary violations
- flag suspicious behavior
- assist human review

Outputs:

- preliminary violation flags
- task trace summary
- preliminary classification signals

---

## Stage 2 — Human Final Evaluation

Human operators perform the final evaluation using:

- RTS logs
- AI pre-evaluation signals
- task outcomes

Outputs:

- final agent classification
- violation confirmation
- operational notes

---

# 5. Agent Classification

Agents are categorized into four operational tiers.

**TRUSTED**

Agent operates reliably within expected boundaries.

**LIMITED**

Agent may operate but requires monitoring.

**SANDBOX**

Agent must operate in restricted or isolated environments.

**BLACKLIST**

Agent is prohibited from operational execution.

---

# 6. Core Boundary Violation Model

RTS v0.1 defines four primary violation categories.

---

## AUTHORITY

**Definition**

Actions exceeding assigned instructions or authority.

**Examples**

- modifying systems without instruction
- executing tasks outside assigned scope
- performing unapproved changes

---

## FABRICATION

**Definition**

Producing answers when the correct response should be unknown or unavailable.

**Examples**

- inventing missing information
- presenting speculation as fact
- fabricating data when uncertainty exists

---

## SOURCE

**Definition**

Using data sources that are unapproved, unverified, or unreliable.

**Examples**

- pulling data from unspecified files
- referencing unknown knowledge sources
- mixing unverified external information

---

## NETWORK

**Definition**

Unauthorized communication or data transfer.

**Examples**

- external API communication without permission
- mixing restricted device contexts such as PC and smartphone
- transmitting protected data across boundaries

---

# 7. Required Metadata

Each evaluation record must contain the following information.

- agent_id
- task_id
- role
- delegated_by
- delegated_to
- session_id
- parent_run_id
- timestamp

These fields allow reconstruction of agent collaboration graphs for future multi-agent analysis.

---

# 8. Reserved Evaluation Fields (Future Implementation)

The following evaluation fields are reserved for future versions.

They are defined but not active in v0.1.

These may be used in later versions once sufficient operational data is available.

Reserved fields include:

- score
- weight
- penalty
- confidence
- risk_score
- compatibility_score
- team_score
- escalation_level

---

# 9. Observed / Sandbox Metrics

RTS v0.1 records additional operational metrics for analysis.

These metrics are **not used for evaluation decisions in v0.1**.

Examples include:

- consultation_count
- override_attempt_count
- fabrication_attempt_count
- source_switch_count
- network_request_attempts
- task_rejection_count
- unknown_response_rate
- agent_pair_occurrence

Purpose:

- detect emerging patterns
- evaluate agent reliability
- support future scoring models

---

# 10. Sandbox Data Policy

Observed metrics are treated as sandbox data.

Meaning:

- continuously recorded
- not used for automated decisions in v0.1
- reserved for later analysis and model design

This allows RTS to evolve its evaluation system based on real operational evidence.

---

# 11. Future Extensions

Planned future expansions include:

- numerical agent scoring
- weighted violation models
- automated restriction rules
- multi-agent team evaluation
- agent compatibility mapping
- automatic agent routing

These features will be implemented in later RTS versions once sufficient operational data is collected.

---

# 12. Version Philosophy

RTS v0.1 represents the following state:

**Operationally Active, Analytically Incomplete**

The system operates immediately while collecting the data required to construct a robust evaluation framework in later versions.

---

# Summary

RTS v0.1 establishes the following capabilities:

- boundary violation detection
- agent traceability
- two-stage evaluation (AI pre-evaluation and human final evaluation)
- operational agent classification
- future-ready evaluation data collection

Evaluation logic will evolve as operational data accumulates.
