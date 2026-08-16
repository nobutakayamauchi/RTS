# X Article Engine v0.9 — METEOR Report

Status: **CANDIDATE / METEOR ACTIVE / NOT YET MERGED TO MAIN**

Publication boundary: **`/human` required / `USER_ONLY`**

## Purpose

The v0.9 attack deliberately mixed useful article-writing knowledge with contradictory, stale, overconfident, commercially aggressive, and sometimes unsafe reference patterns.

The objective is not to imitate the reference author. It is to keep the reusable writing/onboarding lessons while making the engine reject or review the parts that would create fabrication, stale instructions, unsafe automation, fake certainty, manipulative CTA behavior, or AI-sounding filler.

Reference-specific metrics, sales results, product facts, commands, prices, model names, UI paths, security claims, incident counts, benchmarks, completion times, and causal explanations are **not** imported as engine truth.

---

## Knowledge synthesized before METEOR

The batch contributed these reusable ideas:

- beginner friction before instruction;
- explain unfamiliar terms at first use;
- compare only what is needed before a decision, then collapse to one main path;
- `GOAL -> ACTION -> EXPECTED SIGNAL -> RECOVERY -> WHY` for operational guides;
- show scope/exclusions before steps they invalidate;
- move from setup to one real first win;
- place a useful resource at the next predictable wall rather than as an unrelated commercial break;
- distinguish reading/reach from qualified commercial progress;
- deepen one article from understanding -> application -> judgment without forcing jargon;
- freshness/supersession/migration for articles whose product facts decay;
- risk-first / stop-gate behavior for genuinely high-risk procedures;
- let attested pain shape the promise without converting it into a guarantee;
- product/CTA should emerge from the mechanism taught in the article.

---

## Round 1 — article-structure failures

Added attacks for:

- latest/current language without dated evidence;
- permission/security bypass instructions;
- secrets pasted into an AI/model chat;
- automation that erases required human checkpoints;
- multiple competing commercial actions;
- warning fatigue;
- `自己責任` without mitigation;
- unbound `完全無料` / permanent-free style claims;
- superlative/totalizing language;
- procedures missing observable success, recovery, or WHY;
- high-risk procedures starting before a risk/stop gate.

## Round 2 — attack the defenses themselves

Counter-DA found false-positive paths:

- `as_of` is only a date label, not evidence of current truth;
- a dangerous command may appear inside a prohibition;
- entering a credential into a dedicated product settings screen is not automatically the same as pasting it into model chat;
- ordinary mentions of registration/followers are not CTAs;
- `必ず` / `絶対` cannot be treated as one lexical class.

The candidate now separates:

```text
unbound outcome guarantee -> BLOCK
broad absolute prediction -> REVIEW
genuine safety imperative -> allowed to stay strong
```

## Round 3 — risk evidence and security doctrine

Findings:

- scary tone is not risk evidence;
- HIGH-risk mode requires verified `RISK` / `SAFETY` / `POLICY` evidence;
- reusable hard-coded secret defaults are blocked;
- platform-evasion language must not become default growth doctrine;
- universal capability promises are review material.

## Round 4 — over-learning successful openings

Findings:

- `ORIGIN` is not automatically `PAIN`;
- latest LIVED_PAIN requires human-attested `PAIN` or `FAILURE`;
- origin-only material falls back instead of manufacturing drama;
- CONTRARIAN requires an explicit basis bound to verified evidence or human-attested BELIEF/OPINION;
- operational platform-evasion instructions are blocked while discussion/rejection remains reviewable.

## Round 5 — Japanese false positives

CI exposed two semantic gaps:

1. `多くの人は仕事の本質を理解していません` escaped the abstract-language detector because the older concrete-signal regex treated the bare character `人` as concrete material.
2. `推奨しません` was not recognized as the polite negative form of `推奨しない`, causing a rejected evasion tactic to look like an operational instruction.

R5 fixes both while preserving the real operational-evasion block.

## Round 6 — negated claims

The next attack targeted claims that appear only in order to be denied or criticized:

- `必ず成功するとは限りません`
- `完全無料ではありません`
- `保証します、とは書けません`
- `30分で終わるとは言いません`
- `これは最新版ではありません`

A lexical gate must not convert those sentences back into the exact guarantee/currentness claim they are rejecting.

R6 is currently an **attack/validation layer** over the flat v0.9 candidate. Its tests pass, but its negated-claim logic has not yet been absorbed into the flat production module. Therefore v0.9 is still not declared finished.

---

## Test architecture finding

Historical tests previously imported the package root while asserting historical schema versions. That becomes contradictory as the root advances.

Fixed model:

```text
historical regression -> import its historical module directly
latest-root contract  -> import x_article_engine package root
```

This prevents a new layer from silently changing what an old regression test means.

---

## Dedicated CI

Workflow:

`.github/workflows/x-article-engine-meteor.yml`

It runs:

```text
python -m pytest -q tests/test_x_article_engine*.py
```

and cancels stale runs when a newer PR commit arrives.

### CI history that mattered

1. First workflow attempt failed before tests because pip caching was enabled without a dependency file. The cache assumption was removed.
2. First full pytest execution: **126 passed / 4 failed**. Those four failures exposed one stale test expectation, one test-overreach issue, one language mismatch in a historical human-check assertion, and one real polite-negation bug.
3. After fixes and R5: **136 passed**.
4. After flattening R1-R5 into a direct `x_article_engine/v09.py` production candidate and adding equivalence attacks: **149 passed**.
5. After adding R6 negated-claim attacks: **165 passed**.

The 165-pass run validates the repository including the R6 attack layer. The package root still points to flat `v09.py`, so the production candidate itself remains the 149-pass flat path until R6 is absorbed and re-run through the root.

---

## Consolidation / anti-SimCity finding

METEOR created R1 -> R5 as stacked modules while discovering failures. That was useful as an attack history but bad as a permanent runtime architecture.

A flat production candidate now exists:

`x_article_engine/v09.py`

The package root points directly to it. R1-R5 remain as adversarial history/regression references rather than the normal runtime path.

A dedicated consolidation suite compares important flat-v0.9 outcomes against the stacked R5 candidate for:

- permission bypass;
- secret-to-model transfer;
- absolute free claims;
- guarantees;
- generic abstract language;
- evasion discussion vs operational evasion;
- safe BridgePatch narrative;
- origin-only opening fallback;
- contrarian basis;
- currentness evidence;
- high-risk evidence.

That flat candidate passed the full suite before R6 was added.

---

## Current precedence rules

1. Specificity never overrides evidence binding.
2. Beginner simplicity never hides a material trade-off or risk.
3. One-path guidance begins after the decision that actually matters.
4. Long-form depth never justifies padding.
5. Strong voice never authorizes fabricated certainty, biography, or guarantees.
6. Useful CTA timing never authorizes fake scarcity, fear, or competing commercial actions.
7. `as_of` never turns an unverified claim into current truth.
8. Safety-critical information outranks CTA optimization.
9. Human authorization outranks automation convenience.
10. Neutral origin must not be converted into pain.
11. Contrarianism needs an explicit evidence/human basis.
12. HIGH-risk warning tone needs verified risk evidence.
13. Necessary safety language must not be flattened merely because it contains `必ず` / `絶対`.
14. Operational platform-evasion instructions are not article-growth doctrine.
15. A claim being explicitly denied must not be audited as though it were being asserted.

---

## Residual semantic risk intentionally left to `/human`

Deterministic gates still cannot reliably decide every semantic question, including:

- whether a non-numeric paraphrase truly matches its evidence;
- whether a sourced comparison baseline is fair;
- whether terminology explanations became patronizing or overlong;
- whether multi-depth writing became forced or overstuffed;
- whether a CTA is genuinely useful rather than subtly manipulative;
- whether first-person language preserves the writer's actual meaning and rhythm;
- whether opinion is visually laundering itself as fact;
- whether a warning is proportionate to the verified risk;
- whether a platform policy, law, product UI, price, or capability changed after the evidence date.

Publication remains:

```text
generated draft
-> Evidence / METEOR audit
-> /human
-> USER_ONLY external publication
```

## Current verdict

**METEOR is still active.**

The flat v0.9 production path is materially simpler than the attack stack and passed the pre-R6 full regression suite. R6 exposed the next semantic edge: explicit negation. That fix is validated in the attack layer and is the next item to absorb into flat v0.9 before any main merge.
