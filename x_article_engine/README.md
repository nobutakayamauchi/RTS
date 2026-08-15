# X Article Engine v0.2

X Article Engine compiles a bounded commercial/article brief into a model-agnostic generation packet, then audits the resulting draft before mandatory `/human` review.

It does **not** publish to X and it does **not** call an LLM by itself.

## Architecture

```text
Human brief
  + trusted evidence registry
  -> Narrative plan
  -> Evidence-bound generation packet
  -> model draft
  -> audit_draft
  -> /human
  -> Publication Bridge / manual X Articles handoff
```

The split is deliberate:

- narrative structure, objection handling, pacing, and CTA shaping can be delegated heavily;
- facts, numbers, first-person history, customer outcomes, commercial promises, and risk boundaries cannot be left to unconstrained narrative completion.

## Required brief fields

- `offer`: what is being offered;
- `target`: one concrete buyer/reader;
- `pain`: one pre-purchase problem;
- `primary_info`: first-person material explicitly attested by the human;
- `article_type`: `HOW_TO`, `STORY`, or `CASE_RESULT`;
- `cta`: exactly one desired next action;
- `evidence`: factual claims that refer to trusted source IDs.

Optional:

- `topic_mode`: `PROCEDURAL`, `HABIT`, `RELATIONSHIP`, or `BUSINESS`;
- `opening_mode`: `RELATABLE`, `PROOF_FIRST`, or `CONTRARIAN`.

## Trusted evidence boundary

`build_generation_packet()` requires `trusted_source_refs` as a separate keyword-only argument.

```python
packet = build_generation_packet(
    brief,
    trusted_source_refs=trusted_registry,
)
```

This registry must come from a trusted ingestion/verification layer. A user cannot make a claim trusted merely by adding `{"status": "VERIFIED"}` or a fake `source_refs` field to the article brief.

This is an application trust boundary, not cryptographic proof. If an untrusted caller is allowed to control `trusted_source_refs`, evidence safety is defeated. Do not expose that parameter as ordinary end-user input.

## Narrative doctrine

```text
EMOTION -> LOGIC -> EASY_NEXT_ACTION
```

Typical flow:

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

A strong human-attested episode may appear inside a HOW_TO article. Explanation may appear inside a STORY article. The selected type is the dominant structure, not a cage.

## Evidence rules

The engine does not require arbitrary density quotas such as “five numbers.” If evidence contains no useful number, a numberless title is valid.

Automated audit now blocks tested classes of:

- invented Arabic, full-width, and common kanji numeric claims;
- fuzzy quantitative claims such as `何十時間` when not bound;
- selected unbound first-person chronology/role details;
- undeclared or untrusted result sources;
- `CASE_RESULT` without trusted result evidence;
- strengthened commercial promises such as unbound extra-fee or refund claims;
- attempts to override `/human` or publication state from the brief.

Derived arithmetic is not auto-authorized in v0.2. If a computed number is intended for publication, bind that computed claim as verified evidence first.

## Voice must survive safety

Safety is not permission to flatten the article into compliance sludge.

The generation packet explicitly preserves:

- human-attested beliefs and opinions;
- human-attested self-labels such as a personal term already in use;
- direct, confident wording for verified facts;
- vivid examples when they are evidence-bound or human-attested.

Strong opinions are allowed. Strong factual guarantees are not invented.

## `/human` remains mandatory

Automated checks are incomplete by design. Semantic truth, subtle biography inflation, implication, tone, and whether the text is genuinely the owner's voice still require `/human`.

Every packet and audit result remains:

```text
publication_state = BLOCKED_PENDING_HUMAN
publication_authority = USER_ONLY
external_publication_performed = False
```

## DA / counter-DA METEOR

The seven attack vectors and counterexamples are recorded in `DA_METEOR_REPORT.md` and executable regression tests live in `tests/test_x_article_engine_meteor.py`.

The test suite covers:

1. invented numbers;
2. invented biography;
3. fake case results;
4. strengthened commercial promises;
5. “I say it is true” evidence bypass;
6. `/human` bypass;
7. over-sanitization / voice destruction.

## Usage / credit policy

**Not part of the engine.**

Credits, monthly replenishment, generation quotas, coaching limits, and product tiers are business/deployment policy. They should be decided after observing actual model cost, revision rate, `/human` workload, coaching capacity, and customer usage.

## Publication boundary

This module never performs external publication. X Articles continue through mandatory `/human` and a user-controlled handoff. Private X APIs, cookies, or session automation remain out of scope.
