# Post Adapter v0 — Scope Frozen

Status: `BUILD_NEXT AFTER SALES-BLOCKER REVIEW`

## Purpose

Turn one verified development/update record into reviewable, platform-shaped publication drafts without requiring the operator to rewrite the same update for every channel.

Post Adapter v0 is **not** an autonomous posting service.

## Core flow

```text
SOURCE UPDATE
    ↓
NORMALIZE
    ↓
EVIDENCE / LINK BINDING
    ↓
PLATFORM TRANSFORM
    ├─ X
    ├─ note
    ├─ GitHub
    └─ Instagram
    ↓
HUMAN REVIEW
    ↓
APPROVED_FOR_COPY
```

No external publication occurs inside v0.

## Input contract

Required:

- `project_name`
- `update_type`
- `summary`
- `facts[]`
- `source_refs[]`
- `audience`
- `call_to_action`

Optional:

- `media_refs[]`
- `before_state`
- `after_state`
- `metrics[]`
- `known_limits[]`
- `links[]`

If factual claims cannot be tied to a supplied source/evidence reference, they must be marked `UNVERIFIED` or omitted from publish-ready output.

## Output contract

Each run produces one bundle:

```text
post_bundle/
├── manifest.json
├── source_summary.md
├── x.md
├── note.md
├── github.md
└── instagram.md
```

### `manifest.json`

Minimum fields:

- bundle id
- project name
- source references
- generation timestamp
- output files
- verification warnings
- human review state

Human review state is one of:

- `DRAFT`
- `REVIEW_REQUIRED`
- `APPROVED_FOR_COPY`
- `REJECTED`

`PUBLISHED` is not a v0 system state because v0 has no connector/API delivery proof.

### X output

Produce:

- a concise primary post;
- optional thread continuation blocks when useful;
- CTA;
- source/link suggestions;
- warning section for claims needing human confirmation.

Do not hard-code a permanent platform character limit into the core contract. Platform constraints may change and belong in a replaceable adapter rule.

### note output

Produce:

- title candidates;
- lead;
- structured body;
- evidence/limitations section when relevant;
- CTA;
- suggested image insertion points when media refs exist.

v0 does not attempt direct note publication.

### GitHub output

Produce a concise development/update record suitable for one of:

- release note;
- project update;
- README/current-status section;
- PR/issue context.

The adapter must not modify a repository by itself.

### Instagram output

Produce:

- caption;
- opening hook;
- carousel/reel outline when media refs support it;
- alt-text suggestions;
- CTA;
- claim-verification warnings.

v0 does not attempt direct Instagram publication.

## Hard boundaries

Out of scope for v0:

- direct X API posting;
- direct Instagram API posting;
- note automation;
- OAuth or token vault;
- account management;
- scheduling;
- engagement analytics;
- auto-replies;
- bulk campaigns;
- paid promotion;
- automated image generation;
- autonomous publication;
- scraping private or gated content.

These are future adapter capabilities only after the transformation core proves useful.

## Why direct posting is killed in v0

The useful invariant is:

> One source update can be transformed into channel-appropriate drafts with traceable claims and one human approval point.

API integration is not required to prove that invariant. It adds credential, account, platform-policy, failure-recovery, and delivery-evidence concerns. note also does not currently expose an official public posting API, so a universal direct-publish abstraction would be false at v0.

## Safety / evidence rules

1. No fabricated metrics, release state, customer result, deployment state, or availability claim.
2. `code exists` must not be transformed into `feature is deployed` without runtime/deployment evidence.
3. Planned work and completed work must remain distinguishable.
4. A missing critical source reference blocks `APPROVED_FOR_COPY` unless a human explicitly converts the claim to a non-factual/opinion statement.
5. Human approval is required before any output is copied to a public channel.
6. Secrets, customer private data, credentials, and non-public operational identifiers are excluded from generated publication drafts by default.

## Definition of Done

v0 is complete when all of the following are demonstrated on at least one real development update fixture:

1. One normalized input produces all four channel outputs.
2. Every factual claim is traceable to an input fact/source reference or visibly marked unverified.
3. Planned/completed/deployed distinctions survive transformation.
4. Missing evidence fails closed instead of becoming a confident public claim.
5. The four channel outputs are meaningfully different rather than identical text with renamed headings.
6. Human review state is recorded.
7. No external post is created by the test run.
8. The adapter can add a fifth channel without rewriting the normalized source contract.

## Build order

```text
P0 schema + fixture
P1 normalizer
P2 evidence/claim binder
P3 X adapter
P4 note adapter
P5 GitHub adapter
P6 Instagram adapter
P7 bundle renderer
P8 validation + human review gate
```

Do not add API publishing before v0 completion.
