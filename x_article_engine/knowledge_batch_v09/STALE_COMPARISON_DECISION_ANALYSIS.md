# v0.9 Knowledge Intake — Stale Comparison / Decision Archetype

## Source boundary

This analysis comes from a user-supplied public X article about Codex vs Claude Code.

The user explicitly notes that the product roles have since changed substantially. Therefore this source is **not** treated as current product documentation and must not seed present-day facts about Codex, Claude Code, models, plans, pricing, interfaces, capabilities, installation steps, benchmarks, availability, or recommendations.

Any such claim is stale-by-default and requires fresh evidence before reuse.

What survives is the **decision-writing structure**.

## Core lesson

A comparison article should reduce unnecessary migration anxiety, not manufacture a winner.

Useful progression:

```text
reader anxiety / forced-choice feeling
-> answer the decision question early
-> explain the meaningful differences
-> translate differences into reader consequences
-> recommend by reader state / existing stack / goal
-> give one default path
-> let the tutorial begin
```

The goal is not "declare Tool A best." The goal is "help this reader make a bounded decision without paying unnecessary switching cost."

## 1. Answer "Do I need to switch?" before the feature dump

A reader comparing two tools often has a more practical question than "which benchmark wins?"

Typical latent questions:

- Do I need to switch from what I already use?
- Do I need another subscription?
- Am I falling behind if I do not adopt the new tool?
- Is the difference meaningful for my actual work?

Useful doctrine:

```text
comparison request
-> identify the decision the reader actually needs to make
-> answer that first
-> then justify it
```

## 2. Switching cost belongs in the comparison

Raw capability is only one axis.

A useful comparison may include:

- existing subscription / account;
- current familiarity;
- available documentation and support;
- migration effort;
- workflow fit;
- specific task advantage;
- risk of changing tools without a meaningful gain.

Do not tell a reader to migrate merely because a new product is fashionable.

## 3. Compare consequences, not labels

Instead of "A is stronger at X," explain what that means for the reader.

```text
verified difference
-> practical consequence
-> which reader / task cares about it
```

A benchmark is not self-explanatory. Both the benchmark result and the relevance claim must stay evidence-bound.

## 4. Recommend by reader state

A useful comparison can map reader states to choices:

```text
already uses ecosystem A -> default A unless there is a material reason to switch
already uses ecosystem B -> default B unless there is a material reason to switch
true beginner -> choose the path with the lowest justified learning/recovery cost
needs both -> use both only if the second tool adds a real capability or operational advantage
```

These are decision patterns, not current product recommendations.

## 5. "One path" and "comparison" are not contradictory

The article demonstrates a useful sequence:

```text
before tutorial: compare enough to choose
inside tutorial: stop comparing and use one path
```

This resolves a tension in the beginner-guide doctrine.

Comparison belongs at the decision boundary. Once a safe choice is made, unnecessary alternatives can be removed from the execution path.

## 6. Hype reduction can be a legitimate angle

A comparison article can earn attention by lowering anxiety rather than increasing it.

Useful framing:

- "You may not need to switch."
- "The new thing is not automatically the right thing for you."
- "Use the tool that matches your existing workflow unless a verified difference matters."

Do not use this as reflexive contrarianism. The calming conclusion must be supported by actual evidence and scope.

## 7. Stale product articles need aggressive freshness handling

This source is especially useful because its product assumptions later became obsolete.

For comparison/tutorial articles, treat these as high-decay fields:

- model names;
- release dates;
- plan inclusion;
- prices;
- operating-system support;
- interface labels;
- installation paths;
- tool forms (desktop/CLI/web/extensions);
- benchmark leadership;
- current recommendation;
- "additional charge" claims;
- time-to-completion promises.

A past verified comparison must not silently become a current comparison.

## 8. Do not preserve stale recommendations as doctrine

The engine may learn the *shape*:

```text
reader state -> choice
```

It must not preserve historical assignments such as:

```text
reader state X -> Tool A
reader state Y -> Tool B
```

Those mappings must be rebuilt from current evidence whenever the article is generated.

## 9. Risky reference patterns for METEOR

This source also contains patterns that should be attacked rather than copied:

- "100%できます";
- fixed completion-time guarantees;
- "保証します";
- sweeping "no need to learn code" claims;
- product/model/version claims without fresh evidence;
- comparison conclusions built from stale benchmark snapshots;
- treating observed UI wording as durable product truth;
- "latest" language that rapidly expires.

## Candidate engine doctrine

```text
COMPARISON_MODE
1. What decision is the reader actually trying to make?
2. What can stay unchanged?
3. What verified differences are material?
4. What are the switching / learning / cost consequences?
5. Which reader states map to which option under current evidence?
6. Pick one execution path.
7. Tutorial begins only after the decision is closed.
```

## BridgePatch implication

This can later help BridgePatch articles that compare:

- manual workflow vs small one-process tool;
- full system replacement vs bounded automation;
- "keep current process" vs "change one step".

The useful message is not "automation wins." It is:

```text
if the current process is good enough, keep it
if one repeated step is causing disproportionate friction, isolate that step
only replace more when the evidence justifies it
```

That keeps the offer from turning into "everything should be automated" marketing.
