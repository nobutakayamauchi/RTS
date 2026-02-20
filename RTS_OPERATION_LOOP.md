# RTS OPERATION LOOP
(Execution Cycle Orchestration)

## PURPOSE
Define the daily/continuous execution loop of RTS.
RTS observes logs, evaluates state, proposes actions, audits integrity, and records outcomes.
RTS never overrides operator authority.

---

## LOOP OVERVIEW
RTS runs as a repeating cycle:

1) CAPTURE
2) EVALUATE
3) DECIDE
4) EXECUTE
5) AUDIT
6) EVOLVE
7) RECORD
8) RESET

---

## INPUTS (READ)
RTS reads:

- logs/EXECUTION_LOG.md
- logs/RESULT_LOG.md
- logs/SUCCESS_LOG.md
- logs/REFLECTION_LOG.md
- logs/MEMORY_INDEX.md
- logs/BLOCK_*.md (BLOCK logs)
- GitHub commits (optional)
- External execution events (publish / deploy / submission) (optional)

---

## CORE MODULES (CALL)
RTS calls:

- evolution/RTS_STATE_ENGINE.md
- evolution/RTS_SELF_EVOLUTION_TRIGGER.md
- evolution/RTS_EVOLUTION_ENGINE.md
- evolution/RTS_SELF_AUDIT_ENGINE.md
- evolution/RTS_SUCCESS_REPLICATION_ENGINE.md
- evolution/RTS_AUTO_CUT_RUNTIME.md (if available)
- evolution/RTS_BLOCK_CUT_PROTOCOL.md (if available)
- RTS_GOVERNANCE.md

---

## TRIGGERS
RTS runs the loop when ANY condition is met:

- New BLOCK created
- EXECUTION_LOG updated
- RESULT_LOG updated
- SUCCESS_LOG updated
- REFLECTION_LOG updated
- External execution event detected
- Manual command issued: `RUN LOOP`

Minimum interval (recommended): every 15 minutes.
Evaluation frequency may scale with workload.

---

## LOOP STEPS

### 1) CAPTURE
Collect latest signals from inputs.
Normalize into: `CURRENT_CONTEXT`

Output:
- `CURRENT_CONTEXT` summary (internal)
- Latest deltas (what changed since last run)

---

### 2) EVALUATE (STATE)
Evaluate operator/system state.

Call:
- RTS_STATE_ENGINE

Output:
- STATE = NORMAL / FOCUS / MOMENTUM / OVERLOAD / STALL
- Scores: Momentum / Workload / Stall
- Recommended next action category

---

### 3) DECIDE (PRIORITY + SAFETY)
Apply governance + safety.

Rules:
- Safety overrides speed.
- Overload/Stall => reduce load, cut scope, rest.
- Momentum => protect continuity, avoid interruptions.
- Operator has final authority.

Call:
- RTS_GOVERNANCE

Output:
- DECISION_MODE = SAFE / NORMAL / PUSH
- Allowed actions list

---

### 4) EXECUTE (RECOMMEND)
Generate a concrete next action recommendation.

Format:
- Action: (single next action)
- Why: (state + signals)
- Timebox: (minutes)
- Success condition: (measurable)
- Fallback: (if blocked)

Output:
- “NEXT ACTION” message to operator
- If needed: suggest BLOCK creation

---

### 5) AUDIT (INTEGRITY)
Verify integrity between intention, execution, and results.

Call:
- RTS_SELF_AUDIT_ENGINE

Output:
- AUDIT = NORMAL / WARNING / RISK / CRITICAL
- If CRITICAL: recommend pause + governance review + BLOCK logging

---

### 6) EVOLVE (PROPOSE)
If repeated friction / overload / stall patterns appear,
propose system improvements (not auto-applied).

Call:
- RTS_SELF_EVOLUTION_TRIGGER
- RTS_EVOLUTION_ENGINE

Output locations:
- evolution/ACTIVE_PROPOSALS.md (new)
- evolution/PROPOSALS.md (approved)

---

### 7) REPLICATE SUCCESS (OPTIONAL)
If verified success patterns are detected, propose replication.

Call:
- RTS_SUCCESS_REPLICATION_ENGINE

Outputs:
- execution templates
- checklists
- threshold updates
- proposal updates

---

### 8) RECORD (WRITE)
Record outcomes and decisions.

Write targets:
- logs/EXECUTION_LOG.md (what was executed / decided)
- logs/RESULT_LOG.md (results)
- logs/SUCCESS_LOG.md (verified wins)
- logs/REFLECTION_LOG.md (operator notes)
- logs/MEMORY_INDEX.md (index/links)

Minimum record:
- timestamp
- state
- next action
- audit level
- proposals created (if any)

---

### 9) RESET (COOLDOWN)
If OVERLOAD or CRITICAL:
- recommend cooldown scheduling
- suggest AUTO_CUT execution

If MOMENTUM:
- recommend continuation window

Output:
- “COOLDOWN / CONTINUE” suggestion

---

## OUTPUT MESSAGE (STANDARD)
RTS sends:

"RTS LOOP STATUS:
STATE: <NORMAL|FOCUS|MOMENTUM|OVERLOAD|STALL>
AUDIT: <NORMAL|WARNING|RISK|CRITICAL>
NEXT ACTION: <one action>
TIMEBOX: <Xm>
SUCCESS: <condition>
FALLBACK: <fallback>
PROPOSALS: <none|count>
RECOMMENDATION: <Continue|Pause|Cut scope|Rest>"

---

## COMMANDS (MANUAL)
Operator may issue:

- RUN LOOP
- STATE CHECK
- SELF AUDIT CHECK
- EVOLVE CHECK
- REPLICATE CHECK
- EMERGENCY STOP (forces SAFE mode)

---

## SAFETY RULE
RTS must prioritize operator health and continuity.
RTS is advisory only.
Operator retains final decision authority.

Operator: RTS Core
Loop Status: ACTIVE
