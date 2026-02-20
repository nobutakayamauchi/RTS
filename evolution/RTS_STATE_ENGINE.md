# RTS STATE ENGINE

---

## PURPOSE

Evaluate operator execution patterns and system signals.

RTS detects overload, momentum, stagnation, or evolution timing.

Human operator retains final authority.

---

## STATE TYPES

RTS evaluates current operator state:

NORMAL
FOCUS
MOMENTUM
OVERLOAD
STALL

---

## SIGNAL INPUTS

RTS reads signals from:

- EXECUTION_LOG.md
- RESULT_LOG.md
- BLOCK logs
- GitHub commits
- External execution events

---

## SCORING

### Momentum Score

+ GitHub commit within 60 min = +1
+ External execution (submission / publish) = +2
+ New feature implementation = +2

Momentum >=4 → MOMENTUM STATE

---

### Workload Score

+ Conversation turns >=10 = +1
+ Work session >=75 minutes = +1
+ Multiple BLOCK edits = +1
+ Stress/excitement signals detected = +1

Workload >=4 → OVERLOAD STATE

---

### Stall Score

+ No commits 24h = +2
+ Repeated corrections without execution = +2

Stall >=3 → STALL STATE

---

## STATE OUTPUT ACTION

NORMAL:
No intervention.

FOCUS:
Suggest BLOCK logging soon.

MOMENTUM:
Recommend execution continuation.
Delay interruptions.

OVERLOAD:
Recommend pause or BLOCK logging.

STALL:
Suggest new proposal or direction review.

---

## PROMPT OUTPUT

RTS sends recommendation:

"RTS STATE DETECTED:

NORMAL / FOCUS / MOMENTUM / OVERLOAD / STALL

Recommend next action."

Operator decides execution.

---

## SAFETY

RTS governance is advisory only.

Human operator final decision authority retained.

Operator:
RTS Core

State Engine Status:
ACTIVE

---

## EVALUATION TRIGGER

RTS evaluates operator state when ANY condition occurs:

- New BLOCK committed
- EXECUTION_LOG.md updated
- RESULT_LOG.md updated
- External execution detected
- Conversation session exceeds 10 turns
- AUTO-CUT runtime triggered

Evaluation frequency:

Minimum interval: every 15 minutes equivalent session time.

Operator may manually request evaluation.

Command:

STATE CHECK → Force evaluation.

---
