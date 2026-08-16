# v0.9 Knowledge Intake — Freshness / Supersession / Migration Article

## Source boundary

This analysis is extracted from a user-supplied public X article about a newer way to use Claude/Claude Code from a phone and desktop app.

We are learning **article-writing doctrine for fast-changing products, superseding old guidance, migration, and update communication**, not importing the source article's product facts, feature names, release dates, prices, compatibility claims, performance estimates, availability claims, implementation steps, prompts, or commercial claims as engine truth.

Any claim about Claude, Claude Code, Claude Desktop, Dispatch, Computer Use, connectors, supported platforms, plan requirements, timing, pricing, success rates, or feature parity must separately pass the normal evidence boundary and freshness check before publication.

## Why this source matters

Earlier reference guides taught how to take a reader from confusion to first success. This source adds a different problem:

> The old successful guide can become wrong or inefficient because the product changed.

That creates a new article class:

```text
OLD REALITY
-> WHAT CHANGED
-> WHAT OLD STEP IS NOW UNNECESSARY / DIFFERENT
-> WHO SHOULD MIGRATE
-> NEW SHORTEST SAFE PATH
-> FIRST SUCCESS ON THE NEW PATH
```

The article is useful as an archetype for **supersession**, not just tutorial writing.

## 1. Explicitly tell the reader when old guidance is stale

A strong update article does not pretend that a previous guide is still current if the underlying workflow changed materially.

Useful doctrine:

```text
previous guide / previous reality
-> explicit stale-or-changed notice
-> date/scope of the new reality
-> what changed for the reader
```

Do not say "the old article is obsolete" unless the claim is evidence-bound. Sometimes only one section changed.

Prefer precise labels such as:

- superseded for this path;
- still valid for advanced users;
- no longer the shortest beginner route;
- valid only for version/environment X.

## 2. Use before/after comparison to explain change

The article compares an older workflow against a newer one.

Generalizable structure:

```text
BEFORE
- required action A
- constraint B
- target use C

NOW
- action A may be removed/replaced
- new capability D
- new constraint E
```

This is stronger than saying "the product evolved a lot" because the reader can see exactly what changed for them.

All comparison claims must be date- and scope-bound.

## 3. Separate "new capability" from "new recommended path"

A product gaining a feature does not automatically mean every reader should use it.

The engine should distinguish:

```text
feature exists
!=
feature is recommended for this reader
!=
feature replaces the old path for every user
```

A beginner guide may choose the new easier route while still preserving the advanced route as a valid option when materially relevant.

## 4. Migration articles need a legacy-reader branch

The source explicitly addresses people who followed the older terminal guide.

Useful doctrine:

```text
new reader
-> use current default path

existing reader on old path
-> say whether they must migrate
-> say whether coexistence is safe/possible
-> say what they gain/lose by moving
```

Do not make existing readers redo working setup without a reason.

## 5. Fresh technical content needs claim expiry awareness

Some claims decay faster than others.

Examples of fast-decay claim classes:

- supported operating systems;
- plan eligibility;
- UI labels and menu locations;
- installation commands;
- connector availability;
- model or feature release status;
- pricing;
- experimental/beta status;
- success-rate estimates;
- security restrictions.

For these classes, the engine should treat "verified once" as insufficient for indefinite reuse.

Doctrine:

```text
claim has high change probability
-> preserve verification date
-> re-check before reuse in a fresh article
-> avoid copying a stale operational instruction from old knowledge
```

## 6. A current guide should reduce obsolete cognitive load

If a newer route removes a prerequisite, do not force the reader through the old prerequisite just because it appeared in a successful earlier guide.

Example doctrine:

```text
old path required A -> B -> C
new safe path requires B -> C
=> remove A from the beginner path
```

The engine should optimize for the current reader's shortest valid route, not historical completeness.

## 7. Use the new route to create an early proof-of-success moment

Like the earlier beginner guide, the source moves quickly from setup to one tiny remote task.

Useful pattern:

```text
setup
-> send one bounded instruction
-> observe visible result
-> confirm success
-> only then show broader possibilities
```

This prevents the article from becoming a long feature catalogue before the reader experiences value.

## 8. Feature catalogue should follow a concrete mental model

The article first gives a simple overall flow:

```text
phone instruction
-> PC action
-> result visible to reader
```

Then it explains individual features and connectors.

Doctrine:

> Give the reader one simple system picture before listing capabilities.

Without a mental model, feature lists become memorization.

## 9. "What changed" can be a stronger hook than "what is it"

For a product the audience has already heard about, the information gap may be the delta rather than the definition.

Possible opening modes for update articles:

```text
OLD_GUIDE_IS_STALE
WHAT_CHANGED_SINCE_LAST_TIME
YOU_NO_LONGER_NEED_X
THE_TOOL_NOW_DOES_Y
```

But unfamiliar readers still need the ordinary-language definition shortly afterward.

## 10. Constraints belong after capability proof, but before risky reliance

The source demonstrates a useful sequencing tension:

- show enough capability that the reader understands why the tool matters;
- then state current limitations before the reader relies on the tool for consequential work.

The engine should not bury constraints after the CTA.

For material limitations, prefer:

```text
capability
-> concrete example
-> current limitation / condition
-> safe use boundary
```

## 11. User-estimated performance numbers are not universal facts

The source includes an experiential success-rate estimate.

Doctrine:

- if the writer supplies a first-person estimate, keep it explicitly first-person and scoped;
- do not convert it into a platform-wide benchmark;
- do not reuse it as timeless product knowledge;
- prefer reproducible evidence when the claim materially affects decisions.

## 12. Product evolution creates update debt

A successful old article can become a liability when readers continue finding it after the workflow changes.

Useful editorial doctrine:

```text
new guide published
-> identify superseded old guide
-> add a visible update/superseded notice where possible
-> route readers to current guidance
```

The X Article Engine itself may not have publication-edit authority, but it should surface the need for supersession metadata/handoff.

## 13. CTA continuity can break even inside a strong article

The source's late transition from practical AI-tool onboarding to a very large external marketing seminar block creates a useful adversarial example.

Potential problem:

```text
article problem = how to use current tool workflow
CTA problem = broad AI monetization / marketing seminar
```

The relationship may be real, but the bridge is much wider than the article's immediate mechanism.

METEOR should test:

- Does the CTA feel like the next step of the same problem?
- Is the commercial section proportionate to the editorial value?
- Does a long bonus stack swamp the article's conclusion?
- Does the offer require a new problem statement that should instead be a separate article?

Useful rule candidate:

> The bigger the conceptual jump between article problem and offer, the stronger the bridge explanation must be—or the CTA should be separated.

## 14. "Free bonus volume" can reintroduce AI-smell and cognitive overload

Large enumerations of bonuses, chapters, slides, prompts, and claims can overwhelm the reader even if each item is technically relevant.

METEOR should attack whether a commercial block:

- repeats quantity as a substitute for value;
- creates forced lists;
- overwhelms the single CTA;
- introduces unverified proof claims;
- destroys the mobile reading rhythm;
- becomes a second article appended to the first.

## 15. Strong urgency claims require independent evidence and authority

The source contains deadline, no-replay, and scarcity language in the embedded promotion.

These are not writing doctrine.

If a generated article uses urgency, the exact deadline, availability, capacity, replay policy, or "never again" claim must be supplied and verified by the offer owner.

The engine must not invent urgency to improve conversion.

## 16. A current tutorial should expose its time boundary

For fast-changing software, a useful article should tell the reader what date/version/environment it describes.

Possible pattern:

```text
As of YYYY-MM-DD / version X / environment Y
this guide uses path Z.
```

Do not overburden stable articles with dates when freshness is irrelevant.

## 17. New v0.9 candidate: Freshness Gate

Potential packet policy:

```text
for each externally verifiable operational claim:
    classify change_risk = LOW / MEDIUM / HIGH
    if HIGH:
        require verified_at or source freshness
        if stale/unknown -> REVIEW or BLOCK depending consequence
```

High-risk operational instructions with unknown freshness should fail closed.

## 18. New v0.9 candidate: Supersession Metadata

Possible fields:

```text
article_relation:
  mode: NEW | UPDATE | SUPERSEDES | COMPARES
  prior_article_ref: optional
  still_valid_parts: []
  superseded_parts: []
  reader_migration_required: bool/conditional
  freshness_date: date
```

This lets the engine write an update without falsely erasing the old path.

## 19. METEOR targets from this source

Attack these tensions explicitly:

1. **freshness vs evidence reuse** — verified yesterday may be stale today;
2. **simple route vs advanced flexibility** — easier default must not erase material trade-offs;
3. **update hook vs beginner comprehension** — readers may not know the old state;
4. **feature excitement vs current limitations** — capability claims must not outrun safety;
5. **CTA continuity vs monetization ambition** — broad sale can hijack a narrow tutorial;
6. **bonus abundance vs cognitive overload** — more assets can reduce clarity;
7. **urgency vs truth** — deadlines/scarcity cannot be generated from style rules;
8. **old successful content vs current truth** — historical performance is not authority for present instructions;
9. **shortest path vs migration burden** — existing users should not redo setup unnecessarily;
10. **current UI specificity vs decay** — exact menu paths need freshness awareness.

## BridgePatch implication

BridgePatch itself is less exposed to fast-changing UI than a software tutorial, but the doctrine still matters for articles that mention AI tools or platform behavior.

For the current BridgePatch sales article:

- stable first-party pain can remain timeless;
- external software examples should be date/scope bound if they materially matter;
- the core mechanism should not depend on a UI or product feature likely to change;
- if a future BridgePatch workflow changes, a new article should say what changed rather than silently contradicting the old one;
- the CTA should remain the direct continuation of the one-process boundary lesson, not expand into an unrelated general AI offer.
