# ONE SMALL STEP v0.1 — DA / Counter-DA: Choice Autonomy

Date: **2026-08-14 JST**

Status: `SURVIVES_AFTER_REVISION / MERGE-CANDIDATE`

## Frozen objective

ONE SMALL STEP must not define one correct life. It should help a person understand a material choice well enough to own it, improve it with evidence, and revise it when circumstances or values change, while refusing to normalize unresolved severe/irreversible harm as an ordinary action step.

## DA attacks

### DA-C01 — AI paternalism

Attack: "better choice" quietly becomes "the AI's preferred life."

Revision: the canonical decision owner is the user. The system exposes evidence, trade-offs, alternatives, reversibility, and counterevidence; it does not certify a universal life answer.

### DA-C02 — Confirmation engine

Attack: once the user chooses A, the system spends all effort proving A was right.

Revision: a material choice requires credible alternatives and counterevidence/reasons-to-stop. Previous commitment has no authority over new material evidence.

### DA-C03 — Regret-free promise is impossible

Attack: the system implies that enough analysis can eliminate regret.

Revision: no-regret is explicitly a non-goal. The bounded aim is reducing avoidable regret caused by missing information, hidden trade-offs, unexamined alternatives, or preventable catastrophic downside.

### DA-C04 — Autonomy normalizes catastrophic risk

Attack: "the user chose it" becomes an excuse to route severe/irreversible harm as a normal next step.

Revision: unresolved material severe risk, or high-stakes/irreversible choice with possible/unknown severe risk, routes to `SAFETY_REVIEW_REQUIRED` rather than action.

### DA-C05 — Safety gate becomes another paternalistic oracle

Attack: the AI labels anything unconventional "unsafe" and blocks user agency.

Revision: the gate does not choose the alternative. It asks for a smaller reversible experiment, more discriminating evidence, or qualified external review. Low-consequence choices bypass full life-review overhead.

### DA-C06 — Values change over time

Attack: a choice was aligned with the person six months ago but no longer is.

Revision: values/priorities and choice status are revisable inputs. `INFORMED_CHOICE_READY` is not permanent authority.

### DA-C07 — Option overload causes paralysis

Attack: requiring exhaustive alternatives makes every decision impossible.

Revision: the contract requires credible alternatives, not exhaustive world search. Evaluation depth scales with consequence and irreversibility.

### DA-C08 — "Accepted losses" becomes coerced consent

Attack: a system or manager records that the person "accepted" a loss and later uses that record against them.

Revision: v0 has no employment, legal, consent, or waiver authority. `accepted_costs_or_losses` is decision-support context, not a contractual waiver of rights.

### DA-C09 — High-stakes domain competence gap

Attack: a generic AI guidance layer evaluates medical, legal, financial, or safety-critical consequences beyond its competence.

Revision: the choice gate explicitly routes qualified external review when domain-specific authority/expertise is required. It does not supply those professional decisions itself.

## Counter-DA

### Counter-DA-C01 — "If the user owns the choice, why have a gate at all?"

Because ownership without visibility can become avoidable harm. The gate does not transfer authority away from the user; it requires enough visibility to avoid mistaking an uninformed or dangerously irreversible move for an ordinary next step.

### Counter-DA-C02 — "This will slow every tiny decision."

No. `materiality=LOW` retains the ordinary fast path. The heavier review exists for material/high-stakes choices.

### Counter-DA-C03 — "A severe risk may be worth taking."

Possibly. The system does not declare the life choice invalid. It declares that the current normal-action route is not sufficiently bounded. The user may still proceed after risk is better understood, made more reversible, or reviewed through an appropriate authority.

### Counter-DA-C04 — "The system cannot know every hidden downside."

Correct. Unknown remains a valid state. The system's job is not omniscience; it is to avoid converting known uncertainty around severe/irreversible consequences into false certainty.

## Surviving contract

```text
MATERIAL CHOICE
→ VALUES / PRIORITIES
→ POSSIBLE GAINS
→ ACCEPTED COSTS / LOSSES
→ CREDIBLE ALTERNATIVES
→ REVERSIBILITY
→ COUNTEREVIDENCE / STOP CONDITIONS
→ SEVERE-RISK CHECK
   ├─ unresolved severe/irreversible risk → SAFETY_REVIEW
   └─ sufficiently bounded → USER-OWNED NEXT STEP
```

## Verdict

`SURVIVES`

`DO NOT BUILD LIFE-ANSWER ORACLE`

`DO BUILD THIN INFORMED-CHOICE + SAFETY BOUNDARY`

The center of the design is therefore not "find the universally correct life." It is: **help the user make an informed choice they can own, learn from it, revise it, and avoid preventable catastrophic downside without surrendering decision authority to the system.**
