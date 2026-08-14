# ONE SMALL STEP v0.1 — METEOR Addendum: Choice Autonomy / Safety Boundary

Date: **2026-08-14 JST**

Status: `SURVIVES_ISOLATED_GATE_AND_COMPOSITION_HARNESS / PRE-MERGE`

A final philosophy-to-implementation DA found a material gap: the existing core and fear gate could help bound effort and fear, but there was no explicit canonical gate ensuring that a material personal choice exposed its gains, losses, alternatives, reversibility, counterevidence, and severe downside before action.

This was treated as an implementation gap rather than documentation-only philosophy.

## Added contract

`choice_gate.py` runs only before an unstarted material choice and only after earlier core orientation/capacity/goal/measurement/blocker gates have cleared.

A material choice records:

- values/priorities;
- expected gains;
- accepted costs/losses;
- credible alternatives;
- reversibility;
- severe/irreversible harm risk;
- counterevidence or reasons to stop/change course.

The gate always reports `decision_owner=USER`.

Low-consequence choices retain the fast path.

Unresolved material severe risk, or high-stakes/irreversible choices with possible/unknown severe risk, return:

`SAFETY_BOUNDARY -> REDUCE_IRREVERSIBILITY_OR_SEEK_QUALIFIED_REVIEW`

They do not return a normal action step.

## Destructive cases

The added isolated gate tests attack:

1. material choice with no trade-off map;
2. informed reversible material choice;
3. material severe downside;
4. irreversible choice with unknown severe downside;
5. low-consequence choice overhead;
6. earlier orientation precedence.

The canonical-composition harness attacks:

7. fear gate remains reachable when choice review is not active;
8. orientation still dominates pre-action gates;
9. material-choice review cannot be bypassed by the normal guidance entrypoint;
10. safety boundary dominates fear decomposition when both are active.

## Local result

New choice/autonomy extension:

- `choice_gate.py` syntax compile: **PASS**;
- isolated choice-gate tests: **6/6 PASS**;
- representative canonical composition harness: **4/4 PASS**;
- extension total: **10/10 PASS**.

The previously replayed exact repository-intended workload before this extension was **25/25 PASS**. The existing core and fear-gate implementation were not modified; `guidance.py` was changed only to compose `choice_gate.py` before `fear_gate.py`.

There is no configured GitHub Actions run on this PR head, so the final merge gate also requires PR diff/mergeability inspection. This record does not mislabel the isolated composition harness as a full CI run.

## Retained invariants

`SYSTEM != UNIVERSAL LIFE AUTHORITY`

`USER CHOICE != SYSTEM ENDORSEMENT`

`USER CHOICE != CONFIRMATION-ONLY ANALYSIS`

`INFORMED CHOICE != GUARANTEED NO REGRET`

`AUTONOMY != NORMALIZE CATASTROPHIC RISK`

`LOW-CONSEQUENCE CHOICE != FULL LIFE REVIEW`

`MATERIAL SEVERE/IRREVERSIBLE RISK != NORMAL NEXT STEP`

## Verdict

The autonomy philosophy survives only when implemented as a thin informed-choice/safety boundary rather than an AI life-answer oracle.

`SURVIVES / MERGE-CANDIDATE UNDER CURRENT EVIDENCE`
