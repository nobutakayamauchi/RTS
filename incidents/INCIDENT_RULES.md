# RTS Incident Standard — Execution Audit Specification v2

RTS records operational reality.

Execution failure becomes operational memory.

This document defines the audit-grade incident recording structure used by
RTS (Real Time Trust System).

---

# Purpose

RTS incidents are not opinions.

They are reproducible operational evidence.

Each incident must allow:

- independent review
- operational reconstruction
- AI workflow verification
- longitudinal audit analysis

Incidents form part of RTS operational memory infrastructure.

---

# File Naming

INC_YYYYMMDD_HHMM_SYSTEM_SHORTTITLE.md

Example:

INC_20260222_1545_Cursor_ContextLoss.md

Timestamp must represent first operator detection.

---

# Required Structure (Audit Minimum)

Every incident must include:

- Metadata Header (machine readable)
- Timeline
- Symtom Description
- Reproduction Steps
- Operational Impact
- Evidence

Root cause analysis may evolve later.

---

# Metadata Header (Required)

Each incident MUST begin with structured metadata.

Example:

---

incident_id: INC_20260222_1545

system: Cursor

severity: S2

status: OPEN

operator: Nobutaka Yamauchi

environment:

  device: iPhone15Pro
  interface: Mobile GitHub Browser
  workflow: Long Session AI Operation

model:

  provider: OpenAI
  name: GPT
  version: unknown

timeline:

  detected: 2026-02-22T15:45
  investigation_started: 2026-02-22T16:10
  mitigation_started: unknown
  recovered: unknown

reproducible: partial

evidence:

 - https://x.com/example/status/xxxx

---

Machine readability enables automated audit analysis.

---

# Severity Levels

S1 — System Blocking

Workflow cannot continue.

Examples:

- irreversible data loss
- execution lock

---

S2 — Workflow Disruption

Operator forced manual intervention.

Examples:

- hallucination risk
- context loss
- reasoning instability

---

S3 — Minor Friction

Reduced efficiency without operational halt.

Examples:

- UI delay
- retry required.

---

# Timeline (Required)

Incidents must record operational chronology.

Minimum:

- Detection Time
- Investigation Start
- Mitigation Attempt
- Recovery (if applicable)

Timeline establishes audit legitimacy.

---

# Symptom

Observed behaviour.

Facts only.

Avoid speculation.

Example:

Long Cursor coding sessions lose operational context.

Autocomplete breaks randomly.

---

# Reproduction Steps (Required)

Operators must describe reproducibility.

Minimum:

- workflow length
- interaction type
- triggering actions

Example:

1. Open Cursor session longer than 2 hours.
2. Maintain continuous GPT interaction.
3. Observe context resets during autocomplete.

If not reproducible:

State:

"Reproduction unknown."

---

# Environment

Record execution conditions.

Examples:

- device
- browser
- IDE
- API vs Chat UI

Operational environment affects causality.

---

# Model Information

If AI involved:

Record:

- provider
- model name
- known version (if any)

Example:

GPT / Claude / Gemini / Cursor Agent.

---

# Operational Impact

Describe operator consequences.

Examples:

- manual rebuild required
- research delay
- decision risk introduced.

---

# Root Cause (Hypothesis)

Optional during OPEN phase.

Mark clearly as hypothesis.

Avoid definitive claims without evidence.

---

# RTS Intervention

Describe operator response.

Examples:

- execution logging initiated
- workflow isolation
- rollback.

RTS focuses on execution recovery.

---

# Recovery

Record mitigation outcome.

Examples:

- manual audit performed
- workflow rebuilt.

---

# Lessons Learned

Operational learning extracted.

Example:

Persistent execution logging stabilizes AI collaboration.

---

# Evidence (Required)

Evidence must include at least one:

- Public X discussion
- GitHub issue
- Official vendor statement
- Reproducible logs.

Links required.

---

# Status

OPEN

MITIGATED

CLOSED

Status may evolve.

RTS preserves history.

---

# JSON Compatibility

Markdown metadata enables:

- analyze.py automation
- drift detection
- cascade analysis.

Incidents are machine analyzable.

---

# Philosophy

RTS records execution reality.

Human authority remains final.

Memory prevents repeated failure.

Execution becomes memory.
