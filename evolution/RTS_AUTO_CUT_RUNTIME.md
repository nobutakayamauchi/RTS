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
