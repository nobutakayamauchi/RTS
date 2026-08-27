# RTS-FRZ-000022 — Exhausted-AI Human Escalation Gate v1

## Goal

Separate `important/actionable` findings from findings that truly require a human decision.

`HUMAN_NOW` is permitted only after DA, Counter-DA, and completed verification evidence have been folded into the current knowledge state and AI can no longer produce any of:

1. a defensible evidence-backed decision;
2. a concrete evidence-acquisition route;
3. a discriminating next experiment;
4. a bounded safe-defer/recheck condition;

and the unresolved choice materially affects the result.

## Non-goals

- No provider/model calls in the gate itself.
- No semantic truth authority.
- No execution, profile-application, promotion, Canon, or evidence-drop authority.
- No mutation of completed RTS-FRZ-000021.
- Uncertainty, disagreement, importance, retry count, or attempt count alone never authorizes human escalation.

## Advisory dispositions

- `AI_CONTINUE`: a discriminating AI-side route remains.
- `AI_RESOLVE`: explicit evidence supports a defensible bounded decision.
- `WAIT_SAFE_DEFER`: a bounded safe defer/recheck condition exists or the residual ambiguity is non-material.
- `HUMAN_CANDIDATE`: a material dead end is visible, but AI exhaustion has not yet been proven.
- `HUMAN_NOW`: knowledge-integrated exhaustion is proven and an explicit material human choice remains.
- `REVIEW_BLOCKED`: stale/truncated/inconsistent upstream evidence prevents normal classification.

## Critical invariant

`IMPORTANT != HUMAN_REQUIRED`.

`HUMAN_NOW` means the AI-side bounded problem-solving surface has reached a **no-new-discriminating-route fixed point**, not merely that a finding is high-impact or disputed.

## Knowledge integration

- Every completed DA, Counter-DA, and verification result must update the cumulative knowledge state before the next escalation decision.
- A failed/refuting probe is learning evidence: it may close one route and open another.
- An equivalent/replayed probe fingerprint cannot manufacture progress or exhaustion.
- Evidence cannot close a route that was never active.
- The final `SEARCH_FOR_NEW_DISCRIMINATING_ROUTE` only counts after previously known routes are already closed and their evidence has been integrated.

## K0 monotonicity

K1 is an escalation gate, not a work scheduler. Second-pass heuristic recovery may rescue a K0 `HUMAN_NOW` finding before human handoff. It must not promote K0 `HUMAN_LATER` or `DEFER_LOW_VALUE` into active work merely because a loose heuristic can name a possible probe.

## Human handoff

A valid `HUMAN_NOW` packet preserves:

- tested routes;
- learned facts;
- residual ambiguity;
- why no further AI-side discriminating route exists;
- the materially consequential human choice.

## DA death conditions

- High impact automatically becomes HUMAN_NOW while a discriminating route exists.
- Perspective disagreement automatically becomes HUMAN_NOW while evidence can still distinguish it.
- "AI is uncertain" is treated as exhaustion evidence.
- Attempt count or retries are treated as exhaustion evidence.
- Missing verification evidence is treated as exhausted verification.
- New evidence is recorded but not used to reshape the remaining UNKNOWN.
- A no-new-route search performed before known routes are exhausted is reused as final exhaustion proof.
- Safe defer exists but the record is escalated NOW.
- A non-material residual choice becomes HUMAN_NOW merely because no route exists.
- K1 heuristics promote K0 LATER/DEFER work into active work.
- HUMAN_NOW lacks an auditable exhaustion handoff.
- Upstream blocked/stale/truncated input receives a normal disposition.

## Measured live surface

Formal I → J → K0 → K1 validation on the current 76 unresolved official-doc findings produced:

- 35 `AI_CONTINUE`
- 41 `WAIT_SAFE_DEFER`
- 0 `AI_RESOLVE`
- 0 `HUMAN_CANDIDATE`
- 0 `HUMAN_NOW`
- 0 `REVIEW_BLOCKED`

This is evidence for the current surface, not a target count or a permanent promise.
