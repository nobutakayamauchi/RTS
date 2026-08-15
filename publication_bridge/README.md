# Publication Bridge v0

Status: `HUMAN-GATED HANDOFF / NO AUTO PUBLISHING`

Publication Bridge receives an already-reviewed Post Adapter bundle and prepares safe handoff actions for external platforms.

```text
POST ADAPTER
-> DRAFT / REVIEW
-> APPROVED_FOR_COPY
-> PUBLICATION BRIDGE
   -> X: official Web Intent composer
   -> note: copy title / copy body / open official editor
-> USER performs the final platform action
```

## Why this exists

Platform-side draft APIs are not a stable common denominator.

- X's official create-post API publishes immediately, so v0 deliberately does not call it.
- X Web Intent opens a pre-filled composer and keeps the final Post action with the user.
- note's official public route `https://note.com/new` opens the editor, while v0 does not depend on a private posting endpoint.

The durable source of truth is therefore the reviewed bundle and handoff record, not a platform's private draft implementation.

## Run

First create a Post Adapter bundle and explicitly approve it for copy:

```bash
python -m post_adapter source.json \
  --out-dir /tmp/post-bundle \
  --review-state APPROVED_FOR_COPY
```

Then prepare the handoff UI:

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

## X adapter

For each X block, v0 creates an official Web Intent URL using:

```text
https://x.com/intent/tweet?text=...
```

The user sees the actual composer and decides whether to post. Publication Bridge stores no X credentials and does not call `POST /2/tweets`.

## note adapter

The handoff page provides:

- title preview + copy;
- body preview + copy;
- `note.com/new` editor launch.

It does not store a note cookie, scrape a logged-in session, or call a private note endpoint.

## Fail-closed gates

Handoff generation is rejected when:

- `human_review_state` is not `APPROVED_FOR_COPY` / `APPROVED_FOR_HANDOFF`;
- verification warnings remain;
- the source manifest does not explicitly state `external_publication_performed: false`;
- no supported X/note drafts are present.

## Handoff state

```text
DRAFT
-> REVIEW_REQUIRED
-> APPROVED_FOR_COPY
-> APPROVED_FOR_HANDOFF
-> USER OPENS PLATFORM
-> USER PUBLISHES OR SAVES PLATFORM DRAFT
```

v0 never writes `PUBLISHED` itself because it has no publication authority and no external-post verification connector.

## Explicitly forbidden in v0

- automatic X posting;
- note private/undocumented posting API use;
- browser cookie/session exfiltration;
- OAuth/token vault;
- background scheduling;
- auto-retries that could duplicate posts;
- silently weakening Post Adapter evidence gates.

## Extension rule

A future official platform API can be added as a separate adapter. It must not change the reviewed-source contract and must preserve a human approval boundary before any irreversible publication action.
