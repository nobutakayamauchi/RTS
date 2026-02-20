# RTS SUCCESS REPLICATION ENGINE

(Success Pattern Replication System)

---

## PURPOSE

RTS analyzes successful execution patterns and recommends replication or system adoption.

RTS does not auto-execute replication.
Human operator retains final authority.

---

## SUCCESS SOURCE INPUT

RTS reads success signals from:

- SUCCESS_LOG.md
- RESULT_LOG.md
- EXECUTION_LOG.md
- BLOCK logs
- External execution events

---

## SUCCESS SIGNAL CONDITIONS

RTS detects success patterns when:

- Approved evolution proposals repeatedly adopted
- Reduced workload score after execution
- Stable BLOCK execution cycles detected
- External success (publish / deploy / submission)
- Positive operator reflection signals

Repeated pattern >=3 considered stable success.

---

## ANALYSIS PROCESS

RTS evaluates:

- Execution duration
- Operator workload change
- Failure reduction
- External outcome success
- Momentum continuity

RTS extracts repeatable workflow structures.

---

## REPLICATION PROPOSAL TYPES

### SYSTEM

- workflow template recommendation
- governance conversion suggestion
- automation rule addition

### EXECUTION

- BLOCK template reuse suggestion
- similar task replication proposal
- timing optimization

---

## OUTPUT LOCATION

Replication proposals recorded in:

/evolution/ACTIVE_PROPOSALS.md

Approved replication rules move to:

/evolution/PROPOSALS.md

---

## HUMAN RESPONSE

Operator chooses:

APPROVE → replication rule added

REJECT → archive reasoning

LATER → retry after next BLOCK

---

## SAFETY RULE

RTS prioritizes operator health.

If overload risk detected:

RTS delays replication proposal.

---

## ENGINE EXECUTION TRIGGER

RTS evaluates replication when ANY condition is met:

- SUCCESS_LOG.md updated
- RESULT_LOG.md updated
- External execution success detected
- STATE ENGINE reports MOMENTUM state
- Operator manual request

Minimum interval:

Every 60 minutes equivalent execution time.

Command:

REPLICATE CHECK → Force evaluation.

---

Operator: RTS Core  
System Status: ACTIVE
