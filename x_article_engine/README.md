# X Article Engine v0

X Article Engine v0 turns a bounded commercial/article brief into a model-agnostic generation packet, then audits the resulting draft before mandatory `/human` review.

It does **not** publish to X and it does **not** call an LLM by itself.

## Why this exists

Dogfooding long-form X article generation showed a useful split:

- narrative structure, objection handling, pacing, and CTA shaping can be delegated heavily;
- facts, numbers, first-person history, customer outcomes, commercial promises, and risk boundaries cannot be left to unconstrained narrative completion.

The v0 architecture is therefore:

```text
Article brief
  -> Narrative plan
  -> Evidence-bound generation packet
  -> model draft
  -> audit_draft
  -> /human
  -> Publication Bridge / manual X Articles handoff
```

## Inputs

Required:

- `offer`: what is being offered;
- `target`: one concrete buyer/reader;
- `pain`: one pre-purchase problem for this article;
- `primary_info`: first-person material explicitly attested by the human;
- `article_type`: `HOW_TO`, `STORY`, or `CASE_RESULT`;
- `cta`: exactly one desired next action;
- `evidence`: source-bound factual claims.

Optional:

- `topic_mode`: `PROCEDURAL`, `HABIT`, `RELATIONSHIP`, or `BUSINESS` (default `BUSINESS`);
- `opening_mode`: `RELATABLE`, `PROOF_FIRST`, or `CONTRARIAN`.

## Core doctrine

Top-level reader journey:

```text
EMOTION -> LOGIC -> EASY_NEXT_ACTION
```

Article construction:

```text
reader state
-> evidence when available
-> anticipated objection
-> cause
-> solution
-> likely stumbling point
-> one action today
-> one CTA
```

Depth is layered rather than split into separate beginner/advanced articles:

```text
L1: conclusion
L2: why
L3: conditions / exceptions / application
```

A strong human-attested episode may be used inside a HOW_TO article, and explanation may appear inside a STORY article. The selected article type is the dominant structure, not a rigid cage.

## Evidence rules

The engine deliberately does **not** require a quota such as “at least five numbers.” If the evidence contains two useful numbers, use two. If it contains none, the article may have none.

Blocked behavior includes:

- inventing plausible durations, percentages, customer counts, or results;
- inventing first-person chronology, jobs, failures, emotions, or biography;
- turning “scope/total/timing are agreed before start” into a stronger promise such as “no extra charges can ever occur”;
- presenting a newly invented label as established technical terminology;
- using `PROOF_FIRST` or `CASE_RESULT` without the evidence needed to support them.

Derived arithmetic is acceptable only when every operand is verified and the derivation is explicit.

`audit_draft()` v0 detects unbound Arabic-number claims with high-risk units (money, time, percentages, counts) and several strong commercial/guarantee phrases. It is intentionally conservative and incomplete: semantic truth still requires `/human`.

## `/human` is mandatory

`/human` is not an AI-smell remover. It is the boundary where the owner verifies identity-bearing material and adds real point of view.

Before handoff, check:

- Would I actually say this?
- Are all first-person details true and mine?
- Are numbers, prices, timing, results, and scope evidence-bound?
- Did the draft invent emotions, biography, customer outcomes, or certainty?
- Is there only one CTA?
- Were factual/risk boundaries preserved while making the writing sound human?

## Usage / credit policy

**Not part of v0.**

Generation quotas, credits, replenishment cadence, and product tiers are business/deployment policy, not article-quality logic. They should be set only after observing:

- actual model cost per article;
- support/coaching capacity;
- real customer generation frequency;
- revision frequency and `/human` workload;
- abuse/fair-use behavior;
- desired product tiers.

Do not copy a third-party `5,000 credits` or monthly article allowance into the product simply because the reference implementation uses it.

## Publication boundary

This module never performs external publication. X Articles should continue through mandatory `/human` and a user-controlled handoff. Private X APIs, cookies, or session automation are out of scope.
