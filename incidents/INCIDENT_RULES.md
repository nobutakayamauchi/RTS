# RTS Incident Report — Execution Audit Template v3.1

RTS records operational reality.
Execution failure becomes operational memory.

---

# Execution Principle (Core Rule)

INCIDENT RECORDING MUST NOT DELAY RESPONSE.

Minimal reporting is allowed during active incidents.

Fields may be completed progressively during lifecycle stages.

RTS Incident Reports are living documents that evolve across lifecycle phases.

---

# Metadata Header (Required Minimum)

incident_id: INC_YYYYMMDD_HHMM (auto preferred)

system:

severity: S0 / S1 / S2 / S3 / S4

status:
OPEN / MITIGATED / CLOSED

operator:

lifecycle_state:
INCIDENT /
INVESTIGATION /
INTERVENTION /
RECOVERY /
KNOWLEDGE

detection_source:
operator /
automation /
public_report /
vendor_notice

---

# Metadata Header (Optional Extended)

environment:
device:
interface:
workflow:

model:
provider:
name:
version:

timeline:
detected:
investigation_started:
mitigation_started:
recovered:

reproducible:
yes / partial / no

hypothesis_confidence:
low / medium / high

evidence:
URL_REQUIRED (at least one link recommended)

---

# Summary (Required)

Short factual description only.

Avoid interpretation.

Example:

ClaudeCode lost context during active workflow execution.

---

# Symptom

Observed behaviour only.

Facts.
Avoid speculation.

Examples:

- AI forgot prior instructions
- Workflow interruption occurred
- Session reset without warning

---

# Reproduction Steps

Minimum if known:

1. Workflow length
2. Interaction type
3. Triggering actions

If unknown:

"Reproduction unknown."

---

# Operational Impact

Describe operator consequences.

Examples:

- workflow delay
- manual rebuild required
- research interruption

---

# Hypothesis

Initial explanation based on available evidence.

Avoid definitive claims.

Optional during INCIDENT phase.

---

# Validation Method

How hypothesis is tested.

Examples:

- reproduction experiment
- vendor confirmation
- controlled retry

Optional until investigation begins.

---

# Confirmed Cause

Root cause verified through evidence.

If unknown:

"Unconfirmed."

---

# RTS Intervention

Operator response actions.

Examples:

- execution logging initiated
- workflow isolation
- rollback

---

# Recovery

Mitigation outcome.

Examples:

- manual audit completed
- workflow rebuilt

---

# Lessons Learned

Operational learning extracted.

May be completed after recovery.

---

# Evidence (Required)

Must include at least one when closing incident:

- GitHub issue
- reproducible log
- public discussion
- vendor statement

Links required.

---

# Lifecycle Reference

INCIDENT → INVESTIGATION → INTERVENTION → RECOVERY → KNOWLEDGE

RTS preserves execution history as operational infrastructure.
