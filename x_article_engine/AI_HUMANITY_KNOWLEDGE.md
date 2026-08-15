# X Article Engine — Material-First / Anti-AI-Smell Knowledge

## Source boundary

This knowledge was extracted from a public long-form X article supplied during dogfooding.

We import writing doctrine, not the article's medical examples, third-party revenue results, impression counts, or other factual claims. Any such claim must separately pass the normal evidence boundary before it can appear in generated copy.

## Core lesson

AI-sounding prose is often not a model-style problem. It is a **material problem**.

When the model does not have enough concrete material, it tends to preserve the shape of an article by filling space with:

- abstract nouns;
- generic advice;
- neat but weak lists;
- giant subjects;
- invented labels;
- padded wording;
- summaries that repeat what was already said.

The answer is not simply “sound more human.”

The answer is:

```text
specific target
+ evidence
+ lived primary information
+ real failure
+ proper nouns
+ real objections
+ actual opinion
+ a writing recipe
= material-rich draft
```

Writing rules are the recipe. Evidence and lived knowledge are the ingredients.

## 1. Abstract nouns are not banned — empty abstraction is

Words such as:

- 構造
- 設計
- 本質
- 重要
- 最適化

can be useful.

The failure mode is using them instead of saying what is actually happening.

Bad:

> 全体の構造を理解し、適切に設計することが重要です。

Better:

> 最初に、何が入ってきて、何をして、どこへ出すかを決めます。

If deleting the abstract word removes most of the meaning, the sentence probably did not contain enough material.

## 2. Lists must be earned

Do not manufacture:

> ポイントは3つあります。

just because three items look tidy.

Use a list when:

- the items are genuinely parallel;
- each item is strong enough to deserve independent attention;
- a list is clearer than prose.

If ordinary prose is clearer, use prose.

## 3. Do not hide thin content behind formatting

Long bullet blocks can make a draft look organized while avoiding causal explanation.

The engine should prefer:

```text
claim
-> why
-> example
-> exception
```

when that is what the reader needs.

## 4. Do not end with a generic recap

A final `まとめ` that repeats the article is usually dead weight.

Prefer one of these endings:

- return to the opening pain and show what changed;
- pay off an earlier promise;
- give one action the reader can do now;
- let the offer become the natural next step.

## 5. Avoid giant unsupported subjects

Watch for:

- 多くの人は
- 現代人は
- 誰もが
- みんなが
- 一般的に

These phrases are often used when the real target has not been specified.

Write to the configured reader or describe the observed situation instead.

## 6. Direct language beats reflexive hedging

Do not automatically end claims with:

- 〜ではないでしょうか
- 〜と言えるでしょう

If the sentence is a verified fact, state the fact.

If it is an opinion, mark it as the writer's opinion and say it directly.

If uncertainty is real, keep the uncertainty.

The goal is not false confidence. The goal is to remove automatic cowardly phrasing.

## 7. Do not invent terminology to create authority

The pattern:

> これを○○と呼んでいます。

is prohibited when the label was invented by the model.

A source-originated self-label is different.

For example, if the human explicitly uses `シムシティ化`, the article may preserve it because it is primary information. It should still explain the term on first use if a general reader may not know the reference.

## 8. Compress padded phrases

Prefer:

- `できます`

over
- `することが可能です`

Prefer the shortest natural Japanese that preserves meaning.

## 9. The target changes the material that matters

A broad target produces broad advice.

The target should be specific enough that the engine can decide:

- which pain matters;
- which example matters;
- which objection matters;
- which explanation depth matters;
- which offer bridge feels natural.

Do not add fake specificity when the target is vague. Surface the target problem instead.

## 10. Specificity must be evidence-bound

Concrete writing is not permission to hallucinate.

Use exact numbers only when verified.

Use lived scenes only when attested.

Use proper nouns only when known.

Use direct opinions only when genuinely supplied by the human.

If those ingredients are missing, shorten or narrow the article.

## 11. Five useful ingredient classes

When available, prioritize:

1. exact verified numbers;
2. real failure or frustration;
3. proper nouns and actual tools/products;
4. likely reader objections supplied by the brief or framed clearly as questions;
5. the writer's real opinion, rule, anger, or judgment.

These are not quotas. Do not invent missing classes to complete the set.

## 12. Human review test: “What could only have come from me?”

Before publication, identify the sentences that could not have been produced from generic model averages alone.

They should come from:

- evidence;
- the writer's lived experience;
- a failure;
- a real opinion;
- specific context;
- a real constraint;
- an actual offer.

If almost every sentence could fit anyone, the article is still thin.

## 13. Reader learning test

Ask:

> この読者が「知らなかった」と言える具体的なことを3つ挙げられるか？

This is a diagnostic, not a generation quota.

If there are fewer than three, do **not** fabricate three facts.

Instead:

- narrow the article;
- add genuine material;
- improve the explanation;
- or accept that the article should be shorter.

## BridgePatch implication

The current BridgePatch article should now combine:

```text
attested pain
-> real Vlog-development friction
-> unfamiliar words explained immediately
-> no empty 構造/設計/本質 filler
-> no forced three-point list
-> シムシティ化 only because it is human-originated
-> concrete mechanism
-> one-process rule
-> reader analogy
-> BridgePatch（ブリッジパッチ）
-> exact evidence-bound commercial terms
-> one action / CTA
```

The goal is not to disguise AI usage.

The goal is to prevent the model from replacing missing human material with generic prose.