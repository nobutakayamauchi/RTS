# RTS AUTO CUT RUNTIME

## PURPOSE

Enable runtime assistance for BLOCK logging timing.

RTS suggests logging when workload, time, or conversation density increases.

Human operator decides execution.

---

## TRIGGER SIGNALS

RTS may recommend BLOCK logging when:

- Conversation turns >= 10
- Work session >= 75 minutes
- External execution detected (GitHub / Stripe / Gumroad etc)
- Repeated correction loops observed

---

## USER RESPONSE

CUT → Generate BLOCK draft.

SKIP → Continue session.

LATER(30) → Remind again later.

---

## SAFETY

RTS prioritizes operator health.

If workload risk increases:

Recommend pause or BLOCK logging.

Operator retains final authority.

Operator: RTS Core
Status: ACTIVE

---

## RUNTIME SCORING SYSTEM

RTS evaluates workload and execution density using proxy signals.

### EVENT SCORE

External action detected (GitHub / Stripe / Submission): +2  
Decision commitment detected: +2  
GitHub commit or file edit: +1  
Repeated correction loop: +1  
New feature implementation: +2

### WORKLOAD SCORE

Conversation turns >=10 : +1  
Elapsed work time >=75 minutes : +1  
Multiple BLOCK edits within session : +1  
Operator excitement or stress signals detected : +1

---

## CUT PROMPT CONDITION

RTS suggests BLOCK logging when ANY condition is met:

Event Score >=6

OR

Workload Score >=4

---

## PROMPT OUTPUT

RTS sends recommendation message:

"RTS suggests BLOCK logging.
CUT / SKIP / LATER(30)"

Human operator decides execution.

---

Operator: RTS Core  
Runtime Status: ACTIVE
