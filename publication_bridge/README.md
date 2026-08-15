# Publication Bridge v0

Status: `MANDATORY /human GATE / USER-CONTROLLED HANDOFF / NO AUTO PUBLISHING`

Publication Bridge receives Post Adapter material only after it has passed both evidence review and a dedicated `/human` rewrite/review pass.

```text
POST ADAPTER
-> DRAFT / REVIEW
-> APPROVED_FOR_COPY
-> /human
   -> remove machine/report voice
   -> preserve verified facts, prices, URLs, scope and hard boundaries
   -> record final X/note hashes
-> APPROVED_FOR_HANDOFF
-> PUBLICATION BRIDGE
   -> X: official Web Intent composer
   -> note: copy title / copy body / open official editor
-> USER performs the final platform action
```

Post Adapter output is structured evidence-safe material. It is not assumed to be natural public copy.

See [`HUMAN_STYLE_POLICY.md`](HUMAN_STYLE_POLICY.md) for the mandatory external-copy policy.

## Why this exists

Two independent failure modes matter:

1. a natural-sounding post can invent or strengthen facts;
2. an evidence-safe post can read like machine-generated release notes.

The pipeline therefore keeps them separate:

```text
Evidence Binding = what may be claimed
/human = how a real person would say it
Publication Bridge = how reviewed copy reaches a platform without auto-publishing
```

## Run

First create an evidence-safe Post Adapter bundle:

```bash
python -m post_adapter source.json \
  --out-dir /tmp/post-bundle \
  --review-state APPROVED_FOR_COPY
```

Then run `/human` on each external X/note draft. The rewrite itself is a language/review operation, not a deterministic formatter. Do not mark it passed until the final text satisfies `HUMAN_STYLE_POLICY.md` and the evidence-preservation check.

After the final `/human` text is in `x.md` / `note.md`, record the pass:

```bash
python -m publication_bridge.human_gate /tmp/post-bundle \
  --reviewer /human \
  --evidence-preserved
```

This changes the bundle state to `APPROVED_FOR_HANDOFF` and hashes the exact final X/note copy.

Then generate the handoff UI:

```bash
python -m publication_bridge /tmp/post-bundle \
  --out-dir /tmp/publication-handoff
```

Open:

```text
/tmp/publication-handoff/index.html
```

Generated files:

```text
publication-handoff/
├── handoff.json
└── index.html
```

## Tamper / regression boundary

Publication Bridge compares the exact X/note content against the SHA-256 values recorded after `/human`.

If anything changes after `/human` — even another machine step — handoff fails closed and `/human` must be run again.

This prevents the common failure:

```text
/human PASS
-> later automation silently rewrites copy
-> machine voice reaches the platform
```

## X adapter

For each `/human`-approved X block, v0 creates an official Web Intent URL using:

```text
https://x.com/intent/tweet?text=...
```

The user sees the actual composer and decides whether to post. Publication Bridge stores no X credentials and does not call `POST /2/tweets`.

## note adapter

For the `/human`-approved note draft, the handoff page provides:

- title preview + copy;
- body preview + copy;
- `note.com/new` editor launch.

It does not store a note cookie, scrape a logged-in session, or call a private note endpoint.

## Fail-closed gates

Handoff generation is rejected when any of the following is true:

- `human_review_state` is not exactly `APPROVED_FOR_HANDOFF`;
- `/human` attestation is missing;
- `humanization.mode != /human`;
- `/human` did not explicitly pass evidence preservation;
- X or note was not individually reviewed;
- X/note content changed after the `/human` hash was recorded;
- verification warnings remain;
- the source manifest does not explicitly state `external_publication_performed: false`;
- no supported X/note drafts are present.

## Handoff state

```text
DRAFT
-> REVIEW_REQUIRED
-> APPROVED_FOR_COPY
-> /human
-> APPROVED_FOR_HANDOFF
-> USER OPENS PLATFORM
-> USER PUBLISHES OR SAVES PLATFORM DRAFT
```

v0 never writes `PUBLISHED` itself because it has no publication authority and no external-post verification connector.

## Explicitly forbidden in v0

- bypassing `/human` for external-facing copy;
- treating Post Adapter structural output as final human copy;
- automatic X posting;
- note private/undocumented posting API use;
- browser cookie/session exfiltration;
- OAuth/token vault;
- background scheduling;
- auto-retries that could duplicate posts;
- silently weakening Post Adapter evidence gates;
- using `/human` to fabricate anecdotes, reactions, customer outcomes or stronger claims.

## Extension rule

A future official platform API can be added as a separate adapter. It must not change the reviewed-source contract and must preserve both the evidence gate and mandatory `/human` boundary before any irreversible publication action.
