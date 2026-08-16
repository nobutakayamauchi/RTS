# X Article Engine v0.9 — METEOR Report

Status: **CANDIDATE / NOT YET PROMOTED TO MAIN**

Publication boundary: **`/human` required / `USER_ONLY`**

## Purpose

This round intentionally fed the X Article Engine a mixed corpus containing:

- strong beginner-guide patterns;
- long-form sales-article patterns;
- first-person pain/origin patterns;
- multi-depth reader patterns;
- market-gap / timing patterns;
- comparison articles that later became stale;
- high-risk tutorial patterns;
- examples containing dangerous security shortcuts, hard-coded credentials, platform-evasion language, absolute guarantees, and oversized promotional blocks.

The goal was not to imitate the reference author. The goal was to make the engine survive contradictions in the corpus without importing reference-specific claims as truth.

## Source boundary

The supplied reference articles are treated as **writing / onboarding / positioning examples only**.

The engine does not import as timeless truth:

- impression, follower, list, or revenue results;
- claimed causal explanations for those results;
- product prices, model names, plan availability, UI paths, benchmarks, commands, limits, or platform behavior;
- CVE numbers, security incident counts, or safety claims;
- fixed completion times or success rates;
- claims that a particular number of examples, article length, CTA position, or reader-layer model universally causes performance.

Those facts require their own evidence when used in a real article.

---

## Round 1 — attack the gaps left by v0.8

The first attack found that existing evidence protection was strongest against invented numbers/results, but weaker against article-structure failures.

Added attacks for:

- current/latest language without dated evidence;
- permission/security bypass instructions;
- telling a reader to paste secrets into an AI/model chat;
- automation that removes necessary human checkpoints;
- multiple competing reader actions / CTAs;
- warning fatigue;
- `自己責任` used without mitigation;
- unbound `完全無料` / permanent-free style claims;
- superlative/totalizing language;
- procedures without success signals;
- procedures without recovery;
- procedures without WHY;
- high-risk tutorials that begin operational steps before a stop/risk gate.

Result: the engine became harder to trick with a polished-looking unsafe tutorial.

---

## Round 2 — counter-DA attacked the defenses

Round 1 overreacted in several places.

### Finding A: `as_of` is not evidence

A writer-supplied date label cannot make a factual claim current.

Rule hardened to:

```text
CURRENT / UPDATE
-> as_of boundary
+ verified dated/TIMING evidence
```

### Finding B: dangerous text can appear inside a prohibition

Bad detector:

```text
--dangerously-skip-permissions
=> always block
```

Counterexample:

```text
--dangerously-skip-permissions は使わないでください。
```

The latest gate distinguishes recommendation from warning/prohibition.

### Finding C: `必ず` / `絶対` are not one semantic class

The old commercial-strengthening gate was lexical.

That can wrongly punish:

```text
APIキーは絶対に共有しないでください。
権限は必ず確認してください。
```

The latest candidate separates:

1. unbound outcome guarantee -> BLOCK;
2. broad absolute prediction/generalization -> REVIEW;
3. genuine safety imperative -> allow strong wording.

### Finding D: secret destination matters

A secret entered into a dedicated settings screen is not automatically the same as pasting a secret into a model prompt/chat.

The detector now looks for:

```text
secret/credential
+ transfer action
+ model/chat destination
```

### Finding E: CTA detection must detect actions, not vocabulary

Narrative phrases such as `登録前` or `フォロワー数` are not CTAs.

The refined gate looks for requests to buy/apply/join/register/add-friend/follow/reply/DM/consult/fit-check/request material.

---

## Round 3 — attack strong language, risk evidence, and security doctrine

### Finding F: scary tone is not risk evidence

A HIGH-risk article can no longer become HIGH merely because the draft sounds dangerous.

Latest rule:

```text
HIGH risk
-> verified RISK / SAFETY / POLICY evidence required
-> then front-loaded stop/risk gate
-> then bounded procedure
```

### Finding G: hard-coded reusable credentials are an article risk

A public tutorial should not normalize a predictable reusable secret/API key as the default credential.

Operational hard-coded secret literals are blocked; clearly marked dummy/placeholder/prohibition examples are not treated as real defaults.

### Finding H: platform-evasion material must not become growth doctrine

Reference material contained ideas framed around BAN/detection avoidance.

The engine does not learn those as normal marketing optimization.

Round 3 marked such language for review.

---

## Round 4 — attack over-learning from successful reference patterns

### Finding I: ORIGIN is not automatically PAIN

Earlier core logic allowed `ORIGIN` to activate `LIVED_PAIN`.

That creates a hallucination path:

```text
human: "this is why I started"
model: "therefore this must have been painful"
```

Latest-root rule:

```text
LIVED_PAIN requires attested PAIN or FAILURE.
ORIGIN alone stays origin.
```

If no PAIN/FAILURE exists and the user did not explicitly request LIVED_PAIN, the latest layer falls back to RELATABLE instead of manufacturing drama.

### Finding J: contrarianism requires an explicit basis

A CONTRARIAN opening now requires `counterpoint_basis` bound to either:

- verified evidence; or
- human-attested BELIEF / OPINION.

The reference corpus cannot make reverse-taking a default growth trick.

### Finding K: operational platform evasion is stronger than mere discussion

Latest split:

- discussion/rejection of platform-evasion claims -> REVIEW;
- operational instruction teaching evasion/detection avoidance -> BLOCK.

---

## Test architecture finding — the suite itself was stale

A major METEOR finding was outside article logic.

Historical tests imported:

```python
from x_article_engine import build_generation_packet
```

while simultaneously asserting historical schema versions:

```text
v0.4 test expects root == 0.4
v0.5 test expects root == 0.5
v0.7 test expects root == 0.7
v0.8 test expects root == 0.8
```

Those expectations cannot all be true once the root export points to the latest engine.

Fix:

- historical regression tests now import their historical module directly;
- only `test_x_article_engine_latest_root.py` owns the contract for the current root export;
- base/core invariants are pinned to `x_article_engine.core`.

This prevents a new engine layer from silently rewriting the meaning of old regression tests.

---

## CI finding — tests that are not executed are not a gate

v0.3 through v0.8 accumulated tests without a confirmed run in the available environment.

A dedicated workflow has now been added:

`.github/workflows/x-article-engine-meteor.yml`

It runs:

```text
python -m pytest -q tests/test_x_article_engine*.py
```

on X Article Engine pull requests and on relevant changes pushed to main.

**No passing result is claimed in this report yet.**

Historical confirmed result remains only the earlier v0.2 local run: **25 passed**.

The v0.9 PR/CI run is the next adversary.

---

## Current knowledge conflict rules

The candidate now uses these precedence rules:

1. Specificity never overrides evidence binding.
2. Beginner simplicity never hides a material trade-off or risk.
3. One-path guidance starts after the decision that actually matters.
4. Long-form depth never justifies padding.
5. Strong voice never authorizes fabricated certainty, biography, or guarantees.
6. A useful CTA moment never authorizes fake scarcity, fear, or multiple competing actions.
7. `as_of` never turns an unverified claim into current truth.
8. Safety-critical information outranks CTA optimization.
9. Human authorization outranks automation convenience.
10. A neutral origin must not be converted into pain.
11. Contrarianism needs evidence or an attested human position.
12. High-risk warning tone needs verified risk evidence.
13. Strong safety language must not be flattened merely because it contains `必ず` / `絶対`.
14. Platform-evasion operations are not normal article-growth tactics.

---

## Residual risks still intentionally left to `/human`

Deterministic heuristics cannot reliably decide every semantic question.

Residual human checks remain necessary for:

- whether a non-numeric factual paraphrase is truly supported by the cited evidence;
- whether a comparison baseline is actually fair, not merely technically sourced;
- whether an article became over-explained while satisfying terminology rules;
- whether multi-depth writing became forced or overstuffed;
- whether CTA placement is genuinely useful rather than subtly manipulative;
- whether a first-person sentence preserves the writer's actual meaning and tone;
- whether an opinion is being visually laundered as a fact;
- whether a safety warning is proportionate to the verified risk;
- whether an article-specific platform policy or law changed after the evidence date.

Publication therefore remains:

```text
generated draft
-> evidence / METEOR audit
-> /human
-> USER_ONLY external publication
```

---

## Structural debt discovered by METEOR

The attack implementation currently preserves R1 -> R4 as stacked modules so that each round can be inspected and regression-tested independently.

That is useful during the attack phase but **not the desired final architecture**.

Before main promotion, the intended cleanup is:

1. get the dedicated CI suite running;
2. use actual failures as the next METEOR input;
3. stabilize behavior;
4. consolidate R1-R4 into one v0.9 production layer;
5. keep the adversarial tests, not the unnecessary wrapper depth.

In other words: do not let the article engine itself become the kind of SimCity-like support sprawl it is meant to reason about.

## Current verdict

**METEOR still active.**

The candidate is materially harder to fool than v0.8, but it is not yet declared stable or merged to main.
