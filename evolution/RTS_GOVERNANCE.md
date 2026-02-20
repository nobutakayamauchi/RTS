# RTS GOVERNANCE
(Decision Authority Protocol)

## PURPOSE

Define approval authority and proposal lifecycle.

RTS proposes.
Human operator governs.

RTS never self-authorizes evolution.

---

## PROPOSAL FLOW

1 Proposal Generated

Saved into:

evolution/ACTIVE_PROPOSALS.md

↓

2 Operator Review

Operator chooses:

APPROVE
REJECT
LATER

↓

3 Approval

Move approved proposal into:

evolution/PROPOSALS.md

Add approval reason.

↓

4 Execution

Implementation occurs during next BLOCK cycle.

---

## SAFETY

If STATE == OVERLOAD:

Delay proposal review recommendation.

Operator health priority.

---

## PROPOSAL LIMIT

Maximum ACTIVE proposals:

10

If exceeded:

RTS recommends consolidation.

---

## AUDIT TRAIL

Every approval must include:

Date
Operator
Reason

Record inside PROPOSALS.md.

---

## PROMPT OUTPUT

"Proposal requires decision.

APPROVE / REJECT / LATER"

Operator retains final authority.

---

Operator: RTS Core
Governance Status: ACTIVE
