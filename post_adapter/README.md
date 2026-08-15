# Post Adapter v0

Status: `HUMAN-REVIEWED DRAFT TRANSFORMER / NO EXTERNAL PUBLISHING`

Post Adapter v0 turns one evidence-bound development/update record into channel-shaped drafts for X, note, GitHub, and Instagram.

It does not log in to those services and does not publish anything.

## Why this v0 is thin

The useful core is:

```text
one source update
-> normalize
-> bind factual claims to declared evidence
-> transform by channel
-> human review
-> approved-for-copy output
```

Direct posting, OAuth/token storage, scheduling, analytics, auto-replies, and account management are deliberately excluded. They are not necessary to prove whether the transformation layer saves work and preserves claim quality.

## Source contract

Required top-level fields:

- `project_name`
- `update_type`
- `summary`
- `facts[]`
- `source_refs[]`
- `audience`
- `call_to_action`

A publishable fact has this minimum shape:

```json
{
  "claim": "A bounded factual statement.",
  "status": "VERIFIED",
  "source_ref": "source-001"
}
```

`source_ref` must match an `id` in `source_refs[]`.

A fact that is unverified, or claims to be verified without a declared source binding, is not promoted into the publish-ready fact list. It becomes a human-review warning. If no verified facts survive, generation fails closed.

## Run

From the repository root:

```bash
python -m post_adapter post_adapter/fixtures/example_update.json --out-dir /tmp/post-bundle
```

The included dogfood fixture intentionally contains one unsupported completion claim. The expected result is a generated bundle with `REVIEW_REQUIRED`, while the unsupported claim is excluded from the publish-ready portion of each draft and retained as a warning for the reviewer.

For a fully evidence-bound source, a human may explicitly record:

```bash
python -m post_adapter clean_update.json \
  --out-dir /tmp/post-bundle \
  --review-state APPROVED_FOR_COPY
```

`APPROVED_FOR_COPY` is rejected when verification warnings remain.

## Output

```text
post-bundle/
├── manifest.json
├── source_summary.md
├── x.md
├── note.md
├── github.md
└── instagram.md
```

The manifest always records:

```json
"external_publication_performed": false
```

because v0 has no publication authority or delivery connector.

## Tests

```bash
python -m unittest -v tests.test_post_adapter
```

The tests cover:

- four distinct default channel outputs;
- no external-publication state;
- unsupported-claim exclusion;
- fail-closed missing evidence;
- blocking `APPROVED_FOR_COPY` when warnings remain;
- clean human approval state;
- extension with a fifth adapter without changing the normalized source contract.

## Extension boundary

A new output channel is a renderer registered against the normalized source contract. It must not require the source record to be rewritten around one platform.

The v0 public boundary remains:

> Adapt content; do not publish it.
