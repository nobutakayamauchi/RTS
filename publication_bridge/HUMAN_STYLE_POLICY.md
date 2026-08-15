# `/human` External Publication Policy

Status: `MANDATORY BEFORE EXTERNAL HANDOFF`

Post Adapter output is structured evidence-safe material. It is **not** assumed to be natural public copy.

Every external X/note draft MUST pass `/human` before Publication Bridge may hand it to a platform.

## Core invariant

```text
EVIDENCE BINDING decides what may be said.
/human decides how a person would actually say it.
/human MUST NOT create stronger facts.
```

Humanization is not permission to improvise claims.

## Preserve exactly in meaning

Do not strengthen, weaken, invent or silently remove material boundaries involving:

- price / tax treatment;
- product or service scope;
- delivery timing;
- refund/cancellation conditions;
- risk exclusions;
- whether something is live, tested, sold or merely prepared;
- customer/revenue/results claims;
- URLs and contact routes;
- dates when they matter to the claim.

When natural wording conflicts with factual precision, factual precision wins.

## Remove machine/report voice

Public copy should normally avoid raw Post Adapter scaffolding such as:

- `今回確認できたこと`;
- `根拠`;
- `現時点の制約`;
- `Verified changes`;
- one bullet per fact merely because a fact exists;
- equal emphasis on every verified claim;
- repetitive `〜です。〜です。〜です。` endings;
- generic AI transitions such as `つまり`, `重要なのは`, `結論として` when they add no real voice;
- self-congratulatory claims not supported by evidence;
- sterile product-catalog language when a concrete problem can lead instead.

Evidence references belong in the internal source record unless a public citation genuinely helps the reader.

## X `/human`

Prefer:

1. one concrete pain / observation / moment;
2. why the author bothered to make or offer this;
3. only the facts needed for this post;
4. one natural next action.

The post may be imperfect, conversational, short, or slightly asymmetric. Do not force all source facts into the primary post merely because they are verified.

Good signals:

- sounds plausible when read aloud;
- uses contractions/omissions/natural Japanese rhythm where appropriate;
- varies sentence length;
- has an actual point of view;
- CTA does not sound like a banner ad unless that is intentional.

Do not fake typos, slang, emotion, personal experiences, customer reactions or anecdotes that did not occur.

## note `/human`

Prefer a readable article arc instead of a release note:

```text
what kept bothering me / what problem exists
-> what I tried or decided
-> what BridgePatch actually does
-> who it is / is not for
-> price or next step when useful
```

Use headings only when they help reading. Do not expose an internal evidence ledger as article structure by default.

## Final checks

Before recording `/human` PASS:

- read the final text aloud once;
- ask: `Would I actually post this wording from my own account?`;
- remove sentences whose only job is to sound polished;
- verify every price, URL and hard boundary against the evidence-safe source;
- verify no customer/result claim was introduced;
- verify the text does not imply automatic publication or unsupported availability;
- verify each external channel received an actual `/human` pass, not merely a global checkbox.

## State transition

```text
POST_ADAPTER_DRAFT
-> APPROVED_FOR_COPY
-> /human rewrite + factual preservation check
-> humanization output hashes recorded
-> APPROVED_FOR_HANDOFF
-> Publication Bridge
-> USER final platform action
```

Any edit to an X/note draft after the `/human` output hash was recorded invalidates the pass and requires `/human` again.
