# RTS-FRZ-000022 — Exhausted-AI Human Escalation Gate v1

## Goal
Separate `important/actionable` findings from findings that truly require a human decision.

Human escalation is permitted only after bounded DA, Counter-DA, and available verification fail to produce **all three** of:
1. a defensible decision,
2. a discriminating next experiment,
3. a safe defer condition,

and the unresolved choice materially affects outcome, safety, execution architecture, or future engine identity.

## Non-goals
- No provider/model calls in the gate itself.
- No semantic truth authority.
- No execution, profile-application, promotion, or Canon authority.
- No mutation of completed RTS-FRZ-000021.
- Uncertainty/confidence alone never authorizes human escalation.

## Advisory dispositions
- `AI_CONTINUE`: an existing deterministic rule/decision path remains.
- `PROBE_REQUIRED`: a discriminating experiment or verification path exists.
- `WAIT_SAFE_DEFER`: a bounded safe defer/recheck condition exists.
- `HUMAN_CANDIDATE`: no route is currently known, but exhaustion has not been proven.
- `HUMAN_NOW`: explicit exhaustion evidence + no decision + no experiment + no safe defer + material effect.
- `REVIEW_BLOCKED`: stale/truncated/inconsistent upstream evidence.

## Critical invariant
`IMPORTANT != HUMAN_REQUIRED`.

`HUMAN_NOW` means the AI-side bounded problem-solving surface has been exhausted, not merely that a finding is high-impact or disputed.

## DA death conditions
- High impact automatically becomes HUMAN_NOW while a discriminating probe exists.
- Perspective disagreement automatically becomes HUMAN_NOW while more evidence can distinguish it.
- "AI is uncertain" is treated as exhaustion evidence.
- Missing verification evidence is treated as verification exhausted.
- Safe defer/recheck condition exists but record is escalated NOW.
- Verification exhausted with no route, materially consequential unresolved choice, but gate silently defers.
- Non-material unresolved choice becomes HUMAN_NOW merely because no route exists.
- Upstream blocked/stale/truncated input receives a normal disposition.
