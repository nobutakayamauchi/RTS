# Exhausted-AI Human Escalation Gate v1

`human_escalation_gate` is the K1 layer after `review_necessity_triage` (K0).

Its job is not to decide whether a source claim is true and not to schedule every potentially useful piece of work. Its job is narrower: prevent an unresolved finding from being handed to a human while a defensible AI-side decision, evidence-acquisition route, discriminating experiment, or bounded safe-defer condition still exists.

## Core rule

A finding reaches `HUMAN_NOW` only after all of the following hold:

1. DA, Counter-DA, and completed verification evidence have been folded into the current knowledge state.
2. All previously known discriminating routes are closed by explicit evidence.
3. A bounded search for a new discriminating route is performed **after** those closures and finds none.
4. No evidence-backed AI decision exists.
5. No bounded safe-defer trigger exists.
6. The residual ambiguity is materially consequential.
7. The remaining human choice is explicitly named.

Attempt count, retry count, uncertainty, disagreement, or high impact alone never prove exhaustion.

## Dispositions

- `AI_CONTINUE` — a discriminating AI-side route remains.
- `AI_RESOLVE` — explicit evidence supports a defensible bounded decision.
- `WAIT_SAFE_DEFER` — no immediate human decision is needed and a bounded recheck condition exists.
- `HUMAN_CANDIDATE` — a material dead end is visible, but exhaustion has not yet been proven.
- `HUMAN_NOW` — knowledge-integrated exhaustion is proven and a material human choice remains.
- `REVIEW_BLOCKED` — upstream identity/completeness is not safe enough for normal classification.

## Knowledge integration

Verification evidence can close an old route and open a new one. A refutation is therefore not automatically failure; it is new knowledge that can reshape the remaining UNKNOWN.

Equivalent/replayed probe fingerprints are rejected. Closing a route that was never active is rejected. A no-new-route search performed before known routes are closed does not count as exhaustion.

## K0 monotonicity

K1 second-pass heuristic recovery is used to rescue K0 `HUMAN_NOW` findings before human handoff. It does not promote K0 `HUMAN_LATER` or `DEFER_LOW_VALUE` findings into active work merely because a loose heuristic can name a possible probe. K1 is an escalation gate, not a work scheduler.

## Human handoff

`HUMAN_NOW` includes an auditable packet containing:

- tested routes;
- learned facts;
- residual ambiguity;
- why no AI-side discriminating route remains;
- the material human choice.

## Authority boundary

K1 is advisory. It does not grant semantic truth, execution, runtime mutation, profile application, promotion, Canon mutation, or evidence-drop authority.
