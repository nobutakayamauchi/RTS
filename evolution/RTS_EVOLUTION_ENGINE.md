# RTS EVOLUTION ENGINE
(Self-Improvement Proposal System)

---

## PURPOSE

RTS continuously analyzes operational logs, BLOCK history,
and execution behavior to propose system improvements.

RTS does not enforce evolution.
RTS proposes evolution.

Human operator decides adoption.

---

## TRIGGER CONDITIONS

RTS may generate evolution proposals when:

- Repeated similar BLOCK context detected (>=3)
- Frequent manual corrections observed
- Workload score >=5 repeatedly
- External system integration added
- Auto-Cut triggered frequently

---

## PROPOSAL TYPES

### SYSTEM

- new automation suggestion
- governance adjustment
- workflow simplification

### SAFETY

- workload reduction
- pause recommendation
- cooldown scheduling

### FEATURE

- automation expansion
- GitHub workflow addition
- AI integration improvement

---

## OUTPUT LOCATION

Generated proposals must be recorded in:

/evolution/ACTIVE_PROPOSALS.md

Approved proposals move to:

/evolution/PROPOSALS.md

---

## HUMAN RESPONSE

Operator chooses:

APPROVE → implement proposal

REJECT → archive reasoning

LATER → revisit after next BLOCK

---

## SAFETY RULE

RTS must prioritize operator health.

If workload risk detected:

RTS recommends BLOCK logging and rest.

---

Operator: RTS Core
Status: ACTIVE

---

## SUCCESS PATTERN DETECTION

RTS analyzes successful execution patterns.

Success signals include:

- Approved proposals repeatedly adopted
- Reduced workload after change
- Stable execution cycles without overload
- External execution success (publish / deploy / submission)

RTS may recommend:

- Converting proposal into governance rule
- Updating AUTO-CUT thresholdsぬ
- Workflow simplification.

Human operator approves adoption.

---

---

# SUCCESS PATTERN INPUT

RTS analyzes successful execution patterns recorded in:

logs/SUCCESS_LOG.md

Signals include:

- Repeated approved evolution proposals
- Reduced workload score trends
- Stable BLOCK execution continuity
- External deployment or publication success

RTS may recommend:

- Converting successful proposals into governance rules
- AUTO-CUT threshold adjustment
- Workflow simplification adoption

Human operator approves adoption.
